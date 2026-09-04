# zion-pattern-solver download tracker

Isolated Worker `zsolver-download-tracker`. Project `zsolver`.
KV namespace `ZSOLVER_DOWNLOADS` bound as `DOWNLOADS`.
Does **not** 302 to GitHub on `/download`. Serves gzip via `ASSETS.fetch`,
`Cache-Control: private, no-store`.

GET `/` increments a **page-view** counter (separate from downloads).
GET `/download` increments **downloads**.
`/v1` never increments DOWNLOADS KV.
GET `/install.sh` one-click install (does not increment; script curls `/download`).
GET `/v1/skill` returns skill markdown (`text/markdown`). Does not increment views or downloads.

Host: https://zsolver-download-tracker.vibelock.workers.dev

`POST /v1/score` accepts analyst `answers` or document fields
(`title`, `body`/`text`, `filename`, `subjects`, `keywords`, `domain`).
Zioncheck Visual Archive volumes 1–5 only are the seed baseline
(display 75 = complete confidence in intentional suppression).
Derivation is the product of seed patterns × pattern answers ×
pattern questions × pattern of suppression × pattern of official
story to silence. Other documents — even Zioncheck / Arctic Building
mentions — score 1–75 from evidence (lower = more natural occurrence).
Non-matches display 0. Hard cap 75% / floor 25%. Author Aziel Eliab.

