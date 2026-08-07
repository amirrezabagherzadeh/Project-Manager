from concurrent.futures import ThreadPoolExecutor

import pytest

from app.core.rate_limit import FixedWindowRateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.value = 100.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def test_fixed_window_allows_limit_then_returns_retry_time() -> None:
    clock = FakeClock()
    limiter = FixedWindowRateLimiter(clock)

    assert limiter.check("login:client", limit=2, window_seconds=60).allowed is True
    assert limiter.check("login:client", limit=2, window_seconds=60).allowed is True
    denied = limiter.check("login:client", limit=2, window_seconds=60)

    assert denied.allowed is False
    assert denied.retry_after_seconds == 60

    clock.advance(10.2)
    denied_later = limiter.check("login:client", limit=2, window_seconds=60)
    assert denied_later.allowed is False
    assert denied_later.retry_after_seconds == 50


def test_fixed_window_resets_without_sleep() -> None:
    clock = FakeClock()
    limiter = FixedWindowRateLimiter(clock)
    limiter.check("register:client", limit=1, window_seconds=3600)
    assert limiter.check("register:client", limit=1, window_seconds=3600).allowed is False

    clock.advance(3600)

    assert limiter.check("register:client", limit=1, window_seconds=3600).allowed is True


def test_endpoint_and_client_keys_are_independent() -> None:
    limiter = FixedWindowRateLimiter(lambda: 100.0)

    assert limiter.check("login:client-a", limit=1, window_seconds=60).allowed is True
    assert limiter.check("login:client-a", limit=1, window_seconds=60).allowed is False
    assert limiter.check("login:client-b", limit=1, window_seconds=60).allowed is True
    assert limiter.check("register:client-a", limit=1, window_seconds=60).allowed is True


def test_fixed_window_is_thread_safe() -> None:
    limiter = FixedWindowRateLimiter(lambda: 100.0)

    with ThreadPoolExecutor(max_workers=8) as executor:
        decisions = list(
            executor.map(
                lambda _: limiter.check("login:shared", limit=5, window_seconds=60),
                range(20),
            )
        )

    assert sum(decision.allowed for decision in decisions) == 5


@pytest.mark.parametrize(
    ("limit", "window"),
    [(0, 60), (1, 0), (-1, 60), (1, -1)],
)
def test_invalid_rate_limit_configuration_fails(limit: int, window: int) -> None:
    limiter = FixedWindowRateLimiter()

    with pytest.raises(ValueError, match="positive"):
        limiter.check("key", limit=limit, window_seconds=window)
