"""Sliding-window rate limiter held in process memory. No web-framework imports (see dependencies.py).

Known limits (docs/decisions/0004): counters reset on restart and are per instance.
Replace with a shared store before running more than one instance.
"""

from __future__ import annotations

import ipaddress
import math
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int
    remaining: int


class SlidingWindowRateLimiter:
    def __init__(self, clock: Callable[[], float] = time.monotonic, max_keys: int = 10_000) -> None:
        self._clock = clock
        self._max_keys = max_keys
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window_seconds: float) -> RateLimitResult:
        now = self._clock()
        cutoff = now - window_seconds
        with self._lock:
            if len(self._hits) >= self._max_keys:
                self._purge(cutoff)
            window = self._hits.setdefault(key, deque())
            while window and window[0] <= cutoff:
                window.popleft()
            if len(window) >= limit:
                retry = max(1, math.ceil(window[0] + window_seconds - now))
                return RateLimitResult(False, retry, 0)
            window.append(now)
            return RateLimitResult(True, 0, limit - len(window))

    def _purge(self, cutoff: float) -> None:
        stale = [k for k, w in self._hits.items() if not w or w[-1] <= cutoff]
        for key in stale:
            del self._hits[key]

    def tracked_keys(self) -> int:
        with self._lock:
            return len(self._hits)


def resolve_client_ip(forwarded_for: str, peer: str | None, trust_proxy_headers: bool) -> str:
    """Socket peer, or the last X-Forwarded-For entry when exactly one trusted proxy is configured."""
    if trust_proxy_headers:
        last = forwarded_for.split(",")[-1].strip()
        if last:
            try:
                return str(ipaddress.ip_address(last))
            except ValueError:
                pass  # malformed header: fall back to the socket peer
    return peer or "unknown"
