"""Unit tests for dataset cleaning, the shared split and the frozen split guard."""
import json
from pathlib import Path

import pandas as pd
import pytest

from src import data_processing as dp
from src.split_summary import overlap_between, summarise_split

ROOT = Path(__file__).resolve().parent.parent
CFG = {"dataset": {"text_column": "text", "label_column": "target"},
       "labels": {0: "none", 1: "net_zero", 2: "reduction"}}


@pytest.fixture
def full_frame() -> pd.DataFrame:
    """Builds 1000 unique synthetic sentences with a class mix close to the real data."""
    labels = ["none"] * 440 + ["reduction"] * 285 + ["net_zero"] * 275
    return pd.DataFrame({"text": [f"sentence {i}" for i in range(1000)], "label": labels})


def test_pick_column_prefers_configured_name():
    """The configured column name wins when it exists."""
    frame = pd.DataFrame({"text": ["a"], "target": ["none"], "label": ["x"]})
    assert dp._pick_column(frame, "target", dp.LABEL_CANDIDATES) == "target"


def test_pick_column_falls_back_to_candidates():
    """A known alternative name is found when the configured one is absent."""
    frame = pd.DataFrame({"sentence": ["a"], "labels": [0]})
    assert dp._pick_column(frame, "target", dp.LABEL_CANDIDATES) == "labels"


def test_pick_column_error_lists_real_columns():
    """The error message names the actual columns so the config can be corrected."""
    frame = pd.DataFrame({"foo": [1]})
    with pytest.raises(KeyError, match="foo"):
        dp._pick_column(frame, "target", dp.LABEL_CANDIDATES)


def test_normalise_labels_handles_numbers_and_text():
    """Integer ids map through the schema and text labels become snake case names."""
    id2label = {0: "none", 1: "net_zero", 2: "reduction"}
    assert dp._normalise_labels(pd.Series([0, 1, 2]), id2label).tolist() == ["none", "net_zero", "reduction"]
    text = pd.Series(["No target", "net zero", "Reduction"])
    assert dp._normalise_labels(text, id2label).tolist() == ["none", "net_zero", "reduction"]


def test_standardise_returns_only_text_and_label():
    """The cleaned frame has exactly the two internal columns."""
    raw = pd.DataFrame({"text": ["a", "b"], "target": ["none", "net zero"], "extra": [1, 2]})
    out = dp._standardise(raw, CFG)
    assert list(out.columns) == ["text", "label"] and out["label"].tolist() == ["none", "net_zero"]


def test_make_splits_sizes_follow_70_15_15(full_frame):
    """Split sizes are close to 70, 15 and 15 percent and cover every row once."""
    parts = dp.make_splits(full_frame, 42)
    assert sum(len(p) for p in parts.values()) == len(full_frame)
    assert abs(len(parts["train"]) - 700) <= 2
    assert abs(len(parts["validation"]) - 150) <= 2 and abs(len(parts["test"]) - 150) <= 2


def test_make_splits_have_no_overlap(full_frame):
    """No sentence appears in more than one split, which prevents test leakage."""
    parts = dp.make_splits(full_frame, 42)
    assert set(overlap_between(parts).values()) == {0}


def test_make_splits_are_stratified(full_frame):
    """Each split keeps the class shares of the full data within two percentage points."""
    full_share = full_frame["label"].value_counts(normalize=True)
    for part in dp.make_splits(full_frame, 42).values():
        share = part["label"].value_counts(normalize=True)
        assert (share - full_share).abs().max() < 0.02


def test_make_splits_are_reproducible(full_frame):
    """The same seed gives the same test set and a different seed gives a different one."""
    a = dp.make_splits(full_frame, 42)["test"]["text"].tolist()
    b = dp.make_splits(full_frame, 42)["test"]["text"].tolist()
    c = dp.make_splits(full_frame, 7)["test"]["text"].tolist()
    assert a == b and a != c


def test_summarise_split_counts():
    """The summary reports size, class counts and duplicate counts correctly."""
    frame = pd.DataFrame({"text": ["a", "a", "b\nc"], "label": ["none", "none", "net_zero"]})
    out = summarise_split(frame)
    assert out["n"] == 3 and out["class_counts"] == {"none": 2, "net_zero": 1}
    assert out["duplicate_texts"] == 1 and out["rows_with_line_breaks"] == 1


def test_overlap_between_detects_shared_sentences():
    """A sentence present in two splits is counted as an overlap."""
    frames = {"train": pd.DataFrame({"text": ["a", "b"]}), "validation": pd.DataFrame({"text": ["b"]}),
              "test": pd.DataFrame({"text": ["c"]})}
    assert overlap_between(frames) == {"train_validation": 1, "train_test": 0, "validation_test": 0}


@pytest.mark.skipif(not (ROOT / "data" / "test.csv").exists(), reason="Shared split files not present")
def test_real_splits_match_frozen_summary():
    """The local split files must match the committed summary, so nobody works on a different split."""
    frozen = json.loads((ROOT / "outputs" / "split_summary.json").read_text(encoding="utf8"))
    frames = {n: pd.read_csv(ROOT / "data" / f"{n}.csv") for n in ("train", "validation", "test")}
    for name, frame in frames.items():
        now = summarise_split(frame)
        assert now["n"] == frozen["splits"][name]["n"]
        assert now["class_counts"] == frozen["splits"][name]["class_counts"]
    assert set(overlap_between(frames).values()) == {0}
