"""A deeply nested line gets a parse error and the session keeps going."""
import json
import subprocess
import sys

import _support


def test_a_deeply_nested_line_is_answered_and_the_stream_survives():
    stdin = b"[" * 100000 + b"\n" + b'{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}\n'

    proc = subprocess.run(
        [sys.executable, "-m", "keelcheck", "mcp"], cwd=_support.REPO, input=stdin, capture_output=True,
    )

    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    answers = [json.loads(line) for line in proc.stdout.decode("utf-8").splitlines()]
    assert len(answers) == 2, answers
    assert answers[0]["error"]["code"] == -32700 and answers[0]["id"] is None
    assert answers[1]["id"] == 2 and "result" in answers[1]
