from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_root_has_version_and_host():
    body = client.get("/").json()
    assert body["service"] == "cloudops-containers"
    assert "version" in body and "host" in body
