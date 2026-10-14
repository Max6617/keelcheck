"""The adversarial set for the audit (R2, R3, R4), written against the contract Gilbert ruled in D3
and corrected in D8.

**Red against the landed code.** `keel audit` is not in `HEAD`; the set was written to land before
the implementation and turn green on Mason's fix commit. The contract is the CLI only — exit 0 clean
with at least one ratified gate, exit 1 divergence, exit 2 could not run honestly — plus
`.keel/runs.jsonl` and `.keel/review-context.json`. Never `keel/` internals.

A1–A3 were assumptions in `_support.py` when these tests were written; **D8 ruled them**, so the test
shapes here are the ruled ones (vacuity is a divergence, the report prints all four columns, the
pointer is named twice).
"""

from __future__ import annotations

import json
import re

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


def test_a_crlf_worktree_is_not_a_gate_hash_divergence(scratch):
    """D9, measured: ``core.autocrlf=true`` writes CRLF on a Windows checkout while the blob is LF.

    A hash over raw worktree bytes then reports a divergence that is not one — on every Windows
    checkout, in exactly the rule the tool exists for
    (``_artefacts/assay_parser_boundaries_b81c374.txt``). The declared hash here is over the LF
    content git stores; the same gate with a CRLF worktree is not a change.

    The exit code alone cannot carry this test: "hash changed" and "no run record" are both exit 1.
    The observable is the report — a real change names the gate *and* the hash (see the test above),
    so the CRLF run must contain no such naming.
    """
    script = _support.write(scratch / "tools" / "gate.py", "print('coverage')\n")
    digest = _support.hash_file(script)
    requirements = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]
    gates = [("coverage", "tools/gate.py", digest)]
    _support.write_charter(scratch, requirements=requirements, gates=gates)
    sha = _support.init_repo(scratch)
    _support.git(scratch, "config", "core.autocrlf", "true")
    _support.write_charter(scratch, requirements=requirements, gates=gates, ratified=sha)
    _support.commit_all(scratch, "ratified")

    _support.audit(scratch)  # settle whatever run-record policy applies, so only the hash is left
    assert _support.hash_file(script) == digest

    script.write_bytes(b"print('coverage')\r\n")  # what a fresh Windows checkout writes
    after = _support.audit(scratch)

    out = _support.combined(after).lower()
    assert after.returncode != 2, f"the audit could not run on a CRLF worktree:\n{_support.combined(after)}"
    assert "[gate]" not in out, (
        "a CRLF worktree was reported as a gate content-hash change; the hash must be over "
        f"git-normalized content (D9)\n{_support.combined(after)}"
    )


def test_editing_the_recommendation_moves_the_frozen_original(scratch):
    """D11 (F9): the anchor is the whole frozen section, heading included — the user's words *and*
    the recommendation they accepted, which is where the scope lives.

    Gilbert's red test, verbatim: in a copy of `keel/CHARTER.md`, edit the recommendation line, and
    require the audit to report the frozen original moved. Before the fix the parser collected only
    the first blockquote (82 bytes), so an edit to the recommendation left the anchor byte-identical
    and the audit reported *less* than the record defines — the vacuity class on the tool's own
    anchor (D11/F9).

    The observable is the report line, not the exit code: with zero ratified gates this repository is
    divergent anyway (D8 vacuity), so `[original]` is what distinguishes a moved anchor.
    """
    source = _support.KEEL_CHARTER.read_text(encoding="utf-8")
    assert "narrow to the join" in source, "precondition: the recommendation line is gone"

    # A copy, per D11: keel/CHARTER.md itself is never the test's scratch. The copy must point at
    # *this* repository's commit, so the other repo's SHA is replaced after the first commit.
    _support.write(scratch / "CHARTER.md", source)
    sha = _support.init_repo(scratch)
    text = (scratch / "CHARTER.md").read_text(encoding="utf-8")
    # D12: the canonical pointer is a plain `Ratified at: <sha>`; keel's own charter still writes the
    # sha in backticks, so match the label and take the sha wherever it sits, not one spelling.
    text, replaced = re.subn(r"(Ratified at:?\s*`?)([0-9a-f]{7,40})", rf"\g<1>{sha}", text, count=1)
    assert replaced == 1, "the copy has no `Ratified at:` line to repoint"
    assert sha in text, "the copy still names another repository's ratification commit"
    _support.write(scratch / "CHARTER.md", text)
    _support.commit_all(scratch, "name this repository's ratification commit")

    baseline = _support.audit(scratch)
    assert "[original]" not in _support.combined(baseline).lower(), (
        "the untouched copy already reports a frozen-original divergence, so this test could not "
        f"detect a moving anchor:\n{_support.combined(baseline)}"
    )

    # Move the anchor: one word, inside the recommendation, outside the user's own words.
    moved_text = (scratch / "CHARTER.md").read_text(encoding="utf-8")
    assert "narrow to the join and build it" in moved_text
    _support.write(
        scratch / "CHARTER.md",
        moved_text.replace("narrow to the join and build it", "narrow to the join and rebuild it", 1),
    )

    moved = _support.audit(scratch)

    assert moved.returncode == 1, f"exit {moved.returncode}, wanted 1\n{_support.combined(moved)}"
    assert "[original]" in _support.combined(moved).lower(), (
        "editing the recommendation line did not move the frozen original: the anchor covers less "
        f"than the record defines (D11/F9)\n{_support.combined(moved)}"
    )


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


def test_a_charter_with_zero_ratified_gates_is_a_named_finding_not_a_clean_run(scratch):
    """D8 corrected D3 here: an audit that finds zero ratified gates verified nothing.

    D3 first said a complete charter with no gates audits clean. Proctor then measured rentguard —
    0 gate hashes — and D8 ruled that succeeded nothing must say so as a named divergence and must
    not exit 0. Exit 0 on this input would be the audit reporting health it never measured.

    The charter must still name its ratification commit (A2): without that line it is *unratifiable*
    and exits 2, which says "I could not run", not "I ran and found nothing".
    """
    requirements = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]
    _support.write_charter(scratch, requirements=requirements)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=requirements, ratified=sha)
    _support.commit_all(scratch, "ratified")

    proc = _support.audit(scratch)

    assert proc.returncode == 1, (
        f"a vacuous audit exited {proc.returncode}; zero ratified gates is a divergence, not clean\n"
        f"{_support.combined(proc)}"
    )
    assert "[vacuity]" in _support.combined(proc).lower(), "the vacuity finding is not named"


def test_wishes_are_reported_but_do_not_change_the_exit_code(scratch):
    """D3: wishes may exist and are reported; they do not change the exit code.

    D8 changed the baseline twice: a charter with no ratification pointer cannot run honestly (exit
    2, A2), and one that runs with zero ratified gates is already divergent (exit 1, vacuity). So the
    wish must add neither the fatal code nor silence — it is named in the report.
    """
    requirements = [("R9", "nothing is published without the user's word", "—", "—", "**wish**")]
    _support.write_charter(scratch, requirements=requirements)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=requirements, ratified=sha)
    _support.commit_all(scratch, "ratified")

    proc = _support.audit(scratch)

    assert proc.returncode != 2, f"a wish made the audit fatal\n{_support.combined(proc)}"
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
