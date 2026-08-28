# ZionPattern Solver download tracker (Cloudflare Worker)

Counts GitHub-release downloads for **ZionPattern Solver** across the
canonical repository, other branches, and forks. Forks are identified
by GitHub `owner/repo`.

Isolated counter for this product only (`PROJECT=zsolver`,
`DEFAULT_REPO=zion-pattern-solver`). Not mixed with VibeLock,
TemporalLock, ForgeReceipts, or any *Lock.

**This worker is shipped undeployed.** Do not treat
`https://zsolver-download-tracker.vibelock.workers.dev` as live until
someone with the Cloudflare account creates KV and deploys. Until then,
send people to
[GitHub Releases](https://github.com/AzielEliab/zion-pattern-solver/releases).

No secrets belong in this directory. The KV namespace id in
`wrangler.toml` is the placeholder `REPLACE_ME` until you create a
namespace. Do **not** deploy from this tree until KV is a real id.

The homepage shows a **live download count on the button**
(`Download zion-pattern-solver-0.1.0.tar.gz — N counted`).
`GET /download` increments. `GET /count` returns `{project, total}`.
`indexHtml` is async and reads KV before rendering.

Motto: **The solver never claims more than 75% confidence.**

Wrangler name is DNS-safe: `zsolver-download-tracker`
(account `ac575a9b822bea2bed97d0ab73aed238`).

## Bindings

| Binding     | Type | Purpose |
|-------------|------|---------|
| `DOWNLOADS` | KV   | Counters keyed `project|owner|repo|branch|fork` |

## Deploy (do not run from this tree yet)

```bash
cd workers/download-tracker

# 1. Log in once (opens a browser; token stays in wrangler, not in git)
npx wrangler login

# 2. Create the KV namespace. Paste the id into wrangler.toml
#    replacing REPLACE_ME. Binding name MUST stay DOWNLOADS.
npx wrangler kv namespace create DOWNLOADS

# 3. Deploy
npx wrangler deploy
```

The `workers.dev` subdomain wrangler prints
(`zsolver-download-tracker.<account>.workers.dev`) is enough until
custom DNS is ready. This tree documents the intended public URL
`https://zsolver-download-tracker.vibelock.workers.dev`.

## Routes

| Method | Path | Behavior |
|--------|------|----------|
| GET | `/` | Index page with live count on the download button |
| GET | `/download?repo=&tag=&asset=` | Increment KV, 302 to the hosted asset (default: `zion-pattern-solver-0.1.0.tar.gz`) |
| GET | `/count` | JSON `{project, total}` for this project only |
| GET | `/stats` | JSON totals plus per-repo and per-branch breakdown |
| GET | `/go` | Increment KV, 302 to GitHub |
| POST | `/event` | A fork reports a download |

Query params on `/download`: `owner`, `repo` (`AzielEliab/zion-pattern-solver` is
accepted), `branch`, `fork` (`1` or `owner/repo`), `tag`, `asset`.

Tracked asset URL (after deploy):

```
https://zsolver-download-tracker.vibelock.workers.dev/download?asset=zion-pattern-solver-0.1.0.tar.gz
```

The count ticks on that click. Nobody reports anything.

## CORS

All responses include `Access-Control-Allow-Origin: *`.
