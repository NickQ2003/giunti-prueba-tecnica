from app.deploy_verify import verify

SHA = "a" * 40


def test_validates_revision_and_http_services():
    responses = {
        "/api/version": b'{"revision":"' + SHA.encode() + b'"}',
        "/api/health": b'{"status":"ok"}',
        "/": b'<div id="root"></div>',
    }
    assert verify(
        "https://example.com",
        SHA,
        fetcher=lambda url: (200, responses[url.removeprefix("https://example.com")]),
    )


def test_old_revision_times_out():
    now = [0.0]

    def sleep(seconds):
        now[0] += seconds

    assert not verify(
        "https://example.com",
        SHA,
        timeout=20,
        fetcher=lambda url: (200, b'{"revision":"old"}'),
        clock=lambda: now[0],
        sleep=sleep,
    )


def test_rejects_invalid_revision():
    import pytest

    with pytest.raises(ValueError):
        verify("https://example.com", "latest")
