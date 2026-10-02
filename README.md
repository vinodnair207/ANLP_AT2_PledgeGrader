# PledgeGrader

A web application that grades how credible a corporate net zero pledge is. A user pastes a pledge, and three methods (a rule based baseline, fine tuned ClimateBERT and zero shot LLM prompting) each classify it, check four robustness signals and explain what is missing.

Repository: https://github.com/vinodnair207/ANLP_AT2_PledgeGrader

This is Assessment Task 2 Part B for UTS 36118 Applied Natural Language Processing (Spring 2026), Group 14. The deliverables are a technical report of 10 to 15 pages and a working web application. The deadline is Wednesday 14 October 2026 (confirm on Canvas). The team target is Tuesday 13 October.

## What it does

1. The user pastes a pledge.
2. Each method classifies the target type: `net_zero`, `reduction` or `none`.
3. Each method checks four robustness signals: a named target year, Scope 3 coverage, an explanation of offset use, and interim milestones.
4. The app shows a score out of 100 (25 points per signal) and a plain language explanation of what is missing.

## Quick start for a new team member

Requirements: Git, Python 3.10 or newer (tested on 3.11), [uv](https://docs.astral.sh/uv/) and an internet connection for the first run.

1. Install uv if needed. In PowerShell:

   ```
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   Open a new terminal afterwards.

2. Clone the repository and enter it:

   ```
   git clone https://github.com/vinodnair207/ANLP_AT2_PledgeGrader.git
   cd ANLP_AT2_PledgeGrader
   ```

3. Create the environment and install everything:

   ```
   uv sync
   ```

   PyTorch is a large download. If you only need the rule based baseline for now, use `uv sync --no-install-package torch`.

4. Run the tests. All of them should pass (39 at the time of writing):

   ```
   uv run pytest
   ```

5. Run the baseline. The first run downloads the dataset, creates the shared train, validation and test split, and writes results to `outputs/`:

   ```
   uv run python -m src.main --method rules
   ```

   Expected result on the 517 test sentences: accuracy about 0.845 and macro F1 about 0.831. If your numbers differ, tell the group before changing anything.

6. Choose your role (see the table below), create a branch and start work:

   ```
   git checkout -b feat/<your-role>
   ```

After every `git pull`, run `uv sync` again, because new packages are added from time to time.

Notes for Windows: a warning about symlinks from `huggingface_hub` is harmless. A warning about unauthenticated requests is also harmless. To remove it, create a free Hugging Face token and set it as the `HF_TOKEN` environment variable.

## Roles and where to work

Owners are recorded in `docs/contributions_log.md`. Update that file whenever you finish a piece of work, because the report contributions table and the SPARKPlus ratings depend on it.

| Role | Main files | First task |
| --- | --- | --- |
| Data and evaluation lead | `src/data_processing.py`, `src/main.py`, `src/evaluation.py`, `src/significance.py`, `src/signal_key.py`, `src/error_analysis.py`, `src/report_assets.py` | Confirm the split, evaluate every method, run the bootstrap test, build the signal answer key and generate the report tables and figures |
| Rule based baseline owner | `src/rules.py`, `tests/test_rules.py` | Review failures against the signal answer key and extend the tests |
| ClimateBERT fine tuning owner | `src/train_climatebert.py`, `ClimateBertArm` in `src/model.py` | Run training, record metrics, upload the model to the Hugging Face Hub |
| LLM prompting owner | `ZeroShotLLMArm` in `src/model.py` | Write the prompt template and the arm, then check consistency |
| Web application and UX owner | `app.py` (to be created) | Build the Streamlit page on top of the baseline, then add the other arms |
| Coordination and report lead | `docs/`, the report | Keep the contributions log, report structure and checklist current |

Every member also writes at least one report section and labels their own tab of the signal sheet.

## Everyday commands

| Task | Command |
| --- | --- |
| Run the tests | `uv run pytest` |
| Evaluate the rule based method | `uv run python -m src.main --method rules` |
| Train ClimateBERT | `uv run python -m src.train_climatebert` |
| Evaluate ClimateBERT | `uv run python -m src.main --method climatebert` |
| Compare two methods with a paired bootstrap | `uv run python -m src.significance --a rules --b climatebert` |
| Build the signal answer key and score methods on the signals | `uv run python -m src.signal_key --methods rules` |
| Export the error analysis and the manual review sample | `uv run python -m src.error_analysis` |
| Generate every report table and figure | `uv run python -m src.report_assets` |

Evaluation writes `outputs/<method>_metrics.json` and `outputs/<method>_predictions.csv`. These files are committed on purpose, because the report tables are generated from them.

## Prediction file format

The comparison between the three methods only works when every method stores its predictions in the same shape. Each method must save `outputs/<method>_predictions.csv` with three columns: `text`, `gold` and `pred`. The file must cover the same 517 test sentences in the same order as `data/test.csv`, and labels must be exactly `none`, `net_zero` or `reduction`. The command `uv run python -m src.main --method <method>` writes this file for the rule based and ClimateBERT arms. The LLM arm must produce the same file, using the method name `llm`.

The LLM arm must also save `outputs/llm_signals.csv` with the columns `text`, `target_year`, `scope3`, `offsets` and `milestones` (True or False), so that its signals can be scored against the answer key.

Targets for the stored predictions: ClimateBERT by Monday 5 October and the LLM arm by Thursday 8 October.

## Git workflow

- Work on a branch named for your role, for example `feat/llm-arm`.
- Merge to `main` by pull request, with one teammate reviewing.
- Write commit messages that say what changed. Git history is evidence of who built what.
- Never commit secrets. Keep API keys in a local `.env` file, which is git ignored.
- Never commit model weights or the `data/*.csv` files. Both are git ignored. Weights go on the Hugging Face Hub.
- Run `uv run pytest` before every push.

## Project layout

```
config/config.yaml        All settings: seed, dataset, labels, scoring, ClimateBERT, bootstrap
src/utils.py              Config loading, logging, seeding
src/data_processing.py    Dataset download, label cleaning and the shared 70/15/15 split
src/rules.py              Rule based target classifier and the four signal checks
src/model.py              The three method classes behind one interface
src/train_climatebert.py  Fine tunes ClimateBERT and saves it to models/climatebert
src/main.py               Evaluates a method on the shared test set
src/evaluation.py         Accuracy, macro and per class metrics, confusion matrix
src/significance.py       Paired bootstrap test on macro F1
src/split_summary.py      Writes outputs/split_summary.json to check the shared split
src/signal_key.py         Builds the signal answer key, agreement score and signal metrics
src/error_analysis.py     Error table, disagreement summary and manual review sample
src/report_assets.py      Builds every report table and figure from the stored outputs
tests/                    Unit tests
outputs/                  Stored evaluation results (committed)
outputs/report/           Generated report tables (CSV) and figures (PNG)
labelling/                Signal labelling workbook, and completed/ for the finished labels
docs/                     Contributions log and team documents
```

## The shared interface

Every method exposes `predict(text)` and returns a dictionary with these keys: `method`, `label`, `signals` (four booleans), `score` and `explanation`. Keep this format identical across methods, because the app and the evaluation treat all three the same way. The score is always calculated by our own code, 25 points per signal that is present, and it is 0 when the label is `none`. Even the LLM arm only supplies the signal answers.

## Data and the split

- Source: `climatebert/netzero_reduction_data` on Hugging Face (Apache 2.0). It has 3,441 labelled sentences: 1,522 none, 979 reduction and 940 net zero. The label column is called `target`.
- The dataset ships as one block. `load_dataset` in `src/data_processing.py` makes a stratified 70/15/15 split with seed 42: 2,408 train, 516 validation and 517 test sentences.
- The test set is used only to mark the methods. Do not train or tune on it.
- The split is cached in `data/`. The fixed seed makes everyone's split identical.
- `outputs/split_summary.json` records the class counts of every split, and a unit test fails if the split ever changes. Do not edit the split.

Known data issues, to be mentioned in the report:

- About 1 in 4 sentences contains line breaks (133 of the 517 test sentences).
- A few sentences are very long (the longest test sentence is about 7,000 characters, and the 95th percentile is about 650). ClimateBERT reads only 128 tokens, so long sentences are cut off.
- A small share of sentences (roughly 2 percent) are not in English.

## Signal answer key (labelling)

The dataset labels only the target type, so the four signals need their own answer key. The key is built from 100 sentences taken from the test set. Because they come from the test set, use the key only to measure the methods, never to tune them.

How the labelling works:

1. The coordination lead shares one Google Sheet made from `labelling/signal_labelling_shared.xlsx`. It has a Guide tab and one tab per member.
2. Each member labels only their own tab: Y or N for the four signals on every row. Read the Guide tab first, judge only the sentence shown, choose N if unsure, and do not look at model outputs while labelling.
3. Every tab also contains the same 12 shared rows (marked `ALL`). Every member labels them independently, and they give the agreement score for the report. Do not look at another member's tab.
4. A few sentences are not in English. Paste them into a translator if needed and judge the translation.
5. When everyone has finished, the data and evaluation lead downloads the sheet as .xlsx and saves it as `labelling/completed/signal_labels.xlsx`.
6. Run `uv run python -m src.signal_key --methods rules` to build the answer key and score the methods on the signals. It writes `outputs/signal_key.csv`, `outputs/signal_agreement.json` and `outputs/signal_metrics_<method>.json`.

On the shared rows the answer is decided by majority vote, and a tie counts as N. The rule based and ClimateBERT arms use the same signal checks, so they receive identical signal scores. The comparison on signals is therefore between the rules and the LLM arm.

## Code and writing standards

- Every function has a docstring and every block has a short comment explaining what it does and why.
- Comments are factual statements, such as "Reads the raw file". They do not use "we" or "you".
- Use logging instead of print, handle errors with try and except, and read settings from `config/config.yaml`.
- Notebooks are for experiments only. Final logic lives in `src/`.
- Report text is formal and precise. Define every acronym on first use, caption every table and figure, and never invent results, numbers, citations or links. Use a marked placeholder such as `[INSERT macro F1 for ClimateBERT]` until a real result exists.

## Status

| Part | Status |
| --- | --- |
| Shared split and split check | Done. 2,408 train, 516 validation, 517 test, verified by a unit test |
| Rule based arm | Done. Accuracy 0.845, macro F1 0.831 on 517 test sentences |
| Evaluation (per class metrics, confusion matrix) | Done |
| Error analysis export | Done. Runs on whichever predictions exist |
| Report table and figure generator | Done. Reruns after every new set of predictions |
| Signal answer key script | Done. Labelling workbook ready, labelling not started |
| ClimateBERT training script and arm | Written, not yet run |
| Bootstrap significance test | Written and tested, waiting for ClimateBERT and LLM predictions |
| Zero shot LLM arm | Not started. Needs a provider and API key |
| Web app (Streamlit) | Not started |
| Deployment (Hugging Face Spaces) | Not started |
| Report | Not started |

