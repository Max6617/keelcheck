#!/usr/bin/env python3
"""Line coverage for keel, using only the standard library — the suite-and-coverage gate (R8, D19).

    python tools/coverage.py                      # measure, compare against the floor
    python tools/coverage.py --min 0.99           # fail below 99% instead of the recorded floor
    python tools/coverage.py --target 0.94        # the number being climbed towards

Why the standard library and not `coverage`: it is not installed here and there is no network, and
the number matters more than the tooling. `sys.settrace` records the lines that ran and
`trace._find_executable_linenos` says which lines were executable — the same measurement rentguard's
`tools/coverage.py` takes, with no dependency to install.

**The floor is an argument, never ambient state** (D19). Not an environment variable: that is state a
test cannot pin, and `keel gate run` passes no arguments to a gate, so the gate's floor has to be the
script's own default anyway. Not a floor file either: a second artefact whose honesty has to be
maintained. `DEFAULT_FLOOR` is a **ratchet** inside this script, which puts it inside the gate hash:
raising it changes the file, so it needs re-ratification (R2). Raise it in the commit that earns the
rise, never on a round number.

The failing side is forced with `--min 0.99` while the suite is green — `keel gate run` always runs
the ratified default, so a red that only proves the gate passes would prove nothing.

Exit codes: **0** at or above the floor, **1** below it, **2** when nothing could be measured at all.
A line count is a floor, not a promise: it says code was *reached*, never that its behaviour was
checked. Feature coverage is the half this script cannot see.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from trace import _find_executable_linenos

import pytest

REPO = Path(__file__).resolve().parent.parent
PACKAGE = REPO / "keel"
DEFAULT_ARGS = ["tests", "-q", "-p", "no:cacheprovider"]
#: Measured on 2026-10-14 with the suite of that commit; ratchet only upwards (R2: a rise is a gate
#: change). R8's target stays 94% until the measurement reaches it.
DEFAULT_FLOOR = 0.0
TARGET = 0.94


def _git(*args: str) -> str:
    proc = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.stdout.strip()


def _provenance() -> str:
    """The count names a commit, and says whether the tree it measured was dirty (rule 2)."""
    commit = _git("rev-parse", "HEAD") or "(no commit)"
    dirty = "dirty" if _git("status", "--porcelain") else "clean"
    return f"at {commit} worktree {dirty}"


def measure(argv: list[str]) -> tuple[dict[str, tuple[int, int]], set[str]]:
    executed: dict[str, set[int]] = {}
    seen: set[str] = set()

    def tracer(frame, event, arg):
        if event == "line":
            path = Path(frame.f_code.co_filename)
            if path.suffix == ".py" and PACKAGE in path.parents:
                executed.setdefault(str(path), set()).add(frame.f_lineno)
            elif path.suffix == ".py" and path.parent.name == PACKAGE.name:
                # A module of ours, wherever it resolved from: a checkout whose package resolved
                # elsewhere measures nothing rather than failing, and this is what diagnoses it.
                seen.add(str(path.parent))
        return tracer

    sys.settrace(tracer)
    try:
        pytest.main(argv)
    finally:
        sys.settrace(None)

    result: dict[str, tuple[int, int]] = {}
    for path in sorted(PACKAGE.rglob("*.py")):
        try:
            executable = set(_find_executable_linenos(str(path)))
        except Exception:  # noqa: BLE001 - an unreadable module must not hide the others
            continue
        hit = len(executable & executed.get(str(path), set()))
        name = str(path.relative_to(REPO)).replace("\\", "/")
        result[name] = (hit, len(executable))

    total_hit = sum(hit for hit, _ in result.values())
    if result and total_hit == 0:
        # Every module present, nothing hit: that is never a legitimate result of running the suite,
        # it is a checkout whose package resolved where the tracer was not watching. Reporting it as
        # 0.0% would let a hand-set floor turn a broken measurement into a pass.
        return {}, seen
    return result, seen


def _diagnose_unmeasured(seen: set[str]) -> None:
    print("no coverage measured — the tracer reached no module of the keel package in this checkout.")
    print(f"  expected the package here: {PACKAGE}")
    if seen:
        print("  the tracer did reach a package of this name, but elsewhere:")
        for where in sorted(seen):
            print(f"    {where}")
        print("  that is the checkout-placement trap: run this from the repository it measures.")
    else:
        print("  the tracer reached no package of this name at all — did the suite import it?")
    print("  this is a measurement failure, not a coverage result.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min", type=float, default=DEFAULT_FLOOR,
                        help=f"fail below this fraction (ratchet; default {DEFAULT_FLOOR})")
    parser.add_argument("--target", type=float, default=TARGET,
                        help=f"the number being climbed towards (default {TARGET})")
    parser.add_argument("pytest_args", nargs="*", default=DEFAULT_ARGS)
    args = parser.parse_args()

    rows, seen = measure(args.pytest_args or DEFAULT_ARGS)
    if not rows:
        _diagnose_unmeasured(seen)
        return 2

    # A measurement this suite cannot produce honestly. The suite drives keel **from outside** (D3:
    # the CLI is the observable), so nearly all of the package runs in child processes that this
    # tracer cannot see: measured 2026-10-14, `audit.py`, `export.py`, `gate.py`, `review.py`,
    # `record.py` and `cli.py` all reported 0.0% while the suite passed 101 tests against them. Zero
    # hits there is a measurement failure, not a coverage result, and letting it stand would set a
    # floor of about 15% and call the gate green. Until the tracer follows child processes, refuse.
    cli_modules = ["keel/cli.py", "keel/audit.py", "keel/gate.py", "keel/review.py"]
    blind = [name for name in cli_modules if rows.get(name, (0, 0))[0] == 0]
    if len(blind) == len(cli_modules):
        print("coverage cannot be measured honestly from this process: the suite drives the CLI "
              "through child processes (D3), which `sys.settrace` here cannot see.")
        print("  untouched in this measurement: " + ", ".join(blind))
        print("  this is a measurement failure, not a coverage result: see D19 and the note in this")
        print("  script. The gate needs a tracer that follows child processes before its number or")
        print("  its floor means anything.")
        return 2

    print(f"\n{'module':<26}{'lines':>7}{'hit':>7}{'cover':>9}")
    total_lines = total_hit = 0
    for name, (hit, total) in rows.items():
        total_lines += total
        total_hit += hit
        pct = (100.0 * hit / total) if total else 100.0
        print(f"{name:<26}{total:>7}{hit:>7}{pct:>8.1f}%")
    overall = (total_hit / total_lines) if total_lines else 0.0
    print("-" * 49)
    print(f"{'TOTAL':<26}{total_lines:>7}{total_hit:>7}{overall * 100:>8.1f}%")
    print(f"coverage {overall * 100:.1f}% (floor {args.min * 100:.1f}% target "
          f"{args.target * 100:.1f}%) {_provenance()}")

    if overall < args.min:
        print(f"FAIL: {overall * 100:.1f}% is below the floor of {args.min * 100:.1f}%")
        return 1
    if overall < args.target:
        print(f"ok — above the floor, {args.target * 100:.0f}% is still to come")
    else:
        print("target met")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
