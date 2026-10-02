"""Unit tests for the error analysis export."""
import pandas as pd
import pytest

from src import error_analysis as ea


def _write(path, texts, gold, pred):
    """Writes a prediction file in the shared format."""
    pd.DataFrame({"text": texts, "gold": gold, "pred": pred}).to_csv(path, index=False)


@pytest.fixture
def two_methods(tmp_path):
    texts = ["a net zero goal by 2040", "cut emissions 20 percent", "nothing here", "reduce carbon footprint"]
    gold = ["net_zero", "reduction", "none", "reduction"]
    _write(tmp_path / "rules_predictions.csv", texts, gold, ["net_zero", "none", "none", "none"])
    _write(tmp_path / "climatebert_predictions.csv", texts, gold, ["net_zero", "reduction", "net_zero", "none"])
    return tmp_path


def test_load_and_flags(two_methods):
    frame = ea.add_flags(ea.load_predictions(["rules", "climatebert"], two_methods), ["rules", "climatebert"])
    assert list(frame["methods_disagree"]) == [False, True, True, False]
    assert list(frame["correct_rules"]) == [True, False, True, False]


def test_summary_counts_unique_and_shared_errors(two_methods):
    methods = ["rules", "climatebert"]
    frame = ea.add_flags(ea.load_predictions(methods, two_methods), methods)
    summary = ea.summarise(frame, methods)
    assert summary["all_correct"] == 1 and summary["all_wrong"] == 1 and summary["methods_disagree"] == 2
    assert summary["per_method"]["rules"]["errors"] == 2 and summary["per_method"]["rules"]["unique_errors"] == 1
    assert summary["per_method"]["climatebert"]["unique_errors"] == 1


def test_review_sample_pool_and_columns(two_methods):
    methods = ["rules", "climatebert"]
    frame = ea.add_flags(ea.load_predictions(methods, two_methods), methods)
    sample = ea.review_sample(frame, methods, n=10, seed=42)
    assert sorted(sample["row"]) == [1, 2] and "reviewer_category" in sample.columns
    single = ea.add_flags(ea.load_predictions(["rules"], two_methods), ["rules"])
    assert sorted(ea.review_sample(single, ["rules"], n=10, seed=42)["row"]) == [1, 3]


def test_misaligned_files_are_rejected(tmp_path):
    _write(tmp_path / "rules_predictions.csv", ["a", "b"], ["none", "none"], ["none", "none"])
    _write(tmp_path / "llm_predictions.csv", ["a", "c"], ["none", "none"], ["none", "none"])
    with pytest.raises(ValueError):
        ea.load_predictions(["rules", "llm"], tmp_path)


def test_language_heuristic():
    assert ea.looks_non_english("In attuazione del parere reso dalla Commissione Europea e denominato Un pianeta pulito")
    assert not ea.looks_non_english("The company will reduce emissions and report on the progress of its targets.")
