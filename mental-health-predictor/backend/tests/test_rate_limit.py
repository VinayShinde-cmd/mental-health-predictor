from app.rate_limit import SlidingWindowRateLimiter, resolve_client_ip


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_allows_up_to_the_limit_then_blocks_with_retry_after():
    clock = FakeClock()
    limiter = SlidingWindowRateLimiter(clock=clock)
    results = [limiter.hit("k", 3, 60) for _ in range(4)]
    assert [r.allowed for r in results] == [True, True, True, False]
    assert results[2].remaining == 0
    assert results[3].retry_after_seconds == 60


def test_window_slides_so_old_hits_expire():
    clock = FakeClock()
    limiter = SlidingWindowRateLimiter(clock=clock)
    for _ in range(2):
        assert limiter.hit("k", 2, 60).allowed
    assert not limiter.hit("k", 2, 60).allowed
    clock.now += 61
    assert limiter.hit("k", 2, 60).allowed


def test_retry_after_reflects_the_oldest_hit():
    clock = FakeClock()
    limiter = SlidingWindowRateLimiter(clock=clock)
    limiter.hit("k", 1, 60)
    clock.now += 45
    blocked = limiter.hit("k", 1, 60)
    assert not blocked.allowed
    assert blocked.retry_after_seconds == 15


def test_keys_are_independent():
    limiter = SlidingWindowRateLimiter(clock=FakeClock())
    assert limiter.hit("a", 1, 60).allowed
    assert not limiter.hit("a", 1, 60).allowed
    assert limiter.hit("b", 1, 60).allowed


def test_blocked_requests_do_not_extend_the_block():
    clock = FakeClock()
    limiter = SlidingWindowRateLimiter(clock=clock)
    limiter.hit("k", 1, 60)
    for _ in range(50):
        limiter.hit("k", 1, 60)
    clock.now += 61
    assert limiter.hit("k", 1, 60).allowed


def test_memory_is_bounded_by_purging_expired_keys():
    clock = FakeClock()
    limiter = SlidingWindowRateLimiter(clock=clock, max_keys=100)
    for i in range(100):
        limiter.hit(f"ip-{i}", 5, 60)
    clock.now += 120
    limiter.hit("fresh", 5, 60)
    assert limiter.tracked_keys() == 1


def test_client_ip_ignores_forwarded_header_unless_trusted():
    assert resolve_client_ip("1.2.3.4", "10.0.0.1", trust_proxy_headers=False) == "10.0.0.1"


def test_client_ip_uses_last_forwarded_entry_when_trusted():
    assert resolve_client_ip("6.6.6.6, 1.2.3.4", "10.0.0.1", trust_proxy_headers=True) == "1.2.3.4"


def test_client_ip_falls_back_to_peer_on_garbage_header():
    assert resolve_client_ip("not-an-ip", "10.0.0.1", trust_proxy_headers=True) == "10.0.0.1"
    assert resolve_client_ip("", None, trust_proxy_headers=True) == "unknown"
