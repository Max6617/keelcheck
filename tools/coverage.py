#!/usr/bin/env python3
"""Line coverage for keelcheck, using only the standard library — the suite-and-coverage gate (R8, D19).

    python tools/coverage.py                      # measure, compare against the floor
    python tools/coverage.py --min 0.99           # fail below 99% instead of the recorded floor
    python tools/coverage.py --target 0.94        # the number being climbed towards
    python tools/coverage.py --json               # the machine-readable document (D19's shape)
    python tools/coverage.py --min 0.99 -- tests -x   # pytest flags go after `--`

Why the standard library and not `coverage`: it is not installed here and there is no network, and
the number matters more than the tooling. `sys.settrace` records the lines that ran and
`trace._find_executable_linenos` says which lines were executable — the same measurement rentguard's
`tools/coverage.py` takes, with no dependency to install.

**The children count, or the number is a lie.** The suite drives keelcheck from outside (D3: the CLI is the
observable), so a tracer in this process sees almost nothing: measured 2026-10-14, `audit.py`,
`gate.py`, `review.py` and `export.py` all read 0.0% while 101 tests passed against them. So the gate
puts `tools/_child_trace.py` on `PYTHONPATH` behind a flag only *it* sets, and every `python -m keelcheck`
the suite starts records its own lines; the gate merges them. A normal `pytest` run is untouched.
`KEELCHECK_COVERAGE_DIR` is a `pathsep` list, because the suite runs this script and so the gate runs
itself: a nested run prepends its own directory, each child writes every hit into every directory, and
the nested gate then measures only its own run while the outer measurement still receives those lines.
Both other shapes were measured and are wrong — see `_child_setup`.

**The floor is an argument, never ambient state** (D19). Not an environment variable: that is state a
test cannot pin, and `keelcheck gate run` passes no arguments to a gate, so the gate's floor has to be the
script's own default anyway. Not a floor file either: a second artefact whose honesty has to be
maintained. `DEFAULT_FLOOR` is a **ratchet** inside this script, which puts it inside the gate hash:
raising it changes the file, so it needs re-ratification (R2). Raise it in the commit that earns the
rise, never on a round number.

**The failing side is forced with `--min 0.99`** while the suite is green — `keelcheck gate run` always runs
the ratified default, so a red that only proves the gate passes would prove nothing.

**A suite that does not pass is not a coverage result.** `pytest.main` returns a count, not a verdict,
and coverage can sit above the floor on a red tree: lines run whether or not the assertions hold. The
gate therefore fails on the suite's own exit code before it compares anything, and says which of the
two failed — a green number over a red suite is exactly the shape the audit exists to catch.

Exit codes: **0** at or above the floor with the suite passing, **1** below the floor or with the
suite failing, **2** when nothing could be measured honestly — no keelcheck module reached at all, or the
CLI modules untouched while the suite passed, which is the blind measurement a working tracer is
supposed to remove and the check that has to survive it.

`DEFAULT_ARGS` carries `-p no:cacheprovider` on purpose, and `pyproject.toml` therefore declares no
`cache_dir`: pytest creates its cache directory through `tempfile.TemporaryDirectory` (mode 0700),
which this host's sandbox refuses, so a run that keeps the plugin pays a `PytestCacheWarning` and
leaves a `pytest-cache-files-*` directory behind. A key the run's own flag disables would be reported
as unknown, which reads as broken configuration, so the key is not declared at all; `testpaths` and
`norecursedirs` are what hold collection.

A line count is a floor, not a promise: it says code was *reached*, never that its behaviour was
checked. Feature coverage is the half this script cannot see.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import uuid
from pathlib import Path
from trace import _find_executable_linenos

import pytest

REPO = Path(__file__).resolve().parent.parent
PACKAGE = REPO / "keelcheck"
TOOLS = REPO / "tools"
DEFAULT_ARGS = ["tests", "-q", "-p", "no:cacheprovider"]
#: Measured on 2026-10-15 with the suite of `9f2deed`, every CLI module measured through the child
#: tracer: **2031 of 2419 executable lines**, 0.839603, printed as 84.0%. The floor is that number
#: **rounded down** to 0.83 — not to the printed 0.84, which is above the measurement and would make
#: the gate fail on its own first honest run. Ratchet only upwards, and each rise is a gate change
#: inside this hash, so it is raised in the commit that earns it (R2). R8's 94% stays the target.
DEFAULT_FLOOR = 0.83
TARGET = 0.94

#: The flag the gate sets for the run it starts. `tools/_child_trace.py` does nothing without it.
CHILD_FLAG = "KEELCHECK_COVERAGE_CHILD"
CHILD_DIR = "KEELCHECK_COVERAGE_DIR"
CHILD_PACKAGE = "KEELCHECK_COVERAGE_PACKAGE"
SITECUSTOMIZE = "import _child_trace\n_child_trace.activate()\n"

#: Modules that only ever run in a child process when the suite drives the CLI. All of them at zero
#: means the measurement is blind, whatever the total says.
CLI_MODULES = ["keelcheck/cli.py", "keelcheck/audit.py", "keelcheck/gate.py", "keelcheck/review.py"]

BLIND_EXPLANATION = (
    "coverage cannot be measured honestly from this process: the suite drives the CLI through child "
    "processes (D3), and this tracer cannot see them. A floor set from this number would be a lie."
)
UNREACHED_EXPLANATION = (
    "no coverage measured — the tracer reached no module of the keelcheck package in this checkout. "
    "This is a measurement failure, not a coverage result."
)


def _suite_failed(suite_status: int) -> str:
    return (
        f"the suite did not pass (pytest exit {suite_status}): a coverage number over a red suite is "
        "not a pass, and the gate fails on the suite before it compares anything."
    )


def _git(*args: str) -> str:
    proc = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.stdout.strip()


def provenance() -> dict:
    """The count names a commit, and says whether the tree it measured was dirty (rule 2)."""
    return {
        "sha": _git("rev-parse", "HEAD") or "(no commit)",
        "worktree": "dirty" if _git("status", "--porcelain") else "clean",
    }


def _provenance_line(found: dict) -> str:
    return f"at {found['sha']} worktree {found['worktree']}"


def _child_setup() -> Path:
    """Create this run's hit directory and put the child tracer on the next interpreter's path.

    **A gate run inside a gate run is not a hypothetical, it is the suite**:
    `tests/test_coverage_gate.py` runs this script, so the gate runs itself. Measured 2026-10-15, both
    wrong ways: a nested run that gave up measured nothing, its own target read 0.0%, and the suite
    failed inside the gate (1 failed, 109 passed, 5 skipped in 10:06) while passing outside it; a
    nested run that *shared* the outer run's directory instead read 49.9% from the outer suite's hits
    and could no longer refuse the blind target (the suite failed with the other test). So this run
    gets a directory of its own, **added to** the inherited list: the child tracer writes every hit
    into every directory on the list, so the nested gate measures only its own run while the outer
    measurement still receives the lines from these grandchildren.
    """
    # **Not** `tempfile.mkdtemp`: on this host the sandbox refuses writes inside a directory created
    # mode 0700, and a chmod afterwards does not lift it — the same trap that makes `TemporaryDirectory`
    # unusable in the suite, and the same one that makes pytest's own cache directory fail. A plain
    # `mkdir` inherits the parent's permissions and is writable.
    directory = Path(tempfile.gettempdir()) / f"keelcheck-coverage-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TOOLS / "_child_trace.py", directory / "_child_trace.py")
    (directory / "sitecustomize.py").write_text(SITECUSTOMIZE, encoding="utf-8")
    inherited = os.environ.get(CHILD_DIR, "")
    os.environ[CHILD_FLAG] = "1"
    os.environ[CHILD_DIR] = str(directory) + (os.pathsep + inherited if inherited else "")
    os.environ[CHILD_PACKAGE] = str(PACKAGE)
    existing = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = str(directory) + (os.pathsep + existing if existing else "")
    return directory


def _merge_child_hits(directory: Path, executed: dict[str, set[int]]) -> int:
    """Every child's lines, one `path<TAB>line` per executed line, merged into the parent's."""
    merged = 0
    for hit_file in sorted(directory.glob("*.txt")):
        for entry in hit_file.read_text(encoding="utf-8", errors="replace").splitlines():
            name, _, line = entry.partition("\t")
            if name and line.isdigit():
                executed.setdefault(name, set()).add(int(line))
                merged += 1
    return merged


def measure(argv: list[str], *, quiet: bool = False) -> tuple[dict[str, tuple[int, int]], set[str], int]:
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

    directory = _child_setup()
    captured = io.StringIO()
    sys.settrace(tracer)
    # `sys.settrace` reaches only the thread that calls it, and the package runs code on threads
    # (`review.py` starts two daemon threads around `_drain`). Without this, every line that only ever
    # runs on a thread sits in the denominator and can never be hit -- a number wrong in the direction
    # nobody checks. Measured: 2026-10-15, `review.py` line 72 (inside `split_command`) ran on a worker
    # thread and was not recorded before this line existed (tests/test_thread_trace.py).
    threading.settrace(tracer)
    try:
        if quiet:
            # `--json` promises one JSON object on stdout. pytest's own banner goes there, so the
            # document would not be the first thing a consumer reads; the run's output is not the
            # gate's output in that mode. A red suite's output is kept and replayed on stderr.
            with contextlib.redirect_stdout(captured):
                suite_status = int(pytest.main(argv))
        else:
            suite_status = int(pytest.main(argv))
    finally:
        sys.settrace(None)
        threading.settrace(None)
        if directory is not None:
            try:
                # Only this run's own directory: the outer run's hits are not this measurement's, and
                # a nested run that read them could not refuse the blind case.
                _merge_child_hits(directory, executed)
            finally:
                shutil.rmtree(directory, ignore_errors=True)

    if quiet and suite_status != 0 and captured.getvalue():
        sys.stderr.write(captured.getvalue())

    result: dict[str, tuple[int, int]] = {}
    for path in sorted(PACKAGE.rglob("*.py")):
        try:
            # `isinstance(n, int)` is not defensive coding: 3.13's `dis.findlinestarts` yields a `None`
            # entry per code object where 3.12's skips it, so an unfiltered denominator gains one
            # entry per file that no line can ever hit and the rate reads permanently low. Assay
            # measured it on CI: zero executable line numbers differ between 3.12 and 3.13, the whole
            # delta is those `None` keys, and on an unchanged hit count the rate moved 98.2% ->
            # 97.9%. A per-interpreter floor would enshrine that artefact; the filter removes it
            # (Assay's measurement, 2026-10-15).
            executable = {n for n in _find_executable_linenos(str(path)) if isinstance(n, int)}
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
        return {}, seen, suite_status
    return result, seen, suite_status


def _percentages(rows: dict[str, tuple[int, int]]) -> dict[str, float]:
    return {
        name: round((100.0 * hit / total) if total else 100.0, 1)
        for name, (hit, total) in rows.items()
    }


def _emit_json(document: dict) -> None:
    """UTF-8 to stdout whatever the console code page is, like the rest of keelcheck's output (D8)."""
    text = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    buffer = getattr(sys.stdout, "buffer", None)
    if buffer is None:  # pragma: no cover - a captured stdout with no buffer
        print(text, end="")
        return
    sys.stdout.flush()
    buffer.write(text.encode("utf-8"))
    buffer.flush()


def _refusal(found: dict, args: argparse.Namespace, reason: str) -> int:
    """A measurement the gate will not dress up: no number in either output, and exit 2."""
    if args.json:
        _emit_json({"keelcheck": "coverage/1", "total": None, "files": {}, "exit": 2,
                    "provenance": found, "floor": args.min, "target": args.target,
                    "reason": reason})
    return 2


def _diagnose_unmeasured(seen: set[str]) -> None:
    print(UNREACHED_EXPLANATION)
    print(f"  expected the package here: {PACKAGE}")
    if seen:
        print("  the tracer did reach a package of this name, but elsewhere:")
        for where in sorted(seen):
            print(f"    {where}")
        print("  that is the checkout-placement trap: run this from the repository it measures.")
    else:
        print("  the tracer reached no package of this name at all — did the suite import it?")
    print("  this is a measurement failure, not a coverage result.")


def _report(rows: dict[str, tuple[int, int]], percentages: dict[str, float]) -> tuple[int, int]:
    """The per-module table, and the two totals it ends with."""
    print(f"\n{'module':<26}{'lines':>7}{'hit':>7}{'cover':>9}")
    for name, (hit, total) in rows.items():
        print(f"{name:<26}{total:>7}{hit:>7}{percentages[name]:>8.1f}%")
    total_lines = sum(total for _, total in rows.values())
    total_hit = sum(hit for hit, _ in rows.values())
    print("-" * 49)
    print(f"{'TOTAL':<26}{total_lines:>7}{total_hit:>7}"
          f"{(100.0 * total_hit / total_lines) if total_lines else 0.0:>8.1f}%")
    return total_lines, total_hit


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="pytest flags need `--`, because they start with `-`: "
               "`coverage.py --min 0.99 -- tests -x`.")
    parser.add_argument("--min", type=float, default=DEFAULT_FLOOR,
                        help=f"fail below this fraction (ratchet; default {DEFAULT_FLOOR})")
    parser.add_argument("--target", type=float, default=TARGET,
                        help=f"the number being climbed towards (default {TARGET})")
    parser.add_argument("--json", action="store_true", help="machine-readable document (D19)")
    parser.add_argument("pytest_args", nargs="*", default=DEFAULT_ARGS)
    args = parser.parse_args()

    rows, seen, suite_status = measure(args.pytest_args or DEFAULT_ARGS, quiet=args.json)
    found = provenance()
    if not rows:
        if args.json:
            _refusal(found, args, UNREACHED_EXPLANATION)
        else:
            _diagnose_unmeasured(seen)
        return 2

    # A measurement this suite cannot produce honestly: the CLI modules run in child processes, so
    # all of them at zero means the tracer missed the work, not that the work is untested.
    blind = [name for name in CLI_MODULES if rows.get(name, (0, 0))[0] == 0]
    if len(blind) == len(CLI_MODULES):
        reason = f"{BLIND_EXPLANATION} Untouched in this measurement: {', '.join(blind)}."
        if args.json:
            return _refusal(found, args, reason)
        print(reason)
        print("  this is a measurement failure, not a coverage result: see D19 and the note in this")
        print("  script. The gate needs a tracer that follows child processes before its number or")
        print("  its floor means anything.")
        return 2

    percentages = _percentages(rows)
    total_lines = sum(total for _, total in rows.values())
    total_hit = sum(hit for hit, _ in rows.values())
    overall = (total_hit / total_lines) if total_lines else 0.0
    # The suite's own verdict comes first: pytest.main returns a count, and lines run on a red tree.
    suite_reason = None if suite_status == 0 else _suite_failed(suite_status)
    exit_code = 1 if suite_reason else (1 if overall < args.min else 0)

    if args.json:
        _emit_json({"keelcheck": "coverage/1", "total": round(overall * 100, 1),
                    "files": percentages, "exit": exit_code, "provenance": found,
                    "floor": args.min, "target": args.target, "reason": suite_reason,
                    "lines": {"total": total_lines, "hit": total_hit},
                    "suite": {"exit": suite_status, "passed": suite_status == 0}})
        return exit_code

    _report(rows, percentages)
    print(f"coverage {overall * 100:.1f}% (floor {args.min * 100:.1f}% target "
          f"{args.target * 100:.1f}%) {_provenance_line(found)}")

    if suite_reason:
        print(f"FAIL: {suite_reason}")
        return 1
    if exit_code:
        print(f"FAIL: {overall * 100:.1f}% is below the floor of {args.min * 100:.1f}%")
        return 1
    if overall < args.target:
        print(f"ok — above the floor, {args.target * 100:.0f}% is still to come")
    else:
        print("target met")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
