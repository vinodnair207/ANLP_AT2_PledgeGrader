"""Unit tests for the evidence finder and the grading response builder."""
import json
from pathlib import Path

import pytest

from src import evidence, grading, rules

CFG = {"scoring": {"target_year": 25, "scope3": 25, "offsets": 25, "milestones": 25}}
SAMPLE = "Our company will reach net zero by 2040, including Scope 3 emissions."
STRONG = ("We will reach net zero including Scope 3 by 2050, with a 50% cut in emissions by 2030. "
          "Offsets will only be used for residual emissions, through verified carbon removals.")


class FakeArm:
    """Test double with the shared predict interface."""

    def __init__(self, label="net_zero", confidence=None, explanation="Reason.", fail=False):
        self.label, self.confidence, self.explanation, self.fail = label, confidence, explanation, fail

    def predict(self, text):
        if self.fail:
            raise RuntimeError("provider down")
        out = {"label": self.label, "explanation": self.explanation}
        if self.confidence is not None:
            out["confidence"] = self.confidence
        return out


def arms(rules_label="net_zero", bert="net_zero", llm="net_zero"):
    """Builds the three fake arms with the given labels."""
    return {"rules": FakeArm(rules_label), "climatebert": FakeArm(bert, confidence=93.4),
            "llm": FakeArm(llm, explanation="A dated net zero target.")}


# ----- evidence finder ------------------------------------------------------------

def test_evidence_positions_match_the_sample_contract():
    spans = evidence.find_evidence(SAMPLE)
    assert (spans["year"]["start"], spans["year"]["end"], spans["year"]["evidence"]) == (32, 39, "by 2040")
    assert SAMPLE[spans["scope3"]["start"]:spans["scope3"]["end"]] == "Scope 3"
    assert spans["offsets"] is None and spans["milestones"] is None


@pytest.mark.parametrize("text", [SAMPLE, STRONG, "We care about the planet.", "Cut emissions 30% by 2028 and reach "
                                  "net zero by 2040 using offsets, covering our value chain."])
def test_evidence_found_exactly_when_the_rule_signal_is_present(text):
    signals, spans = rules.detect_signals(text), evidence.find_evidence(text)
    for signal, check_id in evidence.CHECK_IDS.items():
        assert signals[signal] == (spans[check_id] is not None)


def test_year_prefers_latest_year_and_milestone_avoids_it():
    spans = evidence.find_evidence("A 50% cut by 2030 and net zero by 2050.")
    assert spans["year"]["evidence"] == "by 2050"
    assert spans["milestones"]["evidence"] == "by 2030"


def test_target_phrase():
    assert evidence.find_target_phrase(SAMPLE, "net_zero").lower() == "net zero"
    assert evidence.find_target_phrase(SAMPLE, "none") is None


# ----- grading ---------------------------------------------------------------------

def test_sample_pledge_scores_fifty_with_three_methods():
    out = grading.grade_pledge(SAMPLE, arms(), CFG)
    assert out["score"] == 50 and out["kind"] == "Net zero"
    assert out["summary"].startswith("Half supported. It names a year and covers the whole supply chain")
    assert [c["id"] for c in out["checks"]] == ["year", "scope3", "offsets", "milestones"]
    assert [m["id"] for m in out["methods"]] == ["rules", "climatebert", "llm"]
    assert out["warnings"] == []


def test_strong_pledge_scores_one_hundred():
    out = grading.grade_pledge(STRONG, arms(), CFG)
    assert out["score"] == 100 and out["summary"].startswith("Fully supported.")


def test_method_blocks_carry_confidence_and_quote():
    blocks = {m["id"]: m for m in grading.grade_pledge(SAMPLE, arms(), CFG)["methods"]}
    assert blocks["climatebert"]["confidence"] == 93 and blocks["rules"]["confidence"] is None
    assert blocks["llm"]["quote"] == "A dated net zero target." and blocks["rules"]["quote"] is None
    assert blocks["rules"]["detail"].startswith("Matched “")


def test_majority_decides_and_a_three_way_tie_goes_to_climatebert():
    assert grading.grade_pledge(SAMPLE, arms("none", "net_zero", "net_zero"), CFG)["kind"] == "Net zero"
    tie = grading.grade_pledge(SAMPLE, arms("none", "reduction", "net_zero"), CFG)
    assert tie["kind"] == "Reduction target"


def test_no_target_gives_zero_and_no_graded_checks():
    out = grading.grade_pledge(SAMPLE, arms("none", "none", "none"), CFG)
    assert out["score"] == 0 and out["kind"] == "No target"
    assert not any(c["found"] for c in out["checks"]) and out["summary"].startswith("No emissions target")


def test_failed_method_is_omitted_with_a_warning():
    pool = arms()
    pool["llm"] = FakeArm(fail=True)
    out = grading.grade_pledge(SAMPLE, pool, CFG)
    assert [m["id"] for m in out["methods"]] == ["rules", "climatebert"]
    assert len(out["warnings"]) == 1 and "Zero shot LLM" in out["warnings"][0]
    assert "provider down" not in out["warnings"][0]


def test_all_methods_failing_raises():
    with pytest.raises(RuntimeError):
        grading.grade_pledge(SAMPLE, {"rules": FakeArm(fail=True)}, CFG)


def test_input_length_limits():
    with pytest.raises(ValueError, match="at least 20"):
        grading.grade_pledge("too short", arms(), CFG)
    with pytest.raises(ValueError, match="under 2,000"):
        grading.grade_pledge("x" * 2001, arms(), CFG)


@pytest.mark.parametrize("seconds, expected", [(0.004, "4 ms"), (0.12, "0.12 s"), (4.83, "4.8 s")])
def test_format_time(seconds, expected):
    assert grading.format_time(seconds) == expected


def test_response_keys_match_the_frontend_sample_when_present():
    """Compares key sets with frontend/src/sampleResult.json once the UI branch is merged."""
    path = Path(__file__).resolve().parent.parent / "frontend" / "src" / "sampleResult.json"
    if not path.exists():
        pytest.skip("frontend sample not present on this branch")
    sample, out = json.loads(path.read_text(encoding="utf8")), grading.grade_pledge(SAMPLE, arms(), CFG)
    assert set(sample) <= set(out)
    assert set(sample["checks"][0]) == set(out["checks"][0])
    assert set(sample["methods"][0]) == set(out["methods"][0])


def test_scope3_evidence_has_no_leading_space():
    """The evidence for a bare value chain mention starts at the first letter of the match."""
    span = evidence.find_evidence("We aim to reach net zero emissions across our operations and value chain.")["scope3"]
    assert span["evidence"] == "value chain"
    assert span["evidence"] == "We aim to reach net zero emissions across our operations and value chain."[span["start"]:span["end"]]
    full = evidence.find_evidence("We cover our entire value chain by 2045.")["scope3"]
    assert full["evidence"] == "entire value chain"


def test_non_english_pledge_gets_a_visible_warning():
    """A French pledge is graded, but the page is told that missing checks may be wrong."""
    french = "Nous nous engageons à atteindre la neutralité carbone d'ici 2050 et à réduire nos émissions de 40 % d'ici 2030."
    out = grading.grade_pledge(french, arms(rules_label="none"), CFG)
    assert grading.NON_ENGLISH_WARNING in out["warnings"]


def test_english_pledge_has_no_language_warning():
    """An English pledge produces no language warning."""
    assert grading.NON_ENGLISH_WARNING not in grading.grade_pledge(STRONG, arms(), CFG)["warnings"]
