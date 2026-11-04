"""An adapter that cannot read the charter denies: it cannot tell what is locked (R5, fail closed)."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import _support
import test_adapter

REPO = _support.REPO


def test_an_unreadable_charter_denies_a_write_to_a_ratified_gate(scratch):
    repo = test_adapter._repo(scratch)
    (repo / "CHARTER.md").write_text("garbage\n", encoding="utf-8")
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Write",
        "tool_input": {"file_path": (repo / "tools" / "gate.py").as_posix(), "content": "x\n"},
    }
    done = subprocess.run(
        [sys.executable, "-m", "keelcheck", "adapter", "claude-code", "--repo", str(repo)],
        input=json.dumps(event), capture_output=True, text=True, encoding="utf-8",
        cwd=str(repo), timeout=120,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": test_adapter._pythonpath()},
    )
    assert done.returncode == 2, f"an unreadable charter allowed a write:\n{done.stdout}\n{done.stderr}"
    hook = json.loads(done.stdout)["hookSpecificOutput"]
    assert hook["permissionDecision"] == "deny"
    assert "charter cannot be read" in hook["permissionDecisionReason"]
