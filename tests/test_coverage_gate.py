"""`tools/coverage.py`, the suite-and-coverage gate (R8, D19, D20).

The gate runs the suite and measures the package. Two properties about it are properties of an honest
measurement rather than a threshold:

1. **The blind case refuses.** A run that reaches no keel code measures zero, and zero is a
   measurement failure, not a 0% score: the gate exits 2 and says why. This must keep holding once the
   tracer follows child processes — a working tracer makes the real measurement non-zero, and the
   refusal could be dropped at the same time and never noticed. Green on landing deliberately: it is a
   pin against that loss, not a red against today.
2. **The tracer reaches the children.** Red until the tracer follows the subprocesses the suite uses
   (D3). It is **not written yet**, on purpose: it asserts on structured output, and `--json` is
   arriving with the tracer, so the shape has to come before the test rather than the other way round
   (D3 — a test is never written against a guess). The red, once the shape is fixed: a target that
   only drives `keel` from outside shows `keel/audit.py` at a non-zero percentage.

**Recursion, named because it is the trap here.** No test in this file may run the gate over the full
suite: the gate runs `pytest tests`, which contains this file, so such a test would re-enter itself.
Both the blind case and the tracer case therefore pass an explicit small target instead.
"""

from __future__ import annotations

import os
import subprocess
import sys

import _support

GATE = _support.REPO / "tools" / "coverage.py"
BLIND_TARGET = "tests/_artefacts/blind_target.py"


def _gate(*args: str) -> subprocess.CompletedProcess:
    """Run the gate the way CI would, from the repository root.

    **Only paths, no pytest flags.** `pytest_args` is a `nargs="*"` positional, so argparse refuses
    anything starting with `-` (`unrecognized arguments: -q -p no:cacheprovider`) even though the
    gate's own `DEFAULT_ARGS` carry exactly those flags. Passing a target replaces the defaults
    wholesale, so a caller cannot add a flag without `--`; that is a finding for Mason, not something
    this test papers over.
    """
    return subprocess.run(
        [sys.executable, str(GATE), *args],
        cwd=str(_support.REPO), capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=900,
    )


def test_a_target_that_reaches_no_keel_code_refuses_instead_of_reporting_zero():
    proc = _gate("--min", "0.0", BLIND_TARGET)
    out = _support.combined(proc)

    assert proc.returncode == 2, (
        "a measurement that found no keel code did not refuse; a zero number would let a hand-set "
        f"floor turn a broken measurement into a pass\n{out}")
    # The measured wording at 866912b: "no coverage measured -- the tracer reached no module of the
    # keel package ... this is a measurement failure, not a coverage result". The child-process
    # explanation belongs to the other refusal path, so the assertion names what the gate prints.
    assert "measurement failure" in out.lower(), (
        f"the refusal does not say it is a measurement failure:\n{out}")
    assert "reached no module" in out.lower(), (
        f"the refusal does not say the tracer reached nothing:\n{out}")
