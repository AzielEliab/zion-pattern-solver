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
