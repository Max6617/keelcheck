"""The residual of `_check_run_record`: a later failure masked by an earlier pass (D2, D8).

The existing gate tests cover the all-red record — every recorded run failed, timed out or errored —
and `_check_run_record` now refuses to call that clean. It does so with:

    if any(run.get("result") == "pass" for run in runs):
        return

`any`, not `last`. So a gate that **passed once and fails now**, with the ratified hash unchanged,
is reported clean: the audit reads the history and ignores the present. A passing run is evidence
about the moment it ran, not about the state the audit is looking at.

Red against the working tree. The fixture keeps the gate's own bytes constant — the hash the charter
ratifies — and moves the thing the gate measures, which is exactly how a real gate goes red without
its own content changing (rentguard's suite: unchanged `tools/coverage.py`, a failing suite).
"""

from __future__ import annotations

import json

import _support

REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]

#: Constant bytes; the charter ratifies this hash and it never changes in this test.
GATE_BODY = (
    "import pathlib, sys\n"
    "ok = pathlib.Path('state.txt').read_text(encoding='utf-8').strip() == 'ok'\n"
    "print('gate ok' if ok else 'gate bad')\n"
    "sys.exit(0 if ok else 1)\n"
)


def _repo_with_state_gate(scratch):
    """A ratified repository whose gate passes or fails on `state.txt`, not on its own bytes."""
    script = _support.write(scratch / "tools" / "gate.py", GATE_BODY)
    _support.write(scratch / "state.txt", "ok\n")
    digest = _support.hash_file(script)
    gates = [("coverage", "tools/gate.py", digest)]
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates, ratified=sha)
    _support.commit_all(scratch, "ratified")
    return script, digest


def test_a_later_failing_run_is_not_masked_by_an_earlier_pass(scratch):
    """Sequence: the gate passes, the audit is clean, the measured state goes bad, the gate fails.
    Effect: the audit must report the failure. The pass from before the change is not a verdict on
    the state the audit is looking at."""
    script, digest = _repo_with_state_gate(scratch)

    first = _support.keelcheck("gate", "run", str(scratch))
    assert first.returncode == 0, (
        f"precondition: the gate passes on state.txt=ok\n{_support.combined(first)}")
    clean = _support.audit(scratch)
    assert clean.returncode == 0, (
        f"precondition: the audit is clean after a passing run\n{_support.combined(clean)}")

    # The gate's own bytes are untouched; the state it measures is not.
    _support.write(scratch / "state.txt", "bad\n")
    _support.commit_all(scratch, "the measured state goes bad")
    assert _support.hash_file(script) == digest, "the gate's ratified hash must not move"

    second = _support.keelcheck("gate", "run", str(scratch))
    assert second.returncode == 1, (
        f"precondition: the second run fails\n{_support.combined(second)}")

    record = [json.loads(line) for line in
              (scratch / ".keel" / "runs.jsonl").read_text(encoding="utf-8").splitlines()
              if line.strip() and json.loads(line).get("kind") == "gate"]
    assert [r["result"] for r in record] == ["pass", "fail"], (
        f"precondition: the record holds a pass then a fail\n{record}")

    proc = _support.audit(scratch)
    out = _support.combined(proc)

    assert proc.returncode != 0, (
        "the audit is clean while the most recent recorded run of the ratified gate failed: "
        "`any(pass)` reads the history and ignores the present\n"
        f"{out}"
    )
    assert "[gate-record]" in out and "fail" in out.lower(), (
        f"the audit does not name the gate and its latest result:\n{out}")
