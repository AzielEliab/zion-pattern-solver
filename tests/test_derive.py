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
    is_seed_corpus,
    rescore_related_on_pattern_break,
    resolve_score_input,
    resolve_score_payload,
    score_document,
)
from zion_pattern_solver.scoring import CONFIDENCE_CAP, SCORE_MEANING, display_meaning

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
        assert result["zsolver_status"] == "seed_baseline", title
        assert result["display_meaning"] == SCORE_MEANING["75"]
        displays.append(result["display"])
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


def test_arctic_building_is_not_seed_baseline() -> None:
    """Narrowed seed: Arctic Building alone is not Visual Archive vols 1–5."""
    result = score_document({"title": "Arctic Building event window, Seattle, 7 August 1936"})
    assert result["seed_corpus"] is False
    assert result["display"] != 75
    assert result["status"] != "seed_baseline"
    if result["display"] == 0:
        assert result["zsolver_status"] == "not_applicable"
    else:
        assert 1 <= result["display"] <= 74
        assert result["zsolver_status"] == "scored"


def test_bare_zioncheck_mention_is_not_seed() -> None:
    result = resolve_score_payload({"title": "Notes on Zioncheck in a later essay"})
    assert result["seed_corpus"] is False
    assert result["display"] != 75


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
    assert result["zsolver_status"] == "not_applicable"
    assert result["status"] == "not_applicable"
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
    assert "Ever Blooming" not in blob.replace("Never Ever Blooming", "")
    assert "Jack Altman" not in blob
    assert "intentional" in blob.lower() or "volumes 1" in blob


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
    assert strong["capped_confidence"] >= 0.15
    assert strong["zsolver_status"] == "scored"
    assert sparse["zsolver_status"] == "scored"
    assert hvac["zsolver_status"] == "not_applicable"


def test_public_volume_title_alone_is_seed_calibration() -> None:
    result = score_document(
        {"title": "The Physics Case: Why Marion Zioncheck Could Not Have Jumped"}
    )
    assert result["seed_corpus"] is True
    assert result["display"] == 75
    assert result["capped_confidence"] == 0.75
    assert result["zsolver_status"] == "seed_baseline"


def test_score_meaning_fields_are_honest() -> None:
    seed = resolve_score_payload(
        {"title": "Marion A. Zioncheck Visual Archive Vol 2 — Contemporary News Coverage & Family Battles"}
    )
    mid = resolve_score_payload(STRONG_MULTI_LAYER)
    none = resolve_score_payload(
        {"title": "AEEM HVAC Energy Valve — Consumer Retrofit Whitepaper", "domain": "engineering"}
    )
    assert seed["score_meaning"]["75"].startswith("complete confidence in intentional")
    assert "natural" in seed["score_meaning"]["1-74"]
    assert seed["score_meaning"]["0"].startswith("not_applicable")
    assert seed["display_meaning"] == display_meaning(75)
    assert mid["display"] < 75
    assert "intentional" in mid["display_meaning"] or "natural" in mid["display_meaning"]
    assert none["display_meaning"] == display_meaning(0)
    assert none["author"] == "Aziel Eliab"


def test_supersession_rescores_related_keeps_seed_at_75() -> None:
    related = [
        {"title": "Marion A. Zioncheck Visual Archive Vol 1 — Primary Documents, Death Certificates & Forensic Analysis"},
        {"title": "Window geometry field memo", "body": "sill height and building access last confirmed"},
        {"title": "AEEM HVAC Energy Valve — Consumer Retrofit Whitepaper", "domain": "engineering"},
    ]
    before = [score_document(d) for d in related]
    payload = resolve_score_payload(
        {
            "pattern_break": {
                "first_hand": True,
                "text": "first-hand pattern-break official story suppression supersession",
            },
            "related": related,
        }
    )
    assert payload["pattern_break"] is True
    assert payload["supersession"] is True
    assert len(payload["rescored"]) == 3
    assert payload["rescored"][0]["display"] == 75
    assert payload["rescored"][0]["seed_corpus"] is True
    assert payload["rescored"][2]["display"] == 0
    assert payload["rescored"][2]["zsolver_status"] == "not_applicable"
    # related non-seed may move after the break is folded in
    assert payload["rescored"][1]["seed_corpus"] is False
    assert before[0]["display"] == 75
    direct = rescore_related_on_pattern_break(
        related,
        {"first_hand": True, "text": "suppression official story first-hand"},
    )
    assert direct[0]["display"] == 75
    assert is_seed_corpus("marion a zioncheck visual archive vol 3 funeral")


def test_ai_surfaces_state_score_meaning() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    method = (root / "docs" / "methodology.md").read_text(encoding="utf-8")
    worker = (root / "workers" / "download-tracker" / "src" / "index.js").read_text(encoding="utf-8")
    for blob in (skill, readme, method, worker):
        assert "0.4.0" in blob
        assert "intentional" in blob.lower()
        assert "Ever Blooming" not in blob or "Never Ever Blooming" in blob
        assert "Jack Altman" not in blob
