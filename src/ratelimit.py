"""Request limits that protect the shared Gemini free tier quota of the public web app.

Two limits apply. A per visitor limit stops one person from flooding the app. A total daily limit
keeps the app below the Gemini quota of 500 requests a day, so that the language model method
does not stop working for everyone. State is held in memory, which is sufficient for one server process.
"""
import threading
import time
from collections import deque

PER_VISITOR_MESSAGE = "Too many requests from this connection. Please wait a minute and try again."
DAILY_MESSAGE = "The daily limit for this free demonstration has been reached. Please try again tomorrow."


class RequestLimiter:
    """Sliding window limiter with one window per visitor and one window for all visitors."""

    def __init__(self, per_visitor: int, per_visitor_seconds: float, total: int, total_seconds: float,
                 clock=time.monotonic):
        self.per_visitor, self.per_visitor_seconds = per_visitor, per_visitor_seconds
        self.total, self.total_seconds = total, total_seconds
        self.clock = clock
        self._visitors: dict[str, deque] = {}
        self._all: deque = deque()
        self._lock = threading.Lock()

    @classmethod
    def from_config(cls, cfg: dict) -> "RequestLimiter":
        """Builds a limiter from the api section of config/config.yaml."""
        api = cfg["api"]
        return cls(api["max_requests_per_minute_per_visitor"], 60, api["max_requests_per_day_total"], 86400)

    @staticmethod
    def _drop_old(window: deque, now: float, seconds: float) -> None:
        """Removes the timestamps that fall outside the window."""
        while window and now - window[0] >= seconds:
            window.popleft()

    def check(self, visitor: str):
        """Records one request and returns None, or returns a message and records nothing when a limit is reached."""
        now = self.clock()
        with self._lock:
            self._drop_old(self._all, now, self.total_seconds)
            if len(self._all) >= self.total:
                return DAILY_MESSAGE
            window = self._visitors.setdefault(visitor, deque())
            self._drop_old(window, now, self.per_visitor_seconds)
            if len(window) >= self.per_visitor:
                return PER_VISITOR_MESSAGE
            window.append(now)
            self._all.append(now)
            # Visitors with an empty window are forgotten so that memory does not grow without bound.
            if len(self._visitors) > 1000:
                for key in [k for k, w in self._visitors.items() if not w or now - w[-1] >= self.per_visitor_seconds]:
                    del self._visitors[key]
            return None
