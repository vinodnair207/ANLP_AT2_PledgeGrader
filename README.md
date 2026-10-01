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

4. Run the tests. All of them should pass:

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

Notes for Windows: a warning about symlinks from `huggingface_hub` is harmless. A warning about unauthenticated requests is also harmless. To remove it, create a free Hugging Face token and set it as the `HF_TOKEN` environment variable.

## Roles and where to work

Owners are recorded in `docs/contributions_log.md`. Update that file whenever you finish a piece of work, because the report contributions table and the SPARKPlus ratings depend on it.

| Role | Main files | First task |
| --- | --- | --- |
| Data and evaluation lead | `src/data_processing.py`, `src/main.py`, `src/significance.py` | Confirm the split, then evaluate every method and run the bootstrap test |
| Rule based baseline owner | `src/rules.py`, `tests/test_rules.py` | Review failures against the signal answer key and extend the tests |
| ClimateBERT fine tuning owner | `src/train_climatebert.py`, `ClimateBertArm` in `src/model.py` | Run training, record metrics, upload the model to the Hugging Face Hub |
| LLM prompting owner | `ZeroShotLLMArm` in `src/model.py` | Write the prompt template and the arm, then check consistency |
| Web application and UX owner | `app.py` (to be created) | Build the Streamlit page on top of the baseline, then add the other arms |
| Coordination and report lead | `docs/`, the report | Keep the contributions log, report structure and checklist current |

Every member also writes at least one report section and labels their share of the signal sheet.

## Everyday commands

| Task | Command |
| --- | --- |
| Run the tests | `uv run pytest` |
| Evaluate the rule based method | `uv run python -m src.main --method rules` |
| Train ClimateBERT | `uv run python -m src.train_climatebert` |
| Evaluate ClimateBERT | `uv run python -m src.main --method climatebert` |
| Compare two methods with a paired bootstrap | `uv run python -m src.significance --a rules --b climatebert` |

Evaluation writes `outputs/<method>_metrics.json` and `outputs/<method>_predictions.csv`. These files are committed on purpose, because the report tables are generated from them.

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
src/significance.py       Paired bootstrap test on macro F1
tests/                    Unit tests
outputs/                  Stored evaluation results (committed)
labelling/                Spreadsheet for the signal answer key
docs/                     Contributions log and team documents
```

## The shared interface

Every method exposes `predict(text)` and returns a dictionary with these keys: `method`, `label`, `signals` (four booleans), `score` and `explanation`. Keep this format identical across methods, because the app and the evaluation treat all three the same way. The score is always calculated by our own code, 25 points per signal that is present, and it is 0 when the label is `none`. Even the LLM arm only supplies the signal answers.

## Data and the split

- Source: `climatebert/netzero_reduction_data` on Hugging Face (Apache 2.0). It has 3,441 labelled sentences: 1,522 none, 979 reduction and 940 net zero. The label column is called `target`.
- The dataset ships as one block. `load_dataset` in `src/data_processing.py` makes a stratified 70/15/15 split with seed 42: 2,408 train, 516 validation and 517 test sentences.
- The test set is used only to mark the methods. Do not train or tune on it.
- The split is cached in `data/`. The fixed seed makes everyone's split identical.

## Signal answer key (labelling)

The dataset labels only the target type, so the four signals need their own answer key. `labelling/signal_gold_set.xlsx` holds 100 sentences from the test set. Rows assigned to `ALL` are labelled by every member, which lets the report give an agreement score. The remaining rows are split across members. Read the Guide sheet first, and do not look at model outputs while labelling.

Because these sentences come from the test set, use the key only to measure the methods, never to tune them.

## Code and writing standards

- Every function has a docstring and every block has a short comment explaining what it does and why.
- Comments are factual statements, such as "Reads the raw file". They do not use "we" or "you".
- Use logging instead of print, handle errors with try and except, and read settings from `config/config.yaml`.
- Notebooks are for experiments only. Final logic lives in `src/`.
- Report text is formal and precise. Define every acronym on first use, caption every table and figure, and never invent results, numbers, citations or links. Use a marked placeholder such as `[INSERT macro F1 for ClimateBERT]` until a real result exists.

## Status

| Part | Status |
| --- | --- |
| Rule based arm | Done. Accuracy 0.845, macro F1 0.831 on 517 test sentences |
| ClimateBERT training script and arm | Written, not yet run |
| Bootstrap significance test | Written, waiting for real predictions |
| Zero shot LLM arm | Not started. Needs a provider and API key |
| Web app (Streamlit) | Not started |
| Deployment (Hugging Face Spaces) | Not started |
| Signal answer key | Spreadsheet drafted, labelling not started |
| Report | Not started |

## Timeline

Days 1 to 2 (1 to 2 Oct): roles, stack, repository and split locked. Days 3 to 5 (3 to 5 Oct): ClimateBERT, LLM arm and app skeleton. Days 6 to 8 (6 to 8 Oct): evaluate all three methods, significance test, error review. Days 9 to 10 (9 to 10 Oct): app polish and public link. Days 11 to 12 (11 to 12 Oct): report draft and peer review. Day 13 (13 Oct): proofread, submit, complete SPARKPlus. Day 14 (14 Oct): deadline buffer.

Choose the web stack by the end of Day 2 and do not change it afterwards.
