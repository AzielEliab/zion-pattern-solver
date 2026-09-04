"""Derive P1–P9 answers from Zioncheck Visual Archive volumes 1–5.

Library adapters send document fields (title, body/text, filename, subjects,
keywords, domain) instead of analyst yes/no answers. A thin keyword pass on
PDF metadata used to yield all-unknown → score 0 → not_applicable. That is
wrong for this product: volumes 1–5 ARE the design seed.

Score meaning (authoritative, 0.4.0):

    75     = complete confidence in intentional suppression (hard cap)
    1–74   = less confidence it was intentional; more natural occurrence
    0      = not_applicable — hidden (non-match)

Seed baseline 75 = Zioncheck Visual Archive volumes 1–5 only.
Other qualifying docs vary 1–75 (intentional-suppression weighting).
Bare Zioncheck / Arctic Building mentions are not the seed.

Method (product of layers, all present in vols 1–5):

    seed_patterns
    × pattern_answers
    × pattern_questions
    × pattern_of_suppression
    × pattern_of_official_story_to_silence

Volume map (public titles on azielcorpuslibrary.net), Aziel Eliab:

    Vol 1 — Primary Documents, Death Certificates & Forensic Analysis
            → seed_patterns  (+ forensic evidence)
    Vol 2 — Contemporary News Coverage & Family Battles
            → pattern_of_official_story_to_silence × pattern_of_suppression
    Vol 3 — Funeral, Personal Photos, Timeline & Research
            → pattern_questions
    Vol 4 — The Physics Case: Why Marion Zioncheck Could Not Have Jumped
            → seed_patterns × pattern_of_official_story_to_silence
              (kinematic contradiction of the official story)
    Vol 5 — The Human & Institutional Evidence
            → pattern_of_suppression  (institutional void)

    pattern_answers is the answering layer: P1–P9 answered from the
    other four volume layers. The archive product is all five.

When a document is a Visual Archive volume 1–5 (title, filename, or
exact public title), it is the calibration base: display 75 /
capped_confidence 0.75. Every layer is active because the product of
those five volumes is the seed.

All other documents score 1–75 from evidence strength (layer votes,
unknowns in the denominator, layer-count, yes-coverage, and
intentional-suppression weighting: suppression + official-silence
layers raise the score; their absence pulls toward natural occurrence).
Hard cap remains 75%. Score 0 / not_applicable still means hide for
non-matches.

First-hand pattern-break on supersession rescored related docs
(seed vols stay 75). Author Aziel Eliab only. Never Ever Blooming.
Does not solve cases.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from zion_pattern_solver.patterns import PATTERNS, iter_questions, priority_map
from zion_pattern_solver.scoring import (
    CONFIDENCE_CAP,
    SCORE_MEANING,
    UNCERTAINTY_FLOOR,
    cap_confidence,
    display_meaning,
    display_score,
    score_answers,
    zsolver_status,
)

VOLUME_METHOD = (
    "seed_patterns×pattern_answers×pattern_questions"
    "×pattern_of_suppression×pattern_of_official_story_to_silence"
)
METHOD = VOLUME_METHOD

LAYER_SEED = "seed_patterns"
LAYER_ANSWERS = "pattern_answers"
LAYER_QUESTIONS = "pattern_questions"
LAYER_SUPPRESSION = "pattern_of_suppression"
LAYER_SILENCE = "pattern_of_official_story_to_silence"

ALL_LAYERS: tuple[str, ...] = (
    LAYER_SEED,
    LAYER_ANSWERS,
    LAYER_QUESTIONS,
    LAYER_SUPPRESSION,
    LAYER_SILENCE,
)

# Which layers drive each ontology node (product / union of those layers).
PATTERN_LAYERS: dict[str, tuple[str, ...]] = {
    "P1": (LAYER_SEED, LAYER_QUESTIONS, LAYER_SILENCE),
    "P2": (LAYER_SEED, LAYER_ANSWERS),
    "P3": (LAYER_ANSWERS, LAYER_QUESTIONS, LAYER_SUPPRESSION),
    "P4": (LAYER_SEED,),
    "P5": (LAYER_SUPPRESSION, LAYER_SILENCE),
    "P6": (LAYER_SUPPRESSION, LAYER_SILENCE),
    "P7": (LAYER_QUESTIONS,),
    "P8": (LAYER_SUPPRESSION, LAYER_SILENCE),
    "P9": (LAYER_SEED, LAYER_ANSWERS, LAYER_SILENCE),
}

DOCUMENT_FIELDS: tuple[str, ...] = (
    "title",
    "body",
    "text",
    "filename",
    "subjects",
    "keywords",
    "domain",
)

# Exact product map. pattern_answers is not a volume; it is the answering
# layer produced from the other four once the seed archive is in view.
VOLUME_METHOD_LAYERS: dict[int, dict[str, Any]] = {
    1: {
        "public_title": "Primary Documents, Death Certificates & Forensic Analysis",
        "layers": (LAYER_SEED,),
        "role": "seed patterns (+ forensic evidence)",
        "signals": (
            "primary documents",
            "death certificate",
            "death certificates",
            "forensic analysis",
            "forensic",
        ),
    },
    2: {
        "public_title": "Contemporary News Coverage & Family Battles",
        "layers": (LAYER_SILENCE, LAYER_SUPPRESSION),
        "role": "official story to silence + suppression",
        "signals": (
            "contemporary news",
            "news coverage",
            "family battles",
            "family",
        ),
    },
    3: {
        "public_title": "Funeral, Personal Photos, Timeline & Research",
        "layers": (LAYER_QUESTIONS,),
        "role": "pattern questions",
        "signals": (
            "funeral",
            "personal photos",
            "timeline",
            "research",
        ),
    },
    4: {
        "public_title": "The Physics Case: Why Marion Zioncheck Could Not Have Jumped",
        "layers": (LAYER_SEED, LAYER_SILENCE),
        "role": "seed kinematic contradiction of official story",
        "signals": (
            "physics case",
            "could not have",
            "could not have jumped",
            "kinematic",
        ),
    },
    5: {
        "public_title": "The Human & Institutional Evidence",
        "layers": (LAYER_SUPPRESSION,),
        "role": "suppression / institutional void",
        "signals": (
            "human & institutional",
            "human and institutional",
            "institutional evidence",
            "institutional void",
            "institutional",
        ),
    },
}

VOLUMES: tuple[dict[str, Any], ...] = tuple(
    {"n": n, **meta} for n, meta in VOLUME_METHOD_LAYERS.items()
)

# Ontology language from P1–P9 templates / heuristics — not an unrelated keyword list.
ONTOLOGY_LAYER_SIGNALS: dict[str, tuple[str, ...]] = {
    LAYER_SEED: (
        "august 7",
        "1936",
        "window geometry",
        "event window",
        "last confirmed",
        "building access",
    ),
    LAYER_ANSWERS: (
        "evidence",
        "archive",
        "finding aid",
        "custody",
        "stationery",
        "investigation",
        "death certificate",
        "coroner",
        "primary document",
    ),
    LAYER_QUESTIONS: (
        "timeline",
        "research",
        "funeral",
        "personal photos",
        "rubye",
        "encoded testimony",
        "witness",
        "question",
    ),
    LAYER_SUPPRESSION: (
        "suppression",
        "discredit",
        "unfit",
        "psychiatric",
        "expungement",
        "not printed",
        "congressional",
        "news coverage",
        "institutional",
        "family battles",
    ),
    LAYER_SILENCE: (
        "official",
        "suicide",
        "jumped",
        "could not have",
        "wire",
        "narrative lock",
        "one-line",
        "physics case",
        "official account",
        "official story",
    ),
}

ANSWER_VALUES = frozenset({"yes", "no", "unknown"})


def _flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple, set)):
        return " ".join(_flatten(item) for item in value)
    if isinstance(value, Mapping):
        return " ".join(_flatten(v) for v in value.values())
    return str(value)


def haystack_from(document: Mapping[str, Any] | None) -> str:
    """Join document fields into a tokenizable lowercase haystack."""
    if not document:
        return ""
    parts: list[str] = []
    for key in DOCUMENT_FIELDS:
        if key in document:
            parts.append(_flatten(document.get(key)))
    raw = " ".join(parts)
    # Filenames use underscores; treat them as spaces so Vol_1 matches.
    normalized = raw.replace("_", " ").replace("-", " ").replace(".", " ")
    return " ".join(normalized.lower().split())


def has_document_fields(payload: Mapping[str, Any] | None) -> bool:
    if not payload:
        return False
    for key in DOCUMENT_FIELDS:
        value = payload.get(key)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, (list, tuple)) and not value:
            continue
        return True
    return False


def looks_like_answers(raw: Any) -> bool:
    if raw is None:
        return False
    if isinstance(raw, list):
        if not raw:
            return False
        for item in raw:
            if isinstance(item, str):
                token = item.strip().lower()
                if token.startswith("p") or token in ANSWER_VALUES:
                    return True
                continue
            if isinstance(item, Mapping):
                value = str(item.get("value") or item.get("answer") or item.get("v") or "").lower()
                if value in ANSWER_VALUES or item.get("pattern_id") or item.get("qid"):
                    return True
        return False
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            key_s = str(key)
            if key_s[:1] in "Pp" and len(key_s) >= 2 and key_s[1].isdigit():
                return True
            inner = value.get("value") or value.get("answer") if isinstance(value, Mapping) else value
            if str(inner or "").lower() in ANSWER_VALUES:
                return True
        return False
    return False


def _volume_numbers_in(text: str) -> list[int]:
    found: list[int] = []
    for n in VOLUME_METHOD_LAYERS:
        if f"vol {n}" in text or f"volume {n}" in text or f"vol{n}" in text:
            found.append(n)
    return found


def is_seed_corpus(text: str) -> bool:
    """True only for Zioncheck Visual Archive volumes 1–5.

    Exact public titles, Visual Archive + vol N, or Zioncheck + vol N.
    Bare Zioncheck / Arctic Building mentions are not the seed baseline.
    """
    if not text:
        return False
    for vol in VOLUME_METHOD_LAYERS.values():
        title = str(vol.get("public_title") or "").lower()
        if title and title in text:
            return True
    vols = _volume_numbers_in(text)
    if vols and ("visual archive" in text or "zioncheck" in text):
        return True
    if "visual archive" in text and "zioncheck" in text:
        return True
    return False


def match_volumes(text: str) -> list[int]:
    """Match vols 1–5 by number, public title, or seed-scoped title signals.

    Bare words such as ``research`` or ``family`` do not count unless the
    haystack is already the Zioncheck / Arctic Building seed archive.
    """
    seedish = is_seed_corpus(text)
    matched: list[int] = []
    for n, vol in VOLUME_METHOD_LAYERS.items():
        numbered = f"vol {n}" in text or f"volume {n}" in text or f"vol{n}" in text
        titled = bool(vol["public_title"]) and str(vol["public_title"]).lower() in text
        signaled = any(signal in text for signal in vol["signals"])
        if numbered or titled or (signaled and seedish):
            matched.append(n)
    return matched


def layers_from_ontology(text: str) -> set[str]:
    """Activate layers from P1–P9 question / heuristic language."""
    active: set[str] = set()
    if not text:
        return active
    for layer, signals in ONTOLOGY_LAYER_SIGNALS.items():
        if any(sig in text for sig in signals):
            active.add(layer)
    # Question templates themselves: if several distinctive prompt tokens appear.
    hits = 0
    for q in iter_questions():
        prompt = q.prompt.lower()
        # distinctive multi-word fragments from the seeded questions
        for frag in (
            "unexplained gap",
            "house stationery",
            "named, on-the-record",
            "street-facing elevation",
            "depicting zioncheck as unfit",
            "political conflicts",
            "work associated with rubye",
            "suicide conclusion",
            "medical-examiner or coroner",
        ):
            if frag in prompt and frag in text:
                hits += 1
    if hits:
        active.add(LAYER_QUESTIONS)
        active.add(LAYER_ANSWERS)
    return active


def vote_strength_from_layer_votes(fired: int) -> float:
    """Map driving-layer vote count to 0.35–1.0 (1→0.35, 2→0.70, 3→1.0)."""
    if fired <= 0:
        return 0.0
    return min(1.0, max(0.35, 0.35 * float(fired)))


INTENTIONAL_LAYERS: frozenset[str] = frozenset({LAYER_SUPPRESSION, LAYER_SILENCE})


def intentional_scale(layers: Sequence[str] | None) -> float:
    """Weight toward intentional suppression vs natural occurrence.

    Both suppression + official-silence active → 1.00.
    Neither → 0.40 (more natural). One of the two → 0.70.
    """
    active = set(layers or ())
    n = sum(1 for layer in INTENTIONAL_LAYERS if layer in active)
    return 0.40 + 0.60 * (n / 2.0)


def active_layers(text: str, *, seed: bool | None = None) -> list[str]:
    """Product of VOLUME_METHOD_LAYERS.

    Seed archive (calibration base) activates every layer. Non-seed documents
    activate only layers evidenced in the text — never a bare marker fill.
    """
    if seed is None:
        seed = is_seed_corpus(text)
    layers: set[str] = set()
    volumes = match_volumes(text)
    if seed:
        # The five volumes together *are* the product. Calibration display 75.
        layers.update(ALL_LAYERS)
        return [layer for layer in ALL_LAYERS]
    for n, vol in VOLUME_METHOD_LAYERS.items():
        if n in volumes:
            layers.update(vol["layers"])
    layers.update(layers_from_ontology(text))
    if layers.intersection(
        {LAYER_SEED, LAYER_QUESTIONS, LAYER_SUPPRESSION, LAYER_SILENCE}
    ):
        layers.add(LAYER_ANSWERS)
    return [layer for layer in ALL_LAYERS if layer in layers]


def _rationale(layers: Sequence[str]) -> str:
    if not layers:
        return ""
    return "volumes-method:" + "×".join(layers)


def derive_answers_from_document(document: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return derived P1–P9 answers plus method metadata."""
    text = haystack_from(document)
    seed = is_seed_corpus(text)
    layers = active_layers(text, seed=seed)
    layer_set = set(layers)
    volumes = match_volumes(text)
    answers: list[dict[str, object]] = []
    for pat in PATTERNS:
        drivers = PATTERN_LAYERS[pat.id]
        fired = [layer for layer in drivers if layer in layer_set]
        if seed:
            answers.append(
                {
                    "pattern_id": pat.id,
                    "value": "yes",
                    "qid": "",
                    "rationale": _rationale(list(drivers)),
                    "vote_strength": 1.0,
                }
            )
        elif fired:
            answers.append(
                {
                    "pattern_id": pat.id,
                    "value": "yes",
                    "qid": "",
                    "rationale": _rationale(fired),
                    "vote_strength": vote_strength_from_layer_votes(len(fired)),
                }
            )
        else:
            rationale = ""
            if pat.id == "P7":
                rationale = "require-miss"
            answers.append(
                {
                    "pattern_id": pat.id,
                    "value": "unknown",
                    "qid": "",
                    "rationale": rationale,
                }
            )
    return {
        "answers": answers,
        "seed_corpus": seed,
        "method": VOLUME_METHOD if layers else None,
        "layers_active": layers or None,
        "volumes_matched": volumes,
        "derived": True,
    }


def derive_answers(document: Mapping[str, Any] | None) -> dict[str, Any]:
    """Alias of ``derive_answers_from_document``."""
    return derive_answers_from_document(document)


def score_document(document: Mapping[str, Any] | None) -> dict[str, Any]:
    """Derive from document fields, then score under the hard 75% cap."""
    derived = derive_answers_from_document(document or {})
    return _attach_scores(derived["answers"], derivation=derived)


def _attach_scores(
    answers: Iterable[Mapping[str, Any]],
    *,
    derivation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    rows = list(answers)
    scored = score_answers(rows, priority_map())
    unknown = sum(
        1
        for ans in rows
        if str(ans.get("value", "unknown")).lower() not in {"yes", "no"}
    )
    n_yes = sum(1 for ans in rows if str(ans.get("value", "")).lower() == "yes")
    seed = bool(derivation.get("seed_corpus")) if derivation else False
    if seed:
        raw = scored.raw_confidence
        capped = CONFIDENCE_CAP
        display = 75
    elif derivation:
        n_layers = len(derivation.get("layers_active") or [])
        layer_scale = n_layers / float(len(ALL_LAYERS))
        coverage = n_yes / float(len(PATTERNS)) if PATTERNS else 0.0
        intent = intentional_scale(derivation.get("layers_active") or [])
        raw = scored.raw_confidence * layer_scale * coverage * intent
        capped = cap_confidence(raw)
        display = display_score(capped)
    else:
        raw = scored.raw_confidence
        capped = cap_confidence(raw)
        display = display_score(capped)
    status = zsolver_status(display, seed=seed)
    payload: dict[str, Any] = {
        "official_contradiction": scored.official_contradiction,
        "alternative_coherence": scored.alternative_coherence,
        "raw_confidence": raw,
        "capped_confidence": capped,
        "uncertainty": max(UNCERTAINTY_FLOOR, 1.0 - capped) if capped else 1.0,
        "confidence_cap": CONFIDENCE_CAP,
        "uncertainty_floor": UNCERTAINTY_FLOOR,
        "answered": len(rows),
        "unknown_answers": unknown,
        "answers": rows,
        "display": display,
        "display_meaning": display_meaning(display),
        "score_meaning": dict(SCORE_MEANING),
        "status": status,
        "zsolver_status": status,
        "derived": bool(derivation),
        "seed_corpus": seed,
        "method": derivation.get("method") if derivation else None,
        "layers_active": derivation.get("layers_active") if derivation else None,
        "author": "Aziel Eliab",
        "disclaimer": (
            "Provisional and assistive only. Does not solve Zioncheck or any case. "
            "Score 75 = complete confidence in intentional suppression (hard cap). "
            "1–74 = less intentional / more natural. "
            "Seed Visual Archive vols 1–5 baseline 75. "
            "Non-matches hidden (not_applicable). Author Aziel Eliab."
        ),
    }
    if derivation and derivation.get("volumes_matched") is not None:
        payload["volumes_matched"] = derivation["volumes_matched"]
    return payload


def _break_event_from(src: Mapping[str, Any]) -> Mapping[str, Any] | None:
    raw = src.get("pattern_break") or src.get("supersession") or src.get("break")
    if isinstance(raw, Mapping):
        return raw
    if isinstance(raw, str) and raw.strip():
        return {"text": raw, "first_hand": True}
    if raw:
        return {"first_hand": True}
    return None


def fold_pattern_break(
    document: Mapping[str, Any],
    break_event: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Fold first-hand pattern-break text into a related document for rescore."""
    merged = dict(document)
    if not break_event:
        return merged
    extra = [_flatten(break_event)]
    blob = _flatten(break_event).lower()
    if break_event.get("first_hand") or break_event.get("first-hand") or "first-hand" in blob or "first hand" in blob:
        extra.append("first-hand pattern-break")
    if "suppression" in blob or break_event.get("suppression"):
        extra.append("suppression official story official account")
    merged["body"] = (" ".join([str(merged.get("body") or ""), *extra])).strip()
    return merged


def rescore_related_on_pattern_break(
    documents: Sequence[Mapping[str, Any]] | None,
    break_event: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """First-hand pattern-break on supersession rescored related docs.

    Seed Visual Archive vols 1–5 stay at display 75. Related non-seed
    documents are re-derived with the break text folded in so new
    first-hand evidence can move 1–74. Non-matches stay hidden.
    """
    out: list[dict[str, Any]] = []
    for doc in documents or ():
        baseline = score_document(doc)
        if is_seed_corpus(haystack_from(doc)) or baseline.get("display", 0) <= 0:
            baseline["pattern_break"] = True
            out.append(baseline)
            continue
        scored = score_document(fold_pattern_break(doc, break_event))
        scored["pattern_break"] = True
        out.append(scored)
    return out


def resolve_score_payload(body: Mapping[str, Any] | None) -> dict[str, Any]:
    """Accept either analyst ``answers`` or document fields."""
    src = dict(body or {})
    related = src.get("related") or src.get("related_docs") or src.get("documents")
    break_event = _break_event_from(src)
    if isinstance(related, Sequence) and not isinstance(related, (str, bytes)) and (
        break_event or src.get("rescore")
    ):
        rescored = rescore_related_on_pattern_break(
            [d for d in related if isinstance(d, Mapping)],
            break_event,
        )
        return {
            "rescored": rescored,
            "pattern_break": True,
            "supersession": True,
            "author": "Aziel Eliab",
            "score_meaning": dict(SCORE_MEANING),
            "disclaimer": (
                "First-hand pattern-break on supersession rescored related docs. "
                "Seed Visual Archive vols 1–5 stay at 75. Does not solve cases. "
                "Author Aziel Eliab."
            ),
        }
    explicit = src.get("answers")
    if looks_like_answers(explicit):
        return _attach_scores(
            _normalize_explicit(explicit),
            derivation=None,
        )
    if has_document_fields(src) or is_seed_corpus(haystack_from(src)):
        return score_document(src)
    if looks_like_answers(src):
        return _attach_scores(_normalize_explicit(src), derivation=None)
    # Empty / unrelated object: still run derive so adapters get a stable shape.
    if src:
        return score_document(src)
    return _attach_scores([], derivation=None)


def resolve_score_input(body: Mapping[str, Any] | None) -> dict[str, Any]:
    """Alias of ``resolve_score_payload``."""
    return resolve_score_payload(body)


def _normalize_explicit(raw: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                parts = item.replace(":", " ").split()
                out.append(
                    {
                        "pattern_id": parts[0] if parts else "",
                        "value": (parts[1] if len(parts) > 1 else "unknown").lower(),
                        "qid": item,
                        "rationale": "",
                    }
                )
                continue
            if isinstance(item, Mapping):
                qid = str(item.get("qid") or item.get("id") or "")
                pid = str(item.get("pattern_id") or item.get("pattern") or "")
                if not pid and ":" in qid:
                    pid = qid.split(":", 1)[0]
                row = {
                    "pattern_id": pid,
                    "value": str(
                        item.get("value") or item.get("answer") or item.get("v") or "unknown"
                    ).lower(),
                    "qid": qid,
                    "rationale": str(item.get("rationale") or ""),
                }
                if item.get("vote_strength") is not None:
                    row["vote_strength"] = item.get("vote_strength")
                out.append(row)
        return out
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            qid = str(key)
            pid = qid.split(":", 1)[0] if ":" in qid else qid
            inner = value.get("value") or value.get("answer") if isinstance(value, Mapping) else value
            rationale = value.get("rationale", "") if isinstance(value, Mapping) else ""
            row = {
                "pattern_id": pid,
                "value": str(inner or "unknown").lower(),
                "qid": qid,
                "rationale": str(rationale or ""),
            }
            if isinstance(value, Mapping) and value.get("vote_strength") is not None:
                row["vote_strength"] = value.get("vote_strength")
            out.append(row)
    return out
