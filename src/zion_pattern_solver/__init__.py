"""ZionPattern Solver (Z-Solver) v0.3 — 75% Cap Edition.

Whitepaper: July 18 2026, Aziel Eliab. Modular, local-first engine. Provisional and assistive
only. Does not solve Zioncheck or any case.

Hard cap: displayed/stored conclusion confidence never exceeds 0.75.
Irreducible uncertainty floor: 25%, documented in every termination.
"""

from __future__ import annotations

__version__ = "0.3.0"
__author__ = "Aziel Eliab"

from zion_pattern_solver.derive import METHOD, derive_answers, resolve_score_input, score_document
from zion_pattern_solver.errors import TerminationRefused, ZSolverError
from zion_pattern_solver.patterns import PATTERNS, get_patterns
from zion_pattern_solver.receipts import Receipt, DISCLAIMER
from zion_pattern_solver.scoring import CONFIDENCE_CAP, UNCERTAINTY_FLOOR, cap_confidence
from zion_pattern_solver.session import Session
from zion_pattern_solver.terminate import terminate

__all__ = [
    "CONFIDENCE_CAP",
    "DISCLAIMER",
    "METHOD",
    "PATTERNS",
    "Receipt",
    "Session",
    "TerminationRefused",
    "UNCERTAINTY_FLOOR",
    "ZSolverError",
    "cap_confidence",
    "derive_answers",
    "get_patterns",
    "resolve_score_input",
    "score_document",
    "terminate",
    "__version__",
]
