"""The request cap is measured in bytes, not characters."""
import io
import json

from keelcheck.mcp import MAX_REQUEST_BYTES, serve


def test_a_request_over_the_cap_in_bytes_but_under_it_in_characters_is_refused():
    padded = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {"pad": "é" * (MAX_REQUEST_BYTES // 2 + 100)}},
        ensure_ascii=False,
    )
    assert len(padded) <= MAX_REQUEST_BYTES < len(padded.encode("utf-8"))
    valid = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    stdout = io.StringIO()

    code = serve(io.StringIO(padded + "\n" + valid + "\n"), stdout)

    answers = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert code == 0
    assert len(answers) == 2, f"expected a refusal and a result: {answers}"
    assert answers[0]["error"]["code"] == -32600, f"the byte-oversized request was not refused: {answers[0]}"
    assert answers[0]["id"] is None
    assert answers[1]["id"] == 2 and "result" in answers[1], f"the stream did not survive: {answers[1]}"
