"""With no git executable on PATH, `audit` and `gate run` exit 2 with a message, not 1 with a traceback."""

from __future__ import annotations

import _support

REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]


def test_no_git_binary_exits_2_without_traceback(scratch):
    script = _support.write(scratch / "tools" / "gate.py", "print('ok')\n")
    gates = [("coverage", "tools/gate.py", _support.hash_file(script))]
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates, ratified=sha)
    _support.commit_all(scratch, "ratified")

    nobin = scratch / "nobin"
    nobin.mkdir()
    env = {"PATH": str(nobin)}
    for proc in (
        _support.audit(scratch, env_extra=env),
        _support.keelcheck("gate", "run", str(scratch), env_extra=env),
    ):
        out = _support.combined(proc)
        assert proc.returncode == 2, out
        assert "Traceback" not in out, out
        assert "git" in out, out
