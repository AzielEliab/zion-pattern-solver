"""UI GET / 200 contains 75% and ZionPattern; bind 127.0.0.1; no CDN."""

from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from zion_pattern_solver.ui import DEFAULT_HOST, DEFAULT_PORT, PAGE_HTML, _State, make_handler, serve


def test_html_contains_cap_and_name() -> None:
    assert "ZionPattern" in PAGE_HTML
    assert "75%" in PAGE_HTML
    assert "25%" in PAGE_HTML
    assert "cdn" not in PAGE_HTML.lower()
    assert "googleapis" not in PAGE_HTML.lower()
    assert "<style>" in PAGE_HTML
    assert "127.0.0.1" in PAGE_HTML
    assert "does" in PAGE_HTML.lower() and "solve" in PAGE_HTML.lower()
    # bar physically capped
    assert "75%" in PAGE_HTML
    assert "allowed" in PAGE_HTML
    assert "floor" in PAGE_HTML.lower()


def test_default_bind() -> None:
    assert DEFAULT_HOST == "127.0.0.1"
    assert DEFAULT_PORT == 8790


def test_ui_get_root_200() -> None:
    handler = make_handler(_State())
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    host, port = httpd.server_address[:2]
    assert host == "127.0.0.1"
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/")
        resp = conn.getresponse()
        body = resp.read().decode("utf-8")
        assert resp.status == 200
        assert "75%" in body
        assert "ZionPattern" in body

        conn.request("GET", "/health")
        health = json.loads(conn.getresponse().read().decode("utf-8"))
        assert health["ok"] is True
        assert health["bind_host"] == "127.0.0.1"

        conn.request("GET", "/api/state")
        state = json.loads(conn.getresponse().read().decode("utf-8"))
        assert state["capped_confidence"] <= 0.75
        assert "patterns_brief" in state
        assert len(state["patterns_brief"]) == 9
        conn.close()
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_ui_answer_and_cap() -> None:
    handler = make_handler(_State())
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request(
            "POST",
            "/api/answer",
            body=json.dumps({"value": "yes", "rationale": "ui test"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        body = json.loads(conn.getresponse().read().decode("utf-8"))
        assert body["capped_confidence"] <= 0.75
        conn.close()
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_serve_rejects_non_loopback(monkeypatch) -> None:
    """serve() rewrites non-loopback hosts to 127.0.0.1 before bind."""
    seen = {}

    class Dummy:
        def __init__(self, addr, handler):
            seen["addr"] = addr

        def serve_forever(self):
            raise KeyboardInterrupt

        def server_close(self):
            seen["closed"] = True

    import zion_pattern_solver.ui as ui

    monkeypatch.setattr(ui, "ThreadingHTTPServer", Dummy)
    ui.serve(host="0.0.0.0", port=8790)
    assert seen["addr"][0] == "127.0.0.1"
