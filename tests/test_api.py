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

def test_lists_records_and_strips_path_from_label():
    binary = client.post("/api/v1/binaries", files={"file": ("../secret.elf", b"\x7fELFtest")})
    assert binary.status_code == 201
    body = binary.json()
    assert body["label"] == "secret.elf"
    assert "/" not in body["label"]
    listed = client.get("/api/v1/binaries")
    assert listed.status_code == 200
    assert any(item["id"] == body["id"] for item in listed.json())
    investigation = client.post(
        "/api/v1/investigations",
        json={"binary_id": body["id"], "objective": "Review input parsing"},
    )
    assert investigation.status_code == 201
    investigations = client.get("/api/v1/investigations")
    assert investigations.status_code == 200
    assert any(item["id"] == investigation.json()["id"] for item in investigations.json())


def test_execution_denied():
    result = client.post("/api/v1/investigations", json={"binary_id": "missing", "objective": "Review input parsing", "dynamic_execution": True})
    assert result.status_code in (403, 404)
