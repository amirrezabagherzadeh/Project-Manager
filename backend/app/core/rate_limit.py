from collections.abc import Callable
from dataclasses import dataclass
from math import ceil
from threading import Lock
from time import monotonic
from typing import Protocol


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int


class RateLimiter(Protocol):
    def check(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision: ...


@dataclass
class _Window:
    started_at: float
    count: int


class FixedWindowRateLimiter:
    def __init__(self, clock: Callable[[], float] = monotonic) -> None:
        self._clock = clock
        self._windows: dict[str, _Window] = {}
        self._lock = Lock()

    def check(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        if limit < 1 or window_seconds < 1:
            raise ValueError("Rate limit and window must be positive")

        now = self._clock()
        with self._lock:
            current = self._windows.get(key)
            if current is None or now - current.started_at >= window_seconds:
                self._windows[key] = _Window(started_at=now, count=1)
                self._prune_expired(now, window_seconds)
                return RateLimitDecision(allowed=True, retry_after_seconds=0)

            elapsed = now - current.started_at
            retry_after = max(1, ceil(window_seconds - elapsed))
            if current.count >= limit:
                return RateLimitDecision(
                    allowed=False,
                    retry_after_seconds=retry_after,
                )

            current.count += 1
            return RateLimitDecision(allowed=True, retry_after_seconds=0)

    def _prune_expired(self, now: float, current_window_seconds: int) -> None:
        if len(self._windows) < 1000:
            return
        expired_keys = [
            key
            for key, window in self._windows.items()
            if now - window.started_at >= current_window_seconds
        ]
        for key in expired_keys:
            self._windows.pop(key, None)
