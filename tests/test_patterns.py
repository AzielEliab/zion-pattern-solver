"""Nine versioned patterns load with required fields."""

from __future__ import annotations

from zion_pattern_solver.patterns import PATTERNS, SCHEMA_VERSION, get_patterns, iter_questions


def test_nine_patterns_load() -> None:
    pats = get_patterns()
    assert len(pats) == 9
    assert len(PATTERNS) == 9
    assert [p.id for p in pats] == [f"P{i}" for i in range(1, 10)]


def test_pattern_fields_and_version() -> None:
    names = [
        "Kinematic & Timeline Impossibility",
        "Document Provenance & Integrity",
        "Witness & Archival Void",
        "Geographic / Location Manipulation",
        "Pre-Event Discrediting & Suppression",
        "Political / Motive Contextual",
        "Secondary Encoded Testimony / Rubye",
        "Rapid Narrative Lock",
        "Forensic / Physical Evidence Gap",
    ]
    prios = ["critical", "critical", "high", "medium", "high", "medium", "critical", "high", "high"]
    for p, name, pri in zip(PATTERNS, names, prios, strict=True):
        assert p.name == name
        assert p.priority == pri
        assert p.version == SCHEMA_VERSION
        assert p.core_contradiction
        assert p.detection_heuristic
        assert p.evidence_priority
        assert len(p.question_templates) >= 2
        for q in p.question_templates:
            assert q.prompt
            assert q.evidence_type
            d = p.to_dict()
            assert isinstance(d["question_templates"], list)
            assert "prompt" in d["question_templates"][0]


def test_questions_walk_all_templates() -> None:
    qs = iter_questions()
    assert len(qs) == sum(len(p.question_templates) for p in PATTERNS)
    assert qs[0].qid == "P1:q0"
    assert all(q.qid.startswith("P") for q in qs)
