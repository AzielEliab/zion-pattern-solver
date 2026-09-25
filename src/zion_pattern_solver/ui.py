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
from zion_pattern_solver.scoring import CONFIDENCE_CAP, UNCERTAINTY_FLOOR
from zion_pattern_solver.session import Session
from zion_pattern_solver.auto import auto_run, load_seed_answers
from zion_pattern_solver.terminate import TERMINATION_TYPES, terminate
from zion_pattern_solver.verify import ask_to_verify

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8790
LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})


class _State:
    def __init__(self) -> None:
        self.session = Session(case="zioncheck-1936")
        try:
            self.fixture = load_seed_answers()
        except (OSError, ValueError):
            self.fixture = {}

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
                if path == "/" and _wants_json(self):
                    self._json(state.snapshot())
                    return
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
            if path in ("/api/ask", "/ask"):
                result = ask_to_verify(str(data.get("question") or data.get("text") or ""))
                if result.get("ok") and result.get("uncertainty_note"):
                    state.session.add_uncertainty_note(
                        text=str(result["uncertainty_note"]),
                        kind="verify",
                        pattern_id=(result.get("linked_patterns") or [{}])[0].get("id"),
                        qid=(result.get("linked_patterns") or [{}])[0].get("qid"),
                    )
                result["snapshot"] = state.snapshot()
                self._json(result, 200 if result.get("ok") else 400)
                return
            if path in ("/api/auto", "/auto"):
                action = str(data.get("action") or "run").strip().lower()
                if action == "pause":
                    snap = state.snapshot()
                    snap["ok"] = True
                    snap["stopped"] = "pause"
                    snap["applied_count"] = 0
                    self._json(snap)
                    return
                limit = 1 if action == "step" else None
                if not state.fixture:
                    self._json(
                        {
                            "ok": False,
                            "error": "No seeded answers are available.",
                            "next": "Run zion-solver auto from the project directory.",
                            "snapshot": state.snapshot(),
                        },
                        400,
                    )
                    return
                result = auto_run(state.session, state.fixture, limit=limit)
                self._json(result, 200 if result.get("ok") else 400)
                return
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


def _wants_json(handler: BaseHTTPRequestHandler) -> bool:
    """Machine clients send Accept: application/json. Browsers get HTML."""
    accept = (handler.headers.get("Accept") or "").lower()
    if "application/json" not in accept:
        return False
    if "text/html" in accept:
        return False
    return True


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    if host not in LOOPBACK:
        host = DEFAULT_HOST
    httpd = ThreadingHTTPServer((host, int(port)), make_handler(_State()))
    print(f"Open http://{host}:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nzion-solver ui stopped")
    finally:
        httpd.server_close()


# The page states these percentages in words. Keep the copy tied to the engine.
_CAP_PCT = f"{int(round(CONFIDENCE_CAP * 100))}%"
_FLOOR_PCT = f"{int(round(UNCERTAINTY_FLOOR * 100))}%"


def _page_html() -> str:
    return (
        _PAGE_TEMPLATE.replace("__CAP_NUM__", f"{CONFIDENCE_CAP:.2f}")
        .replace("__CAP__", _CAP_PCT)
        .replace("__FLOOR__", _FLOOR_PCT)
    )


_PAGE_TEMPLATE = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ZionPattern Solver</title>
<style>
  :root {
    color-scheme: light dark;
    --bg: #f6f3ea;
    --panel: #fffdf8;
    --ink: #1c1914;
    --muted: #4e493f;
    --line: #e4dcc8;
    --gold: #c9a227;
    --gold-ink: #6d5610;
    --on-gold: #1c1914;
    --ok: #1d6b38;
    --err: #8c2e22;
    --track: #efe6d2;
    --allowed: #f8f1df;
    --floor: #3d5c46;
    --floor-bg: #e7efe6;
    --shadow: 0 1px 0 rgba(28, 25, 20, 0.04);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #12110e;
      --panel: #1c1b16;
      --ink: #f4f0e6;
      --muted: #c8bfae;
      --line: #343128;
      --gold: #c9a227;
      --gold-ink: #e6c35c;
      --on-gold: #1c1914;
      --ok: #b7ddc0;
      --err: #f0b2a8;
      --track: #0e0d0b;
      --allowed: #2a261c;
      --floor: #b7d0bc;
      --floor-bg: #1a2420;
      --shadow: none;
    }
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--ink);
    font: 16px/1.5 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
    overflow-x: hidden;
  }
  :focus-visible {
    outline: 2px solid #c9a227;
    outline-offset: 3px;
  }
  .skip {
    position: absolute; left: 0.75rem; top: -4rem;
    background: var(--gold); color: var(--on-gold);
    padding: 0.4rem 0.7rem; border-radius: 8px;
  }
  .skip:focus { top: 0.75rem; }
  header {
    display: flex; justify-content: space-between; align-items: flex-end;
    gap: 1rem; flex-wrap: wrap;
    max-width: 40rem; margin: 0 auto;
    padding: 1.5rem 1.25rem 0.25rem;
  }
  h1 { font-size: 1.55rem; line-height: 1.2; margin: 0; font-weight: 650; letter-spacing: -0.01em; }
  .local { margin: 0.2rem 0 0; color: var(--muted); font-size: 0.92rem; }
  .by { margin: 0; color: var(--muted); font-size: 0.92rem; }
  main { max-width: 40rem; margin: 0 auto; padding: 1rem 1.25rem 2.5rem; }
  .lede { margin: 0.35rem 0 1.1rem; font-size: 1.05rem; }
  .card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 1.15rem 1.15rem 1.25rem;
    box-shadow: var(--shadow);
  }
  h2 { margin: 0 0 0.35rem; font-size: 1rem; font-weight: 650; }
  .track-label {
    display: flex; justify-content: space-between; gap: 0.75rem; flex-wrap: wrap;
    font-size: 0.92rem; color: var(--muted); margin-top: 0.85rem;
  }
  .track-label b { color: var(--gold-ink); font-variant-numeric: tabular-nums; font-weight: 650; }
  .track {
    display: flex; height: 32px; border-radius: 8px; overflow: hidden;
    background: var(--track); border: 1px solid var(--line); margin: 0.4rem 0 1.15rem;
  }
  .allowed { width: __CAP__; background: var(--allowed); position: relative; }
  .fill {
    height: 100%; width: 0%; max-width: 100%;
    background: var(--gold);
  }
  .floor {
    width: __FLOOR__; display: flex; align-items: center; justify-content: center;
    font-size: 0.72rem; letter-spacing: 0.02em; color: var(--floor);
    background: var(--floor-bg); text-align: center; padding: 0 0.2rem;
  }
  .qid { color: var(--gold-ink); font-size: 0.88rem; margin: 0; }
  .prompt { font-size: 1.12rem; margin: 0.45rem 0 1rem; }
  .choices {
    display: flex; gap: 0.5rem; flex-wrap: wrap; margin: 0 0 0.9rem; padding: 0; border: 0;
  }
  .choice {
    flex: 1 1 6.5rem;
    display: flex; align-items: center; justify-content: center; gap: 0.4rem;
    min-height: 44px; margin: 0; padding: 0.4rem 0.7rem;
    border: 1px solid var(--line); border-radius: 9px; background: transparent;
    cursor: pointer; font-weight: 600;
  }
  .choice input { accent-color: #c9a227; }
  .choice:has(input:checked) {
    background: var(--gold); color: var(--on-gold); border-color: var(--gold);
  }
  label.field { display: block; color: var(--muted); font-size: 0.92rem; margin-bottom: 0.35rem; }
  textarea, input[type="text"] {
    width: 100%; max-width: 100%;
    background: var(--bg); color: var(--ink);
    border: 1px solid var(--line); border-radius: 9px;
    padding: 0.6rem 0.7rem; font: inherit; min-height: 5rem; resize: vertical;
  }
  .actions { margin-top: 0.85rem; }
  button, .ghost-file {
    font: inherit; cursor: pointer; border-radius: 9px; min-height: 44px;
    padding: 0.45rem 0.95rem;
  }
  button.primary {
    background: var(--gold); color: var(--on-gold); border: 1px solid var(--gold);
    font-weight: 700; min-width: 11rem;
  }
  button.ghost, .ghost-file {
    background: transparent; color: var(--ink); border: 1px solid var(--line); font-weight: 600;
  }
  button:disabled { opacity: 0.5; cursor: not-allowed; }
  .row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.7rem 0; }
  .status { min-height: 1.4rem; margin: 0.75rem 0 0; color: var(--muted); font-size: 0.95rem; }
  .status.ok { color: var(--ok); }
  .status.err { color: var(--err); }
  details.fold {
    margin-top: 0.85rem;
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.2rem 1.1rem;
  }
  details.fold[open] { padding-bottom: 1.1rem; }
  summary {
    cursor: pointer; font-weight: 700; padding: 0.85rem 0; min-height: 44px;
    display: flex; align-items: center;
  }
  summary::-webkit-details-marker { display: none; }
  .hint { color: var(--muted); margin: 0.2rem 0 0.7rem; font-size: 0.95rem; }
  .plist { list-style: none; margin: 0; padding: 0; }
  .plist li {
    display: flex; justify-content: space-between; gap: 0.75rem; flex-wrap: wrap;
    padding: 0.45rem 0; border-bottom: 1px solid var(--line); font-size: 0.95rem;
  }
  .plist li:last-child { border-bottom: 0; }
  .pid { color: var(--gold-ink); font-variant-numeric: tabular-nums; margin-right: 0.4rem; }
  .pri { color: var(--muted); font-size: 0.82rem; text-transform: lowercase; }
  .note {
    border-left: 2px solid var(--gold); padding: 0.15rem 0 0.15rem 0.7rem; margin: 0.55rem 0;
  }
  .note b { font-weight: 650; }
  pre, .hash {
    background: var(--bg); border: 1px solid var(--line); border-radius: 9px;
    padding: 0.7rem; overflow: auto; max-width: 100%; max-height: 16rem;
    font-size: 0.78rem; line-height: 1.4;
  }
  .hash { font-family: ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace; word-break: break-all; }
  .ask-result { margin-top: 0.85rem; }
  button.auto {
    background: transparent; color: var(--ink); border: 2px solid var(--gold); font-weight: 700;
  }
  footer {
    max-width: 40rem; margin: 0 auto; padding: 0 1.25rem 2.5rem;
    color: var(--muted); font-size: 0.88rem;
  }
  code { font-family: ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace; font-size: 0.92em; }
  @media (max-width: 420px) {
    header, main, footer { padding-left: 1rem; padding-right: 1rem; }
    h1 { font-size: 1.35rem; }
    button.primary, button.auto { width: 100%; }
    .choice { flex-basis: 100%; justify-content: flex-start; }
  }
</style>
</head>
<body>
<a class="skip" href="#ask">Skip to ask</a>
<header>
  <div>
    <h1>ZionPattern Solver</h1>
    <p class="local">On this computer · 127.0.0.1</p>
  </div>
  <p class="by">Aziel Eliab</p>
</header>
<main>
  <p class="lede">Ask a question to verify, or run Auto walk on the seeded case. Displayed confidence stays at or below __CAP__, and a __FLOOR__ uncertainty floor stays on the record.</p>
  <section class="card" id="ask">
    <div class="track-label">
      <span>Displayed confidence</span>
      <b id="capnum">0.00 / __CAP_NUM__</b>
    </div>
    <div class="track" title="The fill stays inside the __CAP__ zone. The __FLOOR__ floor is not filled.">
      <div class="allowed"><div class="fill" id="fill"></div></div>
      <div class="floor">__FLOOR__ floor</div>
    </div>
    <h2>Ask to verify</h2>
    <label class="field" for="ask-text">Your question</label>
    <textarea id="ask-text" placeholder="Did the 1936 timeline leave a gap?"></textarea>
    <div class="actions">
      <button type="button" class="primary" id="btn-ask">Ask to verify</button>
    </div>
    <div class="ask-result" id="ask-result" role="status"></div>
    <h2 style="margin-top:1.25rem">Auto walk</h2>
    <p class="hint">Advances the seeded nodes on this computer. Pause leaves the current question for you.</p>
    <div class="row">
      <button type="button" class="auto" id="btn-auto">Auto walk</button>
      <button type="button" class="ghost" id="btn-pause">Pause</button>
    </div>
    <p class="status" id="auto-status" role="status"></p>
  </section>

  <details class="fold" id="advanced">
    <summary>Advanced</summary>
    <p class="hint">Manual answers, the uncertainty ledger, the nine patterns, and closing the walk.</p>
    <h2>Record answer</h2>
    <p class="qid" id="qid"></p>
    <p class="prompt" id="prompt">Loading the first question…</p>
    <fieldset class="choices" id="choices">
      <legend class="sr" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)">Answer</legend>
      <label class="choice"><input type="radio" name="answer" value="yes"> Yes</label>
      <label class="choice"><input type="radio" name="answer" value="no"> No</label>
      <label class="choice"><input type="radio" name="answer" value="unknown"> Unknown</label>
    </fieldset>
    <label class="field" for="rationale">Why this answer</label>
    <textarea id="rationale" placeholder="What in the public record supports this answer?"></textarea>
    <div class="actions">
      <button type="button" class="ghost" id="btn-record">Record answer</button>
    </div>
    <p class="status" id="qstatus" role="status"></p>
    <div class="row">
      <button type="button" class="ghost" id="btn-reset">New session</button>
      <button type="button" class="ghost" id="btn-import">Import answers</button>
      <input id="import-json" type="file" accept="application/json,.json" hidden>
      <button type="button" class="ghost" id="btn-receipt">Export receipt JSON</button>
    </div>
    <h2>Close the walk</h2>
    <p class="hint">Closing writes a provisional receipt when the cap is near and the ledger has notes.</p>
    <div class="row">
      <button type="button" class="ghost" data-term="official_unsustainable">Official account unsustainable</button>
      <button type="button" class="ghost" data-term="alternative_supported">Alternative account supported</button>
      <button type="button" class="ghost" data-term="evidence_exhaustion">Evidence exhausted</button>
    </div>
    <p class="status" id="tstatus" role="status"></p>
    <pre id="receipt" hidden></pre>

    <h2>Uncertainty ledger</h2>
    <p class="hint">Unknown answers and large score changes are logged here. Closing a walk needs at least three notes.</p>
    <div id="ledger"></div>
    <label class="field" for="manual">Add a note</label>
    <textarea id="manual" placeholder="What is still uncertain?"></textarea>
    <div class="row"><button type="button" class="ghost" id="btn-note">Add to ledger</button></div>

    <h2>Nine patterns</h2>
    <ul class="plist" id="plist"></ul>
    <h2>Scores</h2>
    <div id="scores" class="hint"></div>
  </details>

  <details class="fold">
    <summary>About</summary>
    <p>ZionPattern Solver asks archival questions and keeps a receipt on this computer. Displayed confidence stays at or below __CAP__. The __FLOOR__ uncertainty floor is part of every closed walk.</p>
    <p>__CAP__ means complete confidence the suppression was intentional. A lower number means more natural occurrence.</p>
    <p>A finished walk is provisional and assistive. It does not solve Zioncheck or any case. You decide what the record supports.</p>
    <p>From a terminal, <code>zion-solver doctor</code> checks this install. <code>zion-solver --help</code> lists commands.</p>
    <p>Author: Aziel Eliab.</p>
  </details>
</main>
<footer>Aziel Eliab · AGPL-3.0 · loopback only, no telemetry.</footer>
<script>
(function () {
  var $ = function (id) { return document.getElementById(id); };
  var fill = $("fill");
  var capnum = $("capnum");
  var CAP = __CAP_NUM__;

  function setBar(capped) {
    var c = Math.min(Number(capped) || 0, CAP);
    var pct = CAP > 0 ? Math.min(100, (c / CAP) * 100) : 0;
    fill.style.width = pct + "%";
    capnum.textContent = c.toFixed(2) + " / " + CAP.toFixed(2);
  }

  function clearChoice() {
    var picked = document.querySelectorAll('input[name="answer"]');
    for (var i = 0; i < picked.length; i++) picked[i].checked = false;
  }

  function render(state) {
    var plist = $("plist");
    plist.textContent = "";
    (state.patterns_brief || []).forEach(function (p) {
      var li = document.createElement("li");
      var name = document.createElement("span");
      var id = document.createElement("span");
      id.className = "pid";
      id.textContent = p.id;
      name.appendChild(id);
      name.appendChild(document.createTextNode(p.name));
      var pri = document.createElement("span");
      pri.className = "pri";
      pri.textContent = p.priority;
      li.appendChild(name);
      li.appendChild(pri);
      plist.appendChild(li);
    });
    var scores = state.scores || {};
    setBar(Math.min(scores.capped_confidence || 0, CAP));
    var scoreBox = $("scores");
    scoreBox.textContent = "";
    function line(text) {
      var div = document.createElement("div");
      div.textContent = text;
      scoreBox.appendChild(div);
    }
    line("Official contradiction " + Number(scores.official_contradiction || 0).toFixed(3));
    line("Alternative coherence " + Number(scores.alternative_coherence || 0).toFixed(3));
    line("Raw, before the cap " + Number(scores.raw_confidence || 0).toFixed(3));
    line("Answered " + (state.answered || 0) + " · remaining " + (state.remaining || 0));
    line("Ledger " + ((state.uncertainty_ledger || []).length) + " notes");
    var q = state.question;
    var record = $("btn-record");
    var choices = $("choices");
    if (!q) {
      $("qid").textContent = state.terminated ? "This walk is closed" : "No questions left";
      $("prompt").textContent = state.terminated
        ? "A provisional receipt is ready under Advanced."
        : "The questions are done. Add any last notes, then close the walk under Advanced.";
      record.disabled = true;
      choices.hidden = true;
    } else {
      $("qid").textContent = q.qid + " · " + q.pattern_name;
      $("prompt").textContent = q.prompt;
      record.disabled = false;
      choices.hidden = false;
    }
    var led = $("ledger");
    led.textContent = "";
    (state.uncertainty_ledger || []).forEach(function (n) {
      var d = document.createElement("div");
      d.className = "note";
      var b = document.createElement("b");
      b.textContent = n.id + " · " + n.kind;
      d.appendChild(b);
      d.appendChild(document.createElement("br"));
      d.appendChild(document.createTextNode(n.text || ""));
      led.appendChild(d);
    });
    window.__last = state;
  }

  function load() {
    fetch("/api/state").then(function (r) { return r.json(); }).then(render).catch(function () {
      $("prompt").textContent = "Could not load the session. Reload this page.";
      $("qstatus").className = "status err";
      $("qstatus").textContent = "The local app did not answer. If it stopped, run zion-solver ui again.";
    });
  }

  $("btn-record").addEventListener("click", function () {
    var picked = document.querySelector('input[name="answer"]:checked');
    $("qstatus").className = "status";
    if (!picked) {
      $("qstatus").className = "status err";
      $("qstatus").textContent = "Choose Yes, No, or Unknown, then record the answer.";
      return;
    }
    $("qstatus").textContent = "Recording…";
    fetch("/api/answer", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({value: picked.value, rationale: $("rationale").value})
    }).then(function (r) {
      return r.json().then(function (body) { return {ok: r.ok, body: body}; });
    }).then(function (res) {
      if (!res.ok) {
        $("qstatus").className = "status err";
        $("qstatus").textContent = (res.body.error || "That answer was not recorded.") + " Try Yes, No, or Unknown.";
        return;
      }
      $("rationale").value = "";
      clearChoice();
      $("qstatus").className = "status ok";
      $("qstatus").textContent = "Answer recorded.";
      render(res.body);
    }).catch(function () {
      $("qstatus").className = "status err";
      $("qstatus").textContent = "The local app did not answer. Run zion-solver ui and reload.";
    });
  });

  $("btn-note").addEventListener("click", function () {
    var text = $("manual").value;
    fetch("/api/note", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({text: text})
    }).then(function (r) {
      return r.json().then(function (body) { return {ok: r.ok, body: body}; });
    }).then(function (res) {
      if (!res.ok) {
        $("tstatus").className = "status err";
        $("tstatus").textContent = res.body.error === "text required"
          ? "Write a note, then add it to the ledger."
          : (res.body.error || "The note was not saved.");
        return;
      }
      $("manual").value = "";
      $("tstatus").className = "status ok";
      $("tstatus").textContent = "Note added.";
      render(res.body);
    });
  });

  $("btn-reset").addEventListener("click", function () {
    $("receipt").hidden = true;
    $("tstatus").textContent = "";
    $("qstatus").textContent = "";
    clearChoice();
    fetch("/api/reset", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({case: "zioncheck-1936"})
    }).then(function (r) { return r.json(); }).then(function (body) {
      render(body);
      $("qstatus").className = "status ok";
      $("qstatus").textContent = "New session ready.";
    });
  });

  document.querySelectorAll("button[data-term]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      fetch("/api/terminate", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({type: btn.getAttribute("data-term")})
      }).then(function (r) {
        return r.json().then(function (body) { return {ok: r.ok, body: body}; });
      }).then(function (res) {
        $("tstatus").className = res.ok ? "status ok" : "status err";
        if (res.ok) {
          var hash = res.body.sha256 || "";
          $("tstatus").textContent = "Provisional receipt written. Hash starts with " + hash.slice(0, 12) + ".";
          $("receipt").hidden = false;
          $("receipt").textContent = JSON.stringify(res.body, null, 2);
          if (res.body.capped_confidence != null) setBar(res.body.capped_confidence);
          load();
        } else {
          $("tstatus").textContent = (res.body.error || "The walk was not closed.") + " Add ledger notes under Advanced, then try again.";
        }
      });
    });
  });

  $("btn-import").addEventListener("click", function () { $("import-json").click(); });
  $("import-json").addEventListener("change", function () {
    var f = $("import-json").files && $("import-json").files[0];
    if (!f) return;
    f.text().then(function (text) {
      var obj;
      try { obj = JSON.parse(text); }
      catch (e) {
        $("qstatus").className = "status err";
        $("qstatus").textContent = "That file is not JSON. Choose an answers file, or keep going with the question above.";
        return null;
      }
      return fetch("/api/import", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(obj)
      });
    }).then(function (r) {
      if (!r) return null;
      return r.json();
    }).then(function (body) {
      if (!body) return;
      clearChoice();
      render(body);
      $("qstatus").className = "status ok";
      $("qstatus").textContent = "Answers imported.";
    });
  });

  $("btn-receipt").addEventListener("click", function () {
    var state = window.__last || {};
    var blob = {
      product: "ZionPattern Solver",
      author: "Aziel Eliab",
      disclaimer: "Provisional and assistive. Displayed confidence stays at or below __CAP__. Uncertainty floor __FLOOR__. __CAP__ means complete confidence the suppression was intentional; lower means more natural occurrence. This receipt does not solve Zioncheck or any case.",
      snapshot: state
    };
    $("receipt").hidden = false;
    $("receipt").textContent = JSON.stringify(blob, null, 2);
    $("tstatus").className = "status ok";
    $("tstatus").textContent = "Receipt JSON is below. It stays on this page until you copy it.";
  });

  function addLine(parent, text) {
    var div = document.createElement("div");
    div.textContent = text;
    parent.appendChild(div);
  }

  $("btn-ask").addEventListener("click", function () {
    var box = $("ask-result");
    box.textContent = "";
    addLine(box, "Checking the question against the nine patterns…");
    fetch("/api/ask", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({question: $("ask-text").value})
    }).then(function (r) {
      return r.json().then(function (body) { return {ok: r.ok, body: body}; });
    }).then(function (res) {
      box.textContent = "";
      var body = res.body || {};
      if (!res.ok || !body.ok) {
        addLine(box, body.error || "That question was not verified.");
        if (body.next) addLine(box, body.next);
        return;
      }
      addLine(box, body.provisional_answer || "Provisional.");
      (body.linked_patterns || []).forEach(function (item) {
        var extra = item.qid ? " · " + item.qid : "";
        addLine(box, item.id + "  " + item.name + extra);
      });
      addLine(box, "Displayed confidence " + Number(body.capped_confidence || 0).toFixed(2) + " of " + CAP.toFixed(2));
      addLine(box, "Uncertainty " + Number(body.uncertainty || 0).toFixed(2));
      if (body.sha256) {
        var hash = document.createElement("div");
        hash.className = "hash";
        hash.textContent = body.sha256;
        box.appendChild(hash);
      }
      addLine(box, "Assistive only. This does not solve the case.");
      if (body.snapshot) render(body.snapshot);
    }).catch(function () {
      box.textContent = "The local app did not answer. Run zion-solver ui and reload.";
    });
  });

  window.__autoOn = false;
  function showAuto(body) {
    var status = $("auto-status");
    var answered = body.answered;
    if (answered == null && body.snapshot) answered = body.snapshot.answered;
    var line = "Seeded nodes answered: " + (answered || 0) + ".";
    if (body.stopped === "pause" || !window.__autoOn && body.stopped === "step") {
      line = "Paused. Record the current question under Advanced, or press Auto walk to continue.";
    } else if (body.sha256) {
      line = "Provisional receipt " + String(body.sha256).slice(0, 12) + "…. Displayed confidence stays capped. Assistive only.";
    } else if (body.refusal) {
      line = body.refusal;
    } else if (body.stopped === "step") {
      line = "Auto walk is advancing seeded nodes. Answered " + (answered || 0) + ".";
    }
    status.textContent = line;
  }

  function autoTick() {
    if (!window.__autoOn) {
      $("auto-status").textContent = "Paused. Record the current question under Advanced, or press Auto walk to continue.";
      return;
    }
    fetch("/api/auto", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({action: "step"})
    }).then(function (r) { return r.json(); }).then(function (body) {
      if (body.snapshot) render(body.snapshot);
      var keep = body.stopped === "step" && window.__autoOn;
      if (!keep) window.__autoOn = false;
      showAuto(body);
      if (keep) autoTick();
    }).catch(function () {
      window.__autoOn = false;
      $("auto-status").textContent = "The local app did not answer. Run zion-solver ui and reload.";
    });
  }

  $("btn-auto").addEventListener("click", function () {
    if (window.__autoOn) return;
    window.__autoOn = true;
    $("auto-status").textContent = "Auto walk is advancing seeded nodes…";
    autoTick();
  });
  $("btn-pause").addEventListener("click", function () {
    window.__autoOn = false;
    $("auto-status").textContent = "Paused. Record the current question under Advanced, or press Auto walk to continue.";
  });

  load();
})();
</script>
</body>
</html>
"""

PAGE_HTML = _page_html()
