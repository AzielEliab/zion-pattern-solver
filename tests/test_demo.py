"""Noninteractive demo completes using the seed fixture."""

from __future__ import annotations

import io
from types import SimpleNamespace

from zion_pattern_solver.cli import cmd_demo, main
from zion_pattern_solver.scoring import cap_confidence


def test_demo_noninteractive_completes() -> None:
    args = SimpleNamespace(
        interactive=False,
        answers=None,
        seed=None,
        terminate="",
    )
    buf = io.StringIO()
    rc = cmd_demo(args, out=buf)
    text = buf.getvalue()
    assert rc == 0
    assert "capped_confidence" in text
    assert "0.75" in text or "cap" in text
    assert "provisional" in text.lower() or "assistive" in text.lower() or "not" in text.lower()
    # does not claim to have solved the case
    assert "solved zioncheck" not in text.lower()


def test_demo_via_main() -> None:
    rc = main(["demo"])
    assert rc == 0
