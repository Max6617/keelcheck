"""A tiny target whose **suite fails**, for the gate's red-suite branch.

It drives keelcheck from outside first, so the measurement is non-zero and the coverage number alone
cannot refuse; only the suite check can. Named without a `test_` prefix so the normal suite never
collects it; the gate is given the path explicitly.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]  # tests/_artefacts/x.py -> tests -> keelcheck/


def test_drives_the_cli_in_a_child_and_then_fails():
    # A plain mkdir under the platform temp root, not mkdtemp: on this host mkdtemp makes a mode-0700
    # directory the sandbox refuses to write into, so `keelcheck audit --record` there could not run.
    record_dir = Path(tempfile.gettempdir()) / f"keelcheck-red-{os.getpid()}"
    record_dir.mkdir(parents=True, exist_ok=True)
    record = record_dir / "runs.jsonl"
    proc = subprocess.run(
        [sys.executable, "-m", "keelcheck", "audit", str(REPO), "--record", str(record)],
        cwd=str(REPO), capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=300,
    )
    assert proc.returncode in (0, 1, 2), f"the audit did not run: {proc.returncode}"
    assert False, "this target fails on purpose, after reaching keelcheck in a child process"
