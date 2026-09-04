"""CLI: version, patterns, demo."""

from __future__ import annotations

from zion_pattern_solver import __version__
from zion_pattern_solver.cli import main
from zion_pattern_solver.patterns import PATTERNS


def test_cli_version(capsys) -> None:
    rc = main(["version"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "zion-pattern-solver" in out
    assert __version__ in out


def test_cli_patterns(capsys) -> None:
    rc = main(["patterns"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "75" in out
    for p in PATTERNS:
        assert p.id in out
        assert p.name in out
    assert "does not solve" in out.lower() or "provisional" in out.lower() or "assistive" in out.lower()


def test_help_lists_ui_and_version() -> None:
    from zion_pattern_solver.cli import _build_parser

    text = _build_parser().format_help()
    assert "ui" in text
    assert "version" in text
    assert "127.0.0.1:8790" in text or "zion-solver ui" in text


def test_doctor_passes() -> None:
    from zion_pattern_solver.doctor import run_doctor

    assert run_doctor(as_json=True) == 0
