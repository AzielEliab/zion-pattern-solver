"""Seeded auto walk. Fixture answers advance nodes; receipts follow cap and floor rules.

No network. The walk reuses Session.answer and terminate. Displayed confidence
stays at or below 0.75. A receipt is written only when termination rules pass.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from zion_pattern_solver.errors import SessionError, TerminationRefused
from zion_pattern_solver.scoring import cap_confidence
from zion_pattern_solver.session import Session
from zion_pattern_solver.terminate import (
    ALTERNATIVE_SUPPORTED,
    EVIDENCE_EXHAUSTION,
    OFFICIAL_UNSUSTAINABLE,
    check_termination,
    terminate,
)


def example_dir() -> Path:
    here = Path(__file__).resolve()
    root = here.parents[2]
    candidates = [
        Path.cwd() / "examples" / "zioncheck_irn_nodes",
        root / "examples" / "zioncheck_irn_nodes",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return candidates[0]


def load_seed_answers(path: Path | None = None) -> dict[str, Any]:
    target = path or (example_dir() / "demo_answers.json")
    if not target.is_file():
        raise FileNotFoundError(str(target))
    raw = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("answers file must be a JSON object")
    return raw


def _value_rationale(item: Any) -> tuple[str, str]:
    if isinstance(item, str):
        return item, "seeded walk"
    if isinstance(item, dict):
        return str(item.get("value", "unknown")), str(item.get("rationale") or "seeded walk")
    return "unknown", "seeded walk"


def _closing_kind(session: Session) -> str | None:
    order: list[str] = []
    if session.exhausted():
        order.append(EVIDENCE_EXHAUSTION)
    order.extend((OFFICIAL_UNSUSTAINABLE, ALTERNATIVE_SUPPORTED, EVIDENCE_EXHAUSTION))
    seen: set[str] = set()
    for kind in order:
        if kind in seen:
            continue
        seen.add(kind)
        try:
            check_termination(session, kind)
        except TerminationRefused:
            continue
        return kind
    return None


def _refusal(session: Session) -> str:
    try:
        check_termination(session, EVIDENCE_EXHAUSTION if session.exhausted() else OFFICIAL_UNSUSTAINABLE)
    except TerminationRefused as exc:
        return str(exc)
    return "A receipt was not written."


def auto_run(
    session: Session,
    answers: dict[str, Any] | None = None,
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    """Advance seeded nodes.

    ``limit`` stops after that many new answers (a pause). A full run writes a
    provisional receipt only when the cap and uncertainty-floor rules allow it.
    """
    if answers is None:
        try:
            answers = load_seed_answers()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return {
                "ok": False,
                "error": f"Could not read the seeded answers ({exc}).",
                "next": "Try: zion-solver auto   from the project directory",
                "applied": [],
                "applied_count": 0,
                "stopped": "no-fixture",
                "sha256": None,
                "receipt": None,
            }

    if session.terminated is not None:
        return _pack(
            session,
            applied=[],
            stopped="terminated",
            receipt=None,
            refusal="This walk is already closed. Start a new session to walk again.",
        )

    applied: list[str] = []
    stopped = "done"
    refusal: str | None = None
    while True:
        if limit is not None and len(applied) >= limit:
            stopped = "step" if session.ask() is not None else "done"
            break
        question = session.ask()
        if question is None:
            stopped = "done"
            break
        item = answers.get(question.qid)
        if item is None:
            item = answers.get(question.pattern_id)
        if not item:
            stopped = "no-fixture"
            refusal = (
                f"No seeded answer for {question.qid}. "
                "Record that question yourself, then run Auto walk again."
            )
            break
        value, rationale = _value_rationale(item)
        try:
            session.answer(value, rationale)
        except SessionError as exc:
            stopped = "no-fixture"
            refusal = f"{exc} Next: record the current question, or start a new session."
            break
        applied.append(question.qid)

    receipt = None
    finished = session.ask() is None and session.terminated is None
    if finished and applied and limit is None:
        kind = _closing_kind(session)
        if kind:
            rec = terminate(session, kind)
            receipt = rec.to_dict()
            stopped = "receipt"
            refusal = None
        else:
            refusal = _refusal(session)
            stopped = "done"
    elif finished and applied and limit is not None:
        # The last stepped node finished the walk. Close if the rules allow.
        kind = _closing_kind(session)
        if kind:
            rec = terminate(session, kind)
            receipt = rec.to_dict()
            stopped = "receipt"
            refusal = None

    return _pack(session, applied=applied, stopped=stopped, receipt=receipt, refusal=refusal)


def _pack(
    session: Session,
    *,
    applied: list[str],
    stopped: str,
    receipt: dict[str, Any] | None,
    refusal: str | None,
) -> dict[str, Any]:
    scores = session.scores()
    capped = cap_confidence(scores.capped_confidence)
    sha = None
    if receipt and receipt.get("sha256"):
        sha = str(receipt["sha256"])
    elif session.terminated and session.terminated.get("sha256"):
        sha = str(session.terminated["sha256"])
    return {
        "ok": True,
        "case": session.case,
        "applied": applied,
        "applied_count": len(applied),
        "answered": len(session.history()),
        "remaining": 0 if session.ask() is None else session.walker.remaining(),
        "stopped": stopped,
        "capped_confidence": capped,
        "uncertainty_notes": len(session.uncertainty_ledger),
        "sha256": sha,
        "receipt": receipt,
        "refusal": refusal,
        "snapshot": session.snapshot(),
    }
