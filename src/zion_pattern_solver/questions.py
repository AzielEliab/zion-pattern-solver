"""Walk pattern templates and record yes/no/unknown + rationale."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Sequence

from zion_pattern_solver.errors import SessionError
from zion_pattern_solver.patterns import PATTERNS, Pattern, QueuedQuestion, iter_questions
from zion_pattern_solver.scoring import ALLOWED_ANSWERS, UNKNOWN

AnswerValue = Literal["yes", "no", "unknown"]


@dataclass
class Answer:
    qid: str
    pattern_id: str
    index: int
    prompt: str
    value: str
    rationale: str
    evidence_type: str
    answered_at: str

    def to_dict(self) -> dict:
        return {
            "qid": self.qid,
            "pattern_id": self.pattern_id,
            "index": self.index,
            "prompt": self.prompt,
            "value": self.value,
            "rationale": self.rationale,
            "evidence_type": self.evidence_type,
            "answered_at": self.answered_at,
        }


def normalize_value(value: str) -> str:
    v = (value or "").strip().lower()
    aliases = {"y": "yes", "n": "no", "u": "unknown", "unk": "unknown", "?": "unknown"}
    v = aliases.get(v, v)
    if v not in ALLOWED_ANSWERS:
        raise SessionError(f"answer must be yes/no/unknown, got {value!r}")
    return v


class QuestionWalker:
    """Linear walk of all templates. Human answers one at a time."""

    def __init__(self, patterns: Sequence[Pattern] | None = None) -> None:
        self.queue: tuple[QueuedQuestion, ...] = iter_questions(patterns or PATTERNS)
        self.cursor = 0
        self.answers: list[Answer] = []

    def peek(self) -> QueuedQuestion | None:
        if self.cursor >= len(self.queue):
            return None
        return self.queue[self.cursor]

    def remaining(self) -> int:
        return max(0, len(self.queue) - self.cursor)

    def record(
        self,
        value: str,
        rationale: str,
        answered_at: str,
        question: QueuedQuestion | None = None,
    ) -> Answer:
        q = question or self.peek()
        if q is None:
            raise SessionError("no remaining questions")
        ans = Answer(
            qid=q.qid,
            pattern_id=q.pattern_id,
            index=q.index,
            prompt=q.prompt,
            value=normalize_value(value),
            rationale=(rationale or "").strip(),
            evidence_type=q.evidence_type,
            answered_at=answered_at,
        )
        self.answers.append(ans)
        # advance if this was the head of the queue
        if self.peek() is not None and self.peek().qid == q.qid:
            self.cursor += 1
        return ans

    def is_exhausted(self) -> bool:
        return self.peek() is None
