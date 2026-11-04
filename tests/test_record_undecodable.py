"""A run record line that is not UTF-8 is a `[record]` divergence, not a traceback (R2)."""

from __future__ import annotations

import json

import _support


def test_an_undecodable_record_line_is_a_record_divergence(scratch):
    requirements = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]
    _support.write_charter(scratch, requirements=requirements)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=requirements, ratified=sha)
    _support.commit_all(scratch, "ratified")
    record = scratch / "elsewhere" / "runs.jsonl"
    record.parent.mkdir()
    header = {"kind": "header", "record": "keelcheck/runs", "version": 1}
    record.write_bytes(json.dumps(header).encode() + b"\n" + b"\xff\n")

    proc = _support.audit(scratch, "--record", str(record))

    assert proc.returncode == 1, f"exit {proc.returncode}, wanted 1\n{_support.combined(proc)}"
    assert "Traceback" not in proc.stderr
    assert "[record]" in proc.stdout
