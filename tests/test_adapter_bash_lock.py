"""The Bash lock, pinned: a shell command naming a locked path is denied (an independent verifier,
2026-10-16).

**This file began as a falsification and is now a pin, and the history is here because the two are not
interchangeable.** `tests/test_adapter.py` is the author's, and its deny cases were `Write` and `Edit`;
the only Bash payload in the suite was an *allow* case, while the installer's matcher for `PreToolUse`
carries `Write|Edit|MultiEdit|NotebookEdit|Bash` and the comment above the containment loop in
`adapter.decide` claims "a locked path inside a shell command is found by containment" -- cited by
symbol and quote rather than by line, because both moved while this file was being written (an
independent reviewer measured that class of drift three times in one session).

Measured then, on a repo whose charter ratifies `tools/gate.py`:

    rm -f tools/gate.py             -> exit 0, no output
    echo 'weakened' > tools/gate.py -> exit 0, no output

Cause: `_as_relative` joined a non-absolute target to the repo, so the *whole command string* resolved
to the relative path `"rm -f tools/gate.py"` rather than `None`; `decide` then took the
`candidates = [relative]` branch and the containment loop written for exactly this case
(`if relative is None:`) was never reached, so nothing matched the lock. Recorded as two
`xfail(strict=True)` cases so the hole stayed executable without reddening a tree that was not this
file's to break -- and strict did its job: when the author's fix landed (paths and shell strings read
apart, a command refused when a write token sits before the locked name it contains) both cases XPASSed
and failed, which is why the markers are gone in the same commit as this rewrite.

Three cases: the redirection and the removal must deny, and the **indirect** form
(`cd tools && rm gate.py`) must still be allowed, because that residual is the design's own -- section
*"The smallest deliverable, and the acceptance test written first"*, in the design's own words: "a
command that rewrites a gate through an indirect path (a script, a generated heredoc, a `python -c`) is
not caught by a path-and-verb heuristic". **Cited by heading and quoted words rather than by line
numbers**, because an independent reviewer's correction in an earlier revision moved the block under
this citation and a number would have gone on pointing at the fixtures paragraph. Pinning the third
keeps the first two from being read as "Bash is never denied" -- and it is the case that will fail the
day the heuristic gets smarter, which is the right time for someone to re-read the design rather than
the test.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import _support

REPO = _support.REPO
REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]


def _repo(name: str) -> Path:
    """A ratified charter whose gate row names `tools/gate.py` -- the lock the Bash cases aim at."""
    root = Path(tempfile.gettempdir()) / f"keelcheck-adapter-bash-{name}-{os.getpid()}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    _support.write(root / "tracked.txt", "hello\n")
    _support.write(root / "tools" / "gate.py", "print('ok')\n")
    gates = [("coverage", "tools/gate.py", _support.hash_file(root / "tools" / "gate.py"))]
    _support.write_charter(root, requirements=REQUIREMENTS, gates=gates)
    sha = _support.init_repo(root)
    _support.write_charter(root, requirements=REQUIREMENTS, gates=gates, ratified=sha)
    _support.commit_all(root, "ratified")
    return root


def _bash_event(repo: Path, command: str) -> subprocess.CompletedProcess:
    """One Claude Code `PreToolUse` Bash event through the real CLI, the way a harness runs it.

    **`PYTHONPATH` is extended, never replaced.** A harness runs the adapter with the interpreter the
    installer pinned; here the test starts `python -m` and the package has to be importable, so the
    checkout is prepended to whatever the caller had. Replacing it instead (what this did until the author
    measured the same thing in his file) drops the coverage gate's child-tracer directory, and then the
    CLI children this file spawns are simply not measured: the gate reports a number that cannot see
    them, which is the blindness the tracer exists to remove.
    """
    payload = json.dumps({
        "session_id": "0f7c2b1e-0000-4000-8000-0000000000ff",
        "transcript_path": str(repo / ".claude" / "transcript.jsonl"),
        "cwd": str(repo),
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    })
    inherited = os.environ.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "keelcheck", "adapter", "claude-code", "--repo", str(repo)],
        input=payload, capture_output=True, text=True, encoding="utf-8", cwd=str(repo), timeout=120,
        env={**os.environ, "PYTHONIOENCODING": "utf-8",
             "PYTHONPATH": str(REPO) + (os.pathsep + inherited if inherited else "")},
    )


def _decision(proc: subprocess.CompletedProcess) -> dict:
    return json.loads(proc.stdout)["hookSpecificOutput"]


def test_a_bash_redirection_into_a_locked_path_is_denied():
    repo = _repo("redirect")
    proc = _bash_event(repo, "echo 'weakened: always green' > tools/gate.py")

    assert proc.returncode == 2, (
        f"a shell redirection into a ratified gate script was allowed (exit {proc.returncode}): "
        f"{proc.stdout!r}")
    hook = _decision(proc)
    assert hook["permissionDecision"] == "deny", proc.stdout
    assert "tools/gate.py" in hook.get("permissionDecisionReason", ""), (
        f"the denial does not name the locked path: {hook}")


def test_a_bash_removal_of_a_locked_path_is_denied():
    repo = _repo("remove")
    proc = _bash_event(repo, "rm -f tools/gate.py")

    assert proc.returncode == 2, (
        f"a shell removal of a ratified gate script was allowed (exit {proc.returncode}): "
        f"{proc.stdout!r}")
    assert _decision(proc)["permissionDecision"] == "deny", proc.stdout


def test_the_indirect_bash_form_is_still_the_documented_residual():
    """Not a defect: the design names this residual in the section cited at the top of this file, so
    this case is pinned rather than reported. Pinned so the two cases above are read as one hole that was
    closed, not as "Bash is never denied" -- and so a smarter heuristic announces itself here, where the
    design's sentence is what should change next."""
    repo = _repo("indirect")
    proc = _bash_event(repo, "cd tools && rm -f gate.py")

    assert proc.returncode == 0, (
        f"the indirect form is now denied (exit {proc.returncode}), so the boundary moved and the "
        f"design's residual is stale: {proc.stdout!r}")
