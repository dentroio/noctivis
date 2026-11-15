"""NOCTIVIS proof-of-foundation API. Sample metadata and investigations are stored in PostgreSQL.

The API queues static analysis. It does not launch Ghidra and it does not execute a sample.
"""
import hashlib
import hmac
import os
import secrets
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Response, UploadFile, File
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from noctivis.artifacts import ArtifactStore
from noctivis.connectors import ConnectorError, ModelCallError, chat, validate_llm_config
from noctivis.models import Investigation, InvestigationCreate
from noctivis.registry import CAPABILITIES
from noctivis.store import AnalysisBusy, RecordStore
from noctivis.triage import classify

SESSIONS: dict[str, str] = {}
MAX_UPLOAD = 20 * 1024 * 1024
_bearer = HTTPBearer(auto_error=False)
_operator: tuple[str, str] | None = None


def operator_credentials() -> tuple[str, str]:
    """Name and password for the single local operator. Password comes from the environment."""
    global _operator
    if _operator is None:
        name = os.environ.get("NOCTIVIS_OPERATOR_NAME", "operator").strip() or "operator"
        password = os.environ.get("NOCTIVIS_OPERATOR_PASSWORD")
        if not password:
            password = secrets.token_urlsafe(18)
            print(f"NOCTIVIS operator '{name}' password for this process: {password}", flush=True)
        _operator = (name, password)
    return _operator


def _same(left: str, right: str) -> bool:
    return hmac.compare_digest(hashlib.sha256(left.encode()).digest(), hashlib.sha256(right.encode()).digest())


def require_operator(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Sign in required")
    name = SESSIONS.get(credentials.credentials)
    if name is None:
        raise HTTPException(401, "Sign in required")
    return name


class LoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=1, max_length=200)


class ConnectorBody(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=500)
    enabled: bool = True
    is_default: bool = False
    config: dict


class ConnectorPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    enabled: bool | None = None
    is_default: bool | None = None
    config: dict | None = None


class ConnectorTest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)


def database_url() -> str:
    url = os.environ.get("NOCTIVIS_DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("NOCTIVIS_DATABASE_URL is required")
    return url


def artifact_dir() -> Path:
    raw = os.environ.get("NOCTIVIS_ARTIFACT_DIR", "").strip()
    if not raw:
        raise RuntimeError("NOCTIVIS_ARTIFACT_DIR is required")
    return Path(raw)


def get_artifacts() -> ArtifactStore:
    artifacts = getattr(app.state, "artifacts", None)
    if artifacts is None:
        artifacts = ArtifactStore(artifact_dir())
        app.state.artifacts = artifacts
    return artifacts


def get_store() -> RecordStore:
    store = getattr(app.state, "store", None)
    if store is None or store.closed:
        store = RecordStore(database_url())
        app.state.store = store
    return store


@asynccontextmanager
async def lifespan(api: FastAPI):
    api.state.store = RecordStore(database_url())
    api.state.artifacts = ArtifactStore(artifact_dir())
    try:
        yield
    finally:
        store = getattr(api.state, "store", None)
        if store is not None:
            store.close()


app = FastAPI(title="NOCTIVIS API", version="0.1.0", lifespan=lifespan)


def sample_label(filename: str | None) -> str:
    """Operator-facing name. Display only; never used as a filesystem path."""
    raw = (filename or "sample").replace("\\", "/")
    base = raw.rsplit("/", 1)[-1]
    cleaned = "".join(ch if ch.isprintable() and ch not in "/\\" else "_" for ch in base).strip(" .")
    return (cleaned[:120] or "sample")

operator_credentials()

@app.get("/health")
def health():
    return {"status": "ok", "platform": "noctivis"}

@app.post("/api/v1/auth/login")
def login(body: LoginBody):
    name, password = operator_credentials()
    name_ok = _same(body.username.casefold(), name.casefold())
    password_ok = _same(body.password, password)
    if not (name_ok and password_ok):
        raise HTTPException(401, "Name or password is not valid")
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = name
    return {"access_token": token, "user": {"name": name, "role": "operator"}}

@app.get("/api/v1/auth/me")
def me(operator: str = Depends(require_operator)):
    return {"name": operator, "role": "operator"}

@app.post("/api/v1/auth/logout")
def logout(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)):
    if credentials is not None:
        SESSIONS.pop(credentials.credentials, None)
    return {"status": "signed-out"}

@app.get("/api/v1/capabilities", dependencies=[Depends(require_operator)])
def capabilities():
    return [{"id": c.id, "description": c.description, "tools": c.tools,
             "allows_execution": c.allows_execution} for c in CAPABILITIES.values()]

def _connector_or_422(config: dict) -> dict:
    try:
        return validate_llm_config(config)
    except ConnectorError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/v1/connectors", dependencies=[Depends(require_operator)])
def list_connectors(kind: str = "llm", store: RecordStore = Depends(get_store)):
    if kind != "llm":
        raise HTTPException(404, "Unknown connector kind")
    return store.list_connectors(kind)


@app.post("/api/v1/connectors", status_code=201, dependencies=[Depends(require_operator)])
def create_connector(body: ConnectorBody, store: RecordStore = Depends(get_store)):
    config = _connector_or_422(body.config)
    name = body.name.strip()
    if not name:
        raise HTTPException(422, "Name is required")
    return store.insert_connector({
        "id": str(uuid4()),
        "kind": "llm",
        "name": name,
        "description": body.description.strip(),
        "enabled": body.enabled,
        "is_default": body.is_default,
        "config": config,
    })


@app.patch("/api/v1/connectors/{connector_id}", dependencies=[Depends(require_operator)])
def update_connector(connector_id: str, body: ConnectorPatch, store: RecordStore = Depends(get_store)):
    current = store.get_connector(connector_id)
    if current is None or current["kind"] != "llm":
        raise HTTPException(404, "Unknown connector")
    changes = body.model_dump(exclude_unset=True)
    if "config" in changes:
        changes["config"] = _connector_or_422(changes["config"])
    if "name" in changes and changes["name"] is not None:
        changes["name"] = changes["name"].strip()
    if "description" in changes and changes["description"] is not None:
        changes["description"] = changes["description"].strip()
    updated = store.update_connector(connector_id, changes)
    if updated is None:
        raise HTTPException(404, "Unknown connector")
    return updated


@app.delete("/api/v1/connectors/{connector_id}", dependencies=[Depends(require_operator)])
def delete_connector(connector_id: str, store: RecordStore = Depends(get_store)):
    current = store.get_connector(connector_id)
    if current is None or current["kind"] != "llm":
        raise HTTPException(404, "Unknown connector")
    store.delete_connector(connector_id)
    return {"status": "deleted"}


@app.post("/api/v1/connectors/{connector_id}/test", dependencies=[Depends(require_operator)])
def test_connector(connector_id: str, body: ConnectorTest, store: RecordStore = Depends(get_store)):
    current = store.get_connector(connector_id)
    if current is None or current["kind"] != "llm":
        raise HTTPException(404, "Unknown connector")
    if not current["enabled"]:
        raise HTTPException(409, "This provider is disabled")
    try:
        reply = chat(current["config"], body.prompt)
    except ConnectorError as exc:
        store.mark_connector_checked(connector_id, "error")
        raise HTTPException(422, str(exc)) from exc
    except ModelCallError as exc:
        status = "unreachable" if "unreachable" in str(exc) else "error"
        store.mark_connector_checked(connector_id, status)
        raise HTTPException(502, str(exc)) from exc
    store.mark_connector_checked(connector_id, "connected")
    return {"reply": reply, "connector": store.get_connector(connector_id)}


@app.post("/api/v1/binaries", status_code=201, dependencies=[Depends(require_operator)])
async def upload_binary(
    file: UploadFile = File(...),
    store: RecordStore = Depends(get_store),
    artifacts: ArtifactStore = Depends(get_artifacts),
):
    # Stream to bounded temporary storage. Never execute uploaded content.
    digest = hashlib.sha256()
    total = 0
    fd, name = tempfile.mkstemp(prefix="noctivis-")
    try:
        with os.fdopen(fd, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_UPLOAD:
                    raise HTTPException(413, "Binary exceeds 20 MiB MVP limit")
                digest.update(chunk)
                out.write(chunk)
        metadata = classify(Path(name))
        binary_id = digest.hexdigest()
        artifacts.put(Path(name), binary_id)
        return store.save_binary({
            "id": binary_id,
            "sha256": binary_id,
            "label": sample_label(file.filename),
            **metadata,
        })
    finally:
        Path(name).unlink(missing_ok=True)

@app.get("/api/v1/binaries", dependencies=[Depends(require_operator)])
def list_binaries(store: RecordStore = Depends(get_store)):
    return store.list_binaries()

@app.get("/api/v1/binaries/{binary_id}/content", dependencies=[Depends(require_operator)])
def binary_content(
    binary_id: str,
    store: RecordStore = Depends(get_store),
    artifacts: ArtifactStore = Depends(get_artifacts),
):
    if not store.has_binary(binary_id):
        raise HTTPException(404, "Unknown binary")
    try:
        data = artifacts.read(binary_id)
    except FileNotFoundError:
        raise HTTPException(404, "Stored sample is missing") from None
    except ValueError:
        raise HTTPException(500, "Stored sample failed hash verification") from None
    return Response(content=data, media_type="application/octet-stream")

@app.post("/api/v1/investigations", response_model=Investigation, status_code=201, dependencies=[Depends(require_operator)])
def create_investigation(payload: InvestigationCreate, store: RecordStore = Depends(get_store)):
    if not store.has_binary(payload.binary_id):
        raise HTTPException(404, "Unknown binary")
    if payload.dynamic_execution:
        raise HTTPException(403, "Dynamic execution is disabled in the MVP")
    investigation = Investigation(id=str(uuid4()), **payload.model_dump())
    return store.save_investigation(investigation)

@app.get("/api/v1/investigations", response_model=list[Investigation], dependencies=[Depends(require_operator)])
def list_investigations(store: RecordStore = Depends(get_store)):
    return store.list_investigations()

@app.get("/api/v1/investigations/{investigation_id}", response_model=Investigation, dependencies=[Depends(require_operator)])
def get_investigation(investigation_id: str, store: RecordStore = Depends(get_store)):
    investigation = store.get_investigation(investigation_id)
    if investigation is None:
        raise HTTPException(404, "Investigation not found")
    return investigation


def _require_investigation(store: RecordStore, investigation_id: str) -> Investigation:
    investigation = store.get_investigation(investigation_id)
    if investigation is None:
        raise HTTPException(404, "Investigation not found")
    return investigation


@app.post(
    "/api/v1/investigations/{investigation_id}/analysis",
    status_code=201,
    dependencies=[Depends(require_operator)],
)
def enqueue_analysis(
    investigation_id: str,
    store: RecordStore = Depends(get_store),
    artifacts: ArtifactStore = Depends(get_artifacts),
):
    investigation = _require_investigation(store, investigation_id)
    binary = store.get_binary(investigation.binary_id)
    if binary is None:
        raise HTTPException(404, "Unknown binary")
    if binary["format"] != "ELF":
        raise HTTPException(422, "Static analysis accepts ELF samples")
    try:
        stored = artifacts.path_for(binary["sha256"])
    except ValueError:
        raise HTTPException(500, "Stored sample failed hash verification") from None
    if not stored.is_file():
        raise HTTPException(409, "Stored sample is missing")
    try:
        return store.enqueue_analysis(
            {
                "id": str(uuid4()),
                "investigation_id": investigation.id,
                "binary_id": binary["id"],
                "sha256": binary["sha256"],
            }
        )
    except AnalysisBusy:
        raise HTTPException(409, "Static analysis is already queued or finished for this investigation") from None


@app.get("/api/v1/investigations/{investigation_id}/analysis", dependencies=[Depends(require_operator)])
def get_analysis(investigation_id: str, store: RecordStore = Depends(get_store)):
    _require_investigation(store, investigation_id)
    job = store.latest_analysis_job(investigation_id)
    if job is None:
        raise HTTPException(404, "No analysis job")
    return job


@app.get("/api/v1/investigations/{investigation_id}/evidence", dependencies=[Depends(require_operator)])
def list_evidence(investigation_id: str, store: RecordStore = Depends(get_store)):
    _require_investigation(store, investigation_id)
    return store.list_evidence(investigation_id)
