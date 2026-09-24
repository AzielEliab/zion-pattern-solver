"""Command-line interface for ZionPattern Solver.

    zion-solver
    zion-solver ui
    zion-solver demo
    zion-solver session --case NAME
    zion-solver doctor
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Sequence, TextIO

from zion_pattern_solver import __version__
from zion_pattern_solver.errors import SessionError, TerminationRefused
from zion_pattern_solver.patterns import PATTERNS, SCHEMA_VERSION
from zion_pattern_solver.scoring import CONFIDENCE_CAP, UNCERTAINTY_FLOOR, cap_confidence
from zion_pattern_solver.session import Session
from zion_pattern_solver.terminate import terminate
from zion_pattern_solver.ui import DEFAULT_HOST, DEFAULT_PORT, serve

CAP_LINE = (
    "Displayed confidence stays at or below 75%. "
    "Uncertainty floor 25%. "
    "75 means complete confidence the suppression was intentional; "
    "a lower number means more natural occurrence. "
    "Provisional and assistive."
)

HELP_TEXT = f"""\
usage: zion-solver [--json] <command> [<args>]

Ask a question to verify, or auto-walk the seeded case. Displayed confidence stays at or below 75%.

commands:
  ui         Open the local app at http://127.0.0.1:{DEFAULT_PORT}
  ask        Ask a question to verify
  verify     Same as ask
  auto       Walk the seeded nodes and write a receipt when the rules allow
  demo       Walk the included Zioncheck seed
  session    Start a named local session
  doctor     Check this install
  patterns   List the nine patterns
  version    Print the version
  help       Show this help

examples:
  zion-solver
  zion-solver ui
  zion-solver ask "Did the 1936 timeline leave a gap?"
  zion-solver auto
  zion-solver doctor

advanced:
  zion-solver session --case NAME
  zion-solver session --case NAME --terminate official_unsustainable --emit-receipt receipt.json
  zion-solver demo --interactive
  zion-solver demo --answers FILE.json
  zion-solver patterns --json
  zion-solver ui --port {DEFAULT_PORT}

--json prints machine-readable JSON. People get plain text by default.

Author: Aziel Eliab
"""


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    # src/zion_pattern_solver/cli.py -> repo root is parents[2]
    return here.parents[2]


def _example_dir() -> Path:
    candidates = [
        Path.cwd() / "examples" / "zioncheck_irn_nodes",
        _repo_root() / "examples" / "zioncheck_irn_nodes",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]


def _human_error(prog: str, message: str) -> str:
    choice = re.search(r"invalid choice: '([^']*)'", message)
    if choice:
        bad = choice.group(1)
        return (
            f'Unknown command "{bad}". '
            "Try: zion-solver ui   or   zion-solver --help\n"
        )
    if "required" in message and "--case" in message:
        return (
            "A case name is required.\n"
            "Try: zion-solver session --case zioncheck-1936\n"
        )
    if message.startswith("unrecognized arguments"):
        extra = message.split(":", 1)[-1].strip()
        return f'Unknown option "{extra}".\nTry: {prog} --help\n'
    if "expected one argument" in message or "invalid" in message:
        return f"That option needs a usable value ({message}).\nTry: {prog} --help\n"
    return f"Could not run that ({message}).\nTry: {prog} --help\n"


class SolverParser(argparse.ArgumentParser):
    """Plain misuse messages: a reason and a next step."""

    def error(self, message: str) -> None:
        self.exit(2, _human_error(self.prog, message))


class TopParser(SolverParser):
    def format_help(self) -> str:
        return HELP_TEXT


def _add_json(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        default=argparse.SUPPRESS,
        help="Print JSON for scripts and agents.",
    )


def _wants_json(args: object) -> bool:
    return bool(getattr(args, "as_json", False))


def _build_parser() -> argparse.ArgumentParser:
    p = TopParser(
        prog="zion-solver",
        description=(
            "Walk a local case one question at a time. "
            f"Local UI: zion-solver ui at http://127.0.0.1:{DEFAULT_PORT}."
        ),
    )
    _add_json(p)
    sub = p.add_subparsers(dest="cmd", required=False, parser_class=SolverParser)

    p_version = sub.add_parser("version", help="Print the version.")
    _add_json(p_version)

    p_patterns = sub.add_parser("patterns", help="List the nine patterns.")
    _add_json(p_patterns)

    p_ask = sub.add_parser("ask", help="Ask a question to verify.")
    _add_json(p_ask)
    p_ask.add_argument("question", nargs="*", help="The question, in your own words.")

    p_verify = sub.add_parser("verify", help="Same as ask.")
    _add_json(p_verify)
    p_verify.add_argument("question", nargs="*", help="The question, in your own words.")

    p_auto = sub.add_parser(
        "auto",
        help="Walk the seeded nodes and write a receipt when the rules allow.",
    )
    _add_json(p_auto)
    p_auto.add_argument(
        "--pause-after",
        type=int,
        default=None,
        help="Stop after this many seeded nodes so you can answer the rest.",
    )
    p_auto.add_argument(
        "--answers",
        default=None,
        help="Answers JSON to walk. Default: the Zioncheck seed fixture.",
    )
    p_auto.add_argument(
        "--emit-receipt",
        default=None,
        metavar="FILE.json",
        help="If a receipt is written, also save it here.",
    )

    p_demo = sub.add_parser(
        "demo",
        help="Walk the Zioncheck seed (fixture answers unless --interactive).",
    )
    _add_json(p_demo)
    p_demo.add_argument(
        "--interactive",
        action="store_true",
        help="Ask on stdin instead of using examples/.../demo_answers.json.",
    )
    p_demo.add_argument(
        "--answers",
        default=None,
        help="Override answers JSON path (default: seed fixture).",
    )
    p_demo.add_argument(
        "--seed",
        default=None,
        help="Override seed JSON path.",
    )
    p_demo.add_argument(
        "--terminate",
        default="",
        help="If set, attempt this termination type after the walk.",
    )

    p_sess = sub.add_parser("session", help="Start a named local session.")
    _add_json(p_sess)
    p_sess.add_argument("--case", required=True, help="Case name.")
    p_sess.add_argument(
        "--answers",
        default=None,
        help="Optional answers JSON (qid -> {value, rationale}) for noninteractive use.",
    )
    p_sess.add_argument(
        "--emit-receipt",
        default=None,
        metavar="FILE.json",
        help="If the walk can terminate, write a receipt here.",
    )
    p_sess.add_argument(
        "--terminate",
        default="",
        help="Attempt termination type after answers (official_unsustainable, ...).",
    )

    p_ui = sub.add_parser("ui", help=f"Local app on 127.0.0.1 (default port {DEFAULT_PORT}).")
    _add_json(p_ui)
    p_ui.add_argument("--host", default=DEFAULT_HOST, help="Bind host (default 127.0.0.1).")
    p_ui.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port (default {DEFAULT_PORT}).")

    p_doc = sub.add_parser("doctor", help="Check this install. No network, no telemetry.")
    _add_json(p_doc)

    p_help = sub.add_parser("help", help="Show help.")
    _add_json(p_help)

    return p


def _emit_json(out: TextIO, payload: object) -> None:
    out.write(json.dumps(payload, indent=2))
    out.write("\n")


def _print_welcome(out: TextIO, *, as_json: bool) -> None:
    if as_json:
        _emit_json(
            out,
            {
                "name": "zion-pattern-solver",
                "version": __version__,
                "author": "Aziel Eliab",
                "next": [
                    "zion-solver ui",
                    "zion-solver ask",
                    "zion-solver auto",
                    "zion-solver doctor",
                ],
            },
        )
        return
    out.write(
        "ZionPattern Solver asks a question to verify, or auto-walks a seeded case. "
        "Displayed confidence stays at or below 75%.\n\n"
        "Next, open the local app:\n\n"
        "  zion-solver ui\n\n"
        "Or from here:\n\n"
        "  zion-solver ask \"Did the 1936 timeline leave a gap?\"\n"
        "  zion-solver auto\n\n"
        "Check this install:  zion-solver doctor\n"
        "All commands:        zion-solver --help\n\n"
        "Author: Aziel Eliab\n"
    )


def _print_patterns(out: TextIO, *, as_json: bool = False) -> None:
    if as_json:
        _emit_json(
            out,
            {
                "schema": SCHEMA_VERSION,
                "confidence_cap": CONFIDENCE_CAP,
                "uncertainty_floor": UNCERTAINTY_FLOOR,
                "patterns": [p.to_dict() for p in PATTERNS],
            },
        )
        return
    out.write(f"Nine patterns  (schema {SCHEMA_VERSION})\n")
    out.write(CAP_LINE + "\n\n")
    for pat in PATTERNS:
        out.write(f"  {pat.id}  {pat.name}  [{pat.priority}]\n")
        out.write(f"      {pat.core_contradiction}\n")
        out.write(f"      heuristic: {pat.detection_heuristic}\n")
        out.write(f"      evidence:  {pat.evidence_priority}\n")
        out.write(f"      questions: {len(pat.question_templates)}\n\n")


def _load_answers(path: Path) -> dict:
    hint = "Try: zion-solver demo --answers examples/zioncheck_irn_nodes/demo_answers.json\n"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"Could not read {path} ({exc}).\n{hint}") from exc
    except json.JSONDecodeError:
        raise SystemExit(f"{path} is not valid JSON.\n{hint}") from None
    if not isinstance(raw, dict):
        raise SystemExit(
            f"{path} must be a JSON object keyed by question id.\n"
            "Try: zion-solver demo --help\n"
        )
    return raw


def _apply_fixture(session: Session, answers: dict) -> None:
    while True:
        q = session.ask()
        if q is None:
            break
        item = answers.get(q.qid) or answers.get(q.pattern_id) or {}
        if isinstance(item, str):
            value, rationale = item, "fixture"
        else:
            value = item.get("value", "unknown")
            rationale = item.get("rationale", "fixture")
        session.answer(str(value), str(rationale))


def _interactive_walk(session: Session, out: TextIO, inp: TextIO) -> None:
    out.write(f"Case: {session.case}\n")
    out.write("Answer yes, no, or unknown. A rationale can follow the answer.\n")
    out.write("Type quit to stop.\n\n")
    while True:
        q = session.ask()
        if q is None:
            break
        scores = session.scores()
        out.write(
            f"[{q.qid}] {q.pattern_name} ({q.priority})  "
            f"capped={cap_confidence(scores.capped_confidence):.2f}/{CONFIDENCE_CAP}\n"
        )
        out.write(f"  {q.prompt}\n")
        out.write("  answer [yes/no/unknown]: ")
        out.flush()
        line = inp.readline()
        if not line:
            break
        line = line.strip()
        if line.lower() in {"quit", "exit", "q"}:
            break
        if " " in line:
            value, rationale = line.split(" ", 1)
        else:
            value, rationale = line, ""
        try:
            session.answer(value, rationale)
        except SessionError as exc:
            out.write(f"  {exc}\n")
            out.write("  Try yes, no, or unknown.\n")


def _print_scores(session: Session, out: TextIO) -> None:
    s = session.scores()
    out.write("\nScores (provisional):\n")
    out.write(f"  official_contradiction  {s.official_contradiction:.3f}\n")
    out.write(f"  alternative_coherence   {s.alternative_coherence:.3f}\n")
    out.write(f"  raw_confidence          {s.raw_confidence:.3f}\n")
    out.write(
        f"  capped_confidence       {cap_confidence(s.capped_confidence):.3f}"
        f"  (cap {CONFIDENCE_CAP})\n"
    )
    out.write(f"  uncertainty notes       {len(session.uncertainty_ledger)}\n")
    out.write(f"  {CAP_LINE}\n")


def _finish_terminate(session: Session, args, out: TextIO, *, as_json: bool) -> int:
    kind = (getattr(args, "terminate", "") or "").strip()
    emit = getattr(args, "emit_receipt", None)
    if as_json:
        payload = session.snapshot()
        payload["applied_answers"] = len(session.history())
        if not kind:
            if emit:
                payload["ok"] = False
                payload["error"] = "no termination type given"
                _emit_json(out, payload)
                return 4
            _emit_json(out, payload)
            return 0
        try:
            rec = terminate(session, kind)
        except TerminationRefused as exc:
            payload["ok"] = False
            payload["error"] = str(exc)
            _emit_json(out, payload)
            return 3
        if emit:
            rec.write(emit)
        body = rec.to_dict()
        body["ok"] = True
        body["snapshot"] = session.snapshot()
        _emit_json(out, body)
        return 0

    _print_scores(session, out)
    if not kind:
        if emit:
            out.write(
                "No receipt written. Pass --terminate with a closing type.\n"
                "Try: zion-solver session --help\n"
            )
            return 4
        out.write("\nNext: zion-solver ui\n")
        return 0
    try:
        rec = terminate(session, kind)
    except TerminationRefused as exc:
        out.write(f"Could not close the walk: {exc}\n")
        out.write("Next: add uncertainty notes, then try the same command again.\n")
        return 3
    out.write(f"Closed ({kind}). sha256={rec.sha256}\n")
    if emit:
        rec.write(emit)
        out.write(f"Wrote {emit}\n")
    return 0


def _joined_question(args) -> str:
    parts = getattr(args, "question", None) or []
    if isinstance(parts, str):
        return parts.strip()
    return " ".join(str(part) for part in parts).strip()


def _print_verify(payload: dict, out: TextIO) -> None:
    if not payload.get("ok"):
        out.write(str(payload.get("error") or "That question was not verified.") + "\n")
        if payload.get("next"):
            out.write(str(payload["next"]) + "\n")
        return
    out.write(str(payload.get("provisional_answer") or "Provisional.") + "\n\n")
    linked = payload.get("linked_patterns") or []
    if linked:
        out.write("Linked patterns:\n")
        for item in linked:
            node = f"  {item.get('qid')}" if item.get("qid") else ""
            out.write(f"  {item.get('id')}  {item.get('name')}{node}\n")
        out.write("\n")
    out.write(
        f"Displayed confidence  {float(payload.get('capped_confidence') or 0):.2f}"
        f" / {CONFIDENCE_CAP:.2f}\n"
    )
    out.write(
        f"Uncertainty           {float(payload.get('uncertainty') or 0):.2f}"
        f"  (floor {int(UNCERTAINTY_FLOOR * 100)}%)\n"
    )
    if payload.get("sha256"):
        out.write(f"Receipt sha256        {payload['sha256']}\n")
    out.write("\nAssistive only. This does not solve the case.\n")
    out.write("Author: Aziel Eliab\n")


def cmd_ask(args, out=None) -> int:
    from zion_pattern_solver.verify import ask_to_verify

    out = out or sys.stdout
    payload = ask_to_verify(_joined_question(args))
    if _wants_json(args):
        _emit_json(out, payload)
    else:
        _print_verify(payload, out)
    return 0 if payload.get("ok") else 2


def _print_auto(payload: dict, out: TextIO) -> None:
    if not payload.get("ok"):
        out.write(str(payload.get("error") or "Auto walk did not run.") + "\n")
        if payload.get("next"):
            out.write(str(payload["next"]) + "\n")
        return
    count = int(payload.get("applied_count") or 0)
    stopped = str(payload.get("stopped") or "")
    out.write("Auto walk\n")
    out.write(f"Case: {payload.get('case')}\n")
    if stopped == "step":
        out.write(f"Paused after {count} seeded node{'s' if count != 1 else ''}.\n")
    else:
        out.write(f"Advanced {count} seeded node{'s' if count != 1 else ''}.\n")
    out.write(
        f"Displayed confidence {float(payload.get('capped_confidence') or 0):.3f}"
        f" of {CONFIDENCE_CAP:.2f}.\n"
    )
    out.write(f"Uncertainty notes {int(payload.get('uncertainty_notes') or 0)}.\n")
    if payload.get("sha256"):
        kind = ""
        receipt = payload.get("receipt") or {}
        term = receipt.get("termination") if isinstance(receipt, dict) else None
        if isinstance(term, dict) and term.get("type"):
            kind = f" ({term['type']})"
        out.write(f"Provisional receipt{kind}.\n")
        out.write(f"sha256 {payload['sha256']}\n")
    elif payload.get("refusal"):
        out.write(str(payload["refusal"]) + "\n")
    out.write("\nAssistive only. This does not solve the case.\n")
    if stopped == "step":
        out.write("Next: zion-solver auto    or record the current question in zion-solver ui\n")
    else:
        out.write("Next: zion-solver ui\n")
    out.write("Author: Aziel Eliab\n")


def cmd_auto(args, out=None) -> int:
    from zion_pattern_solver.auto import auto_run, load_seed_answers

    out = out or sys.stdout
    pause_after = getattr(args, "pause_after", None)
    if pause_after is not None and pause_after < 1:
        message = "Pause after needs a number of nodes.\nTry: zion-solver auto --pause-after 3\n"
        if _wants_json(args):
            _emit_json(out, {"ok": False, "error": "pause-after needs a number of nodes", "next": "zion-solver auto --pause-after 3"})
        else:
            out.write(message)
        return 2
    answers = None
    if getattr(args, "answers", None):
        answers = _load_answers(Path(args.answers))
    elif pause_after is None:
        answers = None
    try:
        if answers is None and getattr(args, "answers", None) is None:
            seed_answers = None
        else:
            seed_answers = answers
        if seed_answers is None:
            try:
                seed_answers = load_seed_answers()
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                payload = {
                    "ok": False,
                    "error": f"Could not read the seeded answers ({exc}).",
                    "next": "Try: zion-solver auto   from the project directory",
                }
                if _wants_json(args):
                    _emit_json(out, payload)
                else:
                    _print_auto(payload, out)
                return 2
        from zion_pattern_solver.session import Session

        session = Session(case="zioncheck-1936")
        payload = auto_run(session, seed_answers, limit=pause_after)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        payload = {
            "ok": False,
            "error": f"Could not read the seeded answers ({exc}).",
            "next": "Try: zion-solver auto --answers examples/zioncheck_irn_nodes/demo_answers.json",
        }
    if payload.get("ok") and payload.get("receipt") and getattr(args, "emit_receipt", None):
        from zion_pattern_solver.receipts import Receipt

        Receipt.from_dict(payload["receipt"]).write(args.emit_receipt)
        payload = dict(payload)
        payload["wrote"] = args.emit_receipt
    if _wants_json(args):
        _emit_json(out, payload)
    else:
        _print_auto(payload, out)
        if payload.get("wrote"):
            out.write(f"Wrote {payload['wrote']}\n")
    if not payload.get("ok"):
        return 2
    if int(payload.get("applied_count") or 0) == 0 and payload.get("stopped") == "no-fixture":
        return 2
    return 0


def cmd_demo(args, out=None, inp=None) -> int:
    out = out or sys.stdout
    inp = inp or sys.stdin
    as_json = _wants_json(args)
    ex = _example_dir()
    seed_path = Path(args.seed) if args.seed else ex / "seed.json"
    seed = {}
    if seed_path.is_file():
        try:
            seed = json.loads(seed_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            if not as_json:
                out.write(f"{seed_path} is not valid JSON.\n")
                out.write("Try: zion-solver demo --seed examples/zioncheck_irn_nodes/seed.json\n")
            else:
                _emit_json(out, {"ok": False, "error": f"invalid seed JSON: {seed_path}"})
            return 2
        if not isinstance(seed, dict):
            seed = {}
    case = str(seed.get("case") or "zioncheck-1936")
    session = Session(case=case)
    if args.interactive:
        if not as_json:
            out.write("Zioncheck seed walk\n")
            out.write(f"Case: {case}\n")
            out.write("Provisional and assistive. Displayed confidence stays at or below 75%.\n")
        _interactive_walk(session, out, inp)
    else:
        ans_path = Path(args.answers) if args.answers else ex / "demo_answers.json"
        if not ans_path.is_file():
            if as_json:
                _emit_json(out, {"ok": False, "error": f"missing answers fixture: {ans_path}"})
            else:
                out.write(f"Could not find answers at {ans_path}.\n")
                out.write(
                    "Try: zion-solver demo   from the project directory, "
                    "or pass --answers FILE.json\n"
                )
            return 2
        if not as_json:
            out.write("Zioncheck seed walk\n")
            out.write(f"Case: {case}\n")
            out.write("Provisional and assistive. Displayed confidence stays at or below 75%.\n")
        _apply_fixture(session, _load_answers(ans_path))
        if not as_json:
            out.write(f"Applied {len(session.history())} fixture answers from {ans_path.name}\n")
    return _finish_terminate(session, args, out, as_json=as_json)


def cmd_session(args, out=None, inp=None) -> int:
    out = out or sys.stdout
    inp = inp or sys.stdin
    as_json = _wants_json(args)
    session = Session(case=args.case)
    if args.answers:
        _apply_fixture(session, _load_answers(Path(args.answers)))
        if not as_json:
            out.write(f"Case: {args.case}\n")
            out.write(f"Applied {len(session.history())} answers.\n")
    else:
        if as_json:
            _emit_json(
                out,
                {
                    "ok": False,
                    "error": "session --json needs --answers",
                    "next": "zion-solver session --case NAME --answers FILE.json --json",
                },
            )
            return 2
        _interactive_walk(session, out, inp)
    return _finish_terminate(session, args, out, as_json=as_json)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    as_json = _wants_json(args)

    if not args.cmd:
        _print_welcome(sys.stdout, as_json=as_json)
        return 0
    if args.cmd in {"help"}:
        sys.stdout.write(HELP_TEXT)
        return 0
    if args.cmd == "version":
        if as_json:
            _emit_json(
                sys.stdout,
                {
                    "name": "zion-pattern-solver",
                    "version": __version__,
                    "author": "Aziel Eliab",
                },
            )
        else:
            sys.stdout.write(f"zion-pattern-solver {__version__}\n")
        return 0
    if args.cmd == "patterns":
        _print_patterns(sys.stdout, as_json=as_json)
        return 0
    if args.cmd in {"ask", "verify"}:
        return cmd_ask(args)
    if args.cmd == "auto":
        return cmd_auto(args)
    if args.cmd == "demo":
        return cmd_demo(args)
    if args.cmd == "session":
        return cmd_session(args)
    if args.cmd == "ui":
        serve(host=args.host, port=args.port)
        return 0
    if args.cmd == "doctor":
        from zion_pattern_solver.doctor import run_doctor

        return run_doctor(as_json=as_json)

    sys.stderr.write(
        f'Unknown command "{args.cmd}". Try: zion-solver ui   or   zion-solver --help\n'
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
