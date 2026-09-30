# Contributions log

Purpose: record who built what. The report contributions table and the SPARKPlus ratings are built from this file. Update it whenever a member finishes work. Git history and pull requests are the supporting evidence.

## Role assignments (to be confirmed at the team meeting)

| Role | Owner | Main outputs |
|---|---|---|
| Data and evaluation lead | TBC | Dataset splits, metrics pipeline, bootstrap test, error review |
| Rule based baseline owner | TBC | src/rules.py, signal patterns, tests |
| ClimateBERT fine tuning owner | TBC | src/train_climatebert.py, tuned model on the Hugging Face Hub |
| LLM prompting owner | TBC | Zero shot prompt template, src arm, hallucination checks |
| Web application and UX owner | TBC | Streamlit app, example selector, screenshots, deployment |
| Coordination and report lead | TBC | Report structure, tables, reference check, submission |

## Work log

| Date | Member | Work completed | Evidence (commit, PR or file) |
|---|---|---|---|
| 2026 10 01 | Vinod | Ran the rule based baseline on the real dataset; created the GitHub repository and pushed the initial code | rules_metrics.json, repository initial commit |
| 2026 10 01 | Vinod | Drafted the initial repository scaffold, baseline, ClimateBERT training script and bootstrap test | src/ folder, tests/ folder |

## Baseline result (rule based, 517 test sentences)

Accuracy 0.845, macro precision 0.857, macro recall 0.818, macro F1 0.831. Source: outputs/rules_metrics.json.
