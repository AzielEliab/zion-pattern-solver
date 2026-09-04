"""Scoring: official_contradiction, alternative_coherence, hard 75% cap.

The only function that may produce a stored/displayed conclusion
confidence is ``cap_confidence``. Every score object goes through it.

Display meaning (authoritative, 0.4.0):
    75     — complete confidence in intentional suppression (hard cap)
    1–74   — less confidence it was intentional; more natural occurrence
    0      — not_applicable (hidden non-match)
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Mapping, Sequence

CONFIDENCE_CAP = 0.75
UNCERTAINTY_FLOOR = 0.25
NEAR_CAP = 0.74

SCORE_MEANING_75 = "complete confidence in intentional suppression (hard cap)"
SCORE_MEANING_LOWER = (
    "less confidence it was intentional; more natural occurrence of suppression"
)
SCORE_MEANING_ZERO = "not_applicable — hidden (non-match)"
SCORE_MEANING: Mapping[str, str] = {
    "75": SCORE_MEANING_75,
    "1-74": SCORE_MEANING_LOWER,
    "0": SCORE_MEANING_ZERO,
}

PRIORITY_WEIGHT: Mapping[str, float] = {
    "critical": 1.0,
    "high": 0.70,
    "medium": 0.40,
}

YES = "yes"
NO = "no"
UNKNOWN = "unknown"
ALLOWED_ANSWERS = frozenset({YES, NO, UNKNOWN})


def cap_confidence(raw: float) -> float:
    """Hard cap: displayed/stored conclusion confidence NEVER exceeds 0.75.

    ``min(raw, 0.75)`` after clamping non-finite and negative values to 0.
    This is the single choke point used everywhere.
    """
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    if not isfinite(value) or value < 0.0:
        return 0.0
    return min(value, CONFIDENCE_CAP)


def display_score(capped: float) -> int:
    """Public integer display: 0 when not applicable, else clamped 1–75."""
    value = cap_confidence(capped)
    if value <= 0.0:
        return 0
    return min(75, max(1, int(round(value * 100))))


def display_meaning(display: int) -> str:
    """Honest label for a public display integer."""
    if display <= 0:
        return SCORE_MEANING_ZERO
    if display >= 75:
        return SCORE_MEANING_75
    return SCORE_MEANING_LOWER


def zsolver_status(display: int, *, seed: bool = False) -> str:
    """Library-adapter status: seed_baseline | scored | not_applicable."""
    if display <= 0:
        return "not_applicable"
    if seed and display >= 75:
        return "seed_baseline"
    return "scored"


def _yes_vote_strength(ans: Mapping[str, object], value: str) -> float:
    if value != YES:
        return 0.0
    raw = ans.get("vote_strength", 1.0)
    try:
        vs = float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        vs = 1.0
    if not isfinite(vs) or vs < 0.0:
        return 0.0
    return min(vs, 1.0)


@dataclass(frozen=True)
class Scores:
    official_contradiction: float
    alternative_coherence: float
    raw_confidence: float
    capped_confidence: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "capped_confidence", cap_confidence(self.capped_confidence)
        )
        object.__setattr__(
            self, "official_contradiction", _unit(self.official_contradiction)
        )
        object.__setattr__(
            self, "alternative_coherence", _unit(self.alternative_coherence)
        )
        # raw may exceed the cap; capped never does
        object.__setattr__(self, "raw_confidence", _unit(self.raw_confidence, high=1.0))
        object.__setattr__(
            self, "capped_confidence", cap_confidence(self.raw_confidence)
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "official_contradiction": round(self.official_contradiction, 6),
            "alternative_coherence": round(self.alternative_coherence, 6),
            "raw_confidence": round(self.raw_confidence, 6),
            "capped_confidence": round(cap_confidence(self.capped_confidence), 6),
        }


def _unit(value: float, high: float = 1.0) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not isfinite(v) or v < 0.0:
        return 0.0
    return min(v, high)


def empty_scores() -> Scores:
    return Scores(
        official_contradiction=0.0,
        alternative_coherence=0.0,
        raw_confidence=0.0,
        capped_confidence=0.0,
    )


def score_answers(
    answers: Sequence[Mapping[str, object]] | Iterable[Mapping[str, object]],
    priority_of: Mapping[str, str],
) -> Scores:
    """Compute raw official_contradiction + alternative_coherence, then cap.

    yes  — pattern node is supported by the analyst's reading of the record
    no   — pattern node is not supported
    unknown — excluded from numerators; included in the denominator so a
              lone yes among unknowns cannot saturate at 1.0 → display 75

    yes is weighted by ``vote_strength`` (default 1.0; layer votes use 0.35–1.0).

    official_contradiction: weighted yes / weighted (yes+no+unknown)
    alternative_coherence: same answers, extra weight on critical patterns
    raw_confidence: 0.55 * OC + 0.45 * AC  (may exceed 0.75)
    capped_confidence: cap_confidence(raw)
    """
    oc_num = oc_den = 0.0
    ac_num = ac_den = 0.0
    for ans in answers:
        pid = str(ans.get("pattern_id", ""))
        value = str(ans.get("value", UNKNOWN)).lower()
        priority = str(priority_of.get(pid, "medium")).lower()
        w = float(PRIORITY_WEIGHT.get(priority, 0.40))
        crit = 1.35 if priority == "critical" else 1.0
        vs = _yes_vote_strength(ans, value)
        if value == YES:
            oc_num += w * vs
            oc_den += w
            ac_num += w * crit * vs
            ac_den += w * crit
        elif value == NO:
            oc_den += w
            ac_den += w * crit
        else:
            oc_den += w
            ac_den += w * crit
    oc = (oc_num / oc_den) if oc_den else 0.0
    ac = (ac_num / ac_den) if ac_den else 0.0
    raw = 0.55 * oc + 0.45 * ac
    capped = cap_confidence(raw)
    return Scores(
        official_contradiction=oc,
        alternative_coherence=ac,
        raw_confidence=raw,
        capped_confidence=capped,
    )
