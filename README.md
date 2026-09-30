# PledgeGrader

Repository: https://github.com/vinodnair207/ANLP_AT2_PledgeGrader

Web application that grades corporate net zero pledges using three methods: a rule based baseline, fine tuned ClimateBERT and zero shot LLM prompting.

## Setup
    pip install -r requirements.txt
    python -m pytest tests            # unit tests
    python -m src.main --method rules # evaluates the baseline, writes outputs/

## Layout
src/ (main, data_processing, model, rules, utils), tests/, config/config.yaml, outputs/ (stored evaluation results).
Final logic lives in src/. Notebooks are for experiments only.

## Status
Rule based arm complete. ClimateBERT and LLM arms are stubs in src/model.py and must keep the `predict(text) -> dict` interface.
