"""Unit tests for the zero shot LLM arm. Gemini is replaced by a fake client,
so no API key, network access or free tier quota is needed."""
import json

import pandas as pd
import pytest
from google.genai import errors

from src import llm_arm, llm_experiments, main
from src.llm_arm import LLMUnavailableError, ZeroShotLLMArm, quote_in_text
from src.signal_key import signals_for_method

PLEDGE = "Our company will reach net zero by 2040, including Scope 3 emissions."
POINTS = {"target_year": 25, "scope3": 25, "offsets": 25, "milestones": 25}


def answer(label="net_zero", **signals):
    """Builds a JSON reply in the schema that Gemini is asked to follow."""
    body = {"label": label, "explanation": "A net zero pledge."}
    for name in llm_arm.SIGNALS:
        body[name] = signals.get(name, {"present": False, "evidence": ""})
    return json.dumps(body)


class FakeResponse:
    """Stands in for a Gemini response object."""

    def __init__(self, text):
        self.text = text
        self.usage_metadata = None


class FakeClient:
    """Returns queued replies, or raises queued exceptions, in order. Repeats the last reply when the queue ends."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0
        self.models = self

    def generate_content(self, model, contents, config):
        """Mimics client.models.generate_content."""
        self.calls += 1
        reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        if isinstance(reply, Exception):
            raise reply
        return FakeResponse(reply)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    """Skips retry and spacing waits so the tests run instantly."""
    monkeypatch.setattr(llm_arm.time, "sleep", lambda s: None)


def make_cfg(tmp_path):
    """Returns a minimal config with a temporary cache and no request spacing."""
    return {"scoring": POINTS, "seed": 42, "labels": {0: "none", 1: "net_zero", 2: "reduction"},
            "paths": {"predictions_dir": str(tmp_path)},
            "llm": {"model": "fake-model", "min_seconds_between_calls": 0, "max_retries": 3,
                    "cache_path": str(tmp_path / "cache.json")}}


def make_arm(tmp_path, replies):
    """Builds an arm with a fake client."""
    client = FakeClient(replies)
    return ZeroShotLLMArm(make_cfg(tmp_path), client=client), client


def test_output_matches_shared_format(tmp_path):
    """The arm returns the same keys as the other arms, and the explainer example scores 50."""
    arm, _ = make_arm(tmp_path, [answer(target_year={"present": True, "evidence": "by 2040"},
                                        scope3={"present": True, "evidence": "including Scope 3 emissions"})])
    out = arm.predict(PLEDGE)
    assert {"method", "label", "signals", "score", "explanation"} <= out.keys()
    assert out["method"] == "llm" and out["label"] == "net_zero"
    assert out["signals"] == {"target_year": True, "scope3": True, "offsets": False, "milestones": False}
    assert out["score"] == 50


def test_hallucinated_quote_drops_the_signal(tmp_path):
    """A quote that is not in the input removes the signal and is counted."""
    arm, _ = make_arm(tmp_path, [answer(target_year={"present": True, "evidence": "by 2040"},
                                        offsets={"present": True, "evidence": "without using offsets"})])
    out = arm.predict(PLEDGE)
    assert out["signals"]["offsets"] is False and out["score"] == 25
    assert arm.stats["hallucinated_quotes"] == 1


def test_quote_matching_ignores_line_breaks_and_case():
    """Dataset sentences contain line breaks, so matching collapses whitespace."""
    assert quote_in_text("Net zero by 2050", "We target net zero\nby 2050.")
    assert not quote_in_text("", "anything")
    assert not quote_in_text("by 2060", "net zero by 2050")


def test_score_is_zero_when_label_is_none(tmp_path):
    """The shared rule applies even if the model marks a signal on a non target."""
    arm, _ = make_arm(tmp_path, [answer(label="none", target_year={"present": True, "evidence": "by 2040"})])
    assert arm.predict(PLEDGE)["score"] == 0


def test_cache_is_reused_within_and_across_runs(tmp_path):
    """A sentence is sent once; a new arm reads the cache file back."""
    arm, client = make_arm(tmp_path, [answer()])
    arm.predict(PLEDGE)
    arm.predict(PLEDGE)
    assert client.calls == 1
    arm2, client2 = make_arm(tmp_path, [answer()])
    arm2.predict(PLEDGE)
    assert client2.calls == 0


def test_use_cache_false_forces_a_fresh_call(tmp_path):
    """Consistency checks bypass the cache."""
    arm, client = make_arm(tmp_path, [answer()])
    arm.predict(PLEDGE)
    arm.predict(PLEDGE, use_cache=False)
    assert client.calls == 2


def test_malformed_json_is_retried(tmp_path):
    arm, client = make_arm(tmp_path, ["not json", answer()])
    assert arm.predict(PLEDGE)["label"] == "net_zero" and client.calls == 2


def test_rate_limit_is_retried(tmp_path):
    arm, client = make_arm(tmp_path, [errors.ClientError(429, {"error": {"message": "quota"}}), answer()])
    assert arm.predict(PLEDGE)["label"] == "net_zero" and client.calls == 2


def test_rejected_request_fails_at_once(tmp_path):
    """A bad key will not fix itself, so it is not retried."""
    arm, client = make_arm(tmp_path, [errors.ClientError(403, {"error": {"message": "bad key"}}), answer()])
    with pytest.raises(LLMUnavailableError):
        arm.predict(PLEDGE)
    assert client.calls == 1


def test_gives_up_after_max_retries(tmp_path):
    arm, client = make_arm(tmp_path, ["bad"])
    with pytest.raises(LLMUnavailableError):
        arm.predict(PLEDGE)
    assert client.calls == 3


@pytest.mark.parametrize("text", ["", "   ", "\n"])
def test_empty_text_is_rejected(tmp_path, text):
    arm, _ = make_arm(tmp_path, [answer()])
    with pytest.raises(ValueError):
        arm.predict(text)


def test_missing_key_gives_a_readable_error(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(LLMUnavailableError, match="GEMINI_API_KEY"):
        ZeroShotLLMArm(make_cfg(tmp_path))


def test_main_writes_signals_file_that_signal_key_reads(tmp_path, monkeypatch):
    """The test run stores llm_signals.csv in the format src/signal_key.py expects."""
    cfg = make_cfg(tmp_path)
    test = pd.DataFrame({"text": [PLEDGE, "We value nature."], "label": ["net_zero", "none"]})
    arm = ZeroShotLLMArm(cfg, client=FakeClient([answer(target_year={"present": True, "evidence": "by 2040"})]))
    monkeypatch.setattr(main.data_processing, "get_test_set", lambda c: test)
    monkeypatch.setattr(main.model, "get_arms", lambda c, names: {"llm": arm})
    main.evaluate("llm", cfg)
    signals = signals_for_method("llm", [PLEDGE], tmp_path)
    assert bool(signals.loc[0, "target_year"]) and not bool(signals.loc[0, "scope3"])


def test_consistency_reports_full_agreement_for_a_deterministic_model(tmp_path, monkeypatch):
    cfg = make_cfg(tmp_path)
    val = pd.DataFrame({"text": [PLEDGE, "We value nature."], "label": ["net_zero", "none"]})
    monkeypatch.setattr(llm_experiments.data_processing, "load_dataset", lambda c: {"validation": val})
    fake = FakeClient([answer()])
    monkeypatch.setattr(llm_experiments.llm_arm, "ZeroShotLLMArm",
                        lambda c: ZeroShotLLMArm(c, client=fake))
    result = llm_experiments.consistency(cfg, n=2, runs=3)
    assert result["label_agreement"] == 1.0 and fake.calls == 6
    assert (tmp_path / "llm_consistency.json").exists()


def test_retry_delay_follows_googles_suggestion():
    """A rate limit error carries the wait Google asks for; overload errors back off gradually."""
    msg = errors.ClientError(429, {"error": {"message": "Quota exceeded. Please retry in 55.2s."}})
    assert llm_arm.retry_delay(msg, 1) == pytest.approx(56.2)
    overload = errors.ServerError(503, {"error": {"message": "high demand"}})
    assert [llm_arm.retry_delay(overload, a) for a in (1, 2, 3, 5)] == [5, 10, 20, 60]


def test_daily_quota_stops_instead_of_waiting_hours(tmp_path):
    """A 429 asking for a wait of hours means the daily quota is gone, so the arm stops at once."""
    daily = errors.ClientError(429, {"error": {"message": "Quota exceeded. Please retry in 68457.2s."}})
    arm, client = make_arm(tmp_path, [daily, answer()])
    with pytest.raises(LLMUnavailableError, match="Daily free tier quota"):
        arm.predict(PLEDGE)
    assert client.calls == 1


def test_evidence_spans_give_positions_in_the_original_text(tmp_path):
    """The web page highlights the LLM's quotes, so each quote comes with its position."""
    text = "We will reach net zero\nby 2040 across our operations."
    arm, _ = make_arm(tmp_path, [answer(target_year={"present": True, "evidence": "Net zero by 2040"})])
    out = arm.predict(text)
    span = out["evidence_spans"]["target_year"]
    assert text[span["start"]:span["end"]] == span["evidence"] == "net zero\nby 2040"
    assert out["evidence_spans"]["scope3"] is None
    # A cached answer gets the same positions.
    assert arm.predict(text)["evidence_spans"] == out["evidence_spans"]


def test_live_mode_fails_fast_when_gemini_is_rate_limited(tmp_path):
    """The web app must not keep a user waiting for a rate limit; the other methods are shown instead."""
    cfg = make_cfg(tmp_path)
    busy = errors.ClientError(429, {"error": {"message": "Quota exceeded. Please retry in 40s."}})
    client = FakeClient([busy, answer()])
    arm = ZeroShotLLMArm(cfg, client=client, live=True)
    assert arm.min_interval == 0
    with pytest.raises(LLMUnavailableError, match="busy"):
        arm.predict(PLEDGE)
    assert client.calls == 1


def test_live_mode_retries_a_short_overload_once(tmp_path):
    cfg = make_cfg(tmp_path)
    client = FakeClient([errors.ServerError(503, {"error": {"message": "high demand"}}), answer()])
    arm = ZeroShotLLMArm(cfg, client=client, live=True)
    assert arm.predict(PLEDGE)["label"] == "net_zero" and client.calls == 2


def test_prediction_contains_everything_the_app_shows(tmp_path):
    """Label, four signals with quotes and positions, score and explanation."""
    arm, _ = make_arm(tmp_path, [answer(target_year={"present": True, "evidence": "by 2040"})])
    out = arm.predict(PLEDGE)
    assert {"label", "signals", "evidence", "evidence_spans", "score", "explanation"} <= out.keys()
    assert set(out["signals"]) == set(out["evidence"]) == set(out["evidence_spans"]) == set(llm_arm.SIGNALS)


def test_live_mode_stores_nothing_from_the_user(tmp_path):
    """Text pasted into the live app is never written to the cache file or kept for later requests."""
    cfg = make_cfg(tmp_path)
    client = FakeClient([answer()])
    arm = ZeroShotLLMArm(cfg, client=client, live=True)
    arm.predict(PLEDGE)
    arm.predict(PLEDGE)
    assert client.calls == 2
    assert not (tmp_path / "cache.json").exists()
