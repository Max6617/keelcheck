"""`keel gate run` / `keel gate hash`, driven from outside (R2, D1-D3, D9, D10).

**Two reds against `78dfc0b`, four pins.** The reds are the two ways the enforced half can still
report health it did not measure:

1. a gate that **ran and failed** (or timed out) is recorded with the ratified hash, the audit's
   record check accepts it, and the audit then reports **exit 0, no divergences** — the mechanism the
   requirement rests on is red and the tool says clean;
2. `--record <directory>` works for `keel audit` (its `main` turns the directory into
   `runs.jsonl`) but not for `keel gate run`, which tries to append to the directory as a file and
   exits 2 **after executing the gate** — the run happened and was not recorded, so the next audit
   reports a bypass that did not happen.

The pins are the properties Mason built and stated, green on landing here and locked so they cannot
silently move: an audit run never counts as a gate run; a gate whose content no longer matches the
ratified hash is never executed; the recorded `hash` and `ratified` are the two different sides of
D10; and `keel gate hash` is git-normalized across line endings (D9).
"""

from __future__ import annotations

import json

import _support

REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]


def _gated_repo(scratch, body: str, *, gate: str = "coverage", path: str = "tools/gate.py"):
    """A ratified repository with one gate. Returns (script path, ratified hash)."""
    script = _support.write(scratch / path, body)
    digest = _support.hash_file(script)
    gates = [(gate, path, digest)]
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates, ratified=sha)
    _support.commit_all(scratch, "ratified")
    return script, digest


def _gate_lines(scratch) -> list[dict]:
    record = scratch / ".keel" / "runs.jsonl"
    return [json.loads(l) for l in record.read_text(encoding="utf-8").splitlines()
            if l.strip() and json.loads(l).get("kind") == "gate"]


# --- red: a failed or timed-out gate leaves the audit clean --------------------


def test_a_gate_that_ran_and_failed_does_not_leave_the_audit_clean(scratch):
    """The record proves the gate *executed*, not that it *passed*.

    `_has_run_record` accepts any `kind: gate` line whose `hash` equals the ratified hash, whatever
    its `result`. So a failing gate's record satisfies the audit, the report prints no divergence,
    and the exit code is 0 — a clean audit for a repository whose only mechanism is red.
    """
    _gated_repo(scratch, "import sys\nprint('bad')\nsys.exit(1)\n")

    run = _support.keel("gate", "run", str(scratch))
    assert run.returncode == 1, f"precondition: the gate run reports the failure\n{_support.combined(run)}"

    proc = _support.audit(scratch)
    out = _support.combined(proc)
    assert proc.returncode != 0, (
        "the audit is clean while the only recorded run of the ratified gate failed: the record "
        f"was accepted as proof the gate ran, not that it passed\n{out}"
    )
    assert "coverage" in out and "fail" in out.lower(), (
        f"the audit does not name the gate and its failed result:\n{out}"
    )


def test_a_gate_that_timed_out_does_not_leave_the_audit_clean(scratch):
    """The same hole by the other route: a timeout is recorded with the ratified hash too."""
    _gated_repo(scratch, "import time\ntime.sleep(30)\n")

    run = _support.keel("gate", "run", str(scratch), "--timeout", "1")
    assert run.returncode == 1, f"precondition: the gate run reports the timeout\n{_support.combined(run)}"

    proc = _support.audit(scratch)
    out = _support.combined(proc)
    assert proc.returncode != 0, (
        f"the audit is clean while the gate timed out and never produced a verdict\n{out}")


# --- red: --record as a directory ---------------------------------------------


def test_gate_run_accepts_a_record_directory_like_the_audit_does(scratch):
    """Mason's surface note: `--record PATH` takes a file, or a directory (then PATH/runs.jsonl).

    `keel audit` honours it; `keel gate run` does not, so the two commands disagree about the same
    argument — and the disagreement costs the run record, not just a message.
    """
    _gated_repo(scratch, "print('ok')\n")
    records = scratch / "records"
    records.mkdir()

    _support.audit(scratch, "--record", str(records))
    assert (records / "runs.jsonl").is_file(), "precondition: the audit accepts a record directory"

    run = _support.keel("gate", "run", str(scratch), "--record", str(records))
    assert run.returncode == 0, (
        f"`keel gate run --record <dir>` failed after executing the gate:\n{_support.combined(run)}")
    assert (records / "runs.jsonl").is_file()


# --- pins: properties stated and built ----------------------------------------


def test_an_audit_run_never_counts_as_a_gate_run(scratch):
    """The skipped-gate property. An audit writes a `kind: audit` line, never a `kind: gate` one, so
    a gate that was never executed stays divergence on every audit instead of healing after one."""
    _gated_repo(scratch, "print('ok')\n")

    for _ in range(2):
        _support.audit(scratch)
    skipped = _support.audit(scratch)
    assert skipped.returncode == 1, "a skipped gate healed itself"
    assert "[gate-record]" in _support.combined(skipped), "the missing record is not named"

    ran = _support.keel("gate", "run", str(scratch))
    assert ran.returncode == 0, f"the gate did not run clean\n{_support.combined(ran)}"
    after = _support.audit(scratch)
    assert after.returncode == 0, (
        f"the audit still reports a missing record after the gate ran:\n{_support.combined(after)}")


def test_gate_run_never_executes_a_gate_whose_hash_changed(scratch):
    """R2: a model may propose a gate, never weaken one. Running the unratified content would make
    the lock decorative. The record's `hash` and `ratified` are D10's two sides, and they differ."""
    script, digest = _gated_repo(scratch, "print('ok')\n")
    marker = scratch / "ran.marker"
    script.write_text(
        "import pathlib\n"
        f"pathlib.Path({str(marker)!r}).write_text('ran')\n", encoding="utf-8")

    run = _support.keel("gate", "run", str(scratch))

    assert run.returncode == 1, f"a changed gate was not refused\n{_support.combined(run)}"
    assert "locked" in _support.combined(run).lower(), "the refusal does not name the lock"
    assert not marker.exists(), "keel executed a gate whose content is not the ratified content"

    line = _gate_lines(scratch)[-1]
    assert line["result"] == "locked"
    assert line["ratified"] == digest
    assert line["hash"] != line["ratified"], "D10: the measured hash and the table's must be separate"


def test_gate_hash_is_git_normalized_across_line_endings(scratch):
    """D9: the hash a gate row records is over the bytes git stores, so a CRLF worktree — what a
    fresh Windows checkout writes — is the same gate."""
    script, digest = _gated_repo(scratch, "print('ok')\n")
    _support.git(scratch, "config", "core.autocrlf", "true")
    script.write_bytes(b"print('ok')\r\n")

    proc = _support.keel("gate", "hash", "tools/gate.py", "--repo", str(scratch))

    assert proc.returncode == 0, _support.combined(proc)
    assert proc.stdout.strip() == digest, (
        f"a CRLF worktree hashed {proc.stdout.strip()} instead of the recorded {digest}")
