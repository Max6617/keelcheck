"""The `kind: reviewer` row: a review by an unratified command is `[reviewer-unratified]` (R4, D15).

**Red at the tree before the row kind exists.** `reviewer` is not one of the kinds the parser knows, so
a charter carrying the row is reported as `[gate] kind 'reviewer' is not one of gate, prompt`, and no
`[reviewer-unratified]` appears anywhere. Gilbert's ruling, 2026-10-15: the row names the accepted
reviewer command, is parsed and compared like every other row, and a review line whose command is not
the ratified one does not satisfy a required review.

The row names a **repo-relative wrapper file** and is hashed with the same machinery as a gate row
(`normalize.content_hash` over git-normalized bytes), so nothing new is hashed. Written here rather than
in `test_review_cli.py` because Proctor's lane owns that file and this pair arrived after their fixtures
landed; the fixtures below are the same idiom, kept local so the two files cannot drift into each other.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import _support

REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]

#: A reviewer that answers cleanly about whatever it was handed. The count matters: the runner checks
#: `coverage.files_total` against the export it handed over, and the runner parks four of its own files
#: in that directory (prompt, frozen original, findings, manifest), so a stub that counts everything it
#: can see would be `inconsistent` for a reason that has nothing to do with this test.
CLEAN_STUB = (
    "import json, sys\n"
    "from pathlib import Path\n"
    "sys.stdin.read()\n"
    "RUNNER_FILES = {'REVIEW-PROMPT.md', 'FROZEN-ORIGINAL.md', 'MECHANICAL-FINDINGS.txt',\n"
    "                'KEELCHECK-MANIFEST.json'}\n"
    "n = sum(1 for p in Path('.').rglob('*') if p.is_file() and p.name not in RUNNER_FILES)\n"
    "print(json.dumps({'verdict': 'clean', 'items': [], 'unreviewed': [],\n"
    "                  'coverage': {'files_seen': n, 'files_total': n}}))\n"
)


def _wrapper(scratch, name: str) -> Path:
    """A reviewer wrapper *inside* the repository: a ratified row can only name a repo-relative file."""
    return _support.write(scratch / "tools" / name, CLEAN_STUB)


def _repo(scratch, *, reviewer_row: bool):
    """An auditable repo with a passing gate, a ratified prompt, and optionally the reviewer row."""
    _support.write(scratch / "tracked.txt", "hello\n")
    _support.write(scratch / "tools" / "gate.py", "print('ok')\n")
    _support.write(scratch / "review-prompt.md", "review the state against the original\n")
    _wrapper(scratch, "reviewer.py")
    _wrapper(scratch, "other.py")
    rows = [
        ("coverage", "tools/gate.py", _support.hash_file(scratch / "tools" / "gate.py")),
        ("review-prompt", "review-prompt.md",
         _support.hash_file(scratch / "review-prompt.md"), "prompt"),
    ]
    if reviewer_row:
        rows.append(("reviewer", "tools/reviewer.py",
                     _support.hash_file(scratch / "tools" / "reviewer.py"), "reviewer"))
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=rows, review_required=True)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=rows, ratified=sha,
                           review_required=True)
    _support.commit_all(scratch, "ratified")
    _support.keelcheck("gate", "run", str(scratch), "--timeout", "10")
    return scratch


def _command(scratch, wrapper: str) -> str:
    return f'"{sys.executable}" "{scratch / "tools" / wrapper}"'


def _review(scratch, wrapper: str):
    return _support.keelcheck("review", str(scratch), "--reviewer", _command(scratch, wrapper),
                              "--json", "--timeout", "20")


def test_a_review_by_an_unratified_command_does_not_satisfy_the_requirement(scratch):
    """The negative: the charter ratifies `tools/reviewer.py`, the review runs `tools/other.py`."""
    _repo(scratch, reviewer_row=True)
    review = _review(scratch, "other.py")
    assert review.returncode == 0, (
        f"precondition: the review itself runs and is recorded\n{_support.combined(review)}")

    proc = _support.audit(scratch)
    out = _support.combined(proc)
    flat = out.replace("\\", "/")  # Windows paths in the command, POSIX in the row it names

    assert proc.returncode != 0, (
        "a review run by a command the ratified table does not name was accepted as the review the "
        f"charter requires:\n{out}")
    assert "[reviewer-unratified]" in out, (
        f"the audit does not name the unratified reviewer command:\n{out}")
    assert "tools/other.py" in flat and "tools/reviewer.py" in flat, (
        f"the finding does not name what ran and what was ratified:\n{out}")


def test_a_review_by_the_ratified_command_is_fresh_and_the_audit_is_clean(scratch):
    """The control, so the pair discriminates: same fixture, the ratified wrapper."""
    _repo(scratch, reviewer_row=True)
    review = _review(scratch, "reviewer.py")
    assert review.returncode == 0, f"the review did not run\n{_support.combined(review)}"

    proc = _support.audit(scratch)
    out = _support.combined(proc)

    assert proc.returncode == 0, (
        f"the audit is not clean after a review by the ratified command:\n{out}")
    assert "REVIEW (clean context, R4): fresh" in out, out
    assert "[reviewer-unratified]" not in out, out

    lines = [json.loads(line) for line in
             (scratch / ".keel" / "runs.jsonl").read_text(encoding="utf-8").splitlines()
             if line.strip() and json.loads(line).get("kind") == "review"]
    recorded = " ".join(" ".join(str(p) for p in line["command"]) for line in lines).replace("\\", "/")
    assert lines and "tools/reviewer.py" in recorded, (
        f"the record does not name the command that ran: {lines}")


def test_with_no_reviewer_row_ratified_a_command_is_not_compared(scratch):
    """No row means no comparison: the check pins a command the charter names, it does not invent one."""
    _repo(scratch, reviewer_row=False)
    review = _review(scratch, "other.py")
    assert review.returncode == 0, _support.combined(review)

    proc = _support.audit(scratch)
    out = _support.combined(proc)

    assert "[reviewer-unratified]" not in out, (
        f"a repository that ratifies no reviewer row had its command judged anyway:\n{out}")
    assert "REVIEW (clean context, R4): fresh" in out, out
