# Contributions log

Purpose: record who built what. The report contributions table and the SPARKPlus ratings are built from this file. Update it whenever a member finishes work. Git history and pull requests are the supporting evidence.

## Role assignments

| Role | Owner | Main outputs |
|---|---|---|
| Data and evaluation lead, coordination | Vinod Nair Bhaskaran | Dataset splits, metrics pipeline, bootstrap tests, signal answer key, error analysis, report tables and figures, grading function, web service, request limits, Docker deployment, report Sections 4 and 7 |
| Rule based baseline owner | Victor Rono and Nana Ama Goldwater (shared tasks) | src/rules.py, signal patterns, docs/rules_tuning_notes.md, validation checks |
| ClimateBERT fine tuning owner | Nguyen Nghia Doan Dang (Git name Maris Dang) | Fine tuning run, predictions, significance test, weights on the Hub (Doan16/pledgegrader-climatebert) |
| LLM prompting owner | Chaitya Nanavati | src/llm_arm.py, zero shot prompt, evidence check, caching, consistency check, live mode |
| Web application and UX owner | Ranjan Khanal (interface); Vinod Nair Bhaskaran (service and deployment) | React interface, example selector, result view, backend connection; deployment on Hugging Face Spaces |
| Report lead | Vinod Nair Bhaskaran | Report structure, tables, reference check, submission |

## Work log

| Date | Member | Work completed | Evidence (commit, PR or file) |
|---|---|---|---|
| 2026 10 01 | Vinod | Ran the rule based baseline on the real dataset; created the GitHub repository and pushed the initial code | rules_metrics.json, repository initial commit |
| 2026 10 01 | Vinod | Drafted the initial repository scaffold, baseline, ClimateBERT training script and bootstrap test | src/ folder, tests/ folder |
| 2026 10 02 | Vinod | Verified the dataset columns, built the stratified 70/15/15 split with seed 42, wrote the split summary and a unit test that fails if the split changes | PR 1, commits 9870efd and 0d08c1c; outputs/split_summary.json, tests/test_data_processing.py |
| 2026 10 02 | Vinod | Added per class metrics and a confusion matrix to the evaluation | commit 62316f3; src/evaluation.py, tests/test_evaluation.py |
| 2026 10 02 | Vinod | Built the signal answer key script (majority vote, Fleiss kappa, per signal scoring) and the shared labelling workbook with one tab per member | commits 1f22821 and fc05e72; src/signal_key.py, labelling/signal_labelling_shared.xlsx |
| 2026 10 02 | Vinod | Built the error analysis export and the manual review sample | commit 7bee1da; src/error_analysis.py |
| 2026 10 02 | Vinod | Built the report table and figure generator | commit e7179ae; src/report_assets.py |
| 2026 10 02 | Vinod | Updated the README (prediction file format, new commands, labelling workflow) and merged the work to main | commit 5d4cabd, PR 2 (merge commit 3186349) |
| 2026 10 02 to 10 09 | All six members | Labelled sentences for the 100 sentence signal answer key, one tab per member, 12 shared sentences | labelling/completed workbook, commit 1218d6a |
| 2026 10 05 | Chaitya | Zero shot Gemini arm with evidence check, caching, retries and tests; validation run on 100 sentences (macro F1 0.948) | commits d933258 and b82d440; src/llm_arm.py |
| 2026 10 06 | Chaitya | Live mode for the app, quote positions, test run on 517 sentences (macro F1 0.943), consistency check (100 percent over 3 runs) | commits 33ba961, c86a2c3 and 14f3a22, PR 7 |
| 2026 10 05 | Ranjan | Static files and design for the interface | commit eb2fca2; frontend/ |
| 2026 10 06 | Vinod | Grading function that builds the web app response | commit 78d2e01; src/grading.py |
| 2026 10 06 to 10 07 | Victor | Finalised the validation tuned rule baseline, added validation checks and tuning notes | commits 620898b, 87d3ac0, 1bec1df and 76c9d5b, PRs 4 and 5; src/rules.py, docs/rules_tuning_notes.md |
| 2026 10 08 | Maris | ClimateBERT training, validation and test predictions, significance test, weights uploaded to the Hub | commit 5608ebe, PR 6; Doan16/pledgegrader-climatebert |
| 2026 10 08 | Vinod | Three way bootstrap, error analysis, corrected rules metrics, report assets, loading of the Hub weights | commits d800658 and 0d56cac, PRs 8 and 9 |
| 2026 10 09 | Vinod | Completed signal labelling workbook and signal answer key results | commit 1218d6a, PR 10 |
| 2026 10 12 | Ranjan | Connected the interface to the grading output and added the backend validation message | commits 7c852ad and f9e0e1a, PR 11 |
| 2026 10 12 | Vinod | Scope 3 pattern fix, method warnings, code review fixes, app testing fixes | commits bed9804, 6a6d5f1, c2fb3d4 and ceac639, PRs 12 to 15 |
| 2026 10 12 | Vinod | Docker deployment on Hugging Face Spaces, request limits and interface notices | commit efdb2bb, PR 16 |
| 2026 10 13 | Vinod | Inline score and test set explainers, logging fix, completed error review, README Space link | PR 17 and the README fix |
| 2026 10 06 to 10 07 | Nana | Shared the rule based baseline tasks with Victor: ordered pattern rules, tuning on the validation set, validation checks and tuning notes. The commits are under Victor's Git identity | PRs 4 and 5 (branch for Victor and Nana); src/rules.py, docs/rules_tuning_notes.md |

## Final test results (517 test sentences)

Rule based baseline: accuracy 0.9226, macro F1 0.9137. Fine tuned ClimateBERT: accuracy 0.9613, macro F1 0.9554. Zero shot LLM: accuracy 0.9497, macro F1 0.9426. Source: outputs/report/table_results.csv.
