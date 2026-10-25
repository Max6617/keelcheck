"""The demonstration's reviewer: Claude Code in print mode, wrapped to keep keelcheck's contract honest.

`keelcheck review` hands the prompt on stdin and accepts **exactly one JSON object** on stdout. `claude -p`
prints prose and may fence the JSON in a code block. This wrapper runs the CLI, extracts the first
balanced JSON object from its output, prints that object and nothing else, and exits non-zero with the
raw output on stderr when there is none — so keelcheck's `malformed` verdict still means malformed and not
"the wrapper guessed".

Usage (the reviewer command string keelcheck is given):

    "<python>" "<this file>"

Cost and reach, stated rather than implied: one Claude Code call on the user's own session, a fraction
of a cent, not a purchase. Claude Code loads its own configuration and may carry user-level memory or
project files, so the review's `history_reachable` is **unknown**, not `none` — the export has no
`.git`, but nothing here proves what the reviewer's own harness brings with it.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys


def _first_json_object(text: str) -> str | None:
    """The first balanced `{...}` in ``text`` that parses as JSON, fences and prose stripped."""
    for match in re.finditer(r"\{", text):
        depth = 0
        for index in range(match.start(), len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[match.start():index + 1]
                    try:
                        json.loads(candidate)
                    except json.JSONDecodeError:
                        break
                    return candidate
    return None


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    exe = shutil.which("claude")
    if not exe:
        print("claude-reviewer: no `claude` on PATH", file=sys.stderr)
        return 2

    prompt = sys.stdin.read()
    try:
        proc = subprocess.run(
            [exe, "-p", *argv], input=prompt, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except OSError as exc:
        print(f"claude-reviewer: could not start {exe}: {exc}", file=sys.stderr)
        return 2

    text = proc.stdout or ""
    found = _first_json_object(text)
    if found is None:
        print(f"claude-reviewer: no JSON object in the reviewer's output (exit {proc.returncode})",
              file=sys.stderr)
        # The reviewer's own error is usually on stderr. Without it a failed call records only this
        # wrapper's line, which is why three pre-fix runs failed at the reviewer with no reason named.
        error = (proc.stderr or "").strip()
        if error:
            print("--- claude stderr (tail) ---", file=sys.stderr)
            print(error[-2000:], file=sys.stderr)
        print("--- claude stdout (tail) ---", file=sys.stderr)
        print(text[-4000:], file=sys.stderr)
        return 1

    print(found)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
