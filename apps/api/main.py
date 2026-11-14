"""NOCTIVIS proof-of-foundation API. In-memory state is not production storage."""
import hashlib
import os
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, UploadFile, File
from noctivis.models import Investigation, InvestigationCreate
from noctivis.registry import CAPABILITIES
from noctivis.triage import classify

app = FastAPI(title="NOCTIVIS API", version="0.1.0")
INVESTIGATIONS: dict[str, Investigation] = {}
BINARIES: dict[str, dict] = {}
MAX_UPLOAD = 20 * 1024 * 1024


def sample_label(filename: str | None) -> str:
    """Operator-facing name. Display only; never used as a filesystem path."""
    raw = (filename or "sample").replace("\\", "/")
    base = raw.rsplit("/", 1)[-1]
    cleaned = "".join(ch if ch.isprintable() and ch not in "/\\" else "_" for ch in base).strip(" .")
    return (cleaned[:120] or "sample")

@app.get("/health")
def health():
    return {"status": "ok", "platform": "noctivis"}

@app.get("/api/v1/capabilities")
def capabilities():
    return [{"id": c.id, "description": c.description, "tools": c.tools,
             "allows_execution": c.allows_execution} for c in CAPABILITIES.values()]

@app.post("/api/v1/binaries", status_code=201)
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

@app.get("/api/v1/binaries")
def list_binaries():
    return list(BINARIES.values())

@app.post("/api/v1/investigations", response_model=Investigation, status_code=201)
def create_investigation(payload: InvestigationCreate):
    if payload.binary_id not in BINARIES:
        raise HTTPException(404, "Unknown binary")
    if payload.dynamic_execution:
        raise HTTPException(403, "Dynamic execution is disabled in the MVP")
    investigation = Investigation(id=str(uuid4()), **payload.model_dump())
    INVESTIGATIONS[investigation.id] = investigation
    return investigation

@app.get("/api/v1/investigations", response_model=list[Investigation])
def list_investigations():
    return list(INVESTIGATIONS.values())

@app.get("/api/v1/investigations/{investigation_id}", response_model=Investigation)
def get_investigation(investigation_id: str):
    if investigation_id not in INVESTIGATIONS:
        raise HTTPException(404, "Investigation not found")
    return INVESTIGATIONS[investigation_id]
