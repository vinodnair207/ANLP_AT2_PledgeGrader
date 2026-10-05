"""Evidence finder: locates the words in a pledge that satisfy each of the four checks.

The patterns come from src/rules.py, so a check is reported as found here exactly when
rules.detect_signals reports it as present. Each span is a dictionary with the matched
text and its character positions in the original string, which the web page uses to
highlight the words. Positions are Python string indices, so they match JavaScript
indices for text without characters outside the basic multilingual plane.
"""
import re
from typing import Optional

from src import rules

# Maps the internal signal names to the check ids used by the web page.
CHECK_IDS = {"target_year": "year", "scope3": "scope3", "offsets": "offsets", "milestones": "milestones"}

# A year that follows a preposition is more likely to be a target date than a baseline year.
_YEAR_WITH_PREPOSITION = re.compile(r"\b(?:by|in|before|until|to)\s+(20[2-9]\d)\b", re.I)


def _as_span(match: re.Match) -> dict:
    """Converts a regular expression match into an evidence span."""
    return {"evidence": match.group(0), "start": match.start(), "end": match.end()}


def _overlaps(match: re.Match, span: Optional[dict]) -> bool:
    """Returns True when the match shares characters with the given span."""
    return span is not None and match.start() < span["end"] and match.end() > span["start"]


def find_year(text: str) -> Optional[dict]:
    """Returns the span of the most likely target year, or None when no year is present.

    The latest year is chosen, because the final goal is normally the furthest date.
    A year with a preposition such as "by 2040" is preferred over a bare year.
    """
    candidates = list(_YEAR_WITH_PREPOSITION.finditer(text)) or list(rules.YEAR.finditer(text))
    if not candidates:
        return None
    return _as_span(max(candidates, key=lambda m: int(m.group(1))))


def find_milestone(text: str, year_span: Optional[dict]) -> Optional[dict]:
    """Returns the span of an interim milestone, preferring a match that is not the target year."""
    matches = list(rules.MILESTONES.finditer(text))
    if not matches:
        return None
    separate = [m for m in matches if not _overlaps(m, year_span)]
    return _as_span((separate or matches)[0])


def _first_span(pattern: re.Pattern, text: str) -> Optional[dict]:
    """Returns the span of the first match of the pattern, or None when there is no match."""
    match = pattern.search(text)
    return _as_span(match) if match else None


def find_evidence(text: str) -> dict:
    """Returns the evidence span for each check id, or None for a check that is not met."""
    year = find_year(text)
    return {
        "year": year,
        "scope3": _first_span(rules.SCOPE3, text),
        "offsets": _first_span(rules.OFFSETS, text),
        "milestones": find_milestone(text, year),
    }


def find_target_phrase(text: str, label: str) -> Optional[str]:
    """Returns the words that made the rule based method choose the given label, or None."""
    pattern = {"net_zero": rules.NET_ZERO, "reduction": rules.REDUCTION}.get(label)
    match = pattern.search(text) if pattern else None
    return re.sub(r"\s+", " ", match.group(0)).strip() if match else None
