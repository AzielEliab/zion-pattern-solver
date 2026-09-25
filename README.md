# ZionPattern Solver

Ask a question to verify, or auto-walk a seeded case. Displayed confidence stays at or below 75%. A 25% uncertainty floor stays on the record when a walk closes.

**Author:** Aziel Eliab

## Start

Python 3.10 or newer. The engine uses the Python standard library.

1. `python3 -m venv .venv && . .venv/bin/activate && pip install -e .`
2. `zion-solver ui`
3. Open http://127.0.0.1:8790

`zion-solver` with no arguments prints that same next step. `RUN.txt` is the short card.

## Everyday commands

```bash
zion-solver              # welcome and next step
zion-solver ui           # local app: Ask to verify and Auto walk
zion-solver ask "Did the 1936 timeline leave a gap?"
zion-solver auto         # seeded nodes, receipt when the cap and floor allow
zion-solver demo         # same seed, one question at a time if you pass --interactive
zion-solver doctor       # check this install
zion-solver patterns     # the nine patterns
zion-solver --help
```

People get plain text. Add `--json` for scripts and agents (`zion-solver patterns --json`, `zion-solver doctor --json`). The local app returns HTML in a browser. `Accept: application/json` on `GET /` returns the session snapshot.

## A walk

You answer yes, no, or unknown, with a rationale if you have one. The bar fills only inside the 75% zone. The last quarter of the bar is the uncertainty floor and does not fill.

**75** means complete confidence the suppression was intentional. A lower number means more natural occurrence. `cap_confidence` is `min(raw, 0.75)` after non-finite and negative values are clamped.

Zioncheck Visual Archive volumes 1–5 are the seed baseline at display 75. Other documents, including ones that mention Zioncheck or the Arctic Building, score from 1 to 75 by evidence.

The nine patterns:

1. Kinematic & Timeline Impossibility (critical)
2. Document Provenance & Integrity (critical)
3. Witness & Archival Void (high)
4. Geographic / Location Manipulation (medium)
5. Pre-Event Discrediting & Suppression (high)
6. Political / Motive Contextual (medium)
7. Secondary Encoded Testimony / Rubye (critical)
8. Rapid Narrative Lock (high)
9. Forensic / Physical Evidence Gap (high)

Receipts are canonical UTF-8 JSON (sorted keys, no extra whitespace) with a SHA-256 digest. The `sha256` field is excluded from the digest. This package does not import TemporalLock.

Closing a walk needs the confidence near the cap and at least three uncertainty notes. The closing types are `official_unsustainable`, `alternative_supported`, and `evidence_exhaustion`.

```bash
zion-solver session --case zioncheck-1936
zion-solver demo --interactive
zion-solver session --case zioncheck-1936 --terminate official_unsustainable --emit-receipt receipt.json
```

`zion-solver demo` reads `examples/zioncheck_irn_nodes/seed.json` and `examples/zioncheck_irn_nodes/demo_answers.json`.

## Phone

Flutter sources are in [`mobile/`](mobile/). Application id `com.azieeliab.zionpattern`. Offline. The theme follows the system light or dark setting.

```bash
cd mobile
flutter create --org com.azieeliab --project-name zionpattern .
flutter run
```

`android/` and `ios/` are skeleton notes until `flutter create .` has been run on a machine with the Flutter SDK.

## Notes

A finished walk is provisional and assistive. It does not solve Zioncheck or any case, and it does not replace archival or forensic work. The seed case is a 1936 public figure. Questions stay documentary.

The engine does not open a network connection and does not send telemetry. The local app binds `127.0.0.1` only.

Whitepaper: *ZionPattern Solver, 75% Cap Edition*, July 18 2026, Aziel Eliab. Seeded on the Marion A. Zioncheck (1936) public record.

Counted download (the Worker serves the gzip, HTTP 200):

- https://zsolver-download-tracker.vibelock.workers.dev/
- Tarball: https://zsolver-download-tracker.vibelock.workers.dev/download?asset=zion-pattern-solver-0.2.0.tar.gz
- Install script: https://zsolver-download-tracker.vibelock.workers.dev/install.sh
- GitHub: https://github.com/AzielEliab/zion-pattern-solver
- Zenodo: https://doi.org/10.5281/zenodo.21436155

One-click install, when you want the counted tarball:

```bash
curl -fsSL https://zsolver-download-tracker.vibelock.workers.dev/install.sh | bash
zion-solver ui
```

Agent surface (these routes do not increment the download count):

- `GET https://zsolver-download-tracker.vibelock.workers.dev/v1/health`
- `GET https://zsolver-download-tracker.vibelock.workers.dev/v1/patterns`
- `POST https://zsolver-download-tracker.vibelock.workers.dev/v1/score`
- `POST https://zsolver-download-tracker.vibelock.workers.dev/v1/session`
- OpenAPI: https://zsolver-download-tracker.vibelock.workers.dev/openapi.json
- Suite mesh proxy: https://zsolver-download-tracker.vibelock.workers.dev/v1/mesh (default off)

Tests: `pip install -e ".[dev]" && pytest`

## Layout

```
README.md
RUN.txt
LICENSE
pyproject.toml
src/zion_pattern_solver/
examples/zioncheck_irn_nodes/
tests/
docs/methodology.md
mobile/
workers/download-tracker/
```

## License

GNU Affero General Public License v3.0. See `LICENSE`.

Aziel Eliab.
https://github.com/AzielEliab/zion-pattern-solver
