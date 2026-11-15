import atexit
import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql

os.environ["NOCTIVIS_OPERATOR_NAME"] = "operator"
os.environ["NOCTIVIS_OPERATOR_PASSWORD"] = "test operator password"

ADMIN_URL = "postgresql://noctivis:test%20database%20password@127.0.0.1:5433/postgres"
DATABASE_NAME = "noctivis_test_" + uuid4().hex[:12]
os.environ["NOCTIVIS_DATABASE_URL"] = (
    f"postgresql://noctivis:test%20database%20password@127.0.0.1:5433/{DATABASE_NAME}"
)
ARTIFACT_DIR = Path(tempfile.mkdtemp(prefix="noctivis-artifacts-"))
os.environ["NOCTIVIS_ARTIFACT_DIR"] = str(ARTIFACT_DIR)


def _admin():
    return psycopg.connect(ADMIN_URL, autocommit=True)


with _admin() as admin:
    admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DATABASE_NAME)))


def _drop_database():
    with _admin() as admin:
        admin.execute(
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(DATABASE_NAME))
        )
    shutil.rmtree(ARTIFACT_DIR, ignore_errors=True)


atexit.register(_drop_database)

from fastapi.testclient import TestClient
from main import MAX_UPLOAD, app
from noctivis.artifacts import ArtifactStore
from noctivis.store import RecordStore

client = TestClient(app)
PASSWORD = "test operator password"


def auth_headers() -> dict[str, str]:
    result = client.post("/api/v1/auth/login", json={"username": "operator", "password": PASSWORD})
    assert result.status_code == 200
    return {"Authorization": f"Bearer {result.json()['access_token']}"}


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_login_rejects_a_wrong_password():
    result = client.post("/api/v1/auth/login", json={"username": "operator", "password": "wrong password"})
    assert result.status_code == 401
    blocked = client.get("/api/v1/capabilities")
    assert blocked.status_code == 401


def test_capabilities():
    result = client.get("/api/v1/capabilities", headers=auth_headers())
    assert result.status_code == 200
    assert result.json()[0]["id"] == "binary-intelligence"


def test_binary_and_investigation():
    headers = auth_headers()
    binary = client.post("/api/v1/binaries", files={"file": ("sample.elf", b"\x7fELFtest")}, headers=headers)
    assert binary.status_code == 201
    assert binary.json()["format"] == "ELF"
    investigation = client.post(
        "/api/v1/investigations",
        json={"binary_id": binary.json()["id"], "objective": "Review input parsing"},
        headers=headers,
    )
    assert investigation.status_code == 201
    assert investigation.json()["status"] == "created"


def test_lists_records_and_strips_path_from_label():
    headers = auth_headers()
    binary = client.post("/api/v1/binaries", files={"file": ("../secret.elf", b"\x7fELFtest")}, headers=headers)
    assert binary.status_code == 201
    body = binary.json()
    assert body["label"] == "secret.elf"
    assert "/" not in body["label"]
    listed = client.get("/api/v1/binaries", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == body["id"] for item in listed.json())
    investigation = client.post(
        "/api/v1/investigations",
        json={"binary_id": body["id"], "objective": "Review input parsing"},
        headers=headers,
    )
    assert investigation.status_code == 201
    investigations = client.get("/api/v1/investigations", headers=headers)
    assert investigations.status_code == 200
    assert any(item["id"] == investigation.json()["id"] for item in investigations.json())


def test_investigation_survives_a_new_database_connection():
    headers = auth_headers()
    binary = client.post("/api/v1/binaries", files={"file": ("sample.elf", b"\x7fELFtest")}, headers=headers)
    assert binary.status_code == 201
    created = client.post(
        "/api/v1/investigations",
        json={"binary_id": binary.json()["id"], "objective": "Review input parsing"},
        headers=headers,
    )
    assert created.status_code == 201
    investigation_id = created.json()["id"]
    app.state.store.close()
    app.state.store = RecordStore(os.environ["NOCTIVIS_DATABASE_URL"])
    loaded = client.get(f"/api/v1/investigations/{investigation_id}", headers=headers)
    assert loaded.status_code == 200
    assert loaded.json()["id"] == investigation_id
    assert loaded.json()["objective"] == "Review input parsing"
    assert loaded.json()["binary_id"] == binary.json()["id"]


def test_execution_denied():
    result = client.post(
        "/api/v1/investigations",
        json={"binary_id": "missing", "objective": "Review input parsing", "dynamic_execution": True},
        headers=auth_headers(),
    )
    assert result.status_code in (403, 404)


def test_stored_sample_round_trips_and_matches_its_hash():
    headers = auth_headers()
    payload = b"\x7fELFroundtrip"
    binary = client.post("/api/v1/binaries", files={"file": ("roundtrip.elf", payload)}, headers=headers)
    assert binary.status_code == 201
    binary_id = binary.json()["id"]
    assert binary_id == hashlib.sha256(payload).hexdigest()
    content = client.get(f"/api/v1/binaries/{binary_id}/content", headers=headers)
    assert content.status_code == 200
    assert content.content == payload
    assert hashlib.sha256(content.content).hexdigest() == binary_id
    assert ArtifactStore(ARTIFACT_DIR).read(binary_id) == payload
    blocked = client.get(f"/api/v1/binaries/{binary_id}/content")
    assert blocked.status_code == 401


def test_oversized_upload_is_not_stored(tmp_path):
    headers = auth_headers()
    payload = tmp_path / "big.elf"
    with payload.open("wb") as out:
        out.write(b"\x7fELF")
        out.seek(MAX_UPLOAD)
        out.write(b"x")
    digest = hashlib.sha256()
    with payload.open("rb") as incoming:
        while chunk := incoming.read(1024 * 1024):
            digest.update(chunk)
    with payload.open("rb") as incoming:
        result = client.post("/api/v1/binaries", files={"file": ("big.elf", incoming)}, headers=headers)
    assert result.status_code == 413
    assert not ArtifactStore(ARTIFACT_DIR).path_for(digest.hexdigest()).exists()


def test_model_provider_round_trip_and_rejects_a_stored_key():
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    seen: dict[str, bytes] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            seen["body"] = self.rfile.read(length)
            seen["path"] = self.path.encode()
            payload = json.dumps({"message": {"content": "model reply"}}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, _format, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    headers = auth_headers()
    try:
        port = server.server_address[1]
        created = client.post(
            "/api/v1/connectors",
            json={
                "name": "Local model",
                "description": "Loopback test",
                "is_default": True,
                "config": {"provider": "local", "model": "llama2", "base_url": f"http://127.0.0.1:{port}"},
            },
            headers=headers,
        )
        assert created.status_code == 201, created.text
        connector_id = created.json()["id"]
        second = client.post(
            "/api/v1/connectors",
            json={
                "name": "Other local",
                "is_default": True,
                "config": {"provider": "local", "model": "llama2", "base_url": f"http://127.0.0.1:{port}"},
            },
            headers=headers,
        )
        assert second.status_code == 201
        listed = client.get("/api/v1/connectors?kind=llm", headers=headers)
        defaults = [item for item in listed.json() if item["is_default"]]
        assert len(defaults) == 1
        assert defaults[0]["id"] == second.json()["id"]
        leaked = client.post(
            "/api/v1/connectors",
            json={
                "name": "Hosted",
                "config": {
                    "provider": "hosted",
                    "model": "gpt",
                    "base_url": "https://example.com",
                    "api_key": "test model key",
                },
            },
            headers=headers,
        )
        assert leaked.status_code == 422
        remote = client.post(
            "/api/v1/connectors",
            json={
                "name": "Remote local",
                "config": {"provider": "local", "model": "llama2", "base_url": "http://example.com"},
            },
            headers=headers,
        )
        assert remote.status_code == 422
        blocked = client.get("/api/v1/connectors?kind=llm")
        assert blocked.status_code == 401
        tested = client.post(
            f"/api/v1/connectors/{connector_id}/test",
            json={"prompt": "Say hello"},
            headers=headers,
        )
        assert tested.status_code == 200, tested.text
        assert tested.json()["reply"] == "model reply"
        assert b"Say hello" in seen["body"]
        assert b"\x7fELF" not in seen["body"]
        assert seen["path"] == b"/api/chat"
    finally:
        server.shutdown()


def test_analysis_is_queued_without_launching_ghidra(monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("the API launched a process")

    monkeypatch.setattr(subprocess, "Popen", fail)
    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(os, "system", fail)
    headers = auth_headers()
    binary = client.post("/api/v1/binaries", files={"file": ("sample.elf", b"\x7fELFtest")}, headers=headers)
    assert binary.status_code == 201
    created = client.post(
        "/api/v1/investigations",
        json={"binary_id": binary.json()["id"], "objective": "Inventory the functions"},
        headers=headers,
    )
    assert created.status_code == 201
    investigation_id = created.json()["id"]
    queued = client.post(f"/api/v1/investigations/{investigation_id}/analysis", headers=headers)
    assert queued.status_code == 201, queued.text
    assert queued.json()["status"] == "queued"
    assert queued.json()["sha256"] == binary.json()["sha256"]
    loaded = client.get(f"/api/v1/investigations/{investigation_id}", headers=headers)
    assert loaded.status_code == 200
    assert loaded.json()["status"] == "queued"
    evidence = client.get(f"/api/v1/investigations/{investigation_id}/evidence", headers=headers)
    assert evidence.status_code == 200
    assert evidence.json() == []
    again = client.post(f"/api/v1/investigations/{investigation_id}/analysis", headers=headers)
    assert again.status_code == 409
    blocked = client.post(f"/api/v1/investigations/{investigation_id}/analysis")
    assert blocked.status_code == 401
    other = client.post("/api/v1/binaries", files={"file": ("note.txt", b"not a binary")}, headers=headers)
    assert other.status_code == 201
    plain = client.post(
        "/api/v1/investigations",
        json={"binary_id": other.json()["id"], "objective": "Inventory the functions"},
        headers=headers,
    )
    assert plain.status_code == 201
    rejected = client.post(f"/api/v1/investigations/{plain.json()['id']}/analysis", headers=headers)
    assert rejected.status_code == 422
    source = (Path(__file__).parents[1] / "apps" / "api" / "main.py").read_text()
    assert "subprocess" not in source
    assert "analyzeHeadless" not in source


def test_upload_does_not_spawn_a_process(monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("sample execution was attempted")

    monkeypatch.setattr(subprocess, "Popen", fail)
    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(os, "system", fail)
    headers = auth_headers()
    result = client.post("/api/v1/binaries", files={"file": ("sample.elf", b"\x7fELFtest")}, headers=headers)
    assert result.status_code == 201
