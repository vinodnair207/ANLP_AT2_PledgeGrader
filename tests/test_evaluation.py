"""Unit tests for the shared metric calculations."""
import pytest

from src.evaluation import compute_metrics, confusion_frame

LABELS = ["a", "b", "c"]
GOLD = ["a", "a", "b", "b", "c", "c"]
PREDS = ["a", "b", "b", "b", "c", "a"]


def test_overall_metrics_match_hand_calculation():
    """Accuracy is 4 of 6 and macro recall is the mean of 0.5, 1.0 and 0.5."""
    m = compute_metrics(GOLD, PREDS, LABELS)
    assert m["accuracy"] == pytest.approx(0.6667, abs=1e-4)
    assert m["macro_recall"] == pytest.approx((0.5 + 1.0 + 0.5) / 3, abs=1e-4)


def test_per_class_metrics_match_hand_calculation():
    """Class b has precision 2 of 3 and recall 2 of 2, and every class has support 2."""
    pc = compute_metrics(GOLD, PREDS, LABELS)["per_class"]
    assert pc["b"]["precision"] == pytest.approx(0.6667, abs=1e-4) and pc["b"]["recall"] == 1.0
    assert pc["a"]["precision"] == 0.5 and pc["c"]["precision"] == 1.0
    assert {v["support"] for v in pc.values()} == {2}


def test_confusion_matrix_rows_are_gold_and_columns_are_predicted():
    """The matrix layout is gold by predicted and follows the label order."""
    cm = compute_metrics(GOLD, PREDS, LABELS)["confusion_matrix"]["matrix"]
    assert cm == [[1, 1, 0], [0, 2, 0], [1, 0, 1]]


def test_missing_predicted_class_does_not_crash():
    """A method that never predicts a class gets zero for it instead of an error."""
    m = compute_metrics(["a", "b"], ["a", "a"], LABELS)
    assert m["per_class"]["b"]["recall"] == 0.0 and m["per_class"]["c"]["support"] == 0


def test_confusion_frame_has_readable_names():
    """The CSV export labels rows with gold_ and columns with pred_."""
    frame = confusion_frame(compute_metrics(GOLD, PREDS, LABELS))
    assert list(frame.index) == ["gold_a", "gold_b", "gold_c"] and list(frame.columns) == ["pred_a", "pred_b", "pred_c"]
