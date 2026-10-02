"""Unit tests for the signal answer key: merging, voting, agreement and scoring."""
import numpy as np
import pandas as pd
import pytest

from src import signal_key as sk


def _sheet(path, rows):
    """Writes a small labelling workbook with the same layout as the real sheet."""
    frame = pd.DataFrame(rows, columns=["id", "assigned_to", "text", *sk.SIGNALS, "labeller_name", "notes"])
    with pd.ExcelWriter(path) as writer:
        frame.to_excel(writer, sheet_name="Labelling", index=False)


def _row(i, assigned, marks):
    """Builds one sheet row from a string of four Y or N marks."""
    return [i, assigned, f"sentence {i}", *list(marks), None, None]


def test_incomplete_rows_are_skipped(tmp_path):
    path = tmp_path / "alice.xlsx"
    _sheet(path, [_row(1, "Member 1", "YNYN"), _row(2, "Member 1", "YN")[:3] + [None] * 4 + [None, None]])
    long = sk.load_labelled_sheets([path])
    assert list(long["id"]) == [1]
    assert long.loc[0, "target_year"] and not long.loc[0, "scope3"]


def test_majority_vote_and_tie_resolve_to_no(tmp_path):
    paths = []
    for name, marks in [("a", "YYYY"), ("b", "YNYN"), ("c", "NNYN"), ("d", "NNNN")]:
        path = tmp_path / f"{name}.xlsx"
        _sheet(path, [_row(1, "ALL", marks)])
        paths.append(path)
    key = sk.build_key(sk.load_labelled_sheets(paths))
    row = key.iloc[0]
    # Four labellers: target_year 2 of 4 (tie, False), scope3 1 of 4, offsets 3 of 4, milestones 1 of 4.
    assert (row["target_year"], row["scope3"], row["offsets"], row["milestones"]) == (False, False, True, False)
    assert row["n_raters"] == 4


def test_fleiss_kappa_perfect_and_chance_levels():
    perfect = np.array([[3, 0], [0, 3], [3, 0], [0, 3]])
    assert sk.fleiss_kappa(perfect) == pytest.approx(1.0)
    # Raters that split evenly on every item agree less than chance.
    split = np.array([[2, 1], [1, 2], [2, 1], [1, 2]])
    assert sk.fleiss_kappa(split) < 0
    # A single category used everywhere makes kappa undefined.
    assert sk.fleiss_kappa(np.array([[3, 0], [3, 0]])) is None


def test_agreement_uses_only_shared_rows(tmp_path):
    paths = []
    for name, marks in [("a", "YYYY"), ("b", "YYYY"), ("c", "YNYN")]:
        path = tmp_path / f"{name}.xlsx"
        _sheet(path, [_row(1, "ALL", marks), _row(2, "ALL", "NNNN"), _row(3, "Member 1", "YYYY")])
        paths.append(path)
    result = sk.agreement(sk.load_labelled_sheets(paths))
    assert result["target_year"]["n_items"] == 2 and result["target_year"]["n_raters"] == 3
    assert result["scope3"]["mean_majority_share"] == pytest.approx((2 / 3 + 1.0) / 2, abs=1e-4)


def test_score_signals_counts_and_metrics():
    key = pd.DataFrame({s: [True, True, False, False] for s in sk.SIGNALS})
    predicted = pd.DataFrame({s: [True, False, True, False] for s in sk.SIGNALS})
    out = sk.score_signals(key, predicted)
    assert out["scope3"]["tp"] == 1 and out["scope3"]["fp"] == 1
    assert out["scope3"]["fn"] == 1 and out["scope3"]["tn"] == 1
    assert out["scope3"]["precision"] == 0.5 and out["scope3"]["recall"] == 0.5 and out["macro_f1"] == 0.5


def test_rule_methods_use_shared_checks_and_others_need_a_file(tmp_path):
    texts = ["We will reach net zero by 2040 including Scope 3."]
    frame = sk.signals_for_method("rules", texts, tmp_path)
    assert frame.loc[0, "target_year"] and frame.loc[0, "scope3"]
    with pytest.raises(FileNotFoundError):
        sk.signals_for_method("llm", texts, tmp_path)
    pd.DataFrame({"text": texts, **{s: [True, False, False, True] [i] for i, s in enumerate(sk.SIGNALS)}}).to_csv(
        tmp_path / "llm_signals.csv", index=False)
    llm = sk.signals_for_method("llm", texts, tmp_path)
    assert llm.loc[0, "target_year"] and not llm.loc[0, "scope3"]
