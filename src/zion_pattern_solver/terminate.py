"""Termination rules (75% Cap Edition).

All three termination types require:
  * capped_confidence near the 0.75 cap ( >= NEAR_CAP )
  * an uncertainty_ledger with at least MIN_UNCERTAINTY_NOTES notes
    documenting the 25% irreducible floor

Never terminate without a ledger. The engine never claims a solved case.
"""

from __future__ import annotations

from typing import Any

from zion_pattern_solver.errors import TerminationRefused
from zion_pattern_solver.receipts import DISCLAIMER, Receipt, mint_receipt, utc_now
from zion_pattern_solver.scoring import NEAR_CAP, cap_confidence
from zion_pattern_solver.session import Session

MIN_UNCERTAINTY_NOTES = 3
HIGH_OC = 0.70
HIGH_AC = 0.70

OFFICIAL_UNSUSTAINABLE = "official_unsustainable"
ALTERNATIVE_SUPPORTED = "alternative_supported"
EVIDENCE_EXHAUSTION = "evidence_exhaustion"

TERMINATION_TYPES = (
    OFFICIAL_UNSUSTAINABLE,
    ALTERNATIVE_SUPPORTED,
    EVIDENCE_EXHAUSTION,
)


def _version() -> str:
    from zion_pattern_solver import __version__

    return __version__


def refuse(msg: str) -> None:
    raise TerminationRefused(msg)


def check_termination(session: Session, kind: str) -> None:
    kind = (kind or "").strip()
    if kind not in TERMINATION_TYPES:
        refuse(f"unknown termination type {kind!r}; allowed: {TERMINATION_TYPES}")
    notes = session.uncertainty_ledger
    if len(notes) < MIN_UNCERTAINTY_NOTES:
        refuse(
            f"termination refused: uncertainty_ledger has {len(notes)} notes; "
            f"need at least {MIN_UNCERTAINTY_NOTES} to document the 25% floor"
        )
    scores = session.scores()
    capped = cap_confidence(scores.capped_confidence)
    if capped < NEAR_CAP:
        refuse(
            f"termination refused: capped_confidence {capped:.3f} is not near "
            f"the 0.75 cap (need >= {NEAR_CAP})"
        )
    if kind == OFFICIAL_UNSUSTAINABLE and scores.official_contradiction < HIGH_OC:
        refuse(
            "termination refused: official_unsustainable requires "
            f"official_contradiction >= {HIGH_OC}"
        )
    if kind == ALTERNATIVE_SUPPORTED and scores.alternative_coherence < HIGH_AC:
        refuse(
            "termination refused: alternative_supported requires "
            f"alternative_coherence >= {HIGH_AC}"
        )
    if kind == EVIDENCE_EXHAUSTION and not session.exhausted():
        refuse(
            "termination refused: evidence_exhaustion requires every "
            "template to have been answered (yes/no/unknown)"
        )


def terminate(
    session: Session,
    kind: str,
    issued_at: str | None = None,
) -> Receipt:
    """Build a provisional termination receipt. Raises TerminationRefused."""
    check_termination(session, kind)
    scores = session.scores()
    ts = issued_at or session.now()
    rec = mint_receipt(
        case=session.case,
        issued_at=ts,
        scores=scores,
        history=session.history(),
        uncertainty_ledger=session.ledger_dicts(),
        termination_type=kind,
        version=_version(),
        extra={"disclaimer": DISCLAIMER},
    )
    session.terminated = {
        "type": kind,
        "status": "provisional",
        "issued_at": ts,
        "sha256": rec.sha256,
        "capped_confidence": rec.capped_confidence,
    }
    return rec
