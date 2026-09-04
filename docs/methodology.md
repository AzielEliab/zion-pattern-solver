# Methodology (75% Cap Edition)

Whitepaper: **ZionPattern Solver**, 75% Cap Edition, July 18 2026,
Aziel Eliab.

This engine is **provisional and assistive only**. It does not solve
Zioncheck or any case. It walks nine versioned pattern templates,
records human yes/no/unknown answers with rationales, scores two
axes (`official_contradiction`, `alternative_coherence`), and emits
a SHA-256 receipt.

## Invariants

1. **Hard cap.** Displayed and stored conclusion confidence is
   `cap_confidence(raw) = min(raw, 0.75)` after non-finite/negative
   clamp. One function, used everywhere. Tests force 0.99 → 0.75.
2. **25% uncertainty floor.** Every termination receipt carries an
   `uncertainty_ledger` with at least three notes. Unknown answers
   and high score-deltas write notes automatically.
3. **Local-first.** The engine has no network calls. The localhost
   UI binds `127.0.0.1`.
4. **Human-in-the-loop.** The solver asks; the analyst answers.
5. **Receipts, not verdicts.** Termination types
   (`official_unsustainable`, `alternative_supported`,
   `evidence_exhaustion`) all require near-cap confidence **and**
   a documented ledger. Status on the receipt is always `provisional`.

## Scoring

Weighted yes/no over pattern priority (critical 1.0, high 0.7,
medium 0.4). Critical patterns get a 1.35× weight on the alternative
coherence axis. Unknowns are excluded from those axes and logged.

`raw_confidence = 0.55 * official_contradiction + 0.45 * alternative_coherence`

`capped_confidence = cap_confidence(raw_confidence)`

## Volumes 1–5 derive (library / document fields)

`POST /v1/score` accepts analyst `answers` **or** document fields
(`title`, `body`/`text`, `filename`, `subjects`, `keywords`, `domain`).

Derivation is this product, implemented as `VOLUME_METHOD_LAYERS`:

`seed patterns × pattern answers × pattern questions × pattern of suppression × pattern of official story to silence`

All five layers are found across the Marion A. Zioncheck Visual Archive
volumes 1–5 (public titles on azielcorpuslibrary.net). Author Aziel Eliab.

| Vol | Public title | Layer(s) in the product |
| --- | --- | --- |
| 1 | Primary Documents, Death Certificates & Forensic Analysis | **seed patterns** (+ forensic evidence) |
| 2 | Contemporary News Coverage & Family Battles | **official story to silence** + **suppression** |
| 3 | Funeral, Personal Photos, Timeline & Research | **pattern questions** |
| 4 | The Physics Case: Why Marion Zioncheck Could Not Have Jumped | **seed patterns** (kinematic contradiction of the official story) × official-silence |
| 5 | The Human & Institutional Evidence | **suppression** / institutional void |

**pattern answers** is the answering layer: P1–P9 answered from the other
four volume layers. The archive product is all five.

A Zioncheck / Marion Zioncheck / Arctic Building document is the design
seed, so every layer is active (the five volumes *are* the product).
P1–P9 nodes whose driving layers fired become `yes`. Displayed confidence
is still hard-capped at 75% / 25% floor. Unrelated documents stay unknown
and may display 0 — that is not a seed miss.

Worker: `deriveAnswersFromDocument` + `resolveScorePayload`.
Python: `derive_answers_from_document` + `resolve_score_payload`.

This replaces the failure mode where thin PDF metadata produced
all-unknown answers, score 0, and a library adapter marked the seed
archive `not_applicable`.

## Receipts

Canonical encoding is TemporalLock-style (reimplemented, no import):
UTF-8 JSON, sorted keys, separators `(",", ":")`, scores as numbers
with six decimal places. The `sha256` field is excluded from the
hashed payload. Tampering any hashed field breaks the digest.

## Ethics

Seed questions use the 1936 public historical record around
Representative Marion A. Zioncheck. No graphic content. No
accusations of living people. Pattern 7 (Rubye) is an interrogative
node about public art/documents, not a conclusion.
