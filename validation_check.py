from pathlib import Path

import pandas as pd

from src import data_processing, evaluation, model, utils


# ---------------------------------------------------------
# Load configuration and validation split
# ---------------------------------------------------------

cfg = utils.load_config()

splits = data_processing.load_dataset(cfg)
validation = splits["validation"].reset_index(drop=True)

arm = model.RuleBasedArm(cfg)


# ---------------------------------------------------------
# Generate predictions
# ---------------------------------------------------------

predictions = [
    arm.predict(text)["label"]
    for text in validation["text"]
]

validation["prediction"] = predictions
validation["correct"] = (
    validation["label"] == validation["prediction"]
)


# ---------------------------------------------------------
# Calculate metrics
# ---------------------------------------------------------

labels = list(cfg["labels"].values())

metrics = evaluation.compute_metrics(
    validation["label"],
    validation["prediction"],
    labels
)

print("\nRULE-BASED VALIDATION RESULTS")
print("=" * 50)

print("Validation accuracy:", round(metrics["accuracy"], 4))
print("Validation macro F1:", round(metrics["macro_f1"], 4))

print("\nPer-class results:")

for label, values in metrics["per_class"].items():
    print(
        f"{label:10s}",
        "precision =", round(values["precision"], 4),
        "recall =", round(values["recall"], 4),
        "f1 =", round(values["f1"], 4),
        "support =", values["support"]
    )


# ---------------------------------------------------------
# Misclassification analysis
# ---------------------------------------------------------

errors = validation[
    validation["correct"] == False
].copy()

print("\nTOTAL VALIDATION ERRORS:", len(errors))


# ---------------------------------------------------------
# Net-zero false negatives
# ---------------------------------------------------------

net_zero_missed = errors[
    errors["label"] == "net_zero"
][["text", "label", "prediction"]]

print("\n" + "=" * 50)
print("MISSED NET-ZERO SENTENCES")
print("=" * 50)

for index, row in net_zero_missed.iterrows():
    print("\nTRUE:", row["label"])
    print("PREDICTED:", row["prediction"])
    print("TEXT:", row["text"])


# ---------------------------------------------------------
# Reduction errors
# ---------------------------------------------------------

reduction_missed = errors[
    errors["label"] == "reduction"
][["text", "label", "prediction"]]


# ---------------------------------------------------------
# None false positives
# ---------------------------------------------------------

none_errors = errors[
    errors["label"] == "none"
][["text", "label", "prediction"]]


# ---------------------------------------------------------
# Save results
# ---------------------------------------------------------

output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)

errors.to_csv(
    output_dir / "rules_validation_errors.csv",
    index=False
)

net_zero_missed.to_csv(
    output_dir / "rules_validation_net_zero_errors.csv",
    index=False
)

reduction_missed.to_csv(
    output_dir / "rules_validation_reduction_errors.csv",
    index=False
)

none_errors.to_csv(
    output_dir / "rules_validation_none_errors.csv",
    index=False
)

print("\nSaved:")
print("outputs/rules_validation_errors.csv")
print("outputs/rules_validation_net_zero_errors.csv")
print("outputs/rules_validation_reduction_errors.csv")
print("outputs/rules_validation_none_errors.csv")