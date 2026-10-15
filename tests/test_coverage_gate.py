"""`tools/coverage.py`, the suite-and-coverage gate (R8, D19, D20).

The gate runs the suite and measures the package. Two properties about it are properties of an honest
measurement rather than a threshold:

1. **The blind case refuses.** A run that reaches no keelcheck code measures zero, and zero is a
   measurement failure, not a 0% score: the gate exits 2 and says why. This must keep holding once the
   tracer follows child processes — a working tracer makes the real measurement non-zero, and the
   refusal could be dropped at the same time and never noticed. Green on landing deliberately: it is a
   pin against that loss, not a red against today.
2. **The tracer reaches the children.** Red until the tracer follows the subprocesses the suite uses
   (D3). It is **not written yet**, on purpose: it asserts on structured output, and `--json` is
   arriving with the tracer, so the shape has to come before the test rather than the other way round
   (D3 — a test is never written against a guess). The red, once the shape is fixed: a target that
   only drives `keelcheck` from outside shows `keelcheck/audit.py` at a non-zero percentage.

**Recursion, named because it is the trap here.** No test in this file may run the gate over the full
suite: the gate runs `pytest tests`, which contains this file, so such a test would re-enter itself.
Both the blind case and the tracer case therefore pass an explicit small target instead.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

import _support

GATE = _support.REPO / "tools" / "coverage.py"
BLIND_TARGET = "tests/_artefacts/blind_target.py"
CHILD_TARGET = "tests/_artefacts/child_trace_target.py"
FAILING_TARGET = "tests/_artefacts/failing_target.py"
NESTED_TARGET = "tests/_artefacts/nested_target.py"
HOOK_TARGET = "tests/_artefacts/hook_under_gate_target.py"


def _gate(*args: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Run the gate the way CI would, from the repository root.

    **Only paths, no pytest flags** — unless you pass `--` first. `pytest_args` is a `nargs="*"`
    positional, so argparse refuses anything starting with `-` without the escape
    (`unrecognized arguments: -q -p no:cacheprovider`), even though `DEFAULT_ARGS` carry exactly those
    flags. Mason documented `--` as the supported path in `af85c71` and kept strict parsing on
    purpose: a permissive parser would hand a typo'd gate flag to pytest silently.
    """
    return subprocess.run(
        [sys.executable, str(GATE), *args],
        cwd=str(_support.REPO), capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8", **(env_extra or {})}, timeout=900,
    )


def test_a_target_that_reaches_no_keel_code_refuses_instead_of_reporting_zero():
    proc = _gate("--min", "0.0", BLIND_TARGET)
    out = _support.combined(proc)

    assert proc.returncode == 2, (
        "a measurement that found no keelcheck code did not refuse; a zero number would let a hand-set "
        f"floor turn a broken measurement into a pass\n{out}")
    # The measured wording at 866912b: "no coverage measured -- the tracer reached no module of the
    # keelcheck package ... this is a measurement failure, not a coverage result". The child-process
    # explanation belongs to the other refusal path, so the assertion names what the gate prints.
    assert "measurement failure" in out.lower(), (
        f"the refusal does not say it is a measurement failure:\n{out}")
    assert "reached no module" in out.lower(), (
        f"the refusal does not say the tracer reached nothing:\n{out}")


def test_the_tracer_reaches_the_cli_modules_through_child_processes():
    """The red for the child-process tracer, and the reason the gate exists.

    The suite drives keelcheck from outside (D3), so a tracer in the pytest process sees nothing: measured
    at `866912b`, `audit.py`, `gate.py`, `review.py` and `export.py` all reported 0.0% while 101 tests
    passed against them — 15.3% total, a measurement failure dressed as a score. The target here
    imports nothing; it drives `keelcheck audit` in a subprocess. If the tracer follows children,
    `keelcheck/audit.py` cannot be 0.0%.

    Asserted on `--json` (D19 shape, agreed with Mason and Gilbert), never on the printed table: total,
    per-file percentages keyed by repo-relative path, the decided exit code, and the provenance line —
    full sha plus `worktree clean|dirty` — so a machine consumer gets what the human line has.
    """
    proc = _gate("--min", "0.0", "--json", CHILD_TARGET)

    assert proc.stdout.strip().startswith("{"), (
        "the gate has no `--json` yet, so the tracer cannot be asserted on the agreed shape "
        f"(D19):\n{_support.combined(proc)[:400]}")

    doc = json.loads(proc.stdout)
    files = doc["files"]

    assert files.get("keelcheck/audit.py", 0.0) > 0.0, (
        f"a target that drives the audit in a child process still measures keelcheck/audit.py at 0.0%:\n"
        f"{json.dumps(files, indent=2)[:600]}")
    assert doc["exit"] == proc.returncode, "the document's exit code is not the one the gate returned"
    provenance = doc.get("provenance") or {}
    assert provenance.get("sha") and provenance.get("worktree") in ("clean", "dirty"), (
        f"the document carries no provenance line (D19): {provenance!r}")


def test_a_red_suite_is_not_masked_by_the_coverage_number():
    """Mason's red-suite branch, pinned.

    The target drives keelcheck in a child — so the measurement is non-zero and the floor cannot be the
    thing that refuses — and then fails. Coverage above the floor must not turn a red suite green:
    exit 1, the reason says the suite did not pass, and the JSON carries `suite {exit, passed}`.
    `--min 0.0` is passed deliberately, so a floor of zero cannot mask it either.
    """
    proc = _gate("--min", "0.0", "--json", FAILING_TARGET)

    assert proc.stdout.strip().startswith("{"), (
        f"the gate printed no JSON document:\n{_support.combined(proc)[:400]}")
    doc = json.loads(proc.stdout)

    assert proc.returncode == 1, (
        f"a failing suite exited {proc.returncode}; coverage is not a verdict on the tests:\n"
        f"{_support.combined(proc)[-400:]}")
    assert doc["suite"]["passed"] is False and doc["suite"]["exit"] == 1, (
        f"the document does not report the failing suite: {doc.get('suite')!r}")
    assert "did not pass" in (doc.get("reason") or ""), (
        f"the reason does not say the suite failed: {doc.get('reason')!r}")


def test_a_nested_run_measures_only_itself_and_keeps_the_parents_path(scratch):
    """The nested gate, measured rather than argued.

    The outer gate runs `nested_target.py`, which runs the inner gate over `child_trace_target.py`
    and records that inner document plus its own inherited `PYTHONPATH`. Two properties:

    1. **Isolation** — the inner total equals a standalone run of the same target, so a nested run
       measures its own hits and does not read the outer run's. (Mason's construction: `measure()`
       merges only the directory `_child_setup()` returned; inherited directories are written to,
       never read.)
    2. **The parent's `PYTHONPATH` survives** — the tracer may add a directory, never remove one.
       Gilbert's assertion, and the class that broke the hook tests under the gate: they failed with
       `No module named keelcheck` when the hook fired a commit, because a child could not import the
       tool it was testing. A nested run that cannot import the tool is not a nested run.
    """
    out = scratch / "nested-measurement.json"
    outer = _gate("--min", "0.0", "--json", NESTED_TARGET,
                  env_extra={"KEEL_NESTED_OUT": str(out)})
    recorded = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    standalone = _gate("--min", "0.0", "--json", CHILD_TARGET)

    assert recorded, f"the nested target wrote no measurement:\n{_support.combined(outer)[-400:]}"
    inner = json.loads(recorded["inner_stdout"])
    reference = json.loads(standalone.stdout)

    assert abs(inner["total"] - reference["total"]) < 1e-9, (
        f"a nested run measured {inner['total']} where the same target alone measures "
        f"{reference['total']}, so it is reading hits that are not its own")

    inherited = [p for p in (recorded["inherited_pythonpath"] or "").split(os.pathsep) if p]
    parent = [p for p in (os.environ.get("PYTHONPATH") or "").split(os.pathsep) if p]
    missing = [p for p in parent if p not in inherited]
    assert not missing, (
        "the gate replaced the parent's PYTHONPATH instead of extending it, so a child cannot "
        f"import what the parent could: {missing} (child saw {inherited})")


def test_a_commit_through_the_installed_hook_lands_inside_a_gate_run(scratch):
    """The child that actually failed: `gate -> pytest -> target -> git -> sh -> python -m keelcheck`.

    The nested test above measures `gate -> pytest -> target` and says so; it cannot reach the hook,
    whose script resolves its own import root at *install* time and is then started by git's `sh`.
    On 2026-10-15 two runs of this gate over this suite at the same commit disagreed (exit 0 and exit
    1), and the failing one died here with `No module named keelcheck` — every commit blocked,
    including one whose gates pass. Nothing pinned that shape until now.

    Two properties make it the regression test rather than a rerun (Gilbert, 2026-10-15):

    1. the hook is **installed from the tree under test** inside the gate run, so install-time
       resolution is exercised rather than inherited;
    2. the commit is made **inside the gate run**, and the target records the gate's own child-process
       variables — the outer assertion checks `KEELCHECK_COVERAGE_CHILD` was set for the process that
       made the commit, so a commit made outside a gate cannot pass as if it had been inside one.

    Asserted on the target's recorded document, not on the exit code alone: a skipped or uncollected
    target also exits 0, and "the gate passed" must not be satisfiable by a gate that never ran.
    """
    out = scratch / "hook-under-gate.json"
    proc = _gate("--min", "0.0", HOOK_TARGET, env_extra={"KEEL_HOOK_GATE_OUT": str(out)})

    assert out.exists(), (
        "the target recorded nothing, so it did not reach the end of its own fixture:\n"
        f"{_support.combined(proc)[-800:]}")
    doc = json.loads(out.read_text(encoding="utf-8"))

    if not doc.get("git_sh_works"):
        pytest.skip(f"git cannot start a hook on this host: {doc.get('git_sh_reason')!r}")

    inside = doc.get("inside_gate") or {}
    assert inside.get("KEELCHECK_COVERAGE_CHILD") == "1", (
        "the commit was not made inside a gate run, so this shape could have passed without "
        f"reproducing it: {inside!r}")
    assert doc.get("hook_installed"), (
        f"no hook was installed into the fixture repo:\n{doc.get('install_output')}")
    assert doc.get("commit_returncode") == 0, (
        "the installed hook blocked a commit whose gate passes; a hook that cannot start blocks "
        f"*every* commit:\n{doc.get('commit_output')}")
    assert doc.get("head_after") != doc.get("head_before"), (
        "the commit did not land, so the hook was reached but nothing was verified")
    assert proc.returncode == 0, (
        f"the gate did not pass the target that did all of the above:\n{_support.combined(proc)[-400:]}")
