"""A target that runs the **inner** gate, for the nested-isolation measurement.

Used by `tests/test_coverage_gate.py`: the outer gate runs this file, this file runs the gate again
over `child_trace_target.py`, and the inner document plus this process's inherited `PYTHONPATH` are
written to `KEEL_NESTED_OUT`. Named without a `test_` prefix so the normal suite never collects it.

Two things are measured this way, and the second is the one that matters:

1. **Isolation** — the inner run's total must equal a standalone run's, so a nested gate measures its
   own hits and does not read the outer run's.
2. **The parent's `PYTHONPATH` survives** — the tracer may *add* a directory, never remove one. This
   process is a child of the outer gate, so `inherited` is what the gate handed down; if the tracer
   replaced rather than extended it, a nested run could not import the tool it is testing, which is
   exactly how the hook tests failed under the gate with `No module named keelcheck`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]  # tests/_artefacts/x.py -> tests -> keelcheck repo

OUT = Path(os.environ.get("KEEL_NESTED_OUT")
           or (Path(tempfile.gettempdir()) / "keel-nested-measurement.json"))


def test_the_inner_gate_is_isolated_and_keeps_the_parents_path():
    inherited = os.environ.get("PYTHONPATH", "")
    proc = subprocess.run(
        [sys.executable, str(REPO / "tools" / "coverage.py"), "--min", "0.0", "--json",
         "tests/_artefacts/child_trace_target.py"],
        cwd=str(REPO), capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=900,
    )
    OUT.write_text(json.dumps({
        "inner_stdout": proc.stdout,
        "inner_returncode": proc.returncode,
        "inherited_pythonpath": inherited,
    }), encoding="utf-8")
    assert proc.returncode == 0, (proc.stderr or proc.stdout)[-500:]
