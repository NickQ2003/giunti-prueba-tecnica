from fastapi.testclient import TestClient

from app.main import app


def test_health():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_only_exposes_valid_commit(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "a" * 40)
    assert TestClient(app).get("/api/version").json() == {"revision": "a" * 40}
    monkeypatch.setenv("RENDER_GIT_COMMIT", "secret")
    assert TestClient(app).get("/api/version").json() == {"revision": None}
