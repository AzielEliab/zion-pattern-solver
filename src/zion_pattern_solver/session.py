"""Human-in-the-loop session: ask, answer, scores, uncertainty notes."""

from __future__ import annotations

import uuid
from typing import Any, Callable, Iterable, Mapping

from zion_pattern_solver.errors import SessionError
from zion_pattern_solver.patterns import PATTERNS, Pattern, QueuedQuestion, priority_map
from zion_pattern_solver.questions import Answer, QuestionWalker
from zion_pattern_solver.receipts import UncertaintyNote, utc_now
from zion_pattern_solver.scoring import (
    CONFIDENCE_CAP,
    UNKNOWN,
    Scores,
    cap_confidence,
    empty_scores,
    score_answers,
)

HIGH_DELTA = 0.12


class Session:
    """One local case session. No network. Analyst answers; engine records."""

    def __init__(
        self,
        case: str = "untitled",
        patterns: Iterable[Pattern] | None = None,
        clock: Callable[[], str] | None = None,
    ) -> None:
        self.case = case
        self.patterns: tuple[Pattern, ...] = tuple(patterns) if patterns is not None else PATTERNS
        self._clock = clock or utc_now
        self.walker = QuestionWalker(self.patterns)
        self.uncertainty_ledger: list[UncertaintyNote] = []
        self._note_i = 0
        self.terminated: dict[str, Any] | None = None

    def now(self) -> str:
        return self._clock()

    def ask(self) -> QueuedQuestion | None:
        if self.terminated is not None:
            return None
        return self.walker.peek()

    def answer(self, value: str, rationale: str = "") -> Answer:
        if self.terminated is not None:
            raise SessionError("session already terminated; start a new session")
        q = self.ask()
        if q is None:
            raise SessionError("no remaining questions")
        before = self.scores().capped_confidence
        ans = self.walker.record(value, rationale, answered_at=self.now(), question=q)
        after = self.scores().capped_confidence
        if ans.value == UNKNOWN:
            self.add_uncertainty_note(
                kind="unknown_answer",
                text=(
                    f"Unknown answer on {ans.qid} ({q.pattern_name}). "
                    f"Counts toward the 25% irreducible uncertainty floor. "
                    f"Rationale: {ans.rationale or '(none)'}"
                ),
                pattern_id=ans.pattern_id,
                qid=ans.qid,
            )
        delta = abs(after - before)
        if delta >= HIGH_DELTA:
            self.add_uncertainty_note(
                kind="high_delta",
                text=(
                    f"Score delta {delta:.3f} on {ans.qid} "
                    f"(capped {before:.3f} → {after:.3f}; cap {CONFIDENCE_CAP}). "
                    "High-delta steps are logged so a single answer cannot "
                    "quietly lock a narrative."
                ),
                pattern_id=ans.pattern_id,
                qid=ans.qid,
            )
        return ans

    def scores(self) -> Scores:
        if not self.walker.answers:
            return empty_scores()
        raw = score_answers(
            [a.to_dict() for a in self.walker.answers],
            priority_map(),
        )
        # belt: never return a Scores whose capped field exceeds the cap
        return Scores(
            official_contradiction=raw.official_contradiction,
            alternative_coherence=raw.alternative_coherence,
            raw_confidence=raw.raw_confidence,
            capped_confidence=cap_confidence(raw.capped_confidence),
        )

    def add_uncertainty_note(
        self,
        text: str,
        kind: str = "manual",
        pattern_id: str | None = None,
        qid: str | None = None,
    ) -> UncertaintyNote:
        self._note_i += 1
        note = UncertaintyNote(
            id=f"U{self._note_i:03d}",
            created_at=self.now(),
            kind=kind,
            text=text,
            pattern_id=pattern_id,
            qid=qid,
        )
        self.uncertainty_ledger.append(note)
        return note

    def history(self) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self.walker.answers]

    def ledger_dicts(self) -> list[dict[str, Any]]:
        return [n.to_dict() for n in self.uncertainty_ledger]

    def exhausted(self) -> bool:
        return self.walker.is_exhausted()

    def snapshot(self) -> dict[str, Any]:
        scores = self.scores()
        q = self.ask()
        return {
            "case": self.case,
            "question": None if q is None else q.to_dict(),
            "remaining": self.walker.remaining(),
            "answered": len(self.walker.answers),
            "scores": scores.to_dict(),
            "capped_confidence": cap_confidence(scores.capped_confidence),
            "confidence_cap": CONFIDENCE_CAP,
            "uncertainty_ledger": self.ledger_dicts(),
            "history": self.history(),
            "terminated": self.terminated,
            "patterns": [p.to_dict() for p in self.patterns],
            "disclaimer": (
                "Provisional and assistive only. Does not solve Zioncheck "
                "or any case. Hard cap 75% / uncertainty floor 25%. "
                "75 = complete confidence in intentional suppression; "
                "lower = less confidence it was intentional (more natural occurrence)."
            ),
        }
