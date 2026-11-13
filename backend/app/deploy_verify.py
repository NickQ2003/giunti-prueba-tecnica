"""Verify the public deployment revision without API credentials."""

import json
import os
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def fetch(url):
    with urlopen(url, timeout=10) as response:
        return response.status, response.read(100_000)


def verify(
    base_url, expected_sha, timeout=900, *, fetcher=fetch, clock=time.monotonic, sleep=time.sleep
):
    if not base_url.startswith("https://") or not re.fullmatch(r"[a-f0-9]{40}", expected_sha):
        raise ValueError("invalid deployment URL or commit")
    base_url = base_url.rstrip("/")
    deadline = clock() + timeout
    while clock() < deadline:
        try:
            status, body = fetcher(f"{base_url}/api/version")
            revision = json.loads(body).get("revision") if status == 200 else None
            if revision == expected_sha:
                health_status, health = fetcher(f"{base_url}/api/health")
                home_status, home = fetcher(f"{base_url}/")
                if (
                    health_status == 200
                    and json.loads(health).get("status") == "ok"
                    and home_status == 200
                    and b'id="root"' in home
                ):
                    return True
        except (HTTPError, URLError, TimeoutError, ValueError, TypeError, AttributeError):
            pass
        sleep(min(10, max(0, deadline - clock())))
    return False


if __name__ == "__main__":
    try:
        ok = verify(os.environ.get("PUBLIC_BASE_URL", ""), os.environ.get("HEAD_SHA", ""))
    except ValueError:
        ok = False
    print("Deploy verificado." if ok else "No se pudo confirmar el deploy y el commit esperado.")
    sys.exit(0 if ok else 1)
