"""
RateLimiter — simple in-memory sliding-window limiter, keyed by client IP.

In-memory only: fine for a single Tap process. If Tap is ever scaled to
multiple instances behind a load balancer, each instance would track
independent counts -- would need a shared store (e.g. Redis) at that
point. Not a concern for a single-VPS deployment.
"""

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: float):
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._lock = threading.Lock()
        self._requests: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        """Returns True if this request is allowed, False if rate-limited.
        As a side effect, records this request's timestamp if allowed."""
        now = time.monotonic()
        with self._lock:
            q = self._requests[key]
            while q and now - q[0] > self._window_seconds:
                q.popleft()

            if len(q) >= self._max_requests:
                return False

            q.append(now)
            return True
