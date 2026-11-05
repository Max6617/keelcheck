"""Appending to a record whose last line has no newline keeps that line intact (R2, D1)."""

from __future__ import annotations

from keelcheck import record

HEADER = b'{"kind": "header", "record": "keelcheck/runs", "version": 1}\n'
GATE = b'{"kind": "gate", "gate": "g", "result": "pass"}'


def test_append_after_an_unterminated_line_keeps_both_lines(scratch):
    path = scratch / "runs.jsonl"
    original = HEADER + GATE
    path.write_bytes(original)

    record.append(path, {"kind": "audit"})

    assert path.read_bytes().startswith(original)
    objects, problems = record.read(path)
    assert len(objects) == 3
    assert problems == []


def test_append_after_a_terminated_line_adds_exactly_one_line(scratch):
    path = scratch / "runs.jsonl"
    original = HEADER + GATE + b"\n"
    path.write_bytes(original)

    record.append(path, {"kind": "audit"})

    new = path.read_bytes()[len(original):]
    assert new == b'{"kind": "audit"}\n'
