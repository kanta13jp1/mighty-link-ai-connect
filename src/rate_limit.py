"""Small in-process sliding-window rate limiter for FastAPI routes.

This is an application backstop. Edge protections such as Firebase Hosting,
Cloud Run, Cloud Armor, or CDN controls should remain the first DDoS layer.
"""
from __future__ import annotations

import math
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Optional


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int
    reset_epoch_seconds: int


class SlidingWindowRateLimiter:
    """Thread-safe per-key sliding-window limiter.

    The limiter stores only request timestamps. It is intentionally dependency
    free so the local demo and Cloud Run container can enforce a useful safety
    net without introducing Redis or another managed cache.
    """

    def __init__(self) -> None:
        self._hits: Dict[str, Deque[float]] = {}
        self._lock = threading.Lock()

    def allow(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
        now: Optional[float] = None,
    ) -> RateLimitDecision:
        if limit <= 0:
            return RateLimitDecision(
                allowed=False,
                limit=limit,
                remaining=0,
                retry_after_seconds=max(1, window_seconds),
                reset_epoch_seconds=int(time.time() + max(1, window_seconds)),
            )

        current = time.time() if now is None else now
        cutoff = current - max(1, window_seconds)

        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= limit:
                oldest = hits[0]
                retry_after = max(1, math.ceil((oldest + window_seconds) - current))
                return RateLimitDecision(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    retry_after_seconds=retry_after,
                    reset_epoch_seconds=math.ceil(oldest + window_seconds),
                )

            hits.append(current)
            oldest = hits[0]
            remaining = max(0, limit - len(hits))
            return RateLimitDecision(
                allowed=True,
                limit=limit,
                remaining=remaining,
                retry_after_seconds=0,
                reset_epoch_seconds=math.ceil(oldest + window_seconds),
            )

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


def client_identifier(headers, client_host: Optional[str]) -> str:
    """Return a stable per-client key from proxy headers or socket host."""
    forwarded_for = headers.get("x-forwarded-for", "")
    if forwarded_for:
        first_hop = forwarded_for.split(",", 1)[0].strip()
        if first_hop:
            return first_hop

    real_ip = headers.get("x-real-ip", "").strip()
    if real_ip:
        return real_ip

    return client_host or "unknown"
