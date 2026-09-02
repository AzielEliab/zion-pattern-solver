# ZionPattern Solver (Z-Solver) v0.2

**Modular, local-first engine for systematic interrogation of historical anomalies.**

**Author:** Aziel Eliab



## Quick start

```bash
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
zion-solver ui
```


## One-click install

```bash
curl -fsSL https://zsolver-download-tracker.vibelock.workers.dev/install.sh | bash
```

The script curls the **counted** tarball from this project's Worker
(`/download`, User-Agent `Mozilla/5.0`), extracts, makes a venv, and
`pip install -e .`. Then run `zion-solver ui`.

Or tap **Download** / **One-click install** on the Worker homepage:
https://zsolver-download-tracker.vibelock.workers.dev/

## Counted download (Cloudflare Worker)

**This is the counted download.** GitHub releases exist as a mirror.
The Worker serves the gzip itself (HTTP 200, no 302 to GitHub).

- Homepage: [https://zsolver-download-tracker.vibelock.workers.dev/](https://zsolver-download-tracker.vibelock.workers.dev/)
- Direct tarball: [zion-pattern-solver-0.2.0.tar.gz](https://zsolver-download-tracker.vibelock.workers.dev/download?asset=zion-pattern-solver-0.2.0.tar.gz)
- One-click install: [https://zsolver-download-tracker.vibelock.workers.dev/install.sh](https://zsolver-download-tracker.vibelock.workers.dev/install.sh)
- Skill: [https://zsolver-download-tracker.vibelock.workers.dev/v1/skill](https://zsolver-download-tracker.vibelock.workers.dev/v1/skill)
- OpenAPI: [https://zsolver-download-tracker.vibelock.workers.dev/openapi.json](https://zsolver-download-tracker.vibelock.workers.dev/openapi.json)
- GitHub: [https://github.com/AzielEliab/zion-pattern-solver](https://github.com/AzielEliab/zion-pattern-solver)
- Zenodo DOI: [10.5281/zenodo.21436155](https://doi.org/10.5281/zenodo.21436155) · [record](https://zenodo.org/records/21436155)

Isolated counter: Worker `zsolver-download-tracker`, KV `ZSOLVER_DOWNLOADS`. `/v1` does not increment downloads.

Open http://127.0.0.1:8790 (loopback only). No CDN, no telemetry. Hard cap 75% / uncertainty floor 25%.

Counted download: [https://zsolver-download-tracker.vibelock.workers.dev/](https://zsolver-download-tracker.vibelock.workers.dev/)


Whitepaper: *ZionPattern Solver, 75% Cap Edition*, July 18 2026, Aziel Eliab.

Seeded on the Marion A. Zioncheck (1936) Congressional death investigation. Built for falsifiable analysis under strict epistemic guardrails: hard confidence capping, mandatory uncertainty documentation, receipt generation, and human-in-the-loop operation.

This product is **standalone**. It is not ForgeReceipts, not a *Lock repo, and is not merged into those trees.

## Core Invariant (Non-Negotiable)

- **Maximum confidence on any conclusion: 75%**
- **Irreducible uncertainty floor: 25%** — must be explicitly logged and documented in *every* termination
- All outputs are **provisional and assistive only**. The engine never asserts final historical conclusions.
- **Does not "solve" Zioncheck or any case.**

This cap + floor exists to protect against over-claim, misuse, and the well-documented failure modes of pattern-seeking systems (apophenia, narrative lock-in, institutional capture).

`cap_confidence` is a single function used everywhere: `min(raw, 0.75)` (after non-finite/negative clamp).

## What It Does

The solver systematically generates and pursues questions drawn from Zioncheck-derived anomaly pattern categories until the confidence cap is approached. Every step produces:

- Rationale logging
- Uncertainty quantification (respecting the 25% floor)
- SHA-256 receipts (TemporalLock-style canonical JSON, reimplemented in-tree — no temporallock import)
- Provisional framing suitable for independent verification

### Supported Anomaly Pattern Categories (Zioncheck seed)

1. Kinematic & Timeline Impossibility (critical)
2. Document Provenance & Integrity (critical)
3. Witness & Archival Void (high)
4. Geographic / Location Manipulation (medium)
5. Pre-Event Discrediting & Suppression (high)
6. Political / Motive Contextual (medium)
7. Secondary Encoded Testimony / Rubye (critical)
8. Rapid Narrative Lock (high)
9. Forensic / Physical Evidence Gap (high)

## Receipt & Integrity System

- Every significant output and intermediate state is hashed (SHA-256)
- Canonical UTF-8 JSON, sorted keys, no extra whitespace; `sha256` excluded from the digest
- Designed for compatibility with **TemporalLock** immutable temporal receipt systems (no runtime dependency)
- Export path to **Lumen** capsules (manifest + ethics layer) planned
- Supports "building receipts" against gaslighting or future integrity challenges
- Zero narrative over-claim by design

## Philosophy & Alignment

This tool embodies core Aziel principles:

- **Local-first, offline-capable operation** (the engine has no network)
- **Ethical restraint** — the 75%/25% rule is structural, not advisory
- **Falsifiability**
- **Receipts as primary output** — not conclusions
- **Human-in-the-loop mandatory** — the solver assists; it does not replace judgment or independent forensic/archival verification
- **Forks welcome**

It exists to make suppressed or obscured historical patterns legible while refusing the illusion of certainty.

## Non-Claims & Scope

ZionPattern Solver does **not**:

- "Solve" the Zioncheck case or any historical event
- Produce courtroom-admissible conclusions on its own
- Replace forensic analysis, exhumation, multispectral imaging, or primary source verification
- Accuse living people. The seed case is a 1936 historical public figure.

It surfaces testable anomaly nodes, documents irreducible uncertainty, generates verifiable receipts, and accelerates independent human investigation. All historical or legal weight remains with the analyst + external verification processes.

## Getting Started

Requires Python 3.10+. Runtime is stdlib-only.

```bash
git clone https://github.com/AzielEliab/zion-pattern-solver.git
cd zion-pattern-solver
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

zion-solver version
zion-solver patterns
zion-solver demo              # noninteractive Zioncheck seed (fixture answers)
zion-solver session --case zioncheck-1936
zion-solver ui                # http://127.0.0.1:8790/  (loopback only)

pytest
```

`zion-solver demo` walks `examples/zioncheck_irn_nodes/seed.json` with
`examples/zioncheck_irn_nodes/demo_answers.json` so tests stay deterministic.
Pass `--interactive` to answer on stdin instead.


## iPhone & Android

Flutter sources: [`mobile/`](mobile/). Application id `com.azieeliab.zionpattern`. Offline. No analytics. Dark matte / gold.

75% cap / 25% floor UI. Provisional and assistive. Does not solve cases.

```bash
cd mobile
flutter create --org com.azieeliab --project-name zionpattern .
flutter pub get
flutter run
```

The `android/` and `ios/` folders in this tree are skeleton READMEs until you run `flutter create .` (this machine has no Flutter SDK on PATH). Then open `android/` in Android Studio or `ios/Runner.xcworkspace` in Xcode. Not a store listing.

## Download

Counted downloads (count lives on the button; nobody reports anything):

**https://zsolver-download-tracker.vibelock.workers.dev/**

The worker is an isolated counter for this product only (`PROJECT=zsolver`).
It is not mixed with VibeLock, TemporalLock, or ForgeReceipts. Until that
worker is deployed, use
[GitHub Releases](https://github.com/AzielEliab/zion-pattern-solver/releases).

The solver never claims more than 75% confidence.

## Repository Structure

```
zion-pattern-solver/
├── README.md
├── LICENSE                  # GNU AGPL-3.0 (full text)
├── pyproject.toml
├── src/zion_pattern_solver/ # engine (patterns, scoring, session, receipts, ui)
├── examples/zioncheck_irn_nodes/
├── tests/
├── docs/methodology.md
├── workers/download-tracker/  # undeployed Cloudflare worker
├── receipts/                  # generated locally (gitignored)
└── mobile/                    # Flutter iPhone + Android (`flutter create .`)
```

## Pairing with Research Pack

This solver is the executable companion to the **Marion A. Zioncheck Independent Review Packet & Distribution Pack** (to be archived on Zenodo with DOI).

- Use the solver to interrogate the IRN-Series nodes
- Export receipts that can be referenced alongside the Zenodo record
- Future versions will support direct Lumen capsule export for sealed archival

Once the Zenodo record is live, add the DOI here and in all receipt metadata.

## Contributing & Stress-Testing

- Open issues for new anomaly pattern categories or edge cases
- Adversarial stress-tests are welcome (see companion GodLock repo)
- All contributions must respect the 75% cap / 25% uncertainty floor invariant
- Pull requests should include updated uncertainty documentation examples
- Forks welcome: https://github.com/AzielEliab/zion-pattern-solver

## AI runtime

Provisional and assistive only. **Does not solve Zioncheck or any case.**
Hard cap **75%** / uncertainty floor **25%**.

Worker (no download-KV increment on `/v1`):

- `GET https://zsolver-download-tracker.vibelock.workers.dev/v1/health`
- `GET https://zsolver-download-tracker.vibelock.workers.dev/v1/patterns`
- `POST https://zsolver-download-tracker.vibelock.workers.dev/v1/score` `{answers}`
- `POST https://zsolver-download-tracker.vibelock.workers.dev/v1/session` `{answers}`
- OpenAPI 3.1: https://zsolver-download-tracker.vibelock.workers.dev/openapi.json
- Help: https://zsolver-download-tracker.vibelock.workers.dev/ai

One-URL catalog for ChatGPT / Grok / Venice:
https://aziel-runtime.vibelock.workers.dev/openapi.json


## License

GNU Affero General Public License v3.0 (AGPL-3.0). See `LICENSE`.

This license is chosen to keep derivative works on integrity and evidence tools open and auditable.

## Contact / Attribution

Aziel Eliab.
Part of the broader Aziel Interface / Lumen operational framework for truth-seeking under constraint.

GitHub: [AzielEliab/zion-pattern-solver](https://github.com/AzielEliab/zion-pattern-solver)

---

**Status**: v0.2 — modular release. Core engine + receipt system + localhost UI.

**Do not over-claim. Build receipts. Stay local-first.**
