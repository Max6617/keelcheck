"""A review counts as ratified only when its command runs the ratified wrapper file (R4)."""

from __future__ import annotations

import sys

import _support
import test_reviewer_row

REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]


def test_a_copy_of_the_wrapper_at_another_path_is_unratified(scratch):
    test_reviewer_row._repo(scratch, reviewer_row=True)
    copy = _support.write(scratch / "vendor" / "tools" / "reviewer.py", test_reviewer_row.CLEAN_STUB)
    run = _support.keelcheck(
        "review", str(scratch), "--reviewer", f'"{sys.executable}" "{copy}"', "--json", "--timeout", "20"
    )
    assert run.returncode == 0, _support.combined(run)
    audit = _support.audit(scratch)
    assert audit.returncode != 0, _support.combined(audit)
    assert "[reviewer-unratified]" in _support.combined(audit)
