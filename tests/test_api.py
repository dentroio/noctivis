import os

os.environ["NOCTIVIS_OPERATOR_NAME"] = "operator"
os.environ["NOCTIVIS_OPERATOR_PASSWORD"] = "test operator password"

from fastapi.testclient import TestClient
from main import app

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


def test_execution_denied():
    result = client.post(
        "/api/v1/investigations",
        json={"binary_id": "missing", "objective": "Review input parsing", "dynamic_execution": True},
        headers=auth_headers(),
    )
    assert result.status_code in (403, 404)
