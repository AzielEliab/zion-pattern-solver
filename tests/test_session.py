"""Session ask/answer, unknown notes, high-delta notes."""

from __future__ import annotations

from zion_pattern_solver.scoring import cap_confidence
from zion_pattern_solver.session import Session


def test_unknown_writes_ledger_note() -> None:
    s = Session(case="t", clock=lambda: "2026-07-18T12:00:00Z")
    q = s.ask()
    assert q is not None
    s.answer("unknown", "not in the public file I have")
    kinds = {n.kind for n in s.uncertainty_ledger}
    assert "unknown_answer" in kinds
    assert s.scores().capped_confidence <= 0.75


def test_yes_no_unknown_roundtrip() -> None:
    s = Session(case="t", clock=lambda: "2026-07-18T12:00:00Z")
    s.answer("yes", "gap in published clocks")
    s.answer("no", "this node is not supported")
    s.answer("u", "still open")
    assert [a.value for a in s.walker.answers] == ["yes", "no", "unknown"]
    assert cap_confidence(s.scores().capped_confidence) <= 0.75


def test_snapshot_disclaimer() -> None:
    snap = Session(case="zioncheck-1936").snapshot()
    assert "75%" in snap["disclaimer"] or "cap" in snap["disclaimer"]
    assert "not" in snap["disclaimer"].lower()
    assert "solve" in snap["disclaimer"].lower()
