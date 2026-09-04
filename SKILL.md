---
name: ZionPattern Solver
description: Use when scoring Zioncheck-derived anomaly patterns. Score 75 = complete confidence in intentional suppression (hard cap). 1–74 = less intentional / more natural. Seed Visual Archive vols 1–5 baseline 75. Non-matches hidden. Does not solve cases. Author Aziel Eliab.
---

# ZionPattern Solver 0.4.0

**Score meaning (authoritative):**
- **75** = complete confidence in **intentional** suppression (hard cap)
- **1–74** = less confidence it was intentional; more natural occurrence of suppression
- **0** / `not_applicable` = non-match, hidden

Seed baseline 75 = Zioncheck Visual Archive volumes 1–5 only.
Other qualifying docs vary 1–75. Non-matches are hidden.

Method: seed patterns × pattern answers × pattern questions × pattern of suppression × official story to silence.

First-hand pattern-break on supersession rescored related docs.

Author: **Aziel Eliab** only. Never Ever Blooming. Does not solve cases.

Always send `User-Agent: Mozilla/5.0`. Cloudflare Workers may 403 an empty agent.

## Call these URLs

- Worker OpenAPI: https://zsolver-download-tracker.vibelock.workers.dev/openapi.json
- Worker llms.txt: https://zsolver-download-tracker.vibelock.workers.dev/llms.txt
- Catalog OpenAPI: https://aziel-runtime.vibelock.workers.dev/openapi.json
- MCP: `POST https://aziel-runtime.vibelock.workers.dev/mcp`
- Live skill (this markdown): `GET https://zsolver-download-tracker.vibelock.workers.dev/v1/skill`

Ops (do **not** increment downloads or views): GET /v1/health · GET /v1/patterns · POST /v1/score (`answers` **or** `{title,body,filename,subjects,keywords,domain}`) · POST /v1/session · GET /v1/skill · GET /llms.txt

Catalog slug: `zsolver`.

Grok: import OpenAPI as a custom tool. ChatGPT: GPT Actions. Venice: HTTP tools.

## Example

```bash
curl -s -A 'Mozilla/5.0' https://zsolver-download-tracker.vibelock.workers.dev/v1/health
curl -s -A 'Mozilla/5.0' https://zsolver-download-tracker.vibelock.workers.dev/v1/skill
curl -s -A 'Mozilla/5.0' https://zsolver-download-tracker.vibelock.workers.dev/llms.txt
curl -s -A 'Mozilla/5.0' https://aziel-runtime.vibelock.workers.dev/p/zsolver/skill
```

## Local (after one-click install)

```bash
curl -fsSL https://zsolver-download-tracker.vibelock.workers.dev/install.sh | bash
zion-solver ui
zion-solver doctor
```

Open http://127.0.0.1:8790 (loopback only).

Counted tarball (HTTP 200 gzip, no 302): https://zsolver-download-tracker.vibelock.workers.dev/download?asset=zion-pattern-solver-0.4.0.tar.gz

GitHub: https://github.com/AzielEliab/zion-pattern-solver

DOI: https://doi.org/10.5281/zenodo.21436155

AGPL-3.0. Forks welcome.
