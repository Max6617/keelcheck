"""A timed-out gate's run record keeps what the gate printed before it was killed (R2)."""

from __future__ import annotations

import json

import _support

REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]


def test_a_timed_out_gate_keeps_its_partial_output(scratch):
    path = "tools/gate.py"
    script = _support.write(
        scratch / path,
        "import time\nprint('gate-started', flush=True)\ntime.sleep(30)\n",
    )
    gates = [("coverage", path, _support.hash_file(script))]
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates, ratified=sha)
    _support.commit_all(scratch, "ratified")

    proc = _support.keelcheck("gate", "run", str(scratch), "--timeout", "2", "--json")
    result = json.loads(proc.stdout)["gates"][0]

    assert result["result"] == "timeout", _support.combined(proc)
    assert "gate-started" in result["output"], result["output"]
