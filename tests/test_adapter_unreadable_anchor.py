"""An adapter that cannot read the charter at the ratified commit denies: the locked rows come from there."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import _support
import test_adapter


def test_an_unreadable_anchor_denies_a_write_to_a_ratified_gate(scratch):
    repo = test_adapter._repo(scratch)
    gates = [
        ("coverage", "tools/gate.py", _support.hash_file(repo / "tools" / "gate.py")),
        ("review-prompt", "review-prompt.md", _support.hash_file(repo / "review-prompt.md"), "prompt"),
    ]
    _support.write_charter(repo, requirements=test_adapter.REQUIREMENTS, gates=gates,
                           ratified="0123456789abcdef0123456789abcdef01234567")
    _support.commit_all(repo, "anchor not in the repo")
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
    assert done.returncode == 2, f"an unreadable anchor allowed a write:\n{done.stdout}\n{done.stderr}"
    hook = json.loads(done.stdout)["hookSpecificOutput"]
    assert hook["permissionDecision"] == "deny"
    assert "ratified commit" in hook["permissionDecisionReason"]
