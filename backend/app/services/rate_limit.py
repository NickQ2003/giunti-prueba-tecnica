"""Process-wide protection: no client-supplied IP headers are trusted."""

import math
import threading
import time
from collections import deque
from collections.abc import Callable


class RateLimiter:
    def __init__(self, limit: int, window: int, clock: Callable[[], float] = time.monotonic):
        if limit < 1 or window < 1:
            raise ValueError("limit and window must be positive")
        self.limit = limit
        self.window = window
        self.clock = clock
        self._requests: deque[float] = deque()
        self._lock = threading.Lock()

    def allow(self) -> tuple[bool, int]:
        with self._lock:
            now = self.clock()
            while self._requests and now - self._requests[0] >= self.window:
                self._requests.popleft()
            if len(self._requests) >= self.limit:
                return False, max(1, math.ceil(self.window - (now - self._requests[0])))
            self._requests.append(now)
            return True, 0
