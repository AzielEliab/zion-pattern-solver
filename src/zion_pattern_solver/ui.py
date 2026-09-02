"""Localhost UI for ZionPattern Solver.

Binds 127.0.0.1 only (default port 8790). Self-contained HTML/CSS/JS,
no CDN. The confidence bar's allowed region is physically 75% of the
track; the remaining 25% is the uncertainty floor and cannot fill.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from zion_pattern_solver import __version__
from zion_pattern_solver.errors import SessionError, TerminationRefused
from zion_pattern_solver.patterns import PATTERNS
from zion_pattern_solver.scoring import CONFIDENCE_CAP, UNCERTAINTY_FLOOR, cap_confidence
from zion_pattern_solver.session import Session
from zion_pattern_solver.terminate import TERMINATION_TYPES, terminate

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8790
LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})


class _State:
    def __init__(self) -> None:
        self.session = Session(case="zioncheck-1936")

    def reset(self, case: str = "zioncheck-1936") -> dict[str, Any]:
        self.session = Session(case=case or "untitled")
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        snap = self.session.snapshot()
        snap["version"] = __version__
        snap["bind_host"] = DEFAULT_HOST
        snap["termination_types"] = list(TERMINATION_TYPES)
        snap["patterns_brief"] = [
            {"id": p.id, "name": p.name, "priority": p.priority}
            for p in PATTERNS
        ]
        return snap


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or "0")
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    try:
        data = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def make_handler(state: _State):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:  # noqa: A003
            return

        def _send(self, body: bytes, status: int, ctype: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, body: dict[str, Any], status: int = 200) -> None:
            raw = json.dumps(body, indent=2).encode("utf-8")
            self._send(raw, status, "application/json; charset=utf-8")

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path in ("/", "/index.html"):
                self._send(PAGE_HTML.encode("utf-8"), 200, "text/html; charset=utf-8")
                return
            if path == "/health":
                self._json({"ok": True, "bind_host": DEFAULT_HOST, "port": DEFAULT_PORT})
                return
            if path in ("/api/state", "/state"):
                self._json(state.snapshot())
                return
            if path in ("/api/patterns", "/patterns"):
                self._json({"patterns": [p.to_dict() for p in PATTERNS]})
                return
            if path in ("/api/receipt", "/receipt"):
                snap = state.snapshot()
                if snap.get("terminated"):
                    self._json({"ok": True, "terminated": snap["terminated"], "snapshot": snap})
                else:
                    self._json({"ok": False, "error": "not terminated", "snapshot": snap}, 409)
                return
            self._json({"error": "not found"}, 404)

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            data = _read_json(self)
            if path in ("/api/import", "/import"):
                answers = data.get("answers") if isinstance(data.get("answers"), dict) else data
                case = str(data.get("case") or "zioncheck-1936")
                state.reset(case)
                applied = 0
                if isinstance(answers, dict):
                    while True:
                        q = state.session.ask()
                        if q is None:
                            break
                        item = answers.get(q.qid) or answers.get(q.pattern_id) or {}
                        if isinstance(item, str):
                            value, rationale = item, "imported"
                        else:
                            value = item.get("value", "unknown")
                            rationale = item.get("rationale", "imported")
                        try:
                            state.session.answer(str(value), str(rationale))
                            applied += 1
                        except SessionError:
                            break
                snap = state.snapshot()
                snap["imported"] = applied
                self._json(snap)
                return
            if path in ("/api/reset", "/reset"):
                self._json(state.reset(str(data.get("case") or "zioncheck-1936")))
                return
            if path in ("/api/answer", "/answer"):
                try:
                    state.session.answer(
                        str(data.get("value") or ""),
                        str(data.get("rationale") or ""),
                    )
                except SessionError as exc:
                    self._json({"ok": False, "error": str(exc)}, 400)
                    return
                self._json(state.snapshot())
                return
            if path in ("/api/note", "/note"):
                text = str(data.get("text") or "").strip()
                if not text:
                    self._json({"ok": False, "error": "text required"}, 400)
                    return
                state.session.add_uncertainty_note(text=text, kind="manual")
                self._json(state.snapshot())
                return
            if path in ("/api/terminate", "/terminate"):
                kind = str(data.get("type") or data.get("kind") or "")
                try:
                    rec = terminate(state.session, kind)
                except TerminationRefused as exc:
                    self._json({"ok": False, "error": str(exc), "snapshot": state.snapshot()}, 409)
                    return
                payload = rec.to_dict()
                payload["ok"] = True
                self._json(payload)
                return
            self._json({"error": "not found"}, 404)

    return Handler


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    if host not in LOOPBACK:
        host = DEFAULT_HOST
    httpd = ThreadingHTTPServer((host, int(port)), make_handler(_State()))
    print(
        f"zion-solver ui  http://{host}:{port}/  "
        f"(loopback only; cap {int(CONFIDENCE_CAP*100)}% / floor {int(UNCERTAINTY_FLOOR*100)}%)"
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nzion-solver ui stopped")
    finally:
        httpd.server_close()


PAGE_HTML = r"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ZionPattern Solver — Z-Solver v0.2</title>
<style>
  :root {
    color-scheme: dark;
    --bg: #10110e;
    --bg2: #16180f;
    --panel: #1b1d16;
    --ink: #eef0e4;
    --muted: #9aa08c;
    --line: #2c2f24;
    --gold: #e6c35c;
    --gold2: #c4a35a;
    --floor: #5d7a62;
    --crit: #e07a5f;
    --high: #e09f3e;
    --med: #8faadc;
    --ok: #8fd18f;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: var(--bg); color: var(--ink);
    font: 15px/1.45 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }
  header {
    border-bottom: 1px solid var(--line);
    background: linear-gradient(180deg, #1a1c14, var(--bg));
    padding: 1.1rem 1.5rem 1rem;
  }
  header .brand { display: flex; align-items: baseline; gap: .75rem; flex-wrap: wrap; }
  header h1 { margin: 0; font-size: 1.45rem; letter-spacing: .04em; font-weight: 700; }
  header h1 span { color: var(--gold); font-weight: 600; }
  header .ver { color: var(--muted); font-size: .85rem; }
  .banner {
    margin-top: .85rem;
    border: 1px solid #5a4a22;
    background: #241e10;
    color: #f0e2b4;
    border-radius: 10px;
    padding: .7rem .95rem;
    font-size: .92rem;
  }
  .banner strong { color: var(--gold); }
  main {
    display: grid;
    grid-template-columns: 16rem 1fr 17rem;
    gap: 1rem;
    padding: 1rem 1.25rem 2rem;
    max-width: 72rem;
    margin: 0 auto;
  }
  @media (max-width: 960px) { main { grid-template-columns: 1fr; } }
  .card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 1rem 1.05rem;
  }
  h2 { margin: 0 0 .7rem; font-size: .78rem; letter-spacing: .12em;
    text-transform: uppercase; color: var(--muted); font-weight: 650; }
  .plist { list-style: none; margin: 0; padding: 0; }
  .plist li {
    display: grid; grid-template-columns: 2.2rem 1fr auto;
    gap: .4rem; align-items: start;
    padding: .45rem 0; border-bottom: 1px solid var(--line);
    font-size: .86rem;
  }
  .plist li:last-child { border-bottom: 0; }
  .pid { color: var(--gold2); font-family: ui-monospace, Menlo, monospace; font-size: .8rem; }
  .pri { font-size: .68rem; letter-spacing: .06em; text-transform: uppercase;
    padding: .1rem .35rem; border-radius: 4px; border: 1px solid var(--line); }
  .pri.critical { color: var(--crit); border-color: #5a3228; }
  .pri.high { color: var(--high); border-color: #5a4320; }
  .pri.medium { color: var(--med); border-color: #2a3a55; }
  .track-wrap { margin: .4rem 0 1rem; }
  .track-label { display: flex; justify-content: space-between; font-size: .82rem; color: var(--muted); }
  .track-label b { color: var(--gold); font-variant-numeric: tabular-nums; }
  .track {
    display: flex; height: 28px; border-radius: 8px; overflow: hidden;
    background: #12140e; border: 1px solid var(--line); margin-top: .35rem;
  }
  .allowed { width: 75%; background: #222418; position: relative; }
  .fill {
    height: 100%; width: 0%; max-width: 100%;
    background: linear-gradient(90deg, var(--gold2), var(--gold));
    transition: width .25s ease;
  }
  .floor {
    width: 25%; display: flex; align-items: center; justify-content: center;
    font-size: .68rem; color: var(--floor); letter-spacing: .04em;
    background: repeating-linear-gradient(-45deg, #161910, #161910 6px, #1c1f16 6px, #1c1f16 12px);
  }
  .qbox { min-height: 8rem; }
  .qid { font-family: ui-monospace, Menlo, monospace; color: var(--gold2); font-size: .8rem; }
  .prompt { font-size: 1.05rem; margin: .45rem 0 1rem; }
  textarea {
    width: 100%; background: #12140e; color: var(--ink); border: 1px solid var(--line);
    border-radius: 8px; padding: .55rem .7rem; min-height: 4.2rem; resize: vertical;
    font: inherit;
  }
  .row { display: flex; gap: .5rem; flex-wrap: wrap; margin-top: .7rem; }
  button {
    background: var(--gold); color: #16140a; border: 0; border-radius: 7px;
    padding: .5rem .85rem; font-weight: 650; cursor: pointer; font-size: .9rem;
  }
  button.ghost { background: #2a2d22; color: var(--ink); }
  button.warn { background: #5a3228; color: #f3d4cc; }
  button:disabled { opacity: .45; cursor: not-allowed; }
  .ledger { max-height: 22rem; overflow: auto; }
  .note {
    font-size: .82rem; color: var(--muted); border-left: 2px solid var(--gold2);
    padding: .25rem .6rem; margin: .35rem 0;
  }
  .note b { color: var(--ink); font-weight: 600; }
  pre {
    background: #12140e; border: 1px solid var(--line); border-radius: 8px;
    padding: .7rem; overflow: auto; font-size: .75rem; max-height: 14rem;
  }
  footer { color: var(--muted); font-size: .8rem; padding: 0 1.25rem 2rem;
    max-width: 72rem; margin: 0 auto; }
  .empty { color: var(--muted); font-size: .9rem; }
  .status { font-size: .85rem; color: var(--muted); margin-top: .5rem; }
  .status.ok { color: var(--ok); }
  .status.err { color: var(--crit); }
</style>
<body>
<header>
  <div class="brand">
    <h1>ZionPattern <span>Solver</span></h1>
    <div class="ver">Z-Solver v0.2 · 75% Cap Edition · local 127.0.0.1</div>
  </div>
  <div class="banner">
    <strong>75% maximum confidence</strong> &nbsp;·&nbsp;
    <strong>25% uncertainty floor</strong> must be logged on every termination.
    Provisional and assistive only — this engine does <strong>not</strong> solve
    Zioncheck or any case. Human-in-the-loop. No network in the engine.
  </div>
</header>
<main>
  <section class="card">
    <h2>Nine patterns</h2>
    <ul class="plist" id="plist"></ul>
  </section>
  <section class="card">
    <h2>Capped confidence</h2>
    <div class="track-wrap">
      <div class="track-label">
        <span>Displayed conclusion</span>
        <b id="capnum">0.00 / 0.75</b>
      </div>
      <div class="track" title="The fill lives in the 75% zone. The 25% floor cannot be painted over.">
        <div class="allowed"><div class="fill" id="fill"></div></div>
        <div class="floor">25% floor</div>
      </div>
    </div>
    <div class="qbox">
      <h2>Current question</h2>
      <div class="qid" id="qid"></div>
      <div class="prompt" id="prompt">Loading…</div>
      <label class="empty" for="rationale">Rationale (required for a useful receipt)</label>
      <textarea id="rationale" placeholder="What in the public record supports this answer?"></textarea>
      <div class="row">
        <button data-v="yes">Yes</button>
        <button class="ghost" data-v="no">No</button>
        <button class="ghost" data-v="unknown">Unknown</button>
      </div>
      <div class="status" id="qstatus"></div>
    </div>
    <div class="row" style="margin-top:1.1rem">
      <button class="ghost" id="btn-reset">New session</button>
      <button class="ghost" id="btn-receipt">Export receipt JSON</button>
      <label class="ghost">Import JSON <input type="file" id="import-json" accept="application/json,.json"></label>
    </div>
    <div class="row">
      <button class="warn" data-term="official_unsustainable">Terminate · official unsustainable</button>
      <button class="warn" data-term="alternative_supported">Terminate · alternative supported</button>
      <button class="warn" data-term="evidence_exhaustion">Terminate · evidence exhaustion</button>
    </div>
    <div class="status" id="tstatus"></div>
    <pre id="receipt" hidden></pre>
  </section>
  <section class="card">
    <h2>Uncertainty ledger</h2>
    <p class="empty">Every unknown and high-delta step is logged. Termination needs at least 3 notes.</p>
    <div class="ledger" id="ledger"></div>
    <label class="empty" for="manual">Add a note</label>
    <textarea id="manual" placeholder="Document remaining uncertainty…"></textarea>
    <div class="row"><button class="ghost" id="btn-note">Add to ledger</button></div>
    <h2 style="margin-top:1.2rem">Scores</h2>
    <div class="empty" id="scores"></div>
  </section>
</main>
<footer>
  Author Aziel Eliab.
  AGPL-3.0 · Forks welcome · github.com/AzielEliab/zion-pattern-solver
  · The solver never claims more than 75% confidence.
</footer>
<script>
(function () {
  const $ = (id) => document.getElementById(id);
  const fill = $("fill");
  const capnum = $("capnum");
  const CAP = 0.75;

  function setBar(capped) {
    const c = Math.min(Number(capped) || 0, CAP);
    const pct = Math.min(100, (c / CAP) * 100);
    fill.style.width = pct + "%";
    capnum.textContent = c.toFixed(2) + " / 0.75";
  }

  function priClass(p) { return "pri " + (p || "medium"); }

  function render(state) {
    const plist = $("plist");
    plist.innerHTML = "";
    (state.patterns_brief || []).forEach(function (p) {
      const li = document.createElement("li");
      li.innerHTML = '<span class="pid">' + p.id + '</span><span>' + p.name +
        '</span><span class="' + priClass(p.priority) + '">' + p.priority + "</span>";
      plist.appendChild(li);
    });
    const scores = state.scores || {};
    setBar(Math.min(scores.capped_confidence || 0, CAP));
    $("scores").innerHTML =
      "official contradiction " + (scores.official_contradiction || 0).toFixed(3) +
      "<br>alternative coherence " + (scores.alternative_coherence || 0).toFixed(3) +
      "<br>raw (uncapped) " + (scores.raw_confidence || 0).toFixed(3) +
      "<br>answered " + (state.answered || 0) + " · remaining " + (state.remaining || 0) +
      "<br>ledger " + ((state.uncertainty_ledger || []).length) + " notes";
    const q = state.question;
    if (!q) {
      $("qid").textContent = state.terminated
        ? "Session terminated (provisional)"
        : "No remaining questions";
      $("prompt").textContent = state.terminated
        ? "Export the receipt. This is not a solved case."
        : "Walk complete. Document uncertainty, then terminate if the cap is near.";
    } else {
      $("qid").textContent = q.qid + " · " + q.pattern_name + " · " + q.evidence_type;
      $("prompt").textContent = q.prompt;
    }
    const led = $("ledger");
    led.innerHTML = "";
    (state.uncertainty_ledger || []).forEach(function (n) {
      const d = document.createElement("div");
      d.className = "note";
      d.innerHTML = "<b>" + n.id + " · " + n.kind + "</b><br>" + (n.text || "");
      led.appendChild(d);
    });
    window.__last = state;
  }

  async function load() {
    const r = await fetch("/api/state");
    render(await r.json());
  }

  document.querySelectorAll("button[data-v]").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      $("qstatus").textContent = "";
      const r = await fetch("/api/answer", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({value: btn.getAttribute("data-v"), rationale: $("rationale").value})
      });
      const body = await r.json();
      if (!r.ok) {
        $("qstatus").className = "status err";
        $("qstatus").textContent = body.error || "answer failed";
        return;
      }
      $("rationale").value = "";
      render(body);
    });
  });

  $("btn-note").addEventListener("click", async function () {
    const r = await fetch("/api/note", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({text: $("manual").value})
    });
    const body = await r.json();
    if (!r.ok) return;
    $("manual").value = "";
    render(body);
  });

  $("btn-reset").addEventListener("click", async function () {
    $("receipt").hidden = true;
    $("tstatus").textContent = "";
    const r = await fetch("/api/reset", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({case: "zioncheck-1936"})
    });
    render(await r.json());
  });

  document.querySelectorAll("button[data-term]").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const r = await fetch("/api/terminate", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({type: btn.getAttribute("data-term")})
      });
      const body = await r.json();
      $("tstatus").className = r.ok ? "status ok" : "status err";
      $("tstatus").textContent = r.ok
        ? ("Provisional receipt " + (body.sha256 || "").slice(0, 16) + "… (not a solved case)")
        : (body.error || "refused");
      if (r.ok) {
        $("receipt").hidden = false;
        $("receipt").textContent = JSON.stringify(body, null, 2);
        if (body.capped_confidence != null) setBar(body.capped_confidence);
      }
    });
  });

  const importEl = $("import-json");
  if (importEl) importEl.addEventListener("change", async function () {
    const f = importEl.files && importEl.files[0];
    if (!f) return;
    let obj;
    try { obj = JSON.parse(await f.text()); } catch (e) { $("qstatus").textContent = "invalid JSON"; return; }
    const r = await fetch("/api/import", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(obj)
    });
    render(await r.json());
  });
  $("btn-receipt").addEventListener("click", function () {
    const state = window.__last || {};
    const blob = {
      product: "ZionPattern Solver",
      disclaimer: "Provisional and assistive only. Does not solve Zioncheck or any case. 75% cap / 25% floor.",
      snapshot: state
    };
    $("receipt").hidden = false;
    $("receipt").textContent = JSON.stringify(blob, null, 2);
  });

  load();
})();
</script>
</body>
</html>
"""
