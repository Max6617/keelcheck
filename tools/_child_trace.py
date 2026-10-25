"""The child-process half of the coverage gate (R8, D19).

The suite drives keelcheck from outside (D3), so the gate's tracer in the pytest process sees almost
nothing: measured 2026-10-14, `audit.py`, `gate.py`, `review.py` and `export.py` all reported 0.0%
while 101 tests passed against them. This module is the other half — it runs *inside* every child
interpreter the suite starts and records the lines of the package that ran there.

The gate activates it, and only it: the bootstrap on `PYTHONPATH` calls :func:`activate`, which does
nothing at all unless the gate has set `KEELCHECK_COVERAGE_CHILD`. A normal `pytest` run, or any other
python process on the machine, sets none of this and is untouched.

    KEELCHECK_COVERAGE_CHILD=1        set by the gate for the run it starts
    KEELCHECK_COVERAGE_DIR=<dirs>     where each child writes its hits, one file per process; a `pathsep`
                                 separated list, because a gate run inside a gate run (the suite runs
                                 `tools/coverage.py` itself) writes to its own directory *and* to the
                                 outer measurement's, so neither loses the other's lines
    KEELCHECK_COVERAGE_PACKAGE=<dir>  the package root whose files count

Hits are written at exit, one `path<TAB>line` per executed line. A process killed before exit writes
nothing, which is why the gate still checks that the measurement is not blind rather than trusting it.
"""

from __future__ import annotations

import atexit
import os
import sys
import threading
from pathlib import Path

__all__ = ["activate"]


def activate() -> None:
    """Start the tracer in this interpreter when the gate asked for it. Otherwise do nothing."""
    if not os.environ.get("KEELCHECK_COVERAGE_CHILD"):
        return
    package = os.environ.get("KEELCHECK_COVERAGE_PACKAGE")
    outs = [part for part in (os.environ.get("KEELCHECK_COVERAGE_DIR") or "").split(os.pathsep) if part]
    if not package or not outs:
        return
    root = Path(package).resolve()
    hits: set[tuple[str, int]] = set()
    known: dict[str, Path | None] = {}

    def traced_file(filename: str) -> Path | None:
        """The resolved path when it is one of ours, cached per code object's filename."""
        if filename in known:
            return known[filename]
        found: Path | None = None
        if filename.endswith(".py"):
            try:
                candidate = Path(filename).resolve()
                if root in candidate.parents:
                    found = candidate
            except OSError:
                found = None
        known[filename] = found
        return found

    def tracer(frame, event, arg):
        if event == "line":
            found = traced_file(frame.f_code.co_filename)
            if found is not None:
                hits.add((str(found), frame.f_lineno))
        return tracer

    sys.settrace(tracer)
    # The child is what measures the modules, so the same rule as the parent's tracer: `sys.settrace`
    # reaches only the calling thread, and a package line that only runs on a worker thread would sit in
    # the denominator unhittable (see tools/coverage.py and tests/test_thread_trace.py).
    threading.settrace(tracer)

    def flush() -> None:
        # Every directory the gate that started this process asked for, fixed at activation: a nested
        # gate rewrites the variable for its own children, and this process's targets must not move.
        for out in outs:
            try:
                target = Path(out) / f"{os.getpid()}.txt"
                with open(target, "a", encoding="utf-8") as handle:
                    for path, line in sorted(hits):
                        handle.write(f"{path}\t{line}\n")
            except OSError:  # pragma: no cover - the gate reports a blind measurement instead
                pass

    atexit.register(flush)
