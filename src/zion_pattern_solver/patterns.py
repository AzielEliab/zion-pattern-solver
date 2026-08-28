"""Nine ZionPattern ontology nodes (versioned dataclasses).

Seeded on the Marion A. Zioncheck (1936) public historical record.
Questions are archival / documentary. They do not accuse living people
and they do not "solve" the case. Pattern version: 0.2.0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

SCHEMA_VERSION = "0.2.0"

CRITICAL = "critical"
HIGH = "high"
MEDIUM = "medium"


@dataclass(frozen=True)
class QuestionTemplate:
    """One interrogative node. ``prompt`` is shown to the human analyst."""

    prompt: str
    evidence_type: str


@dataclass(frozen=True)
class Pattern:
    """One anomaly pattern category (whitepaper 75% Cap Edition)."""

    id: str
    name: str
    priority: str
    core_contradiction: str
    question_templates: tuple[QuestionTemplate, ...]
    detection_heuristic: str
    evidence_priority: str
    version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "priority": self.priority,
            "core_contradiction": self.core_contradiction,
            "question_templates": [
                {"prompt": q.prompt, "evidence_type": q.evidence_type}
                for q in self.question_templates
            ],
            "detection_heuristic": self.detection_heuristic,
            "evidence_priority": self.evidence_priority,
            "version": self.version,
        }


def _q(*pairs: tuple[str, str]) -> tuple[QuestionTemplate, ...]:
    return tuple(QuestionTemplate(prompt=p, evidence_type=e) for p, e in pairs)


P1 = Pattern(
    id="P1",
    name="Kinematic & Timeline Impossibility",
    priority=CRITICAL,
    core_contradiction=(
        "The published August 7, 1936 timeline cannot simultaneously "
        "satisfy last-confirmed public movements, building access, and "
        "the reported event window without an unexplained gap."
    ),
    question_templates=_q(
        (
            "Does the published August 7, 1936 timeline leave an unexplained "
            "gap between the last confirmed public sighting of Representative "
            "Marion A. Zioncheck and the Arctic Building event window?",
            "timeline",
        ),
        (
            "Do contemporaneous public accounts disagree on the clock time "
            "and sequence of movements inside or toward the Arctic Building?",
            "timeline",
        ),
        (
            "Is the official kinematic account (window geometry, approach, "
            "and elapsed time) under-specified in surviving public reports "
            "such that it cannot be independently reconstructed?",
            "forensic",
        ),
    ),
    detection_heuristic=(
        "Flag when two or more public clocks or routes cannot be true at once, "
        "or when reconstruction requires unstated intervals."
    ),
    evidence_priority="timeline tables, building plans, contemporaneous press clocks",
)

P2 = Pattern(
    id="P2",
    name="Document Provenance & Integrity",
    priority=CRITICAL,
    core_contradiction=(
        "Publicly catalogued stationery and note artifacts tied to the 1936 "
        "record raise provenance and physical-integrity questions (emboss, "
        "transport, overwrite) that the official account does not resolve."
    ),
    question_templates=_q(
        (
            "Do public archival catalogs describe the purported 1936 note as "
            "written on U.S. House stationery whose custody chain is incomplete?",
            "document",
        ),
        (
            "Have independent catalogs or later inventories noted physical "
            "anomalies (off-center emboss, transport creases, erasure or "
            "overwrite marks) on documents associated with the 1936 record?",
            "document",
        ),
        (
            "Is there a published finding aid that cannot place the note's "
            "creation time relative to the Arctic Building event window?",
            "document",
        ),
    ),
    detection_heuristic=(
        "Flag stationery/note items whose catalog entries mention incomplete "
        "custody, later insertion, or physical alteration indicators."
    ),
    evidence_priority="finding aids, stationery photographs, custody logs",
)

P3 = Pattern(
    id="P3",
    name="Witness & Archival Void",
    priority=HIGH,
    core_contradiction=(
        "Named contemporaneous witnesses and expected institutional records "
        "are missing, delayed, unnamed, or compressed in the public archive."
    ),
    question_templates=_q(
        (
            "Does the public archive lack named, on-the-record witnesses for "
            "the minutes surrounding the Arctic Building event, beyond later "
            "second-hand summaries?",
            "witness",
        ),
        (
            "Are expected institutional files (building, police blotter, "
            "coroner docket) absent, delayed, or reduced to a short summary "
            "in surviving catalogs?",
            "archive",
        ),
        (
            "Do later retellings introduce an unnamed or late-appearing "
            "figure whose role is not anchored in a contemporaneous named source?",
            "witness",
        ),
    ),
    detection_heuristic=(
        "Flag unnamed 'someone' figures, missing blotters, and summaries that "
        "replace primary witness lists."
    ),
    evidence_priority="blotters, named depositions, building logs, catalog gaps",
)

P4 = Pattern(
    id="P4",
    name="Geographic / Location Manipulation",
    priority=MEDIUM,
    core_contradiction=(
        "Public location claims — Arctic Building, travel between Washington, "
        "D.C. and Seattle, and reported routes — contain inconsistencies in "
        "the surviving 1936 record."
    ),
    question_templates=_q(
        (
            "Do public sources disagree on which Arctic Building floor, "
            "window, or street-facing elevation is described?",
            "geographic",
        ),
        (
            "Is the D.C.–Seattle travel itinerary in the days before "
            "August 7, 1936 internally inconsistent across public schedules?",
            "timeline",
        ),
        (
            "Do maps or building directories from 1936 fail to corroborate "
            "a location detail that later narratives treat as settled?",
            "geographic",
        ),
    ),
    detection_heuristic=(
        "Flag floor/window/route mismatches and itineraries that skip "
        "required travel time."
    ),
    evidence_priority="1936 directories, rail/air schedules, building plans",
)

P5 = Pattern(
    id="P5",
    name="Pre-Event Discrediting & Suppression",
    priority=HIGH,
    core_contradiction=(
        "In the months before August 1936, public and Congressional framing "
        "shifted toward incapacity and psychiatric narratives in ways that "
        "later constrained what questions could be asked."
    ),
    question_templates=_q(
        (
            "Does the Congressional Record or contemporaneous press show a "
            "pre-August 1936 shift toward depicting Zioncheck as unfit, "
            "before the Arctic Building event?",
            "media",
        ),
        (
            "Are there public expungement, omission, or 'not printed' notes "
            "in the Congressional Record around Zioncheck's 1936 speeches?",
            "document",
        ),
        (
            "Did official or press psychiatric framing precede independent "
            "examination of the 1936 scene in published accounts?",
            "media",
        ),
    ),
    detection_heuristic=(
        "Flag incapacity narratives that lock in before scene measurements "
        "or named forensic files exist."
    ),
    evidence_priority="Congressional Record, 1936 press, hospital-admission public notices",
)

P6 = Pattern(
    id="P6",
    name="Political / Motive Contextual",
    priority=MEDIUM,
    core_contradiction=(
        "Zioncheck's public political conflicts (New Deal left, anti-war "
        "positions, Washington state machine fights) supply motive-context "
        "that a suicide-only official account does not engage. Context is "
        "not proof."
    ),
    question_templates=_q(
        (
            "Does the official public account engage Zioncheck's documented "
            "1935–1936 political conflicts as investigative context, or "
            "does it omit them?",
            "political",
        ),
        (
            "Are there contemporaneous public threats, expulsions-from-floor "
            "episodes, or machine-politics clashes recorded in newspapers "
            "or the Record that later summaries drop?",
            "political",
        ),
        (
            "Would an analyst relying only on the official one-line cause "
            "miss publicly documented political context from 1936?",
            "political",
        ),
    ),
    detection_heuristic=(
        "Flag official summaries that strip documented political conflict "
        "and leave only a medical/suicide line."
    ),
    evidence_priority="1936 newspapers, Congressional Record, campaign files",
)

P7 = Pattern(
    id="P7",
    name="Secondary Encoded Testimony / Rubye",
    priority=CRITICAL,
    core_contradiction=(
        "Later public artistic and documentary work associated with Rubye "
        "(widow of Marion A. Zioncheck) is treated by some researchers as "
        "encoded testimony. This is a pattern to interrogate, not a "
        "conclusion and not an accusation of any living person."
    ),
    question_templates=_q(
        (
            "Does publicly exhibited or published work associated with Rubye "
            "after 1936 use dates, architecture, or documentary fragments "
            "that point back to the August 1936 record?",
            "artistic",
        ),
        (
            "Have catalogs of that work noted geometric or archival markers "
            "that independent researchers have proposed as testimony rather "
            "than solely as memorial art?",
            "artistic",
        ),
        (
            "Is there a citable public source (exhibition note, memoir, "
            "dated artwork) rather than rumor for any Rubye-linked claim "
            "used in this session?",
            "document",
        ),
    ),
    detection_heuristic=(
        "Require a citable public artifact. Treat interpretation as "
        "provisional; never treat art as a verdict."
    ),
    evidence_priority="exhibition catalogs, dated public artworks, memoirs",
)

P8 = Pattern(
    id="P8",
    name="Rapid Narrative Lock",
    priority=HIGH,
    core_contradiction=(
        "Press and official statements locked a suicide narrative within "
        "hours, before independent measurement of the scene appears in "
        "the public record."
    ),
    question_templates=_q(
        (
            "Did major Seattle or wire-service accounts on August 7–8, 1936 "
            "state a suicide conclusion before naming an independent "
            "examiner or publishing scene measurements?",
            "media",
        ),
        (
            "Do later editions copy the first-day cause line with no added "
            "forensic detail?",
            "media",
        ),
        (
            "Is there a public correction, reopen, or dissenting official "
            "note in 1936 that failed to move the locked narrative?",
            "media",
        ),
    ),
    detection_heuristic=(
        "Flag same-day cause-of-death lock plus copy-forward across editions."
    ),
    evidence_priority="edition timestamps, wire copy, official bulletins",
)

P9 = Pattern(
    id="P9",
    name="Forensic / Physical Evidence Gap",
    priority=HIGH,
    core_contradiction=(
        "No surviving independent forensic file (scene measurements, window "
        "geometry, medical-examiner chain of custody) is adequate to test "
        "the official kinematic claim."
    ),
    question_templates=_q(
        (
            "Does a public catalog list a 1936 medical-examiner or coroner "
            "file with measurements that would let an independent analyst "
            "test the official account?",
            "forensic",
        ),
        (
            "Are window dimensions, sill height, and interior layout of the "
            "relevant Arctic Building room present in a 1936 or later "
            "survey usable as evidence?",
            "forensic",
        ),
        (
            "Is the chain of custody for physical items (clothing, note, "
            "photographs) documented in a public finding aid?",
            "forensic",
        ),
    ),
    detection_heuristic=(
        "Flag missing measurements, missing examiner name, or custody that "
        "jumps from scene to narrative."
    ),
    evidence_priority="coroner dockets, building surveys, photo logs",
)

PATTERNS: tuple[Pattern, ...] = (P1, P2, P3, P4, P5, P6, P7, P8, P9)

assert len(PATTERNS) == 9
assert [p.id for p in PATTERNS] == [f"P{i}" for i in range(1, 10)]


def get_patterns() -> tuple[Pattern, ...]:
    return PATTERNS


def by_id(pattern_id: str) -> Pattern:
    for p in PATTERNS:
        if p.id == pattern_id:
            return p
    raise KeyError(pattern_id)


def priority_map() -> dict[str, str]:
    return {p.id: p.priority for p in PATTERNS}


@dataclass(frozen=True)
class QueuedQuestion:
    """A concrete question instance with a stable id (P1:q0)."""

    pattern_id: str
    index: int
    prompt: str
    evidence_type: str
    pattern_name: str
    priority: str

    @property
    def qid(self) -> str:
        return f"{self.pattern_id}:q{self.index}"

    def to_dict(self) -> dict:
        return {
            "qid": self.qid,
            "pattern_id": self.pattern_id,
            "index": self.index,
            "prompt": self.prompt,
            "evidence_type": self.evidence_type,
            "pattern_name": self.pattern_name,
            "priority": self.priority,
        }


def iter_questions(patterns: Sequence[Pattern] | None = None) -> tuple[QueuedQuestion, ...]:
    """Walk every template in pattern order (P1..P9)."""
    src = PATTERNS if patterns is None else tuple(patterns)
    out: list[QueuedQuestion] = []
    for pat in src:
        for i, tmpl in enumerate(pat.question_templates):
            out.append(
                QueuedQuestion(
                    pattern_id=pat.id,
                    index=i,
                    prompt=tmpl.prompt,
                    evidence_type=tmpl.evidence_type,
                    pattern_name=pat.name,
                    priority=pat.priority,
                )
            )
    return tuple(out)
