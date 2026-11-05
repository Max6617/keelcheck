"""A ratified row written `./tools/gate.py` locks that gate like `tools/gate.py` does (R5)."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

import _support
import test_adapter

REQUIREMENTS = test_adapter.REQUIREMENTS


def _dot_slash_repo(scratch):
    _support.write(scratch / "tools" / "gate.py", "print('ok')\n")
    gates = [("coverage", "./tools/gate.py", _support.hash_file(scratch / "tools" / "gate.py"))]
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates, ratified=sha)
    _support.commit_all(scratch, "ratified")
    return scratch


@pytest.mark.parametrize("kind", ["write", "bash"])
def test_a_dot_slash_row_is_locked(scratch, kind):
    repo = _dot_slash_repo(scratch)
    if kind == "write":
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": (repo / "tools" / "gate.py").as_posix(), "content": "x\n"},
        }
    else:
        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "rm tools/gate.py"},
        }
    done = subprocess.run(
        [sys.executable, "-m", "keelcheck", "adapter", "claude-code", "--repo", str(repo)],
        input=json.dumps(event), capture_output=True, text=True, encoding="utf-8",
        cwd=str(repo), timeout=120,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": test_adapter._pythonpath()},
    )
    assert done.returncode == 2, f"a ./ row was not locked:\n{done.stdout}\n{done.stderr}"
    assert json.loads(done.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
