"""Tests for the HTTP API. The methods are replaced by stubs, so no model, key or network is needed."""
import pytest

pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from src import api, utils  # noqa: E402
from src.ratelimit import RequestLimiter  # noqa: E402

PLEDGE = ("We will reach net zero across Scopes 1, 2 and 3 by 2040, with a 50% cut in absolute emissions "
          "by 2030 against a 2020 baseline. Offsets will only be used for residual emissions.")


class StubArm:
    """Returns a fixed label, or raises, so the API can be tested without real models."""

    def __init__(self, label="net_zero", fail=False):
        self.label, self.fail = label, fail

    def predict(self, text: str) -> dict:
        """Mimics the predict method of a real method."""
        if self.fail:
            raise RuntimeError("stub failure")
        return {"label": self.label, "confidence": 90.0, "explanation": "stub"}


@pytest.fixture
def client(monkeypatch):
    """Builds a client without running the startup step, with only stub methods loaded."""
    monkeypatch.setitem(api.state, "cfg", utils.load_config())
    monkeypatch.setitem(api.state, "arms", {"rules": StubArm(), "climatebert": StubArm()})
    return TestClient(api.app)


def test_health_lists_the_loaded_methods(client):
    """The health route shows which methods are ready."""
    assert client.get("/api/health").json() == {"status": "ok", "methods": ["rules", "climatebert"]}


def test_grade_returns_the_score_checks_and_methods(client):
    """A full pledge scores 100 because the Scope 3 list wording is recognised."""
    body = client.post("/api/grade", json={"text": PLEDGE}).json()
    assert body["score"] == 100 and body["kind"] == "Net zero"
    assert [m["id"] for m in body["methods"]] == ["rules", "climatebert"]
    assert all(c["found"] for c in body["checks"])


def test_grade_warns_about_a_method_that_did_not_load(client):
    """The missing LLM method produces a readable warning for the page."""
    body = client.post("/api/grade", json={"text": PLEDGE}).json()
    assert any("Zero shot LLM is unavailable" in w for w in body["warnings"])


def test_grade_rejects_text_that_is_too_short_or_too_long(client):
    """The length limits return a 400 with a readable message."""
    short = client.post("/api/grade", json={"text": "too short"})
    assert short.status_code == 400 and "at least 20" in short.json()["detail"]
    long = client.post("/api/grade", json={"text": "x" * 2001})
    assert long.status_code == 400 and "under 2,000" in long.json()["detail"]


def test_grade_reports_503_when_every_method_fails(client, monkeypatch):
    """If no method can answer, the user gets a clear message instead of a crash."""
    monkeypatch.setitem(api.state, "arms", {"rules": StubArm(fail=True)})
    response = client.post("/api/grade", json={"text": PLEDGE})
    assert response.status_code == 503 and "No method could grade" in response.json()["detail"]


def test_grade_returns_429_when_the_visitor_limit_is_reached(client, monkeypatch):
    """The third request in a minute is refused with a readable message and a Retry-After header."""
    monkeypatch.setitem(api.state, "limiter", RequestLimiter(2, 60, 100, 86400))
    for _ in range(2):
        assert client.post("/api/grade", json={"text": PLEDGE}).status_code == 200
    response = client.post("/api/grade", json={"text": PLEDGE})
    assert response.status_code == 429 and "Too many requests" in response.json()["detail"]
    assert response.headers["retry-after"] == "60"


def test_invalid_text_does_not_use_up_the_allowance(client, monkeypatch):
    """Rejected input returns 400 and is not counted by the limiter."""
    monkeypatch.setitem(api.state, "limiter", RequestLimiter(1, 60, 100, 86400))
    assert client.post("/api/grade", json={"text": "too short"}).status_code == 400
    assert client.post("/api/grade", json={"text": PLEDGE}).status_code == 200


def test_forwarded_address_identifies_the_visitor(client, monkeypatch):
    """Two visitors behind the same proxy are counted separately through X-Forwarded-For."""
    monkeypatch.setitem(api.state, "limiter", RequestLimiter(1, 60, 100, 86400))
    first = client.post("/api/grade", json={"text": PLEDGE}, headers={"x-forwarded-for": "1.1.1.1"})
    second = client.post("/api/grade", json={"text": PLEDGE}, headers={"x-forwarded-for": "2.2.2.2"})
    again = client.post("/api/grade", json={"text": PLEDGE}, headers={"x-forwarded-for": "1.1.1.1"})
    assert (first.status_code, second.status_code, again.status_code) == (200, 200, 429)
