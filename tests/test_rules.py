"""Unit tests for the rule based baseline."""
from src import rules
from src.utils import load_config

POINTS = load_config()["scoring"]


def test_net_zero_full_signals():
    text = ("We will reach net zero by 2040 including Scope 3, limit offsets to residual "
            "emissions, and set an interim target of 50% by 2030.")
    out = rules.score_and_explain(text, POINTS)
    assert out["label"] == "net_zero" and out["score"] == 100


def test_reduction_label():
    assert rules.classify_target("We reduce our emissions by 30% by 2030.") == "reduction"


def test_none_label_scores_zero():
    out = rules.score_and_explain("Our board met on Tuesday.", POINTS)
    assert out["label"] == "none" and out["score"] == 0


def test_missing_signals_are_explained():
    out = rules.score_and_explain("We aim for net zero.", POINTS)
    assert "target year" in out["explanation"] and out["score"] == 0
