"""The adversarial set for the audit (R2, R3, R4), written against the contract Gilbert ruled in D3.

**Red first.** Nothing here exists yet: at `489f47d` `keel audit` is an unknown command, so every
test below fails. That is the point — these are the tests that would catch a charter tool lying about
itself, and they land before the code that has to earn them.

The contract (D3) is the CLI only — exit 0 no divergence, exit 1 divergence, exit 2 could not run
honestly — plus `.keel/runs.jsonl` and `.keel/review-context.json`. Never `keel/` internals.

**Three things D1/D3 leave open are assumed in `_support.ASSUMPTIONS`, not here**: the gate table
shape (A1), where the ratification commit is named (A2), and the record paths (A3). When Gilbert
rules them, `_support.py` changes and these tests do not.
"""

from __future__ import annotations

import json

import _support


# --- the guard: no test may pass for the wrong reason -------------------------


def test_the_audit_command_exists_and_help_succeeds():
    """Without this, every "exit 1" test below would pass while `audit` is an unknown command.
    A missing command is not a passing audit."""
    proc = _support.audit("--help")
    assert proc.returncode == 0, f"`keel audit --help` failed: {_support.combined(proc)[-400:]}"
    assert "audit" in _support.combined(proc).lower()


# --- exit 1: divergence -------------------------------------------------------


def test_a_charter_missing_a_required_section_is_divergence(scratch):
    """R1's format names six sections. A charter missing one is divergence, not a warning."""
    _support.write_charter(
        scratch,
        requirements=[("R1", "the parser exists", "code: the charter parser", "—", "**met**")],
        omit_sections=("Permissions",),
    )
    _support.init_repo(scratch)

    proc = _support.audit(scratch)

    assert proc.returncode == 1, f"exit {proc.returncode}, wanted 1\n{_support.combined(proc)}"
    assert "permissions" in _support.combined(proc).lower(), "the divergence is not named"


def test_a_gate_file_changed_after_ratification_is_divergence_and_is_named(scratch):
    """Property: a gate's content hash cannot be edited without the audit failing.

    Assume A1/A2: the charter names the gate and the hash, and the reference hash is read from the
    ratification commit. The script is changed after ratification; the audit must fail and name it.
    """
    script = _support.write(scratch / "tools" / "coverage.py", "print('coverage')\n")
    digest = _support.hash_file(script)
    _support.write_charter(
        scratch,
        requirements=[("R1", "the parser exists", "code: the charter parser", "—", "**met**")],
        gates=[("coverage", "tools/coverage.py", digest)],
    )
    sha = _support.init_repo(scratch)
    _support.write_charter(
        scratch,
        requirements=[("R1", "the parser exists", "code: the charter parser", "—", "**met**")],
        gates=[("coverage", "tools/coverage.py", digest)],
        ratified=sha,
    )
    _support.commit_all(scratch, "name the ratification commit")

    _support.write(script, "print('coverage')\nprint('loosened')\n")

    proc = _support.audit(scratch)

    assert proc.returncode == 1, f"exit {proc.returncode}, wanted 1\n{_support.combined(proc)}"
    out = _support.combined(proc)
    assert "coverage" in out, f"the failing gate is not named:\n{out}"
    assert "hash" in out.lower(), f"the failure does not mention the hash:\n{out}"


def test_rewriting_the_hash_in_the_working_tree_charter_does_not_silence_it(scratch):
    """The attack D1 exists for: edit the gate script *and* paste the new hash into the working-tree
    charter. The reference hash comes from the ratification commit, so the audit must still fail."""
    script = _support.write(scratch / "tools" / "coverage.py", "print('coverage')\n")
    old = _support.hash_file(script)
    requirements = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]
    _support.write_charter(scratch, requirements=requirements,
                           gates=[("coverage", "tools/coverage.py", old)])
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=requirements,
                           gates=[("coverage", "tools/coverage.py", old)], ratified=sha)
    _support.commit_all(scratch, "ratified")

    _support.write(script, "print('coverage')\nprint('loosened')\n")
    new = _support.hash_file(script)
    assert new != old
    text = (scratch / "CHARTER.md").read_text(encoding="utf-8")
    _support.write(scratch / "CHARTER.md", text.replace(old, new))

    proc = _support.audit(scratch)

    assert proc.returncode == 1, (
        "rewriting the hash in the working-tree charter silenced the audit\n"
        f"{_support.combined(proc)}"
    )
    assert "coverage" in _support.combined(proc)


def test_a_named_gate_with_no_run_record_is_divergence_not_a_pass(scratch):
    """Property: an audit must not report success for a gate that never ran. A local hook is a
    detector, not a lock (D2), so a bypass is a *missing* record and must be divergence."""
    script = _support.write(scratch / "tools" / "coverage.py", "print('coverage')\n")
    digest = _support.hash_file(script)
    requirements = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]
    _support.write_charter(scratch, requirements=requirements,
                           gates=[("coverage", "tools/coverage.py", digest)])
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=requirements,
                           gates=[("coverage", "tools/coverage.py", digest)], ratified=sha)
    _support.commit_all(scratch, "ratified")

    assert not (scratch / ".keel" / "runs.jsonl").exists(), "precondition: no run record exists"
    proc = _support.audit(scratch)

    assert proc.returncode == 1, (
        f"a gate with no run record passed the audit (exit {proc.returncode})\n"
        f"{_support.combined(proc)}"
    )
    assert "coverage" in _support.combined(proc), "the gate with no run record is not named"


def test_the_run_record_is_append_only(scratch):
    """Two runs leave two lines; the first is never rewritten. This is what makes a missing record
    evidence rather than an absence."""
    _support.write_charter(
        scratch,
        requirements=[("R1", "the parser exists", "code: the charter parser", "—", "**met**")],
    )
    _support.init_repo(scratch)

    _support.audit(scratch)
    record = scratch / ".keel" / "runs.jsonl"
    assert record.exists(), "the audit wrote no run record"
    first = record.read_text(encoding="utf-8")
    _support.audit(scratch)
    second = record.read_text(encoding="utf-8")

    assert second.startswith(first), "the run record was rewritten, not appended"
    lines = [line for line in second.splitlines() if line.strip()]
    assert len(lines) >= 2, f"the second run added no line: {lines}"
    for line in lines:
        json.loads(line)   # one JSON object per line


# --- exit 0: wishes are reported, not fatal -----------------------------------


def test_a_complete_charter_with_no_gates_audits_clean(scratch):
    _support.write_charter(
        scratch,
        requirements=[("R1", "the parser exists", "code: the charter parser", "—", "**met**")],
    )
    _support.init_repo(scratch)

    proc = _support.audit(scratch)

    assert proc.returncode == 0, f"exit {proc.returncode}\n{_support.combined(proc)}"


def test_wishes_are_reported_but_do_not_change_the_exit_code(scratch):
    """D3: wishes may exist and are reported; they do not change the exit code."""
    _support.write_charter(
        scratch,
        requirements=[("R9", "nothing is published without the user's word", "—", "—", "**wish**")],
    )
    _support.init_repo(scratch)

    proc = _support.audit(scratch)

    assert proc.returncode == 0, f"a wish changed the exit code\n{_support.combined(proc)}"
    assert "R9" in _support.combined(proc), "the wish is not reported"


def test_fail_on_wish_makes_wishes_fatal_when_asked(scratch):
    _support.write_charter(
        scratch,
        requirements=[("R9", "nothing is published without the user's word", "—", "—", "**wish**")],
    )
    _support.init_repo(scratch)

    proc = _support.audit(scratch, "--fail-on-wish")

    assert proc.returncode == 2, f"exit {proc.returncode}, wanted 2\n{_support.combined(proc)}"


# --- exit 2: could not run honestly -------------------------------------------


def test_a_file_that_is_not_a_charter_cannot_run_honestly(scratch):
    """A requirements heading with no table is not a wish, it is not a charter. Reporting "pass"
    for something that could not be read is the worst outcome."""
    _support.write(scratch / "CHARTER.md", "# not a charter\n\n## Requirements\n\nnothing here\n")
    _support.init_repo(scratch)

    proc = _support.audit(scratch)

    assert proc.returncode == 2, f"exit {proc.returncode}, wanted 2\n{_support.combined(proc)}"


# --- property 4: clean context ------------------------------------------------


def test_the_review_context_is_written_without_the_history(scratch):
    """R4 as now written: the runner writes the reviewer's inputs to `.keel/review-context.json`.

    Property: what is handed to the fresh reviewer is the frozen original and the current state —
    never the history that produced it. A runner that forwards the git log or a previous audit
    report is defective, not untidy, because the clean context *is* the mechanism.
    """
    sentinel = "HISTORY-SENTINEL-must-not-reach-the-reviewer"
    _support.write_charter(
        scratch,
        requirements=[("R1", "the parser exists", "code: the charter parser", "—", "**met**")],
    )
    _support.write(scratch / "AUDIT-2026-10-01.md", f"a previous run mentioned {sentinel}\n")
    _support.init_repo(scratch)
    _support.git(scratch, "commit", "-q", "--allow-empty", "-m", sentinel)

    _support.audit(scratch)

    context = scratch / ".keel" / "review-context.json"
    assert context.exists(), "the runner did not record what it would hand the reviewer"
    text = context.read_text(encoding="utf-8")
    assert _support.FROZEN_SENTINEL in text, "the frozen original is not in the reviewer's input"
    assert sentinel not in text, "history reached the reviewer's input"
