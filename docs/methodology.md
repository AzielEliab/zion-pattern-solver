# Methodology (0.4.0 — intentional-suppression edition)

Whitepaper: **ZionPattern Solver**, 75% Cap Edition, July 18 2026,
Aziel Eliab only. Never Ever Blooming.

This engine is **provisional and assistive only**. It does not solve
Zioncheck or any case. It walks nine versioned pattern templates,
records human yes/no/unknown answers with rationales, scores two
axes (`official_contradiction`, `alternative_coherence`), and emits
a SHA-256 receipt.

**Score meaning (authoritative):**

- **75** = complete confidence in **intentional** suppression (hard cap)
- **1–74** = less confidence it was intentional; more natural occurrence
  of suppression
- **0** / `not_applicable` = non-match, hidden

Seed baseline 75 = Zioncheck Visual Archive volumes 1–5 only.

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

Weighted yes/no/unknown over pattern priority (critical 1.0, high 0.7,
medium 0.4). Critical patterns get a 1.35× weight on the alternative
coherence axis. Unknowns are excluded from numerators and **included**
in the denominator so a lone yes cannot saturate at 1.0. Yes answers
may carry `vote_strength` (0.35–1.0 from layer votes; default 1.0).

`raw_confidence = 0.55 * official_contradiction + 0.45 * alternative_coherence`

`capped_confidence = cap_confidence(raw_confidence)`

`display = 0` when capped is 0; otherwise `round(capped * 100)` clamped to 1–75.

That integer is confidence that suppression was **intentional**.
Lower values mean the same suppression pattern is more likely a
natural occurrence.

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

A **Zioncheck Visual Archive volumes 1–5** document (title, filename,
or exact public title) is the **calibration base**: `display` 75 and
`capped_confidence` 0.75. Every layer is active because the five
volumes *are* the product. Bare Zioncheck / Arctic Building mentions
are not the seed. Author Aziel Eliab.

All other qualifying documents score **1–75** from evidence strength
and intentional-suppression weighting:

- Unknowns add to the scoring denominator (a lone yes cannot saturate).
- Yes answers are weighted by `vote_strength` 0.35–1.0 from layer votes.
- Raw confidence is scaled by `layers_active / 5`, yes-coverage, and
  an intentional scale (suppression + official-silence layers → 1.00;
  neither → 0.40, more natural).
- Hard cap remains 75% / uncertainty floor 25% when a positive score exists.
- Display is `round(capped * 100)` clamped to 1–75 when positive.
- Score 0 / `not_applicable` still means hide for non-matches.

First-hand pattern-break on supersession rescored related docs.
Seed vols 1–5 stay at 75; related non-seed documents are re-derived
with the break text folded in.

Worker: `deriveAnswersFromDocument` + `resolveScorePayload`.
Python: `derive_answers_from_document` + `resolve_score_payload`.

This replaces the failure mode where thin PDF metadata produced
all-unknown answers, score 0, and a library adapter marked the seed
archive `not_applicable` — and the later failure mode where every
qualifying non-seed document also displayed a flat 75.

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
