---
title: PledgeGrader
sdk: docker
app_port: 7860
pinned: false
---

# PledgeGrader

A web application that grades how credible a corporate net zero pledge is. A user pastes a pledge, and three methods read it on identical terms: a rule based baseline, a fine tuned ClimateBERT classifier and zero shot prompting of a large language model (Gemini). The app shows each method's target type, checks four robustness signals, and returns a score out of 100 with a plain language explanation of what is missing.

* Repository: https://github.com/vinodnair207/ANLP_AT2_PledgeGrader
* Public application: [INSERT Hugging Face Space URL]
* Fine tuned weights: https://huggingface.co/Doan16/pledgegrader-climatebert (pinned to one commit in `config/config.yaml`)

This is Assessment Task 2 Part B for UTS 36118 Applied Natural Language Processing (Spring 2026), Group 14. The deadline is Saturday 17 October 2026. The team plans to submit on Friday 16 October.

## What it does

1. The user pastes a pledge or picks an example.
2. Each method classifies the target type: `net_zero`, `reduction` or `none`. The overall label is a majority vote, and ties are settled in the order ClimateBERT, language model, rules.
3. The rule based signal checks look for four things: a named target year, Scope 3 coverage, an explanation of offset use, and interim milestones. Each is worth 25 points. A pledge labelled `none` scores 0.
4. The page shows the score, the checks with the quoted evidence, a warning when the methods disagree or a method is unavailable, and one card per method.

## Results on the held out test set

The shared test set holds 517 sentences from `climatebert/netzero_reduction_data` (stratified 70/15/15 split, seed 42).

| Method | Accuracy | Macro F1 |
| --- | --- | --- |
| Rule based baseline | 0.9226 | 0.9137 |
| Fine tuned ClimateBERT | 0.9613 | 0.9554 |
| Zero shot Gemini | 0.9497 | 0.9426 |

A paired bootstrap test (10,000 resamples on macro F1) finds ClimateBERT and the language model both better than the rules (p = 0.0008 and p = 0.0062) and not separable from each other (p = 0.3104). All numbers are read from `outputs/<method>_metrics.json`, and the report tables are generated from the stored outputs.

## Quick start

Requirements: Git, Python 3.10 or newer, [uv](https://docs.astral.sh/uv/), Node.js 22 or newer for the frontend, and an internet connection for the first run.

1. Install uv if needed. In PowerShell:

   ```
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. Clone the repository and install the Python packages:

   ```
   git clone https://github.com/vinodnair207/ANLP_AT2_PledgeGrader.git
   cd ANLP_AT2_PledgeGrader
   uv sync
   ```

   PyTorch is a large download. After every `git pull`, run `uv sync` again.

3. Run the tests:

   ```
   uv run pytest
   ```

4. Add the Gemini key. Copy `.env.example` to `.env` and replace the placeholder with a key from Google AI Studio. The `.env` file is ignored by git. Without a key the app still runs, and the language model method is shown as unavailable.

5. Start the application. In the first terminal, start the API:

   ```
   uv run uvicorn src.api:app --reload
   ```

   In a second terminal, start the frontend:

   ```
   cd frontend
   npm ci
   npm run dev
   ```

   Open http://localhost:5173. The development server forwards `/api` requests to port 8000.

6. To serve everything from one address, as in production, build the frontend and start only the API:

   ```
   cd frontend
   npm run build
   cd ..
   uv run uvicorn src.api:app
   ```

   Open http://localhost:8000.

The first start downloads the ClimateBERT weights from the Hugging Face Hub, so it takes longer than later starts. If torch is not installed, the app runs with the other two methods and shows a warning.

## Reproducing the results

Seeds are fixed at 42 and the settings live in `config/config.yaml`. Each command writes its output to `outputs/`.

| Task | Command |
| --- | --- |
| Evaluate the rule based method | `uv run python -m src.main --method rules` |
| Train ClimateBERT | `uv run python -m src.train_climatebert` |
| Evaluate ClimateBERT | `uv run python -m src.main --method climatebert` |
| Check the Hub weights reproduce the stored predictions | `uv run python -m src.verify_hub_model` |
| Evaluate the language model (needs `GEMINI_API_KEY`) | `uv run python -m src.main --method llm` |
| Compare two methods with a paired bootstrap | `uv run python -m src.significance --a rules --b climatebert` |
| Score the methods on the four signals | `uv run python -m src.signal_key --methods rules llm` |
| Export the error analysis and review sample | `uv run python -m src.error_analysis` |
| Generate every report table and figure | `uv run python -m src.report_assets` |

The dataset split is downloaded and cached in `data/` on the first run. The CSV files are ignored by git and are identical on every machine because of the fixed seed. A unit test fails if the split ever changes.

## Deployment on Hugging Face Spaces

The `Dockerfile` builds the React frontend, installs the pinned packages from `requirements.txt` (with the CPU build of torch), downloads the pinned ClimateBERT weights and starts the API on port 7860. The metadata block at the top of this file tells Spaces to use the Docker SDK.

1. Create a new Space at https://huggingface.co/new-space, choose the Docker SDK and a blank template, and make it public.
2. In the Space settings, open Variables and secrets and add a secret named `GEMINI_API_KEY`. Never commit the key.
3. Add the Space as a git remote and push the main branch. Use a Hugging Face access token with write permission as the password:

   ```
   git remote add space https://huggingface.co/spaces/<username>/<space name>
   git push space main
   ```

4. Wait for the build to finish, open the Space and grade one example from a fresh browser window.

Free Spaces go to sleep after a period without visits, so open the link a few minutes before it is needed. The app limits each visitor to 6 requests a minute and the whole app to 400 requests a day (`api` section of the config), which keeps the Gemini free tier of 500 requests a day from running out.

To refresh `requirements.txt` after changing dependencies, run `uv lock` and then `uv export --frozen --no-hashes --no-dev --no-emit-project -o requirements.txt`.

## Project layout

```
config/config.yaml        All settings: seed, dataset, labels, scoring, ClimateBERT, LLM, API limits
src/api.py                FastAPI routes and static hosting of the built frontend
src/grading.py            Combines the three methods into one label, score and explanation
src/ratelimit.py          Per visitor and daily request limits
src/rules.py              Rule based target classifier and the four signal checks
src/model.py              Rule based and ClimateBERT methods behind one interface
src/llm_arm.py            Zero shot Gemini method: prompt, schema, cache and quote check
src/train_climatebert.py  Fine tunes ClimateBERT
src/data_processing.py    Dataset download, label cleaning and the shared split
src/main.py               Evaluates a method on the shared test set
src/evaluation.py         Accuracy, macro and per class metrics, confusion matrix
src/significance.py       Paired bootstrap test on macro F1
src/signal_key.py         Signal answer key, agreement score and signal metrics
src/error_analysis.py     Error table, disagreement summary and review sample
src/report_assets.py      Builds every report table and figure from the stored outputs
frontend/                 React and Vite web application
tests/                    Unit tests
outputs/                  Stored evaluation results (committed on purpose)
```

## Data and licensing

The sentences come from `climatebert/netzero_reduction_data` on Hugging Face (Apache 2.0): 3,441 labelled sentences, split into 2,408 train, 516 validation and 517 test. The test set is used only to mark the methods. Statistics about corporate pledges are credited to the Net Zero Tracker (2025). Source details and the full reference list are in the report.

## Limits to keep in mind

* The checks are built for English text. The app warns when a pledge looks like another language.
* The score comes from fixed pattern checks, so wording outside those patterns can be marked as missing even when the idea is present.
* The pledge text is sent to Google for the language model method, so confidential text must not be pasted.
* The app is a first check and not a substitute for expert verification.

## Git workflow

* Work on a branch, merge to `main` by pull request and write commit messages that say what changed.
* Never commit secrets, model weights or the `data/*.csv` files.
* Run `uv run pytest` before every push.
