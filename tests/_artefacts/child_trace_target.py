"""A tiny pytest target that drives keelcheck from **outside** — the D3 shape the tracer exists to follow.

Named without a `test_` prefix so the normal suite never collects it; the coverage gate is given the
path explicitly. One test, one subprocess: nothing here imports keelcheck, which is the whole point — if
the tracer works, `keelcheck/audit.py` is reached from the child process or not at all.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]  # tests/_artefacts/x.py -> tests -> keelcheck/


def test_drive_the_audit_in_a_subprocess():
    record = Path(tempfile.mkdtemp(prefix="keelcheck-trace-")) / "runs.jsonl"
    proc = subprocess.run(
        [sys.executable, "-m", "keelcheck", "audit", str(REPO), "--record", str(record)],
        cwd=str(REPO), capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=300,
    )
    # exit 1 or 2 both mean the audit ran and reported; what matters here is that it executed
    assert proc.returncode in (0, 1, 2), f"the audit did not run: {proc.returncode}"
