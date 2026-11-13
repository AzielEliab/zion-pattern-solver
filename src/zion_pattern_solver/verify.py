"""Ask a question to verify. Maps words onto the in-package patterns and score.

No network and no external model. A linked pattern is shared vocabulary with
the nine nodes. Displayed confidence comes from the existing document score
and never exceeds 0.75. A receipt is minted only when the question is clear
enough to score.
"""

from __future__ import annotations

import re
from typing import Any

from zion_pattern_solver import __version__
from zion_pattern_solver.auto import load_seed_answers
from zion_pattern_solver.derive import score_document
from zion_pattern_solver.patterns import PATTERNS, Pattern, QueuedQuestion, iter_questions
from zion_pattern_solver.receipts import mint_receipt, utc_now
from zion_pattern_solver.scoring import CONFIDENCE_CAP, UNCERTAINTY_FLOOR, Scores, cap_confidence

_STOP = frozenset(
    {
        "a", "an", "the", "of", "and", "or", "to", "in", "on", "for", "with",
        "did", "does", "do", "was", "were", "is", "are", "what", "when", "where",
        "who", "why", "how", "this", "that", "it", "from", "by", "be", "as", "at",
        "if", "not", "any", "into", "about", "there", "their", "have", "has",
        "had", "can", "could", "would", "should", "please", "verify", "question",
    }
)
_LINK_MIN = 0.75
_NEXT = 'Try: zion-solver ask "Did the 1936 timeline leave a gap?"'


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {word for word in words if len(word) >= 3 and word not in _STOP}


def _pattern_text(pattern: Pattern) -> str:
    parts = [
        pattern.id,
        pattern.name,
        pattern.priority,
        pattern.core_contradiction,
        pattern.detection_heuristic,
        pattern.evidence_priority,
    ]
    parts.extend(question.prompt for question in pattern.question_templates)
    return " ".join(parts)


def _weights() -> dict[str, float]:
    owners: dict[str, int] = {}
    for pattern in PATTERNS:
        for token in _tokens(_pattern_text(pattern)):
            owners[token] = owners.get(token, 0) + 1
    return {token: 1.0 / count for token, count in owners.items() if count}


def _overlap(left: set[str], right: set[str], weights: dict[str, float]) -> float:
    return sum(weights.get(token, 0.0) for token in left if token in right)


def _best_question(pattern: Pattern, question_tokens: set[str], weights: dict[str, float]) -> tuple[QueuedQuestion | None, float]:
    best: QueuedQuestion | None = None
    best_score = 0.0
    for node in iter_questions((pattern,)):
        score = _overlap(question_tokens, _tokens(node.prompt), weights)
        if score > best_score:
            best = node
            best_score = score
    return best, best_score


def _fixture_for(qid: str) -> dict[str, str] | None:
    try:
        answers = load_seed_answers()
    except (OSError, ValueError):
        return None
    item = answers.get(qid)
    if isinstance(item, str):
        return {"value": item, "rationale": ""}
    if isinstance(item, dict) and item.get("value"):
        return {"value": str(item.get("value")), "rationale": str(item.get("rationale") or "")}
    return None


def ask_to_verify(question: str) -> dict[str, Any]:
    text = " ".join((question or "").split())
    if not text:
        return {
            "ok": False,
            "error": "A question is required.",
            "next": _NEXT,
        }
    tokens = _tokens(text)
    if len(tokens) < 1:
        return {
            "ok": False,
            "error": "That question is too thin to match a pattern.",
            "next": _NEXT,
        }

    weights = _weights()
    ranked: list[tuple[float, Pattern, QueuedQuestion | None]] = []
    for pattern in PATTERNS:
        score = _overlap(tokens, _tokens(_pattern_text(pattern)), weights)
        node, _node_score = _best_question(pattern, tokens, weights)
        ranked.append((score, pattern, node))
    ranked.sort(key=lambda item: item[0], reverse=True)

    scored = score_document({"title": text, "body": text, "text": text})
    capped = cap_confidence(float(scored.get("capped_confidence") or 0.0))
    uncertainty = max(UNCERTAINTY_FLOOR, 1.0 - capped) if capped else 1.0

    linked: list[dict[str, Any]] = []
    for score, pattern, node in ranked:
        if score < _LINK_MIN:
            continue
        row: dict[str, Any] = {
            "id": pattern.id,
            "name": pattern.name,
            "priority": pattern.priority,
            "overlap": round(score, 3),
        }
        if node is not None and _overlap(tokens, _tokens(node.prompt), weights) > 0:
            row["qid"] = node.qid
            row["prompt"] = node.prompt
            fixture = _fixture_for(node.qid)
            if fixture:
                row["seed_fixture"] = fixture
        linked.append(row)
        if len(linked) == 3:
            break

    if not linked and capped <= 0.0:
        return {
            "ok": False,
            "error": "That question does not line up with the nine patterns.",
            "next": _NEXT,
            "capped_confidence": 0.0,
            "uncertainty": 1.0,
        }

    top = linked[0] if linked else None
    sentences = ["Provisional."]
    if top:
        sentences.append(f"Closest pattern is {top['id']} {top['name']}.")
        if top.get("qid"):
            sentences.append(f"Closest node is {top['qid']}.")
    else:
        sentences.append("The wording does not line up with one pattern node.")
    sentences.append(
        f"Displayed confidence for this wording is {capped:.2f} of {CONFIDENCE_CAP:.2f}."
    )
    sentences.append(
        f"Uncertainty is {uncertainty:.2f}, and the {int(UNCERTAINTY_FLOOR * 100)}% floor stays in place."
    )
    if top and top.get("seed_fixture") and top.get("qid"):
        fixture = top["seed_fixture"]
        sentences.append(
            f"The seeded walk records {fixture['value']} for {top['qid']}."
        )
    provisional = " ".join(sentences)
    note = (
        f"Verification question mapped in this package. "
        f"Linked {', '.join(item['id'] for item in linked) if linked else 'no single pattern'}. "
        f"Displayed confidence {capped:.3f} of {CONFIDENCE_CAP}. "
        f"Uncertainty {uncertainty:.3f} keeps the {int(UNCERTAINTY_FLOOR * 100)}% floor. "
        "Assistive only. This does not solve the case."
    )
    scores = Scores(
        official_contradiction=float(scored.get("official_contradiction") or 0.0),
        alternative_coherence=float(scored.get("alternative_coherence") or 0.0),
        raw_confidence=float(scored.get("raw_confidence") or 0.0),
        capped_confidence=capped,
    )
    ledger = [
        {
            "id": "U001",
            "created_at": utc_now(),
            "kind": "verify",
            "text": note,
            "pattern_id": top["id"] if top else None,
            "qid": top.get("qid") if top else None,
        }
    ]
    receipt = mint_receipt(
        case="verify",
        issued_at=utc_now(),
        scores=scores,
        history=[],
        uncertainty_ledger=ledger,
        termination_type=None,
        version=__version__,
        extra={
            "kind": "verify",
            "question": text,
            "provisional_answer": provisional,
            "linked_patterns": linked,
            "uncertainty": round(uncertainty, 6),
        },
    )
    return {
        "ok": True,
        "question": text,
        "provisional_answer": provisional,
        "linked_patterns": linked,
        "capped_confidence": cap_confidence(receipt.capped_confidence),
        "uncertainty": uncertainty,
        "uncertainty_note": note,
        "sha256": receipt.sha256,
        "receipt": receipt.to_dict(),
        "author": "Aziel Eliab",
    }
