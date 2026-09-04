"""Volumes 1–5 derive: seed archive never scores 0 / not_applicable."""

from __future__ import annotations

import pytest

from zion_pattern_solver.derive import (
    LAYER_QUESTIONS,
    LAYER_SEED,
    LAYER_SILENCE,
    LAYER_SUPPRESSION,
    METHOD,
    VOLUME_METHOD,
    VOLUME_METHOD_LAYERS,
    VOLUMES,
    derive_answers,
    derive_answers_from_document,
    resolve_score_input,
    resolve_score_payload,
    score_document,
)
from zion_pattern_solver.scoring import CONFIDENCE_CAP

VOLUME_TITLES = [
    "Marion A. Zioncheck Visual Archive Vol 1 — Primary Documents, Death Certificates & Forensic Analysis",
    "Marion A. Zioncheck Visual Archive Vol 2 — Contemporary News Coverage & Family Battles",
    "Marion A. Zioncheck Visual Archive Vol 3 — Funeral, Personal Photos, Timeline & Research",
    "Marion A. Zioncheck Visual Archive Vol 4 — The Physics Case: Why Marion Zioncheck Could Not Have Jumped",
    "Marion A. Zioncheck Vol 5 — The Human & Institutional Evidence",
]

CORPUS_FILENAMES = [
    "Marion_A_Zioncheck_Visual_Archive_Vol_1_Primary_Documents_Death_Certificates_For.pdf",
    "Marion_A_Zioncheck_Visual_Archive_Vol_2_Contemporary_News_Coverage_Family_Battle.pdf",
    "Marion_A_Zioncheck_Visual_Archive_Vol_3_Funeral_Personal_Photos_Timeline_Researc.pdf",
    "Marion_A_Zioncheck_Vol_4_The_Physics_Case_Why_Marion_Zioncheck_Could_Not_Have_Ju.pdf",
    "Marion_A_Zioncheck_Vol_5_The_Human_Institutional_Evidence.pdf",
]


def _yes(result: dict) -> list[dict]:
    return [a for a in result["answers"] if a.get("value") == "yes"]


def test_five_public_volume_titles_are_seed_and_capped() -> None:
    assert len(VOLUMES) == 5
    for title in VOLUME_TITLES:
        result = resolve_score_payload({"title": title})
        yeses = _yes(result)
        assert result["seed_corpus"] is True, title
        assert result["derived"] is True, title
        assert result["capped_confidence"] > 0, title
        assert result["capped_confidence"] <= CONFIDENCE_CAP, title
        assert result["display"] > 0, title
        assert yeses, f"expected non-empty yes answers for {title}"
        assert result["method"] == VOLUME_METHOD
        assert result["method"] == METHOD
        assert result["layers_active"]
        assert set(result["layers_active"]) >= {
            "seed_patterns",
            "pattern_answers",
            "pattern_questions",
            "pattern_of_suppression",
            "pattern_of_official_story_to_silence",
        }


def test_corpus_filenames_with_thin_pdf_metadata_are_not_zero() -> None:
    """Prior failure: filename + keywords 'Zioncheck, evidence, archive' → all unknown → 0."""
    for name in CORPUS_FILENAMES:
        payload = {
            "filename": name,
            "subjects": "Marion Zioncheck, investigation",
            "keywords": "Zioncheck, evidence, archive",
            "domain": "history",
        }
        result = resolve_score_input(payload)
        assert result["seed_corpus"] is True, name
        assert result["capped_confidence"] > 0, name
        assert result["capped_confidence"] <= 0.75, name
        assert result["display"] != 0, name
        assert _yes(result), name


def test_arctic_building_document_is_seed() -> None:
    result = score_document({"title": "Arctic Building event window, Seattle, 7 August 1936"})
    assert result["seed_corpus"] is True
    assert result["capped_confidence"] > 0
    assert result["capped_confidence"] <= 0.75
    assert _yes(result)


def test_unrelated_document_may_display_zero() -> None:
    result = resolve_score_input(
        {
            "title": "AEEM HVAC Energy Valve — Consumer Retrofit Whitepaper",
            "domain": "engineering",
            "filename": "aeem-hvac-energy-valve-whitepaper-v1.pdf",
        }
    )
    assert result["seed_corpus"] is False
    assert result["capped_confidence"] == 0.0
    assert result["display"] == 0
    assert result["method"] is None
    assert not _yes(result)


def test_explicit_answers_are_not_overwritten_by_title() -> None:
    result = resolve_score_input(
        {
            "title": "Marion A. Zioncheck Visual Archive Vol 1 — Primary Documents",
            "answers": [{"pattern_id": "P1", "value": "no"}],
        }
    )
    assert result["derived"] is False
    assert result["answers"][0]["value"] == "no"
    # a single no still scores 0 (yes/yes+no = 0); must not force seed yeses
    assert all(a["value"] != "yes" for a in result["answers"])


def test_answers_only_payload_still_caps() -> None:
    result = resolve_score_input(
        {
            "answers": [
                {"pattern_id": "P1", "value": "yes"},
                {"pattern_id": "P2", "value": "yes"},
                {"pattern_id": "P7", "value": "yes"},
            ]
        }
    )
    assert result["derived"] is False
    assert result["capped_confidence"] == 0.75
    assert result["display"] == 75


def test_volume_method_layers_are_the_exact_product() -> None:
    assert VOLUME_METHOD == (
        "seed_patterns×pattern_answers×pattern_questions"
        "×pattern_of_suppression×pattern_of_official_story_to_silence"
    )
    assert list(VOLUME_METHOD_LAYERS) == [1, 2, 3, 4, 5]
    assert VOLUME_METHOD_LAYERS[1]["layers"] == (LAYER_SEED,)
    assert VOLUME_METHOD_LAYERS[2]["layers"] == (LAYER_SILENCE, LAYER_SUPPRESSION)
    assert VOLUME_METHOD_LAYERS[3]["layers"] == (LAYER_QUESTIONS,)
    assert VOLUME_METHOD_LAYERS[4]["layers"] == (LAYER_SEED, LAYER_SILENCE)
    assert VOLUME_METHOD_LAYERS[5]["layers"] == (LAYER_SUPPRESSION,)
    assert "Family Battles" in VOLUME_METHOD_LAYERS[2]["public_title"]
    assert "Jumped" in VOLUME_METHOD_LAYERS[4]["public_title"]


def test_derive_answers_rationales_name_layers() -> None:
    derived = derive_answers_from_document(
        {"title": "Marion A. Zioncheck Visual Archive Vol 4 — The Physics Case"}
    )
    yeses = [a for a in derived["answers"] if a["value"] == "yes"]
    assert yeses
    assert all(a["rationale"].startswith("volumes-method:") for a in yeses)
    assert derived["seed_corpus"] is True
    assert 4 in derived["volumes_matched"]


def test_author_is_aziel_eliab_only() -> None:
    from pathlib import Path

    from zion_pattern_solver import __author__
    from zion_pattern_solver import derive as derive_mod

    assert __author__ == "Aziel Eliab"
    blob = Path(derive_mod.__file__).read_text(encoding="utf-8")
    assert "Aziel Eliab" in blob
    assert "Ever Blooming" not in blob
    assert "Jack Altman" not in blob


@pytest.mark.parametrize("n,title", [(v["n"], v["public_title"]) for v in VOLUMES])
def test_each_volume_public_title_maps(n: int, title: str) -> None:
    result = score_document({"title": f"Marion A. Zioncheck Visual Archive Volume {n} — {title}"})
    assert result["seed_corpus"] is True
    assert result["capped_confidence"] > 0
    assert n in result["volumes_matched"]
    assert _yes(result)


def test_worker_engine_matches_python() -> None:
    """Worker JS port must score volume titles the same way (seed, cap, yeses)."""
    import shutil
    import subprocess
    from pathlib import Path

    node = shutil.which("node")
    if not node:
        pytest.skip("node not available")
    script = Path(__file__).resolve().parents[1] / "workers" / "download-tracker" / "test-derive.mjs"
    proc = subprocess.run([node, str(script)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "ok worker volumes 1-5 derive" in proc.stdout
