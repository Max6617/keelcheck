"""D12's pin for the adapter line: **an adapter line between two audits produces no `[anchor-moved]`.**

The design (in its own words *"an adapter line between two audits produces no
`[anchor-moved]`"*, landing with the adapter rather than before it) puts one best-effort `kind: adapter`
line into the existing record on a deny. That line carries **no anchor** — it is what
`keelcheck.adapter._record_refusal` appends, and this file reads the line the adapter actually wrote
rather than trusting that. So a check that compares a run against *the entry before it* would see
`None -> <sha>` and report the anchor as moved on every deny, which is the false alarm the design's
line exists to avoid.

**The two citations above carry no line numbers, deliberately.** An independent reviewer measured three drifts of this
class in one session — the design note, `audit.py`, and this file's own `adapter.py`
range, which was `:234-243` when this was written and is `_record_refusal` at `:328` an hour later, in a
file that is still being edited. A citation by symbol or by quoted words cannot go stale; where a range
is genuinely the only way to point at something, measure it in the commit that writes it.

**Pinned as behaviour, not as a code path.** Nothing here names `_anchor_moved` or its selection rule,
and nothing imports `keelcheck/`: the fixture writes the line through the real CLI (`keelcheck adapter
claude-code`), runs two audits through the real CLI, and asserts on what the report says. If the
selection rule were replaced tomorrow by something that reads the same behaviour out of the record,
both tests would still hold — and if it regressed to "the previous entry", both would fail.

Two tests, because an absence on its own is not evidence: the second moves the anchor for real with an
adapter line in between, and requires the report to fire anyway. Without it, "no `[anchor-moved]`"
could just as well mean the check never fires here at all. An independent verifier's file; the author's is
`tests/test_adapter.py`, and the two do not share a fixture on purpose.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import _support

REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]
ANCHOR_LINE = re.compile(r"^Ratified at:\s*(\S+)\s*$", re.MULTILINE)


def _auditable(scratch):
    """A repository whose audit is clean: a ratified charter, one passing gate, its run recorded.

    Clean is what makes the pin readable -- if the audit fires for some other reason, "no
    `[anchor-moved]`" would be a sentence about a report nobody can interpret.
    """
    _support.write(scratch / "tracked.txt", "hello\n")
    _support.write(scratch / "tools" / "gate.py", "print('ok')\n")
    gates = [("coverage", "tools/gate.py", _support.hash_file(scratch / "tools" / "gate.py"))]
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates, ratified=sha)
    _support.commit_all(scratch, "ratified")
    _support.keelcheck("gate", "run", str(scratch), "--timeout", "10")
    return scratch, gates, sha


def _record(repo) -> list[dict]:
    path = repo / ".keel" / "runs.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _anchor(repo) -> str:
    found = ANCHOR_LINE.search((repo / "CHARTER.md").read_text(encoding="utf-8"))
    assert found, "the fixture charter names no anchor"
    return found.group(1)


def _adapter_deny(repo):
    """One real adapter event, denied: this is the line the design puts in the record.

    The payload is not an event, so the adapter fails **closed** and denies -- which is the cheapest
    deterministic deny, and it exercises the same write path as a locked-path deny. The test asserts
    the exit code and the line, so a silently-allowing adapter cannot pass as a denying one.
    """
    return subprocess.run(
        [sys.executable, "-m", "keelcheck", "adapter", "claude-code", "--repo", str(repo)],
        cwd=str(_support.REPO), input="this is not a harness event\n", capture_output=True,
        text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=120,
    )


def _the_adapter_line(repo) -> dict:
    """The adapter's own line, with the fixture's precondition checked rather than assumed.

    The condition that makes the pin discriminating: the line carries no anchor, so a check that
    selected it would see `None -> <sha>` and fire. If that ever changes, this fails loudly instead of
    letting the two audits below pass for a reason that has nothing to do with the design.
    """
    adapter = [line for line in _record(repo) if line.get("kind") == "adapter"]
    assert adapter, "the adapter appended no line, so there is nothing between the two audits"
    line = adapter[-1]
    assert line.get("ratified") != _anchor(repo), (
        "the adapter's line carries the current anchor, so the audit could select it and still not "
        f"fire -- the fixture would stop discriminating: {line}")
    return line


def _between_the_audits(repo) -> None:
    """Called after both audits: the adapter line must sit *between* them, or this is another test."""
    kinds = [line.get("kind") for line in _record(repo)]
    audit_at = [i for i, kind in enumerate(kinds) if kind == "audit"]
    adapter_at = [i for i, kind in enumerate(kinds) if kind == "adapter"]
    assert len(audit_at) == 2, f"the fixture did not leave two audit lines to compare: {kinds}"
    assert adapter_at and audit_at[0] < adapter_at[-1] < audit_at[1], (
        f"the adapter line is not between the two audits, so the pin is not the pin: {kinds}")


def test_an_adapter_line_between_two_audits_causes_no_anchor_moved(scratch):
    repo, _, sha = _auditable(scratch)

    first = _support.audit(repo)
    assert first.returncode == 0, (
        f"the fixture is not clean before the adapter line, so this test would measure the wrong "
        f"thing:\n{_support.combined(first)[-600:]}")

    denied = _adapter_deny(repo)
    assert denied.returncode == 2, (
        f"the adapter did not deny, so it wrote no line: exit {denied.returncode}\n"
        f"{_support.combined(denied)[-400:]}")
    _the_adapter_line(repo)   # asserts the kind and the missing anchor, before the second audit

    second = _support.audit(repo)
    out = _support.combined(second)
    _between_the_audits(repo)

    assert _anchor(repo) == sha, "the fixture's anchor moved, so this is not the pin's scenario"
    assert second.returncode == 0, (
        "an adapter line between two audits made the second audit report a divergence:\n"
        f"{out[-600:]}")
    assert "anchor-moved" not in out, (
        "an adapter line -- which carries no anchor -- was read as the previous run, so the audit "
        f"reports the anchor as moved on an ordinary deny (D12's false alarm):\n{out[-600:]}")


def test_an_adapter_line_does_not_hide_a_real_anchor_move(scratch):
    """The control, and the reason the test above is evidence rather than an empty assertion: with
    the same fixture and the same adapter line in between, a *real* move of the anchor must still be
    reported, against the previous **audit** and not against the adapter."""
    repo, gates, first_sha = _auditable(scratch)
    assert _support.audit(repo).returncode == 0
    assert _adapter_deny(repo).returncode == 2
    _the_adapter_line(repo)

    moved_to = _support.commit_all(repo, "a commit for the anchor to name")
    _support.write_charter(repo, requirements=REQUIREMENTS, gates=gates, ratified=moved_to)
    _support.commit_all(repo, "the charter names the new anchor")

    second = _support.audit(repo)
    out = _support.combined(second)
    _between_the_audits(repo)

    assert second.returncode == 1, (
        f"a moved anchor produced exit {second.returncode}, not 1:\n{out[-600:]}")
    assert "anchor-moved" in out, (
        f"the real move was not reported at all:\n{out[-600:]}")
    assert first_sha in out and moved_to in out, (
        "the report does not name both anchors, so it is not the move being reported:\n"
        f"{out[-600:]}")
