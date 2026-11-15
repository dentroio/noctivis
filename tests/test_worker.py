import atexit
import hashlib
import os
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql

from noctivis.artifacts import ArtifactStore
from noctivis.models import Investigation
from noctivis.store import RecordStore
from noctivis.worker import run_once

ADMIN_URL = "postgresql://noctivis:test%20database%20password@127.0.0.1:5433/postgres"
DATABASE_NAME = "noctivis_test_ghidra_" + uuid4().hex[:12]
DATABASE_URL = f"postgresql://noctivis:test%20database%20password@127.0.0.1:5433/{DATABASE_NAME}"
FIXTURE = Path(__file__).parent / "fixtures" / "add.o"
GHIDRA_HOME = Path.home() / "Library" / "Application Support" / "noctivis" / "ghidra_11.4.3_PUBLIC"
JAVA_HOME = Path("/opt/homebrew/opt/openjdk@21")


def _admin():
    return psycopg.connect(ADMIN_URL, autocommit=True)


with _admin() as admin:
    admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DATABASE_NAME)))


def _drop_database():
    with _admin() as admin:
        admin.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(DATABASE_NAME)))


atexit.register(_drop_database)


def test_fixture_produces_an_inventory_and_a_decompilation(tmp_path):
    os.environ["GHIDRA_HOME"] = str(GHIDRA_HOME)
    if JAVA_HOME.is_dir():
        os.environ["JAVA_HOME"] = str(JAVA_HOME)
    payload = FIXTURE.read_bytes()
    sha256 = hashlib.sha256(payload).hexdigest()
    assert payload.startswith(b"\x7fELF")
    before = FIXTURE.stat().st_mode
    artifacts = ArtifactStore(tmp_path / "artifacts")
    artifacts.put(FIXTURE, sha256)
    store = RecordStore(DATABASE_URL)
    try:
        store.save_binary(
            {"id": sha256, "sha256": sha256, "label": "add.o", "format": "ELF", "size_bytes": len(payload)}
        )
        investigation = Investigation(
            id=str(uuid4()),
            binary_id=sha256,
            objective="Inventory the fixture",
            max_tool_calls=30,
        )
        store.save_investigation(investigation)
        store.enqueue_analysis(
            {
                "id": str(uuid4()),
                "investigation_id": investigation.id,
                "binary_id": sha256,
                "sha256": sha256,
            }
        )
        assert run_once(store, artifacts) is True
        evidence = store.list_evidence(investigation.id)
        by_kind = {item["kind"]: item for item in evidence}
        assert set(by_kind) == {"function_inventory", "decompilation"}
        for item in evidence:
            assert item["sha256"] == sha256
            assert item["tool"] == "ghidra"
            assert "11.4" in item["tool_version"]
        names = {item["name"] for item in by_kind["function_inventory"]["body"]["functions"]}
        assert {"add", "main"} <= names
        decompiled = by_kind["decompilation"]["body"]
        assert decompiled["name"] == "main"
        assert "add" in decompiled["text"]
        finished = store.get_investigation(investigation.id)
        assert finished is not None
        assert finished.status.value == "completed"
        assert FIXTURE.stat().st_mode == before
    finally:
        store.close()
