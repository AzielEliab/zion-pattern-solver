"""Termination refused without notes; succeeds near cap with ledger."""

from __future__ import annotations

import pytest

from zion_pattern_solver.errors import TerminationRefused
from zion_pattern_solver.receipts import verify_payload
from zion_pattern_solver.scoring import cap_confidence
from zion_pattern_solver.session import Session
from zion_pattern_solver.terminate import (
    ALTERNATIVE_SUPPORTED,
    EVIDENCE_EXHAUSTION,
    MIN_UNCERTAINTY_NOTES,
    OFFICIAL_UNSUSTAINABLE,
    terminate,
)


def _walk(session: Session, unknown_n: int = 0) -> None:
    u = 0
    while True:
        q = session.ask()
        if q is None:
            break
        if u < unknown_n:
            session.answer("unknown", "fixture unknown")
            u += 1
        else:
            session.answer("yes", "fixture yes")


def test_termination_refused_without_enough_uncertainty_notes() -> None:
    s = Session(case="t", clock=lambda: "2026-07-18T12:00:00Z")
    _walk(s, unknown_n=0)
    s.uncertainty_ledger.clear()
    assert len(s.uncertainty_ledger) < MIN_UNCERTAINTY_NOTES
    assert cap_confidence(s.scores().capped_confidence) == 0.75
    with pytest.raises(TerminationRefused, match="uncertainty_ledger"):
        terminate(s, OFFICIAL_UNSUSTAINABLE)


def test_termination_refused_when_not_near_cap() -> None:
    s = Session(case="t", clock=lambda: "2026-07-18T12:00:00Z")
    s.answer("unknown", "a")
    s.answer("unknown", "b")
    s.answer("unknown", "c")
    assert len(s.uncertainty_ledger) >= MIN_UNCERTAINTY_NOTES
    with pytest.raises(TerminationRefused, match="not near"):
        terminate(s, OFFICIAL_UNSUSTAINABLE)


def test_termination_near_cap_with_notes_succeeds_and_hash_stable() -> None:
    clock = lambda: "2026-07-18T12:00:00Z"
    s1 = Session(case="zioncheck-1936", clock=clock)
    _walk(s1, unknown_n=4)
    rec1 = terminate(s1, OFFICIAL_UNSUSTAINABLE, issued_at="2026-07-18T12:00:00Z")
    assert rec1.capped_confidence == 0.75
    assert rec1.capped_confidence <= 0.75
    assert rec1.hash_ok()
    assert rec1.payload["termination"]["status"] == "provisional"
    assert "does not solve" in rec1.payload["disclaimer"].lower() or "not" in rec1.payload["disclaimer"].lower()

    s2 = Session(case="zioncheck-1936", clock=clock)
    _walk(s2, unknown_n=4)
    rec2 = terminate(s2, OFFICIAL_UNSUSTAINABLE, issued_at="2026-07-18T12:00:00Z")
    assert rec1.sha256 == rec2.sha256
    assert verify_payload(rec1.payload)


def test_all_three_termination_types() -> None:
    clock = lambda: "2026-07-18T12:00:00Z"
    for kind in (OFFICIAL_UNSUSTAINABLE, ALTERNATIVE_SUPPORTED, EVIDENCE_EXHAUSTION):
        s = Session(case="t", clock=clock)
        _walk(s, unknown_n=4)
        rec = terminate(s, kind, issued_at="2026-07-18T12:00:00Z")
        assert rec.payload["termination"]["type"] == kind
        assert rec.capped_confidence <= 0.75
        assert rec.hash_ok()
