"""NOCTIVIS proof-of-foundation API. In-memory state is not production storage."""
import hashlib
import hmac
import os
import secrets
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from noctivis.models import Investigation, InvestigationCreate
from noctivis.registry import CAPABILITIES
from noctivis.triage import classify

app = FastAPI(title="NOCTIVIS API", version="0.1.0")
INVESTIGATIONS: dict[str, Investigation] = {}
BINARIES: dict[str, dict] = {}
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

@app.post("/api/v1/binaries", status_code=201, dependencies=[Depends(require_operator)])
async def upload_binary(file: UploadFile = File(...)):
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
        BINARIES[binary_id] = {
            "id": binary_id,
            "sha256": binary_id,
            "label": sample_label(file.filename),
            **metadata,
        }
        return BINARIES[binary_id]
    finally:
        Path(name).unlink(missing_ok=True)

@app.get("/api/v1/binaries", dependencies=[Depends(require_operator)])
def list_binaries():
    return list(BINARIES.values())

@app.post("/api/v1/investigations", response_model=Investigation, status_code=201, dependencies=[Depends(require_operator)])
def create_investigation(payload: InvestigationCreate):
    if payload.binary_id not in BINARIES:
        raise HTTPException(404, "Unknown binary")
    if payload.dynamic_execution:
        raise HTTPException(403, "Dynamic execution is disabled in the MVP")
    investigation = Investigation(id=str(uuid4()), **payload.model_dump())
    INVESTIGATIONS[investigation.id] = investigation
    return investigation

@app.get("/api/v1/investigations", response_model=list[Investigation], dependencies=[Depends(require_operator)])
def list_investigations():
    return list(INVESTIGATIONS.values())

@app.get("/api/v1/investigations/{investigation_id}", response_model=Investigation, dependencies=[Depends(require_operator)])
def get_investigation(investigation_id: str):
    if investigation_id not in INVESTIGATIONS:
        raise HTTPException(404, "Investigation not found")
    return INVESTIGATIONS[investigation_id]
