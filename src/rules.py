"""Rule based baseline: regular expression target classification and four robustness signals."""
import re

# Pattern for net zero style language, checked before reduction language.
NET_ZERO = re.compile(
    r"\b(net[\s\-]?zero|carbon[\s\-]neutral|climate[\s\-]neutral|zero (?:net )?(?:carbon|emissions|ghg)|carbon[\s\-]negative)\b",
    re.I,
)
# Pattern for emission reduction language (verb plus emissions noun or a percentage).
REDUCTION = re.compile(
    r"\b(reduc\w+|cut\w*|decreas\w+|lower\w*|halv\w+)\b.{0,80}?(emission|ghg|carbon|co2|footprint|intensity|\d+\s?%)",
    re.I,
)
# Four robustness signals.
YEAR = re.compile(r"\b(20[2-9]\d)\b")
SCOPE3 = re.compile(r"\bscope\s?3\b|value chain|supply chain emissions|indirect emissions", re.I)
OFFSETS = re.compile(r"\boffset\w*|carbon credit\w*|carbon removal\w*|neutrali[sz]\w*|insetting", re.I)
MILESTONES = re.compile(
    r"\b(interim|milestone\w*|by 20(?:2\d|3[0-5])\b|short term|near term|science[\s\-]based|SBTi)", re.I
)

NAMES = {"target_year": "a named target year", "scope3": "Scope 3 (value chain) coverage",
         "offsets": "an explanation of how offsets are used", "milestones": "interim milestones"}
ADVICE = {"target_year": "state the year by which the target is to be met",
          "scope3": "say whether Scope 3 emissions are included",
          "offsets": "explain whether offsets or removals are relied on, and how much",
          "milestones": "set interim targets on the way to the final goal"}


def classify_target(text: str) -> str:
    """Returns one of: net_zero, reduction, none."""
    if NET_ZERO.search(text):
        return "net_zero"
    if REDUCTION.search(text):
        return "reduction"
    return "none"


def detect_signals(text: str) -> dict:
    """Returns a boolean flag for each of the four robustness signals."""
    return {
        "target_year": bool(YEAR.search(text)),
        "scope3": bool(SCOPE3.search(text)),
        "offsets": bool(OFFSETS.search(text)),
        "milestones": bool(MILESTONES.search(text)),
    }


def score_and_explain(text: str, points: dict) -> dict:
    """Builds the full baseline output: label, signals, score out of 100 and explanation."""
    label = classify_target(text)
    signals = detect_signals(text)
    # A pledge with no detected target cannot earn robustness points.
    score = 0 if label == "none" else sum(points[k] for k, v in signals.items() if v)
    missing = [k for k, v in signals.items() if not v]
    if label == "none":
        reason = "No emissions target was detected, so the statement cannot be graded for robustness."
    elif not missing:
        reason = "All four robustness signals were detected. Expert verification is still advised."
    else:
        parts = [f"{NAMES[k]} (to improve, {ADVICE[k]})" for k in missing]
        reason = "The pledge is missing: " + "; ".join(parts) + "."
    return {"method": "rules", "label": label, "signals": signals, "score": score, "explanation": reason}
