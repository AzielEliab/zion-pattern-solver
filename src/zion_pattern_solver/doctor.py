"""Self-check for ZionPattern Solver. No network, no telemetry.

    zion-solver doctor
"""

from __future__ import annotations

import json
from typing import Callable

from zion_pattern_solver import __version__

Check = tuple[str, bool, str]


def _ok(name: str, detail: str = "") -> Check:
    return name, True, detail


def _fail(name: str, detail: str) -> Check:
    return name, False, detail


def _check_version() -> Check:
    if __version__ == "0.4.0":
        return _ok("version", __version__)
    return _fail("version", __version__)


def _check_derive() -> Check:
    from zion_pattern_solver.derive import score_document

    title = (
        "Marion A. Zioncheck Visual Archive Vol 1 — "
        "Primary Documents, Death Certificates & Forensic Analysis"
    )
    result = score_document({"title": title})
    capped = result["capped_confidence"]
    yeses = [a for a in result["answers"] if a.get("value") == "yes"]
    if capped <= 0.0 or capped > 0.75:
        return _fail("derive", f"capped_confidence={capped}")
    if not yeses:
        return _fail("derive", "seed volume produced no yes answers")
    if not result.get("seed_corpus"):
        return _fail("derive", "seed_corpus false for Vol 1")
    if result.get("display") != 75:
        return _fail("derive", f"display={result.get('display')}")
    return _ok("derive", "volumes 1-5 seed method")


def _check_identity() -> Check:
    author = getattr(__import__("zion_pattern_solver", fromlist=["__author__"]), "__author__", "Aziel Eliab")
    if "Aziel Eliab" not in str(author):
        return _fail("identity", str(author))
    blob = str(author) + " " + "THIS IS: modular local-first interrogation engine with a hard 75% confidence cap and 25% uncertainty floor. THIS IS NOT: a solved case, a court, or a truth machine. Provisional and assistive only. Author: Aziel Eliab."
    if ("GodLock" + ".AZ") in blob:
        return _fail("identity", "forbidden identity label leaked")
    return _ok("identity", "Aziel Eliab")


def _check_cap() -> Check:
    from zion_pattern_solver.scoring import CONFIDENCE_CAP, cap_confidence
    if CONFIDENCE_CAP != 0.75:
        return _fail("cap", str(CONFIDENCE_CAP))
    if cap_confidence(0.99) != 0.75:
        return _fail("cap_confidence", str(cap_confidence(0.99)))
    return _ok("cap", "0.75 hard cap")


CHECKS: tuple[Callable[[], Check], ...] = (
    _check_version,
    _check_identity,
    _check_cap,
    _check_derive,
)


def run_doctor(*, as_json: bool = False) -> int:
    results = []
    failed = 0
    for fn in CHECKS:
        name, ok, detail = fn()
        results.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            failed += 1
        mark = "ok" if ok else "FAIL"
        if not as_json:
            print(f"[{mark}] {name}" + (f" — {detail}" if detail else ""))
    payload = {
        "ok": failed == 0,
        "failed": failed,
        "checks": results,
        "version": __version__,
        "author": "Aziel Eliab",
        "network": False,
        "telemetry": False,
    }
    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        print("doctor", "passed" if failed == 0 else "failed")
    return 0 if failed == 0 else 1
