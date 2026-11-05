"""`keelcheck hook install` exits 2 outside a git repository and creates nothing."""

from __future__ import annotations

import _support

REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]


def test_install_outside_a_repository_exits_2_and_creates_nothing(scratch):
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=[], ratified="1234567abc")
    proc = _support.keelcheck(
        "hook", "install", str(scratch),
        env_extra={"GIT_CEILING_DIRECTORIES": str(scratch.parent)},
    )
    assert proc.returncode == 2, f"expected exit 2:\n{_support.combined(proc)}"
    assert "not a git repository" in proc.stderr
    assert not (scratch / ".git").exists()
