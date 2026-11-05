"""`keelcheck hook install` exits 2, with no traceback, when the hook cannot be written."""

from __future__ import annotations

import _support

REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]


def test_install_into_an_unwritable_hooks_dir_exits_2(scratch):
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=[])
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=[], ratified=sha)
    _support.commit_all(scratch, "ratify")
    _support.write(scratch / "blocker", "not a directory\n")
    _support.git(scratch, "config", "core.hooksPath", "blocker/hooks")
    proc = _support.keelcheck("hook", "install", str(scratch))
    assert proc.returncode == 2, f"expected exit 2:\n{_support.combined(proc)}"
    assert "Traceback" not in proc.stderr
    assert "blocker" in proc.stderr
