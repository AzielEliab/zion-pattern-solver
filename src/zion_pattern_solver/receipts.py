"""JSON receipts: history, scores, uncertainty ledger, SHA-256, disclaimer.

Canonical encoding (TemporalLock-style, reimplemented in-tree — this
package does not import temporallock):

    UTF-8 JSON, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    The ``sha256`` field is excluded from the hashed payload.
    Floats in scores are emitted with 6 decimal places.

Displayed ``capped_confidence`` always passes through ``cap_confidence``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from zion_pattern_solver.errors import ReceiptError
from zion_pattern_solver.scoring import CONFIDENCE_CAP, UNCERTAINTY_FLOOR, Scores, cap_confidence

DISCLAIMER = (
    "Provisional and assistive only. ZionPattern Solver does not solve "
    "Zioncheck or any case. Maximum displayed/stored conclusion confidence "
    "is 75% — complete confidence the suppression was intentional. Lower "
    "scores mean less confidence it was intentional (more natural occurrence). "
    "Irreducible uncertainty floor is 25% and must be documented in "
    "the uncertainty_ledger of every termination receipt. Human-in-the-loop. "
    "Local-first. Not a courtroom verdict."
)

SCHEMA = "zion-pattern-solver.receipt.v0.2"
CONFIDENCE_DECIMALS = 6
_PLACEHOLDER = "__ZS_FLOAT__"


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _fmt(value: float) -> str:
    return f"{float(value):.{CONFIDENCE_DECIMALS}f}"


def _walk_replace(obj: Any) -> Any:
    """Replace floats with a placeholder string so json.dumps stays stable."""
    if isinstance(obj, float):
        return _PLACEHOLDER + _fmt(obj)
    if isinstance(obj, dict):
        return {k: _walk_replace(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_walk_replace(v) for v in obj]
    return obj


def canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    """Canonical UTF-8 JSON of payload without the sha256 field."""
    body = {k: v for k, v in payload.items() if k != "sha256"}
    walked = _walk_replace(body)
    raw = json.dumps(walked, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    # unquote placeholders so scores remain JSON numbers with 6 decimals
    while True:
        start = raw.find('"' + _PLACEHOLDER)
        if start < 0:
            break
        end = raw.find('"', start + 1)
        token = raw[start + 1 + len(_PLACEHOLDER) : end]
        raw = raw[:start] + token + raw[end + 1 :]
    return raw.encode("utf-8")


def digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def verify_payload(payload: Mapping[str, Any]) -> bool:
    stored = str(payload.get("sha256", ""))
    if not stored:
        return False
    return stored == digest(payload)


@dataclass
class UncertaintyNote:
    id: str
    created_at: str
    kind: str
    text: str
    pattern_id: str | None = None
    qid: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "kind": self.kind,
            "text": self.text,
            "pattern_id": self.pattern_id,
            "qid": self.qid,
        }


@dataclass
class Receipt:
    payload: dict[str, Any]

    @property
    def sha256(self) -> str:
        return str(self.payload.get("sha256", ""))

    @property
    def capped_confidence(self) -> float:
        return cap_confidence(self.payload.get("capped_confidence", 0.0))

    def hash_ok(self) -> bool:
        return verify_payload(self.payload)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.payload, indent=indent, ensure_ascii=False) + "\n"

    def write(self, path: str) -> None:
        from pathlib import Path

        Path(path).write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Receipt":
        if not isinstance(data, Mapping):
            raise ReceiptError("receipt must be a JSON object")
        payload = dict(data)
        if "capped_confidence" in payload:
            payload["capped_confidence"] = cap_confidence(payload["capped_confidence"])
        scores = payload.get("scores")
        if isinstance(scores, dict) and "capped_confidence" in scores:
            scores = dict(scores)
            scores["capped_confidence"] = cap_confidence(scores["capped_confidence"])
            payload["scores"] = scores
        return cls(payload=payload)

    @classmethod
    def load(cls, path: str) -> "Receipt":
        from pathlib import Path

        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(raw)


def mint_receipt(
    *,
    case: str,
    issued_at: str,
    scores: Scores,
    history: list[dict[str, Any]],
    uncertainty_ledger: list[dict[str, Any]],
    termination_type: str | None,
    version: str,
    extra: Mapping[str, Any] | None = None,
) -> Receipt:
    capped = cap_confidence(scores.capped_confidence)
    if capped > CONFIDENCE_CAP:
        raise ReceiptError("capped_confidence exceeded 0.75")
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "product": "ZionPattern Solver",
        "version": version,
        "case": case,
        "issued_at": issued_at,
        "termination": {
            "type": termination_type,
            "status": "provisional",
        },
        "scores": scores.to_dict(),
        "capped_confidence": round(capped, CONFIDENCE_DECIMALS),
        "history": list(history),
        "uncertainty_ledger": list(uncertainty_ledger),
        "disclaimer": DISCLAIMER,
        "uncertainty_floor": UNCERTAINTY_FLOOR,
        "confidence_cap": CONFIDENCE_CAP,
    }
    if extra:
        for k, v in extra.items():
            if k == "sha256":
                continue
            payload[k] = v
    payload["sha256"] = digest(payload)
    rec = Receipt(payload=payload)
    if rec.capped_confidence > CONFIDENCE_CAP:
        raise ReceiptError("capped_confidence exceeded 0.75 after mint")
    return rec
