"""One-job Ghidra worker. The API process does not import this module.

This process runs on the analysis guest. On the Proxmox backend that is the Linux
guest for ELF. The ARM Mac queues the job and keeps PostgreSQL on loopback.
"""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from noctivis.artifacts import ArtifactStore
from noctivis.store import RecordStore

_SHA256 = re.compile(r"[0-9a-f]{64}")
PINNED_VERSION = "11.4"
_ANALYSIS_TIMEOUT = "60"
_PROCESS_TIMEOUT = 300
_MAX_FUNCTIONS = 5000
_MAX_TEXT = 200_000


class AnalysisError(Exception):
    pass


def run_once(store: RecordStore, artifacts: ArtifactStore) -> bool:
    """Claim one queued job and write its evidence. Returns false when the queue is empty."""
    job = store.claim_analysis_job()
    if job is None:
        return False
    try:
        _analyze(store, artifacts, job)
    except Exception as exc:
        message = str(exc).strip() or exc.__class__.__name__
        store.fail_analysis_job(job["id"], job["investigation_id"], message[:500])
        raise
    return True


def _analyze(store: RecordStore, artifacts: ArtifactStore, job: dict) -> None:
    sha256 = job["sha256"]
    if _SHA256.fullmatch(sha256) is None:
        raise AnalysisError("analysis job has no sha256")
    data = artifacts.read(sha256)
    if not data.startswith(b"\x7fELF"):
        raise AnalysisError("stored sample is not an ELF")
    with tempfile.TemporaryDirectory(prefix="noctivis-ghidra-") as temporary:
        root = Path(temporary).resolve()
        sample = root / f"{sha256}.elf"
        sample.write_bytes(data)
        sample.chmod(0o600)
        output = root / "evidence.json"
        project = root / "project"
        project.mkdir()
        payload = _run_ghidra(sample, output, project, sha256)
    _store_payload(store, job, payload)


def _run_ghidra(sample: Path, output: Path, project: Path, sha256: str) -> dict:
    home = _ghidra_home()
    launcher = (home / "support" / "analyzeHeadless").resolve()
    launcher.relative_to(home)
    if not launcher.is_file():
        raise AnalysisError("GHIDRA_HOME does not contain support/analyzeHeadless")
    script = (Path(__file__).resolve().parent / "ghidra" / "DumpEvidence.java").resolve()
    if not script.is_file() or script.parent.name != "ghidra":
        raise AnalysisError("the Ghidra evidence script is missing")
    for path in (sample, output, project):
        path.resolve().relative_to(sample.parent)
    command = [
        str(launcher),
        str(project),
        "noctivis",
        "-import",
        str(sample),
        "-processor",
        "x86:LE:64:default",
        "-analysisTimeoutPerFile",
        _ANALYSIS_TIMEOUT,
        "-scriptPath",
        str(script.parent),
        "-deleteProject",
        "-postScript",
        script.name,
        str(output),
        sha256,
    ]
    environment = os.environ.copy()
    environment["GHIDRA_HEADLESS_MAXMEM"] = environment.get("GHIDRA_HEADLESS_MAXMEM", "1G")
    java_home = environment.get("JAVA_HOME", "").strip()
    if java_home:
        java_bin = Path(java_home).expanduser() / "bin"
        if not (java_bin / "java").is_file():
            raise AnalysisError("JAVA_HOME does not contain bin/java")
        environment["JAVA_HOME"] = str(Path(java_home).expanduser())
        environment["JAVA_HOME_OVERRIDE"] = environment["JAVA_HOME"]
        environment["PATH"] = str(java_bin) + os.pathsep + environment.get("PATH", "")
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            timeout=_PROCESS_TIMEOUT,
            env=environment,
        )
    except subprocess.TimeoutExpired as exc:
        raise AnalysisError("Ghidra did not finish within 300 seconds") from exc
    if completed.returncode != 0 or not output.is_file():
        combined = (completed.stdout + b"\n" + completed.stderr).decode("utf-8", errors="replace")
        lines = [line.strip() for line in combined.splitlines() if line.strip()]
        useful = [line for line in lines if "ERROR" in line or "Exception" in line]
        tail = (useful[-1] if useful else lines[-1] if lines else "no analyzer output")[:240]
        raise AnalysisError(f"Ghidra exited with status {completed.returncode}: {tail}")
    try:
        payload = json.loads(output.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AnalysisError("Ghidra did not write evidence") from exc
    if not isinstance(payload, dict):
        raise AnalysisError("Ghidra did not write evidence")
    return payload


def _store_payload(store: RecordStore, job: dict, payload: dict) -> None:
    if payload.get("sha256") != job["sha256"] or payload.get("tool") != "ghidra":
        raise AnalysisError("Ghidra evidence cited a different sample")
    version = payload.get("tool_version")
    if not isinstance(version, str) or PINNED_VERSION not in version or len(version) > 80:
        raise AnalysisError("Ghidra evidence did not cite the pinned version")
    functions = payload.get("functions")
    decompilation = payload.get("decompilation")
    if not isinstance(functions, list) or not functions:
        raise AnalysisError("Ghidra returned no functions")
    if len(functions) > _MAX_FUNCTIONS:
        raise AnalysisError("Ghidra returned more functions than this worker stores")
    cleaned = []
    for item in functions:
        if not isinstance(item, dict):
            raise AnalysisError("Ghidra returned a function without a name")
        name = item.get("name")
        entry = item.get("entry")
        if not isinstance(name, str) or not isinstance(entry, str) or not name or len(name) > 500 or len(entry) > 200:
            raise AnalysisError("Ghidra returned a function without a name")
        cleaned.append({"name": name, "entry": entry})
    if not isinstance(decompilation, dict):
        raise AnalysisError("Ghidra returned an empty decompilation")
    text = decompilation.get("text")
    name = decompilation.get("name")
    entry = decompilation.get("entry")
    if not isinstance(text, str) or not text.strip() or len(text) > _MAX_TEXT:
        raise AnalysisError("Ghidra returned an empty decompilation")
    if not isinstance(name, str) or not isinstance(entry, str) or not name:
        raise AnalysisError("Ghidra returned an empty decompilation")
    store.complete_analysis_job(
        job,
        version,
        {"functions": cleaned},
        {"name": name, "entry": entry, "text": text},
    )


def _ghidra_home() -> Path:
    raw = os.environ.get("GHIDRA_HOME", "").strip()
    if not raw:
        raise AnalysisError("GHIDRA_HOME is not set")
    home = Path(raw).expanduser().resolve()
    if not home.is_dir():
        raise AnalysisError("GHIDRA_HOME is not a directory")
    return home
