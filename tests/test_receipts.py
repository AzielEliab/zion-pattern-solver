"""Receipt hash stable; tampering breaks hash; cap on stored confidence."""

from __future__ import annotations

import json

from zion_pattern_solver.receipts import Receipt, digest, mint_receipt, verify_payload
from zion_pattern_solver.scoring import Scores, cap_confidence
from zion_pattern_solver.session import Session
from zion_pattern_solver.terminate import OFFICIAL_UNSUSTAINABLE, terminate


def _filled() -> Session:
    s = Session(case="zioncheck-1936", clock=lambda: "2026-07-18T12:00:00Z")
    u = 0
    while True:
        q = s.ask()
        if q is None:
            break
        if u < 4:
            s.answer("unknown", "u")
            u += 1
        else:
            s.answer("yes", "y")
    return s


def test_tampering_receipt_json_breaks_hash() -> None:
    rec = terminate(_filled(), OFFICIAL_UNSUSTAINABLE, issued_at="2026-07-18T12:00:00Z")
    payload = json.loads(json.dumps(rec.to_dict()))
    assert verify_payload(payload)
    payload["capped_confidence"] = 0.99
    assert not verify_payload(payload)
    payload2 = json.loads(json.dumps(rec.to_dict()))
    payload2["history"][0]["rationale"] = "tampered"
    assert not verify_payload(payload2)
    # loading still recaps stored confidence
    loaded = Receipt.from_dict({"capped_confidence": 0.99, "sha256": "x"})
    assert loaded.capped_confidence == 0.75


def test_mint_uses_cap_function() -> None:
    scores = Scores(
        official_contradiction=1.0,
        alternative_coherence=1.0,
        raw_confidence=0.99,
        capped_confidence=0.99,
    )
    rec = mint_receipt(
        case="t",
        issued_at="2026-07-18T12:00:00Z",
        scores=scores,
        history=[],
        uncertainty_ledger=[{"id": "U001", "text": "floor", "kind": "floor", "created_at": "Z", "pattern_id": None, "qid": None}],
        termination_type=None,
        version="0.2.0",
    )
    assert rec.capped_confidence == 0.75
    assert rec.payload["scores"]["capped_confidence"] <= 0.75
    assert rec.hash_ok()
    again = digest(rec.payload)
    assert again == rec.sha256


def test_disclaimer_present() -> None:
    rec = terminate(_filled(), OFFICIAL_UNSUSTAINABLE, issued_at="2026-07-18T12:00:00Z")
    text = rec.payload["disclaimer"].lower()
    assert "75" in rec.payload["disclaimer"]
    assert "provisional" in text or "assistive" in text
    assert "zioncheck" in text
