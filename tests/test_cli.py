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


def test_bare_command_welcomes(capsys) -> None:
    rc = main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "zion-solver ui" in out
    assert "Aziel Eliab" in out
    assert "75%" in out


def test_unknown_command_has_next_step(capsys) -> None:
    import pytest

    with pytest.raises(SystemExit) as caught:
        main(["bogus"])
    assert caught.value.code == 2
    err = capsys.readouterr().err
    assert 'Unknown command "bogus"' in err
    assert "zion-solver --help" in err


def test_session_missing_case_has_next_step(capsys) -> None:
    import pytest

    with pytest.raises(SystemExit) as caught:
        main(["session"])
    assert caught.value.code == 2
    err = capsys.readouterr().err
    assert "zioncheck-1936" in err


def test_version_json(capsys) -> None:
    import json

    rc = main(["version", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["version"] == __version__
    assert payload["name"] == "zion-pattern-solver"
    assert payload["author"] == "Aziel Eliab"


def test_ask_timeline_is_provisional(capsys) -> None:
    import json

    rc = main(["ask", "Did the 1936 timeline leave a gap before the Arctic Building?"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Provisional" in out
    assert "P1" in out
    assert "sha256" in out
    assert "does not solve" in out.lower()


def test_ask_json_and_empty(capsys) -> None:
    import json

    rc = main(["--json", "ask", "Did the 1936 timeline leave a gap?"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["capped_confidence"] <= 0.75
    assert len(payload["sha256"]) == 64
    assert payload["author"] == "Aziel Eliab"

    rc = main(["verify"])
    assert rc == 2
    err = capsys.readouterr().out
    assert "question" in err.lower()
    assert "zion-solver ask" in err


def test_auto_writes_capped_receipt(capsys) -> None:
    import json

    rc = main(["auto", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["applied_count"] >= 1
    assert payload["capped_confidence"] <= 0.75
    assert payload["sha256"]
    assert len(payload["sha256"]) == 64
    assert payload["receipt"]["capped_confidence"] <= 0.75


def test_auto_pause_after(capsys) -> None:
    rc = main(["auto", "--pause-after", "2"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Paused after 2" in out
    assert "0.75" in out or "cap" in out.lower() or "confidence" in out.lower()


def test_patterns_json_shape(capsys) -> None:
    import json

    rc = main(["--json", "patterns"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["patterns"]) == 9
    assert payload["confidence_cap"] == 0.75
