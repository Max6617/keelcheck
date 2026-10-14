"""The parser's machine-readable report must not crash on a real charter.

**Red first, measured at `489f47d`.** `python -m keel charter ../rentguard/CHARTER.md --json` exits 1
with `UnicodeEncodeError: 'charmap' codec can't encode character '\\u2192'` — the arrow in rentguard
R5's text ("the real A4000→4090 fallback") cannot be written to a cp1252 stdout, and `--json` uses
`ensure_ascii=False`.

The plain report is safe only by accident: it does not print requirement text, so it never reaches
the arrow. The machine-readable path — the one tools and the run record will consume — is the one
that breaks, and it breaks on the project's own demonstration input.

`PYTHONIOENCODING=cp1252` is pinned inside the test rather than inherited, so the suite measures the
code and not the console it happens to run on (team rule).
"""

from __future__ import annotations

import os
import subprocess
import sys

import _support


def test_json_report_of_a_real_charter_survives_a_cp1252_console():
    proc = subprocess.run(
        [sys.executable, "-m", "keel.charter", str(_support.RENTGUARD_CHARTER), "--json"],
        cwd=_support.REPO, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "cp1252"},
    )

    assert proc.returncode == 0, (
        "the JSON report of rentguard/CHARTER.md failed on a cp1252 console, so the "
        f"machine-readable output is unusable on a default Windows shell:\n{proc.stderr[-500:]}"
    )
    assert proc.stdout.strip().startswith("{"), "no JSON was printed"
