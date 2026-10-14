"""The demonstration's reviewer wrapper, tested with a fake `claude` — no model, no call.

The wrapper exists so that `claude -p`'s prose and code fences do not turn keel's own validation into
guesswork: what reaches keel must be one JSON object, and when there is none the wrapper must exit
non-zero instead of printing something plausible. A stand-in `claude` on `PATH` makes both branches
deterministic and free.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import _support

WRAPPER = _support.REPO / "tests" / "_artefacts" / "claude-reviewer.py"


def _fake_claude(scratch, output: str, *, exit_code: int = 0, capture_stdin: bool = False):
    """A `claude` on PATH that prints ``output`` once and optionally records its stdin."""
    bindir = scratch / "bin"
    _support.write(bindir / "claude.py", "")  # placeholder so the directory exists
    script = bindir / "claude.py"
    _support.write(
        script,
        "import sys, pathlib\n"
        + ("pathlib.Path(r'%s').write_text(sys.stdin.read(), encoding='utf-8')\n"
           % (scratch / "stdin.txt") if capture_stdin else "sys.stdin.read()\n")
        + f"sys.stdout.write({output!r})\n"
        + f"sys.exit({exit_code})\n",
    )
    # a `claude` executable that runs the python file; a .cmd shim works on Windows
    shim = bindir / "claude.cmd"
    shim.write_text(f'@"{sys.executable}" "{script}" %*\n', encoding="ascii", newline="\n")
    return bindir, shim


def _run_wrapper(scratch, prompt="review this", *, path_extra=None):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    env["PATH"] = str(path_extra) + os.pathsep + env.get("PATH", "") if path_extra else env.get("PATH", "")
    return subprocess.run(
        [sys.executable, str(WRAPPER)], input=prompt, capture_output=True, text=True,
        encoding="utf-8", env=env, cwd=str(_support.REPO), timeout=60,
    )


def test_fenced_and_prose_wrapped_json_is_extracted_exactly(scratch):
    """`claude -p` answers in prose and fences the object; keel must still receive one clean object."""
    payload = {"verdict": "clean", "items": [], "unreviewed": [],
               "coverage": {"files_seen": 1, "files_total": 1}}
    output = "Certainly — here is the review:\n\n```json\n" + json.dumps(payload) + "\n```\nDone.\n"
    bindir, _ = _fake_claude(scratch, output)

    proc = _run_wrapper(scratch, path_extra=bindir)

    assert proc.returncode == 0, f"the wrapper failed:\n{proc.stderr[-400:]}"
    assert json.loads(proc.stdout) == payload, f"stdout is not the object:\n{proc.stdout!r}"
    assert proc.stdout.strip().startswith("{") and proc.stdout.strip().endswith("}"), (
        "the wrapper printed something other than the object itself")


def test_the_prompt_reaches_the_reviewer_on_stdin(scratch):
    payload = {"verdict": "clean", "items": [], "unreviewed": [],
               "coverage": {"files_seen": 1, "files_total": 1}}
    bindir, _ = _fake_claude(scratch, json.dumps(payload), capture_stdin=True)

    _run_wrapper(scratch, prompt="THE PROMPT TEXT", path_extra=bindir)

    assert (scratch / "stdin.txt").read_text(encoding="utf-8") == "THE PROMPT TEXT", (
        "the prompt did not reach the reviewer unchanged")


def test_output_without_a_json_object_fails_loudly(scratch):
    """No object → non-zero and the raw output on stderr, never a guessed object on stdout."""
    bindir, _ = _fake_claude(scratch, "I could not complete the review.\n")

    proc = _run_wrapper(scratch, path_extra=bindir)

    assert proc.returncode != 0, "the wrapper exited 0 without a JSON object"
    assert proc.stdout.strip() == "", f"the wrapper printed a claim it does not have:\n{proc.stdout!r}"
    assert "could not complete the review" in proc.stderr, "the raw output was not surfaced"


def test_prose_that_merely_looks_like_json_is_not_accepted(scratch):
    """A fenced example inside the prose is not the reviewer's answer if it does not parse."""
    bindir, _ = _fake_claude(scratch, "Use this shape: {verdict: clean} but I found nothing.\n")

    proc = _run_wrapper(scratch, path_extra=bindir)

    assert proc.returncode != 0, "an unparseable brace was accepted as the reviewer's object"
