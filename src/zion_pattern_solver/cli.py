"""Command-line interface for ZionPattern Solver.

    zion-solver version
    zion-solver patterns
    zion-solver demo
    zion-solver session --case NAME
    zion-solver ui
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from zion_pattern_solver import __version__
from zion_pattern_solver.errors import SessionError, TerminationRefused
from zion_pattern_solver.patterns import PATTERNS
from zion_pattern_solver.receipts import utc_now
from zion_pattern_solver.scoring import CONFIDENCE_CAP, UNCERTAINTY_FLOOR, cap_confidence
from zion_pattern_solver.session import Session
from zion_pattern_solver.terminate import TERMINATION_TYPES, terminate
from zion_pattern_solver.ui import DEFAULT_HOST, DEFAULT_PORT, serve

DISCLAIMER_LINE = (
    "Provisional and assistive only. Does not solve Zioncheck or any case. "
    f"Hard cap {int(CONFIDENCE_CAP*100)}% / uncertainty floor {int(UNCERTAINTY_FLOOR*100)}%. "
    "75 = complete confidence in intentional suppression; "
    "lower = more natural occurrence."
)


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


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="zion-solver",
        description=(
            "ZionPattern Solver (Z-Solver) v0.3 — 75% Cap Edition. "
            "Local-first, human-in-the-loop. Provisional/assistive only. "
            "Local UI: `zion-solver ui` at http://127.0.0.1:8790."
        ),
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("version", help="Print package version.")
    sub.add_parser("patterns", help="List the nine versioned patterns.")

    p_demo = sub.add_parser(
        "demo",
        help="Zioncheck seed walkthrough (default: noninteractive fixture).",
    )
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

    p_ui = sub.add_parser("ui", help="Localhost UI on 127.0.0.1 (default port 8790).")
    p_ui.add_argument("--host", default=DEFAULT_HOST, help="Bind host (default 127.0.0.1).")
    p_ui.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port (default 8790).")
    p_doc = sub.add_parser("doctor", help="Self-check. No network, no telemetry.")
    p_doc.add_argument("--json", action="store_true", dest="as_json", help="Print JSON.")

    return p


def _print_patterns(out) -> None:
    out.write(f"ZionPattern Solver v{__version__} — nine patterns (schema 0.2.0)\n")
    out.write(DISCLAIMER_LINE + "\n\n")
    for pat in PATTERNS:
        out.write(f"  {pat.id}  {pat.name}  [{pat.priority}]\n")
        out.write(f"      {pat.core_contradiction}\n")
        out.write(f"      heuristic: {pat.detection_heuristic}\n")
        out.write(f"      evidence:  {pat.evidence_priority}\n")
        out.write(f"      questions: {len(pat.question_templates)}\n\n")


def _load_answers(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit("answers file must be a JSON object keyed by qid")
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


def _interactive_walk(session: Session, out, inp) -> None:
    out.write(DISCLAIMER_LINE + "\n")
    out.write("Answers: yes / no / unknown. Type quit to stop.\n\n")
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
            out.write(f"  ! {exc}\n")


def _print_scores(session: Session, out) -> None:
    s = session.scores()
    out.write("\nScores (provisional):\n")
    out.write(f"  official_contradiction  {s.official_contradiction:.3f}\n")
    out.write(f"  alternative_coherence   {s.alternative_coherence:.3f}\n")
    out.write(f"  raw_confidence          {s.raw_confidence:.3f}\n")
    out.write(f"  capped_confidence       {cap_confidence(s.capped_confidence):.3f}  (cap {CONFIDENCE_CAP})\n")
    out.write(f"  uncertainty notes       {len(session.uncertainty_ledger)}\n")
    out.write(f"  {DISCLAIMER_LINE}\n")


def cmd_demo(args, out=None, inp=None) -> int:
    out = out or sys.stdout
    inp = inp or sys.stdin
    ex = _example_dir()
    seed_path = Path(args.seed) if args.seed else ex / "seed.json"
    seed = {}
    if seed_path.is_file():
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
    case = str(seed.get("case") or "zioncheck-1936")
    out.write(f"Z-Solver demo  case={case}\n")
    out.write(str(seed.get("disclaimer") or DISCLAIMER_LINE) + "\n")
    session = Session(case=case)
    if args.interactive:
        _interactive_walk(session, out, inp)
    else:
        ans_path = Path(args.answers) if args.answers else ex / "demo_answers.json"
        if not ans_path.is_file():
            out.write(f"missing answers fixture: {ans_path}\n")
            return 2
        _apply_fixture(session, _load_answers(ans_path))
        out.write(f"applied {len(session.history())} fixture answers from {ans_path.name}\n")
    _print_scores(session, out)
    kind = (args.terminate or "").strip()
    if kind:
        try:
            rec = terminate(session, kind)
            out.write(f"terminated ({kind}) sha256={rec.sha256}\n")
        except TerminationRefused as exc:
            out.write(f"termination refused: {exc}\n")
            return 3
    return 0


def cmd_session(args, out=None, inp=None) -> int:
    out = out or sys.stdout
    inp = inp or sys.stdin
    session = Session(case=args.case)
    if args.answers:
        _apply_fixture(session, _load_answers(Path(args.answers)))
    else:
        _interactive_walk(session, out, inp)
    _print_scores(session, out)
    kind = (args.terminate or "").strip()
    if kind:
        try:
            rec = terminate(session, kind)
            out.write(f"terminated ({kind}) sha256={rec.sha256}\n")
            if args.emit_receipt:
                rec.write(args.emit_receipt)
                out.write(f"wrote {args.emit_receipt}\n")
        except TerminationRefused as exc:
            out.write(f"termination refused: {exc}\n")
            return 3
    elif args.emit_receipt:
        out.write("no --terminate given; receipt not written\n")
        return 4
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "version":
        sys.stdout.write(f"zion-pattern-solver {__version__}\n")
        return 0
    if args.cmd == "patterns":
        _print_patterns(sys.stdout)
        return 0
    if args.cmd == "demo":
        return cmd_demo(args)
    if args.cmd == "session":
        return cmd_session(args)
    if args.cmd == "ui":
        serve(host=args.host, port=args.port)
        return 0

    if args.cmd == "doctor":
        from zion_pattern_solver.doctor import run_doctor
        return run_doctor(as_json=getattr(args, "as_json", False))

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
