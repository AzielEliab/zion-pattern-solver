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
    assert 'MESH_DEFAULT_OFF = true' in MESH
    assert 'MESH_PRODUCT = "zsolver"' in MESH
    assert "QNM-BUILD-1.0" in MESH
    assert "QNS-CD-1.0" in MESH
    assert "Aziel Eliab" in MESH
    assert "everblooming" not in MESH.lower()
    assert "everblooming" not in WRANGLER.lower()
