"""The append-only run record and the reviewer's input file (D3, D8 A2/A3).

Two files, and both exist so that a bypass leaves a mark rather than an absence:

``runs.jsonl``
    Append-only, one JSON object per line, tracked by git so that a deleted line is a diff
    rather than a secret. Its **first line is the header** naming the ratified commit (D8
    A2): the pointer is written twice -- in the charter's living state and here -- and
    nowhere is it trusted alone. Then one ``audit`` object per audit run (written even when
    the run fails, A3) and one ``gate`` object per gate execution, carrying the gate name,
    its path, its hash at that moment, the commit and the exit status (D3).

``review-context.json``
    What the runner would hand a clean-context reviewer (R4). Written by the audit so that
    the claim "the reviewer saw no history" is at least a recorded claim (W2 admits it is
    not proved).

Nothing here rewrites a line. A record that has been rotated or deleted is a human
decision, and the audit reports the gap instead of repairing it.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

__all__ = [
    "HEADER_KIND",
    "RECORD_NAME",
    "REVIEW_CONTEXT_NAME",
    "append",
    "ensure_header",
    "first_header",
    "last_of_kind",
    "now",
    "read",
    "record_paths",
    "write_json",
]

RECORD_NAME = "runs.jsonl"
REVIEW_CONTEXT_NAME = "review-context.json"
DEFAULT_DIR = ".keel"
HEADER_KIND = "header"
RECORD_ID = "keel/runs"
VERSION = 1


def now() -> str:
    """UTC, second precision: records are compared, not parsed for prose."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def record_paths(repo: Path | str, record: Path | str | None = None) -> tuple[Path, Path]:
    """(runs.jsonl, review-context.json). ``--record`` moves both (D4 keeps rentguard read-only).

    ``--record`` accepts a file or a directory, and both commands read it the same way: a directory
    means ``<dir>/runs.jsonl`` beside ``<dir>/review-context.json``. A path with no suffix that does
    not exist yet is a directory too -- a mistyped record path must not silently become a file whose
    parent (possibly the whole workspace) is then excluded from the reviewer's export. Two commands
    disagreeing about one argument cost a gate run its record once, so the rule lives here and
    nowhere else.
    """
    if record is None:
        base = Path(repo) / DEFAULT_DIR
        return base / RECORD_NAME, base / REVIEW_CONTEXT_NAME
    target = Path(record)
    if target.is_dir() or (not target.exists() and not target.suffix):
        return target / RECORD_NAME, target / REVIEW_CONTEXT_NAME
    return target, target.with_name(REVIEW_CONTEXT_NAME)


def read(path: Path | str) -> tuple[list[dict], list[str]]:
    """The record's objects, plus a problem string for every line that is not one."""
    path = Path(path)
    if not path.is_file():
        return [], []
    objects: list[dict] = []
    problems: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            problems.append(f"{path}:{number} is not JSON ({exc.msg})")
            continue
        if not isinstance(value, dict):
            problems.append(f"{path}:{number} is not a JSON object")
            continue
        objects.append(value)
    return objects, problems


def headers(objects: list[dict]) -> list[dict]:
    return [o for o in objects if o.get("kind") == HEADER_KIND]


def first_header(objects: list[dict]) -> dict | None:
    for obj in objects:
        if obj.get("kind") == HEADER_KIND:
            return obj
    return None


def last_of_kind(objects: list[dict], kind: str) -> dict | None:
    """The newest entry of a kind. Used for `[anchor-moved]` and `[gate-table]` (D10, D12)."""
    for obj in reversed(objects):
        if obj.get("kind") == kind:
            return obj
    return None


def ensure_header(path: Path | str, *, when: str | None = None) -> bool:
    """Write the header line if the record is new. Returns True when it was written.

    D12: the header carries **no anchor**. The anchor value lives in exactly one place -- the
    charter's ``Ratified at:`` line -- and each run entry records the anchor *it used*, which
    is what the next run compares against for ``[anchor-moved]``. A second copy in the header
    would go stale forever after a legitimate re-ratification and fail the audit for a right
    reason. The header now only declares the record's format and version.
    """
    path = Path(path)
    if path.exists() and path.stat().st_size > 0:
        return False
    _write_line(
        path,
        {"kind": HEADER_KIND, "record": RECORD_ID, "version": VERSION, "at": when or now()},
    )
    return True


def append(path: Path | str, obj: dict) -> None:
    """Append one JSON object as one line."""
    _write_line(Path(path), obj)


def write_json(path: Path | str, obj: dict) -> None:
    """Write the reviewer's input file (replaced each run: it describes the current state)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, indent=2, ensure_ascii=False)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text + "\n")


def _write_line(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")
        handle.flush()
        os.fsync(handle.fileno())
