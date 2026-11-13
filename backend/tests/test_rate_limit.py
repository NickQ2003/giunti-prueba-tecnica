from fastapi.testclient import TestClient

from app.main import app
from app.services.rate_limit import RateLimiter


def test_window_and_retry_after():
    now = [100.0]
    limiter = RateLimiter(2, 60, clock=lambda: now[0])
    assert limiter.allow() == (True, 0)
    assert limiter.allow() == (True, 0)
    assert limiter.allow() == (False, 60)
    now[0] += 60
    assert limiter.allow() == (True, 0)


def test_api_limit_ignores_spoofed_forwarded_ip(monkeypatch):
    monkeypatch.setattr("app.main.limiter", RateLimiter(1, 60))
    client = TestClient(app)
    assert client.post("/api/process", headers={"X-Forwarded-For": "1.2.3.4"}).status_code == 422
    response = client.post("/api/process", headers={"X-Forwarded-For": "5.6.7.8"})
    assert response.status_code == 429
    assert response.json()["error"]["codigo"] == "rate_limited"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
    assert int(response.headers["Retry-After"]) > 0
    assert client.get("/api/health").status_code == 200
