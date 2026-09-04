"""Hard cap: displayed/stored conclusion confidence NEVER exceeds 0.75."""

from __future__ import annotations

import math

import pytest

from zion_pattern_solver.scoring import (
    CONFIDENCE_CAP,
    SCORE_MEANING,
    cap_confidence,
    display_meaning,
    display_score,
    score_answers,
    zsolver_status,
    Scores,
)


def test_cap_0_99_becomes_0_75() -> None:
    assert cap_confidence(0.99) == 0.75
    assert cap_confidence(0.99) == CONFIDENCE_CAP


def test_cap_never_exceeds() -> None:
    for raw in (0.0, 0.1, 0.75, 0.7500001, 0.99, 1.0, 2.0, 99.0, 1e9):
        assert cap_confidence(raw) <= 0.75
    assert cap_confidence(1.0) == 0.75


def test_display_score_clamps_positive() -> None:
    assert display_score(0.0) == 0
    assert display_score(0.001) == 1
    assert display_score(0.75) == 75
    assert display_score(0.99) == 75
    assert display_score(0.51) == 51
    assert display_meaning(75) == SCORE_MEANING["75"]
    assert "natural" in display_meaning(40)
    assert display_meaning(0) == SCORE_MEANING["0"]
    assert zsolver_status(75, seed=True) == "seed_baseline"
    assert zsolver_status(40) == "scored"
    assert zsolver_status(0) == "not_applicable"


def test_cap_identity_below() -> None:
    assert cap_confidence(0.5) == 0.5
    assert cap_confidence(0.0) == 0.0
    assert cap_confidence(0.75) == 0.75


def test_cap_nonfinite_and_negative() -> None:
    assert cap_confidence(float("nan")) == 0.0
    assert cap_confidence(float("inf")) == 0.0
    assert cap_confidence(float("-inf")) == 0.0
    assert cap_confidence(-0.4) == 0.0
    assert cap_confidence("nope") == 0.0  # type: ignore[arg-type]


def test_scores_object_recaps() -> None:
    s = Scores(
        official_contradiction=1.0,
        alternative_coherence=1.0,
        raw_confidence=0.99,
        capped_confidence=0.99,
    )
    assert s.capped_confidence == 0.75
    assert s.capped_confidence <= CONFIDENCE_CAP
    d = s.to_dict()
    assert d["capped_confidence"] <= 0.75
    assert d["raw_confidence"] == pytest.approx(0.99)


def test_score_answers_all_yes_hits_cap() -> None:
    answers = [
        {"pattern_id": "P1", "value": "yes"},
        {"pattern_id": "P2", "value": "yes"},
        {"pattern_id": "P7", "value": "yes"},
    ]
    pri = {"P1": "critical", "P2": "critical", "P7": "critical"}
    s = score_answers(answers, pri)
    assert s.raw_confidence == pytest.approx(1.0)
    assert s.capped_confidence == 0.75
    assert s.capped_confidence <= 0.75


def test_unknowns_in_denominator_prevent_saturation() -> None:
    pri = {f"P{i}": "medium" for i in range(1, 10)}
    pri["P1"] = "critical"
    answers = [{"pattern_id": "P1", "value": "yes"}] + [
        {"pattern_id": f"P{i}", "value": "unknown"} for i in range(2, 10)
    ]
    s = score_answers(answers, pri)
    assert s.raw_confidence < 0.40
    assert s.capped_confidence < 0.40
    assert s.capped_confidence > 0.0


def test_vote_strength_scales_yes() -> None:
    pri = {"P1": "critical", "P2": "critical"}
    full = score_answers(
        [{"pattern_id": "P1", "value": "yes"}, {"pattern_id": "P2", "value": "yes"}],
        pri,
    )
    partial = score_answers(
        [
            {"pattern_id": "P1", "value": "yes", "vote_strength": 0.35},
            {"pattern_id": "P2", "value": "yes", "vote_strength": 0.35},
        ],
        pri,
    )
    assert full.raw_confidence == pytest.approx(1.0)
    assert partial.raw_confidence == pytest.approx(0.35)
    assert partial.capped_confidence < full.capped_confidence
