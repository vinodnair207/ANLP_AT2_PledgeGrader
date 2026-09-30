"""Command line entry point: evaluates the rule based baseline on the shared test set.

Usage: python -m src.main --method rules
"""
import argparse
import json
import logging
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from src import data_processing, model, utils

logger = logging.getLogger(__name__)


def evaluate(method: str, cfg: dict) -> dict:
    """Runs one method over the test set, stores predictions, and returns metrics."""
    test = data_processing.get_test_set(cfg)
    arm = model.get_arms(cfg, (method,))[method]
    # Labels are already standardised to string names by data_processing.
    gold = test["label"]
    preds = [arm.predict(t)["label"] for t in test["text"]]
    p, r, f1, _ = precision_recall_fscore_support(gold, preds, average="macro", zero_division=0)
    metrics = {"method": method, "n": len(test), "accuracy": accuracy_score(gold, preds),
               "macro_precision": p, "macro_recall": r, "macro_f1": f1}
    out = Path(cfg["paths"]["predictions_dir"])
    out.mkdir(parents=True, exist_ok=True)
    # Stores row level predictions so the error review and bootstrap test can reuse them.
    pd.DataFrame({"text": test["text"], "gold": gold, "pred": preds}).to_csv(out / f"{method}_predictions.csv", index=False)
    (out / f"{method}_metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics


def main() -> None:
    """Parses arguments, evaluates the chosen method and logs the metrics."""
    parser = argparse.ArgumentParser(description="PledgeGrader evaluation")
    parser.add_argument("--method", default="rules", choices=["rules", "climatebert"])
    args = parser.parse_args()
    utils.setup_logging()
    cfg = utils.load_config()
    utils.set_seed(cfg["seed"])
    try:
        logger.info("Metrics: %s", evaluate(args.method, cfg))
    except Exception:  # Logs the full traceback, then exits with a readable message.
        logger.exception("Evaluation failed")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
