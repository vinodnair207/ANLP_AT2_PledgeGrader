"""Model arms. Each arm exposes predict(text) returning a dict with a label key.

All three arms share the same interface. The zero shot LLM arm is defined in
src/llm_arm.py and re-exported here.
"""
from pathlib import Path

from src import rules
# The zero shot LLM arm lives in its own module because it carries the prompt and API handling.
from src.llm_arm import ZeroShotLLMArm


class RuleBasedArm:
    """Traditional baseline built on regular expressions."""

    name = "rules"

    def __init__(self, cfg: dict):
        self.points = cfg["scoring"]

    def predict(self, text: str) -> dict:
        """Classifies and scores one pledge."""
        return rules.score_and_explain(text, self.points)


class ClimateBertArm:
    """Fine tuned ClimateBERT classifier for the target type.

    The transformer predicts the target type only. The four robustness signals
    still come from the shared pattern checks, so the score stays comparable
    across arms.
    """

    name = "climatebert"

    def __init__(self, cfg: dict):
        # Heavy imports are deferred so that the rule based arm works without torch.
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        path = Path(cfg["climatebert"]["output_dir"])
        if not path.exists():
            raise FileNotFoundError(f"No fine tuned model at {path}. Run: python -m src.train_climatebert")
        self.torch = torch
        self.max_length = cfg["climatebert"]["max_length"]
        self.points = cfg["scoring"]
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.model = AutoModelForSequenceClassification.from_pretrained(path).eval()

    def predict(self, text: str) -> dict:
        """Classifies one pledge with the transformer and scores it with the shared signal checks."""
        inputs = self.tokenizer(text, truncation=True, max_length=self.max_length, return_tensors="pt")
        with self.torch.no_grad():
            logits = self.model(**inputs).logits
        label = self.model.config.id2label[int(logits.argmax(dim=-1))]
        signals = rules.detect_signals(text)
        score = 0 if label == "none" else sum(self.points[k] for k, v in signals.items() if v)
        return {"method": self.name, "label": label, "signals": signals, "score": score,
                "explanation": rules.score_and_explain(text, self.points)["explanation"]}


def get_arms(cfg: dict, names=("rules", "climatebert")) -> dict:
    """Builds the requested arms. ClimateBERT is skipped when no trained model exists yet."""
    arms = {}
    if "rules" in names:
        arms["rules"] = RuleBasedArm(cfg)
    if "climatebert" in names and Path(cfg["climatebert"]["output_dir"]).exists():
        arms["climatebert"] = ClimateBertArm(cfg)
    if "llm" in names:
        arms["llm"] = ZeroShotLLMArm(cfg)
    return arms
