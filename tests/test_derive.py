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
    apply_volumes_method,
    derive_answers,
    derive_answers_from_document,
    is_zioncheck_seed_document,
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
    displays = []
    for title in VOLUME_TITLES:
        result = resolve_score_payload({"title": title})
        yeses = _yes(result)
        assert result["seed_corpus"] is True, title
        assert result["derived"] is True, title
        assert result["capped_confidence"] == CONFIDENCE_CAP, title
        assert result["display"] == 75, title
        displays.append(result["display"])
        assert yeses, f"expected non-empty yes answers for {title}"
        assert result["method"] == VOLUME_METHOD
        assert result["method"] == METHOD
        assert result["layers_active"]
        # Single-volume titles do not stuff all five layers.
        assert set(result["layers_active"]) <= {
            "seed_patterns",
            "pattern_answers",
            "pattern_questions",
            "pattern_of_suppression",
            "pattern_of_official_story_to_silence",
        }
    assert displays == [75, 75, 75, 75, 75]


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
        assert result["capped_confidence"] == 0.75, name
        assert result["display"] == 75, name
        assert _yes(result), name


def test_arctic_building_mention_is_not_seed_floor() -> None:
    """Arctic Building / Zioncheck mentions score 1–75 by evidence, not flat 75."""
    result = score_document({"title": "Arctic Building event window, Seattle, 7 August 1936"})
    assert result["seed_corpus"] is False
    assert result["display"] != 75
    assert result["capped_confidence"] < CONFIDENCE_CAP
    if result["display"] > 0:
        assert 1 <= result["display"] <= 75


def test_zioncheck_mention_without_volume_is_not_seed() -> None:
    result = score_document({"title": "Marion Zioncheck newspaper clipping"})
    assert result["seed_corpus"] is False
    assert result["display"] < 75


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


def test_answers_only_intentional_patterns_hit_cap() -> None:
    result = resolve_score_input(
        {
            "answers": [
                {"pattern_id": "P5", "value": "yes"},
                {"pattern_id": "P6", "value": "yes"},
                {"pattern_id": "P8", "value": "yes"},
            ]
        }
    )
    assert result["derived"] is False
    assert result["capped_confidence"] == 0.75
    assert result["display"] == 75


def test_answers_only_non_intentional_is_below_cap() -> None:
    result = resolve_score_input({"answers": [{"pattern_id": "P1", "value": "yes"}]})
    assert result["derived"] is False
    assert result["seed_corpus"] is False
    assert result["display"] < 75
    assert result["raw_confidence"] == pytest.approx(0.35)


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
    assert result["capped_confidence"] == 0.75
    assert result["display"] == 75
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


SPARSE_NON_SEED = {
    "title": "Death certificate inventory note",
    "domain": "records",
}

WEAK_SINGLE_LAYER = {
    "title": "Window geometry field memo",
    "body": "sill height and building access last confirmed",
}

STRONG_MULTI_LAYER = {
    "title": "Official narrative lock and institutional suppression file",
    "body": (
        "timeline research funeral personal photos witness question "
        "evidence archive finding aid custody stationery investigation coroner "
        "suppression discredit unfit psychiatric congressional news coverage "
        "family battles official suicide jumped could not have wire "
        "narrative lock physics case official account official story"
    ),
}


def test_non_seed_documents_vary_between_1_and_75() -> None:
    sparse = resolve_score_payload(SPARSE_NON_SEED)
    weak = resolve_score_payload(WEAK_SINGLE_LAYER)
    strong = resolve_score_payload(STRONG_MULTI_LAYER)
    hvac = resolve_score_payload(
        {
            "title": "AEEM HVAC Energy Valve — Consumer Retrofit Whitepaper",
            "domain": "engineering",
        }
    )
    assert sparse["seed_corpus"] is False
    assert weak["seed_corpus"] is False
    assert strong["seed_corpus"] is False
    assert 1 <= sparse["display"] <= 75
    assert 1 <= weak["display"] <= 75
    assert 1 <= strong["display"] <= 75
    assert sparse["display"] < 75
    assert weak["display"] < 75
    assert hvac["display"] == 0
    displays = {sparse["display"], weak["display"], strong["display"]}
    assert len(displays) >= 2
    assert strong["display"] > sparse["display"]
    assert strong["display"] > weak["display"]
    assert strong["capped_confidence"] <= CONFIDENCE_CAP
    assert strong["capped_confidence"] >= 0.20


def test_public_volume_title_alone_is_seed_calibration() -> None:
    result = score_document(
        {"title": "The Physics Case: Why Marion Zioncheck Could Not Have Jumped"}
    )
    assert result["seed_corpus"] is True
    assert result["display"] == 75
    assert result["capped_confidence"] == 0.75


def test_is_zioncheck_seed_document_is_volumes_1_to_5_only() -> None:
    assert is_zioncheck_seed_document(
        "marion a zioncheck visual archive vol 1 primary documents"
    )
    assert is_zioncheck_seed_document(
        "the physics case: why marion zioncheck could not have jumped"
    )
    assert not is_zioncheck_seed_document("arctic building event window seattle 1936")
    assert not is_zioncheck_seed_document("marion zioncheck newspaper clipping")
    assert not is_zioncheck_seed_document("zioncheck arctic building notes")


def test_apply_volumes_method_does_not_stuff_seed_floor() -> None:
    vol1 = apply_volumes_method(
        "marion a zioncheck visual archive vol 1 primary documents death certificates"
    )
    assert vol1["seed_corpus"] is True
    assert "seed_patterns" in vol1["layers"]
    assert set(vol1["layers"]) != {
        "seed_patterns",
        "pattern_answers",
        "pattern_questions",
        "pattern_of_suppression",
        "pattern_of_official_story_to_silence",
    }
    mention = apply_volumes_method("arctic building event window seattle 1936")
    assert mention["seed_corpus"] is False
