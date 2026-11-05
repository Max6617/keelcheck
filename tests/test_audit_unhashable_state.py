"""An unhashable current state is 'could not run honestly' (exit 2), never a traceback (R3, R4)."""

from __future__ import annotations

import json

import _support


def test_audit_exits_2_when_the_state_cannot_be_hashed(scratch):
    _support.write(scratch / "tracked.txt", "hello\n")
    _support.write(scratch / "tools" / "gate.py", "print('ok')\n")
    rows = [("coverage", "tools/gate.py", _support.hash_file(scratch / "tools" / "gate.py"))]
    _support.write_charter(scratch, gates=rows)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, gates=rows, ratified=sha)
    _support.commit_all(scratch, "ratified")
    _support.keelcheck("gate", "run", str(scratch), "--timeout", "10")

    line = {"kind": "review", "result": "pass", "verdict": "clean", "manifest": "sha256:x", "command": ["x"]}
    with open(scratch / ".keel" / "runs.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(line) + "\n")
    _support.write(scratch / ".gitattributes", "*.txt ident\n")
    _support.write(scratch / "notes.txt", "$Id: abc $\n")
    _support.commit_all(scratch, "ident file")

    proc = _support.audit(scratch)

    assert proc.returncode == 2, _support.combined(proc)
    assert "Traceback" not in proc.stderr
    assert "NOT AUDITABLE" in proc.stdout
