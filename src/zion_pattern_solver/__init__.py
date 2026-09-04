"""ZionPattern Solver (Z-Solver) v0.4 — intentional-suppression edition.

Whitepaper: July 18 2026, Aziel Eliab. Modular, local-first engine. Provisional and assistive
only. Does not solve Zioncheck or any case.

Score 75 = complete confidence in intentional suppression (hard cap).
1–74 = less intentional / more natural. Seed Visual Archive vols 1–5 baseline 75.
"""

from __future__ import annotations

__version__ = "0.4.0"
__author__ = "Aziel Eliab"

from zion_pattern_solver.derive import (
    METHOD,
    VOLUME_METHOD,
    VOLUME_METHOD_LAYERS,
    derive_answers,
    derive_answers_from_document,
    resolve_score_input,
    resolve_score_payload,
    score_document,
)
from zion_pattern_solver.errors import TerminationRefused, ZSolverError
from zion_pattern_solver.patterns import PATTERNS, get_patterns
from zion_pattern_solver.receipts import Receipt, DISCLAIMER
from zion_pattern_solver.scoring import (
    CONFIDENCE_CAP,
    SCORE_MEANING,
    UNCERTAINTY_FLOOR,
    cap_confidence,
    display_meaning,
    display_score,
    zsolver_status,
)
from zion_pattern_solver.session import Session
from zion_pattern_solver.terminate import terminate

__all__ = [
    "CONFIDENCE_CAP",
    "SCORE_MEANING",
    "DISCLAIMER",
    "METHOD",
    "VOLUME_METHOD",
    "VOLUME_METHOD_LAYERS",
    "PATTERNS",
    "Receipt",
    "Session",
    "TerminationRefused",
    "UNCERTAINTY_FLOOR",
    "ZSolverError",
    "cap_confidence",
    "display_meaning",
    "display_score",
    "zsolver_status",
    "derive_answers",
    "derive_answers_from_document",
    "get_patterns",
    "resolve_score_input",
    "resolve_score_payload",
    "score_document",
    "terminate",
    "__version__",
]
