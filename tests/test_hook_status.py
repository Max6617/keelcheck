"""`keelcheck hook status` reports what is installed, and exits 2 when there is no repository to ask."""

from __future__ import annotations

import json

import _support

REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]


def test_status_outside_a_repository_exits_2(scratch):
    proc = _support.keelcheck("hook", "status", str(scratch))
    assert proc.returncode == 2, f"expected exit 2:\n{_support.combined(proc)}"
    assert "not a git repository" in proc.stderr


def test_status_reports_not_installed_then_installed(scratch):
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=[])
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=[], ratified=sha)
    _support.commit_all(scratch, "ratified")

    before = _support.keelcheck("hook", "status", "--json", str(scratch))
    assert before.returncode == 0, _support.combined(before)
    assert json.loads(before.stdout)["hooks"]["pre-commit"]["state"] == "not-installed"

    installed = _support.keelcheck("hook", "install", str(scratch))
    assert installed.returncode == 0, _support.combined(installed)

    after = _support.keelcheck("hook", "status", "--json", str(scratch))
    assert after.returncode == 0, _support.combined(after)
    assert json.loads(after.stdout)["hooks"]["pre-commit"]["state"] == "installed"
