"""R5's third surface: `keelcheck mcp` — a bounded stdio call that returns (R5, R6).

**Red before the code existed.** There is no `keelcheck/mcp.py`, `python -m keelcheck --help` lists
seven commands with no `mcp`, and every session below fails at `unknown command: mcp` rather than at a
protocol mistake. The smallest thing that makes it green is the surface itself.

What is asserted, and why each one is the property rather than a convenience:

1. the command is reachable the way the other surfaces are (`python -m keelcheck mcp`), and registered
   in the CLI's own help;
2. a stdio session answers `initialize` and `tools/list` as JSON-RPC 2.0, newline-delimited;
3. **the process ends when its stdin closes.** That is R6's "no daemon and no server" made observable:
   the whole session is one `communicate` call, so a surface that outlives its input fails by timeout
   rather than passing quietly;
4. `audit` comes back as a **result, not a protocol error** — a divergence is what the audit is for, and
   the caller sees the exit code the way a shell would;
5. the surface opens no socket, checked at the source, because that is the half of R6 a behavioural test
   cannot see.

Kept in this file rather than `test_review_cli.py` or `test_hook_cli.py` so Proctor verifies it instead
of rewriting it (Gilbert's assignment, 2026-10-16).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import _support

REPO = _support.REPO
MCP = REPO / "keelcheck" / "mcp.py"
REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]


def _session(lines: list[dict], *, timeout: float = 60.0) -> tuple[int, list[dict], str]:
    """One bounded session: write every request, close stdin, read everything back.

    The close is the test. A surface that never returns cannot pass here, because the only way this
    call ends is the process ending.
    """
    payload = "".join(json.dumps(line) + "\n" for line in lines)
    done = subprocess.run(
        [sys.executable, "-m", "keelcheck", "mcp"],
        input=payload, capture_output=True, text=True, encoding="utf-8",
        cwd=str(REPO), timeout=timeout,
        env={**_support_env(), "PYTHONIOENCODING": "utf-8"},
    )
    answers = [json.loads(line) for line in done.stdout.splitlines() if line.strip()]
    return done.returncode, answers, done.stderr


def _support_env() -> dict:
    import os

    return dict(os.environ)


def _initialize(request_id: int = 1) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "keelcheck-tests", "version": "0"},
        },
    }


def _diverging_repo(scratch) -> Path:
    """A ratified charter with no executable gate: the audit reports `[vacuity]`, exit 1."""
    _support.write(scratch / "tracked.txt", "hello\n")
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=[])
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=[], ratified=sha)
    _support.commit_all(scratch, "ratified")
    return scratch


def test_the_cli_lists_and_runs_the_mcp_command():
    listed = _support.keelcheck("--help")
    assert "mcp" in _support.combined(listed), (
        f"the CLI does not list the MCP surface:\n{_support.combined(listed)}")

    help_text = _support.keelcheck("mcp", "--help")
    assert help_text.returncode == 0, (
        f"`keelcheck mcp --help` does not run:\n{_support.combined(help_text)}")


def test_a_stdio_session_answers_initialize_and_tools_list_and_ends_on_eof():
    code, answers, stderr = _session([_initialize(), {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}])
    assert code == 0, f"the session did not end cleanly on stdin EOF: exit {code}\n{stderr}"

    by_id = {answer.get("id"): answer for answer in answers}
    assert 1 in by_id and "result" in by_id[1], f"no result for initialize: {answers}"
    init = by_id[1]["result"]
    assert init.get("protocolVersion"), f"initialize names no protocol version: {init}"
    assert init.get("serverInfo", {}).get("name") == "keelcheck", f"serverInfo is wrong: {init}"
    assert "tools" in init.get("capabilities", {}), f"no tools capability: {init}"

    assert 2 in by_id and "result" in by_id[2], f"no result for tools/list: {answers}"
    names = {tool.get("name") for tool in by_id[2]["result"].get("tools", [])}
    assert "audit" in names, f"tools/list does not offer `audit`: {names}"


def test_an_unknown_method_is_a_protocol_error_not_a_crash():
    code, answers, stderr = _session([{"jsonrpc": "2.0", "id": 1, "method": "no/such/method"}])
    assert code == 0, f"a protocol error ended the process badly: exit {code}\n{stderr}"
    assert answers and "error" in answers[0], f"an unknown method produced no error: {answers}"
    assert answers[0]["error"].get("code"), f"the error carries no code: {answers[0]}"


def test_audit_comes_back_as_a_result_with_the_exit_code(scratch):
    repo = _diverging_repo(scratch)
    code, answers, stderr = _session([
        _initialize(),
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "audit", "arguments": {"repo": str(repo)}}},
    ])
    assert code == 0, f"the session did not end cleanly: exit {code}\n{stderr}"

    by_id = {answer.get("id"): answer for answer in answers}
    assert 2 in by_id, f"no answer to the tool call: {answers}"
    answer = by_id[2]
    assert "error" not in answer, (
        "a diverging audit was reported as a protocol error: a divergence is the result the caller "
        f"asked for\n{answer}")
    result = answer.get("result", {})
    text = "\n".join(part.get("text", "") for part in result.get("content", []))
    assert result.get("isError") is False, f"a diverging audit marked as an error: {result}"
    assert "exit: 1" in text or "exit 1" in text, (
        f"the result does not carry the audit's exit code:\n{text[:600]}")
    assert "[vacuity]" in text, f"the result does not carry the audit's findings:\n{text[:600]}"


def test_a_usage_error_is_exit_two():
    done = _support.keelcheck("mcp", "--not-a-flag")
    assert done.returncode == 2, (
        f"a usage error did not exit 2:\n{_support.combined(done)}")


def test_the_surface_opens_no_socket_and_has_no_loop_that_outlives_the_call():
    """R6's other half, at the source: no socket, no listening, no bind."""
    assert MCP.is_file(), f"the surface does not exist: {MCP}"
    text = MCP.read_text(encoding="utf-8")
    for forbidden in ("import socket", "socket.", ".listen(", ".bind(", "socketserver", "http.server"):
        assert forbidden not in text, (
            f"R6 forbids a server: `{forbidden}` appears in {MCP.name}")
