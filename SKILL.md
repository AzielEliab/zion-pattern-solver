---
name: ZionPattern Solver
description: Use when calling this product's hosted /v1 (health, skill, OpenAPI) or aziel-runtime. Author Aziel Eliab.
---

# ZionPattern Solver

The solver never claims more than 75% confidence.

**Score meaning:** **75** = complete confidence the suppression was **intentional**. Lower = less confidence it was intentional; more natural occurrence of suppression. Hard cap 75% / uncertainty floor 25%.

Zioncheck Visual Archive **volumes 1–5 only** are the seed baseline at display 75. Other documents (even if they mention Zioncheck or the Arctic Building) score 1–75 by evidence — not a flat 75.

Author: **Aziel Eliab**.

**THIS IS / THIS IS NOT:** THIS IS: modular local-first interrogation engine with a hard 75% confidence cap and 25% uncertainty floor. THIS IS NOT: a solved case, a court, or a truth machine. Provisional and assistive only. Author: Aziel Eliab.

Always send `User-Agent: Mozilla/5.0`. Cloudflare Workers may 403 an empty agent.

## Call these URLs

- Worker OpenAPI: https://zsolver-download-tracker.vibelock.workers.dev/openapi.json
- Catalog OpenAPI: https://aziel-runtime.vibelock.workers.dev/openapi.json
- MCP: `POST https://aziel-runtime.vibelock.workers.dev/mcp`
- Live skill (this markdown): `GET https://zsolver-download-tracker.vibelock.workers.dev/v1/skill`

Ops (do **not** increment downloads or views): GET /v1/health · GET /v1/patterns · POST /v1/score (`answers` **or** `{title,body,filename,subjects,keywords,domain}`) · POST /v1/session · GET /v1/skill

Catalog slug: `zsolver`.

Grok: import OpenAPI as a custom tool. ChatGPT: GPT Actions. Venice: HTTP tools.

## Example

```bash
curl -s -A 'Mozilla/5.0' https://zsolver-download-tracker.vibelock.workers.dev/v1/health
curl -s -A 'Mozilla/5.0' https://zsolver-download-tracker.vibelock.workers.dev/v1/skill
curl -s -A 'Mozilla/5.0' https://aziel-runtime.vibelock.workers.dev/p/zsolver/skill
```

## Local (after one-click install)

```bash
curl -fsSL https://zsolver-download-tracker.vibelock.workers.dev/install.sh | bash
zion-solver ui
zion-solver doctor
```

Open http://127.0.0.1:8790 (loopback only).

Counted tarball (HTTP 200 gzip, no 302): https://zsolver-download-tracker.vibelock.workers.dev/download?asset=zion-pattern-solver-0.2.0.tar.gz

GitHub: https://github.com/AzielEliab/zion-pattern-solver

DOI: https://doi.org/10.5281/zenodo.21436155

AGPL-3.0. Forks welcome.
