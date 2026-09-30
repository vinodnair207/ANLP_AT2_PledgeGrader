"""Unit tests for the paired bootstrap."""
import numpy as np

from src.significance import paired_bootstrap


def test_clearly_better_method_is_significant():
    rng = np.random.default_rng(0)
    gold = rng.integers(0, 3, 400)
    good = gold.copy()                      # Perfect predictions
    bad = rng.integers(0, 3, 400)           # Random predictions
    out = paired_bootstrap(gold, bad, good, 300, 42)
    assert out["observed_diff"] > 0.4 and out["p_value"] < 0.05


def test_identical_methods_are_not_significant():
    rng = np.random.default_rng(1)
    gold = rng.integers(0, 3, 300)
    pred = rng.integers(0, 3, 300)
    assert paired_bootstrap(gold, pred, pred, 200, 42)["p_value"] == 1.0
