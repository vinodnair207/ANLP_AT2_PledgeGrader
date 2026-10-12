"""Tests for the request limiter that protects the Gemini quota."""
from src.ratelimit import DAILY_MESSAGE, PER_VISITOR_MESSAGE, RequestLimiter


class Clock:
    """Hand driven clock, so that the windows can be tested without waiting."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def make(per_visitor=2, total=3):
    """Builds a limiter with small limits and a controllable clock."""
    clock = Clock()
    return RequestLimiter(per_visitor, 60, total, 86400, clock=clock), clock


def test_visitor_limit_blocks_then_recovers_after_the_window():
    """A third request inside one minute is refused, and allowed again once the minute has passed."""
    limiter, clock = make()
    assert limiter.check("a") is None and limiter.check("a") is None
    assert limiter.check("a") == PER_VISITOR_MESSAGE
    clock.now = 61
    assert limiter.check("a") is None


def test_visitors_are_counted_separately():
    """One visitor reaching the limit does not block another."""
    limiter, _ = make()
    limiter.check("a"), limiter.check("a")
    assert limiter.check("b") is None


def test_total_limit_applies_to_all_visitors_for_the_day():
    """After the total allowance is used, every visitor is refused with the daily message."""
    limiter, clock = make(per_visitor=5, total=3)
    assert [limiter.check(v) for v in "abc"] == [None, None, None]
    assert limiter.check("d") == DAILY_MESSAGE
    clock.now = 86401
    assert limiter.check("d") is None


def test_refused_requests_are_not_recorded():
    """A refused request does not extend the wait for the visitor."""
    limiter, clock = make(per_visitor=1, total=10)
    limiter.check("a")
    clock.now = 30
    assert limiter.check("a") == PER_VISITOR_MESSAGE
    clock.now = 61
    assert limiter.check("a") is None
