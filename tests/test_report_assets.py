"""Unit tests for the report asset generator."""
import json
import shutil
from pathlib import Path

import pytest

from src import report_assets as ra

# Real stored outputs from the repository are used as the test input.
OUTPUTS = Path(__file__).resolve().parent.parent / "outputs"


@pytest.fixture
def stored_outputs(tmp_path):
    """Copies the committed baseline outputs to a temporary directory and adds a small error summary."""
    for name in ("split_summary.json", "rules_metrics.json"):
        shutil.copy(OUTPUTS / name, tmp_path / name)
    flag = {"rows_with_flag": 10, "error_rate_with_flag": 0.4, "error_rate_without_flag": 0.1}
    summary = {"per_method": {"rules": {"by_flag": {k: dict(flag) for k in ra.FLAG_NAMES}}}}
    (tmp_path / "error_summary.json").write_text(json.dumps(summary))
    return tmp_path


def test_split_table_matches_stored_counts(stored_outputs):
    table = ra.split_table(json.loads((stored_outputs / "split_summary.json").read_text()))
    assert list(table["split"]) == ["train", "validation", "test"]
    assert int(table["sentences"].sum()) == 3441
    assert table.loc[table["split"] == "test", "none_count"].item() == 229


def test_results_tables_use_method_display_names(stored_outputs):
    metrics = {"rules": json.loads((stored_outputs / "rules_metrics.json").read_text())}
    overall, per_class = ra.results_tables(metrics)
    assert overall.loc[0, "method"] == "Rule based baseline"
    assert overall.loc[0, "macro_f1"] == metrics["rules"]["macro_f1"]
    assert list(per_class["class"]) == ra.CLASS_ORDER


def test_generate_all_writes_tables_and_figures(stored_outputs, tmp_path):
    report_dir = tmp_path / "report"
    written = ra.generate_all(stored_outputs, report_dir)
    for name in ("table_split.csv", "table_results.csv", "table_per_class.csv", "figure_macro_f1.png",
                 "figure_confusion_rules.png", "figure_error_rates.png"):
        assert name in written and (report_dir / name).stat().st_size > 0


def test_missing_optional_outputs_are_skipped(tmp_path):
    assert ra.generate_all(tmp_path, tmp_path / "report") == []
