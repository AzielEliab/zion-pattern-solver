"""Worker UI rose-star brand mark contract.

Visible mark is /sigil.png with empty alt and no words.
Public identity is Aziel Eliab only. Do not put “everblooming sigil”
on the mark. FragGate / Remain-OFF / mesh.js stay untouched.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "workers/download-tracker/src/index.js").read_text(encoding="utf-8")
MESH = (ROOT / "workers/download-tracker/src/mesh.js").read_text(encoding="utf-8")
WRANGLER = (ROOT / "workers/download-tracker/wrangler.toml").read_text(encoding="utf-8")

ROSE_STAR_SHA256 = "af095e8b0916a7262860a53619c7110f25539988806775b1c7bff8df7b0ee848"
BRAND_MARK = (
    '<div class="brandrow"><img class="brandmark" src="/sigil.png" '
    'width="40" height="40" alt="" decoding="async"></div>'
)


def test_home_and_ai_rose_star_brand_mark_empty_alt() -> None:
    assert INDEX.count(BRAND_MARK) == 2
    assert 'class="brandrow"' in INDEX
    assert 'class="brandmark"' in INDEX
    assert 'src="/sigil.png"' in INDEX
    assert 'alt=""' in INDEX
    assert 'rel="icon" type="image/png" href="/sigil.png"' in INDEX
    assert ".brandrow" in INDEX
    assert ".brandmark" in INDEX
    assert "Aziel Eliab" in INDEX
    assert "everblooming sigil" not in INDEX.lower()
    assert "Everblooming sigil" not in INDEX
    assert 'alt="Everblooming' not in INDEX
    assert "Everblooming sigil ·" not in INDEX


def test_public_sigil_png_is_official_rose_star() -> None:
    path = ROOT / "workers/download-tracker/public/sigil.png"
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 60_000
    assert hashlib.sha256(data).hexdigest() == ROSE_STAR_SHA256
    assert 'directory = "./public"' in WRANGLER
    assert "/sigil.png" not in WRANGLER


def test_fraggate_remain_off_mesh_untouched() -> None:
    # #13: the suite mesh presents as read-only presence ON, never as a live mesh (no mesh-off kill switch).
    assert 'MESH_DEFAULT_OFF = false' in MESH
    assert 'MESH_DEFAULT_OFF = true' not in MESH
    assert 'MESH_PRESENCE = "read-only presence ON; not a live mesh"' in MESH
    assert 'MESH_CAVEAT = "Not a live end-to-end QNM mesh."' in MESH
    assert 'MESH_NODE_LIVE = false' in MESH
    assert "read-only presence ON; not a live mesh" in INDEX
    # FragGate / Remain-OFF part unchanged: no Node Gate, no anonymity network, no auto-heal, FragGate slug "mesh".
    assert 'MESH_NODE_GATE = false' in MESH
    assert 'MESH_ANONYMITY_NETWORK = false' in MESH
    assert 'MESH_AUTO_HEAL = false' in MESH
    assert 'MESH_SLUG = "mesh"' in MESH
    assert "/v1/fraggate/call" in MESH
    assert 'MESH_PRODUCT = "zsolver"' in MESH
    assert "QNM-BUILD-1.0" in MESH
    assert "QNS-CD-1.0" in MESH
    assert "Aziel Eliab" in MESH
    assert "everblooming" not in MESH.lower()
    assert "everblooming" not in WRANGLER.lower()


def test_docs_no_stale_mesh_default_off() -> None:
    """#13: docs must not claim the suite mesh is default OFF; they say read-only presence ON, not live."""
    import re as _re
    for rel in ("README.md", "SKILL.md", "workers/download-tracker/README.md"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert not _re.search(r"default\s+off", text, _re.I), rel
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "read-only presence ON; not a live mesh" in skill
