from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    assert client.get("/health").json()["status"] == "ok"

def test_capabilities():
    result = client.get("/api/v1/capabilities")
    assert result.status_code == 200
    assert result.json()[0]["id"] == "binary-intelligence"

def test_binary_and_investigation():
    binary = client.post("/api/v1/binaries", files={"file": ("sample.elf", b"\x7fELFtest")})
    assert binary.status_code == 201
    assert binary.json()["format"] == "ELF"
    investigation = client.post("/api/v1/investigations", json={"binary_id": binary.json()["id"], "objective": "Review input parsing"})
    assert investigation.status_code == 201
    assert investigation.json()["status"] == "created"

def test_execution_denied():
    result = client.post("/api/v1/investigations", json={"binary_id": "missing", "objective": "Review input parsing", "dynamic_execution": True})
    assert result.status_code in (403, 404)
