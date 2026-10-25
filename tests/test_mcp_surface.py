"""R5's third surface: `keelcheck mcp` — a bounded stdio call that returns (R5, R6).

**Red before the code existed.** There is no `keelcheck/mcp.py`, `python -m keelcheck --help` lists
seven commands with no `mcp`, and every session below fails at `unknown command: mcp` rather than at a
protocol mistake. The smallest thing that makes it green is the surface itself.

What is asserted, and why each one is the property rather than a convenience:

1. the command is reachable the way the other surfaces are (`python -m keelcheck mcp`), and registered
   in the CLI's own help;
2. a stdio session answers `initialize` and `tools/list` as JSON-RPC 2.0, newline-delimited, and
   **notifications are never answered** — the protocol requires it, and a surface that answers them
   desynchronises every client that sends one;
3. **the process ends when its stdin closes.** That is R6's "no daemon and no server" made observable:
   the whole session is one `communicate` call, so a surface that outlives its input fails by timeout
   rather than passing quietly;
4. `audit` comes back as a **result, not a protocol error**, for a diverging repository (exit 1) and for
   a clean one (exit 0) — a divergence is what the audit is for, and the caller sees the exit code the
   way a shell would;
5. every rejection is a *named* code rather than a crash: unparseable line, non-object request, missing
   method, unknown method, unknown tool, and `params`/`arguments` that are not objects;
6. the surface opens no socket and has no loop that outlives the call, checked at the source, because
   that is the half of R6 a behavioural test cannot see.

The unit-level cases call `handle()` directly, which is how the error paths become reachable without
inventing a malformed CLI session for each one; the subprocess cases are the ones that prove the process
boundary. Kept in this file rather than `test_review_cli.py` or `test_hook_cli.py` so an independent verifier verifies it
instead of rewriting it (the maintainer's assignment, 2026-10-16).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import _support

REPO = _support.REPO
MCP = REPO / "keelcheck" / "mcp.py"
REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]


def _session(lines: list[dict | str], *, timeout: float = 60.0) -> tuple[int, list[dict], str]:
    """One bounded session: write every request, close stdin, read everything back.

    The close is the test. A surface that never returns cannot pass here, because the only way this
    call ends is the process ending. A `str` entry is written verbatim, so a caller can send something
    that is not JSON.
    """
    payload = "".join(
        (line if isinstance(line, str) else json.dumps(line)) + "\n" for line in lines
    )
    done = subprocess.run(
        [sys.executable, "-m", "keelcheck", "mcp"],
        input=payload, capture_output=True, text=True, encoding="utf-8",
        cwd=str(REPO), timeout=timeout,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    answers = [json.loads(line) for line in done.stdout.splitlines() if line.strip()]
    return done.returncode, answers, done.stderr


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


def _call(name: str, arguments: dict, request_id: int = 2) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "method": "tools/call",
            "params": {"name": name, "arguments": arguments}}


def _diverging_repo(scratch) -> Path:
    """A ratified charter with no executable gate: the audit reports `[vacuity]`, exit 1."""
    _support.write(scratch / "tracked.txt", "hello\n")
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=[])
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=[], ratified=sha)
    _support.commit_all(scratch, "ratified")
    return scratch


def _clean_repo(scratch, record: Path | None = None) -> Path:
    """A ratified charter with one passing gate and its run recorded at `record`: audit clean, exit 0.

    The gate run and the audit must agree on the record path, which is the point of the test that uses
    this: the tool reads the record it is given, so a run written elsewhere is not a run.
    """
    _support.write(scratch / "tracked.txt", "hello\n")
    _support.write(scratch / "tools" / "gate.py", "print('ok')\n")
    gates = [("coverage", "tools/gate.py", _support.hash_file(scratch / "tools" / "gate.py"))]
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates, ratified=sha)
    _support.commit_all(scratch, "ratified")
    extra = ("--record", str(record)) if record else ()
    _support.keelcheck("gate", "run", str(scratch), *extra, "--timeout", "10")
    return scratch


# --- the process boundary -----------------------------------------------------


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
    tools = by_id[2]["result"].get("tools", [])
    names = {tool.get("name") for tool in tools}
    assert "audit" in names, f"tools/list does not offer `audit`: {names}"
    schema = next(tool for tool in tools if tool["name"] == "audit").get("inputSchema", {})
    assert "repo" in schema.get("properties", {}), f"audit's schema names no repo: {schema}"


def test_a_notification_is_never_answered():
    """The protocol's own rule, and a client desynchronises without it."""
    code, answers, stderr = _session([
        _initialize(),
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/list"},
    ])
    assert code == 0, f"the session did not end cleanly: exit {code}\n{stderr}"
    ids = [answer.get("id") for answer in answers]
    assert ids == [1, 3], f"a notification was answered: {answers}"


def test_the_session_survives_a_malformed_line_and_answers_the_next_request():
    code, answers, stderr = _session([
        _initialize(),
        "{not json at all",
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    ])
    assert code == 0, f"a bad line ended the session badly: exit {code}\n{stderr}"
    ids = [answer.get("id") for answer in answers]
    assert ids == [1, None, 2], f"the parse error was not reported in place: {answers}"
    assert answers[1]["error"]["code"] == -32700, f"wrong code for a parse error: {answers[1]}"


def test_a_request_over_the_size_cap_is_refused_and_the_stream_survives():
    """**Renamed from "…is refused rather than read", because the code does not do that.** An independent verifier,
    2026-10-16: the module docstring says an unbounded read is how a bounded call stops being bounded,
    and `for line in stdin` (mcp.py:149) materialises the whole line *before* `len(line) > MAX` is
    asked (mcp.py:153). Measured: 128 MiB with no newline gives the child a **156.2 MiB peak working
    set** and only then a -32600. So what a test can hold is the refusal and the stream after it, and
    the read bound is reported to the owner of `keelcheck/mcp.py` rather than asserted against it from
    here — a portable assertion on memory is not the kind of test this suite keeps.
    """
    # A long *non-space* payload: `serve` strips whitespace before measuring, so a line of spaces would
    # be trimmed to nothing and test the parse path instead of the cap.
    huge = json.dumps({"jsonrpc": "2.0", "id": 9, "method": "tools/list",
                       "params": {"pad": "0" * (1024 * 1024 + 16)}})
    code, answers, stderr = _session([huge, _initialize(request_id=2)])
    assert code == 0, f"an oversized request ended the session badly: exit {code}\n{stderr}"

    refusals = [answer for answer in answers if answer.get("error", {}).get("code") == -32600]
    assert refusals, (
        f"an oversized request was not refused with -32600: {[a.get('error') for a in answers]}")
    assert refusals[0]["id"] is None, (
        f"a refusal for a request that was never read cannot carry its id: {refusals[0]}")
    assert not [answer for answer in answers if answer.get("id") == 9], (
        "the oversized request was answered as a request, so its body was parsed: "
        f"{[a for a in answers if a.get('id') == 9]}")
    assert [answer.get("id") for answer in answers] == [None, 2], (
        f"the stream desynchronised after the refusal: {answers}")


def test_every_answer_carries_jsonrpc_2_0_and_echoes_the_id():
    """The member every JSON-RPC answer must carry, and which no case here asserted until now: drop it
    and a strict client is entitled to discard the answer, while all thirteen original cases still
    pass. Measured 2026-10-16: `jsonrpc` is `"2.0"` in every answer, so this is a pin, not a red."""
    code, answers, stderr = _session([
        _initialize(request_id=1),
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 7, "method": "no/such/method"},
    ])
    assert code == 0, f"the session did not end cleanly: exit {code}\n{stderr}"
    assert [answer.get("id") for answer in answers] == [1, 2, 7], answers
    for answer in answers:
        assert answer.get("jsonrpc") == "2.0", f"an answer without the required member: {answer}"
        assert ("result" in answer) != ("error" in answer), (
            f"an answer carries both a result and an error, or neither: {answer}")


def test_a_blank_line_is_not_a_request_and_does_not_desynchronise():
    """The one input path with no case: `serve` skips empty lines before parsing (mcp.py:151-152). A
    client that sends a stray newline — which every hand-written harness does — must not get an answer
    for it, and must not lose the next request."""
    code, answers, stderr = _session([
        _initialize(request_id=1),
        "   ",
        "",
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    ])
    assert code == 0, f"a blank line ended the session badly: exit {code}\n{stderr}"
    assert [answer.get("id") for answer in answers] == [1, 2], (
        f"a blank line was answered or the stream desynchronised: {answers}")


def test_an_unknown_method_is_a_protocol_error_not_a_crash():
    code, answers, stderr = _session([{"jsonrpc": "2.0", "id": 1, "method": "no/such/method"}])
    assert code == 0, f"a protocol error ended the process badly: exit {code}\n{stderr}"
    assert answers and answers[0]["error"]["code"] == -32601, f"wrong error: {answers}"
    assert "no/such/method" in answers[0]["error"]["message"], answers[0]


def test_audit_comes_back_as_a_result_with_the_exit_code(scratch):
    repo = _diverging_repo(scratch)
    code, answers, stderr = _session([
        _initialize(),
        _call("audit", {"repo": str(repo)}),
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
    assert "exit: 1" in text, f"the result does not carry the audit's exit code:\n{text[:600]}"
    assert "[vacuity]" in text, f"the result does not carry the audit's findings:\n{text[:600]}"


def test_a_clean_repository_comes_back_with_exit_zero_and_a_named_record(scratch):
    """The other side of the same call, and the `record` argument doing what it says."""
    record = scratch / "elsewhere" / "runs.jsonl"
    record.parent.mkdir(parents=True, exist_ok=True)
    repo = _clean_repo(scratch, record)
    code, answers, stderr = _session([
        _initialize(),
        _call("audit", {"repo": str(repo), "record": str(record)}),
    ])
    assert code == 0, f"the session did not end cleanly: exit {code}\n{stderr}"

    by_id = {answer.get("id"): answer for answer in answers}
    result = by_id[2].get("result", {})
    text = "\n".join(part.get("text", "") for part in result.get("content", []))
    assert result.get("isError") is False, f"a clean audit marked as an error: {result}"
    assert "exit: 0" in text, f"a clean audit did not report exit 0:\n{text[:600]}"
    # The tool's own words, not the absence of a word: a clean run prints `DIVERGENCES: none`, so
    # `"DIVERGENCES" not in text` would fail on a clean audit (measured, 2026-10-16).
    assert "DIVERGENCES: none" in text, (
        f"a clean audit did not say so in its own words:\n{text[:600]}")
    assert record.is_file(), f"the `record` argument was not honoured: {record}"


def test_a_usage_error_is_exit_two():
    done = _support.keelcheck("mcp", "--not-a-flag")
    assert done.returncode == 2, (
        f"a usage error did not exit 2:\n{_support.combined(done)}")


def test_a_request_must_say_jsonrpc_2_0():
    """JSON-RPC 2.0 requires the member to be exactly `"2.0"`; anything else is an invalid request."""
    code, answers, stderr = _session([
        {"id": 1, "method": "tools/list"},                      # member absent
        {"jsonrpc": "1.0", "id": 2, "method": "tools/list"},    # wrong version
        _initialize(request_id=3),                              # the control: this one must work
    ])
    assert code == 0, f"the session did not end cleanly: exit {code}\n{stderr}"
    by_id = {answer.get("id"): answer for answer in answers}
    for request_id in (1, 2):
        answer = by_id.get(request_id, {})
        assert answer.get("error", {}).get("code") == -32600, (
            f"a request without `jsonrpc: \"2.0\"` was not refused: {answer}")
    assert "result" in by_id.get(3, {}), f"the valid request was refused too: {answers}"


def _peak_mib(pid: int) -> float | None:
    """The peak working set of a live process, or None where it cannot be read.

    Peak rather than current: the defect is the *high-water mark* of holding an over-long line, and it
    has already happened by the time the child answers. Windows through `psapi`, elsewhere through
    `/proc`, so this is a measurement on either platform rather than a skip.
    """
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return None
        try:
            counters = Counters()
            counters.cb = ctypes.sizeof(Counters)
            if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                return None
            return counters.PeakWorkingSetSize / (1024 * 1024)
        finally:
            kernel32.CloseHandle(handle)
    try:
        with open(f"/proc/{pid}/status", encoding="utf-8") as status:
            for line in status:
                if line.startswith("VmHWM:"):
                    return int(line.split()[1]) / 1024
    except OSError:
        return None
    return None


def test_an_over_long_request_is_refused_without_holding_it_in_memory():
    """The cap must refuse *before* the line is in memory, not after.

    An independent verifier measured the first landing: 128 MiB with no newline cost 156.2 MiB of peak working set for a
    1 MiB cap. The line is written from here and never held by the assertion; what is checked is the
    child's own high-water mark, plus the two behaviours the refusal must keep — a `-32600` with a
    **null id**, and a stream that stays ordered for the request behind it.
    """
    line_mib = 32
    payload = "0" * (line_mib * 1024 * 1024)
    proc = subprocess.Popen(
        [sys.executable, "-m", "keelcheck", "mcp"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", cwd=str(REPO),
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    try:
        proc.stdin.write(payload)
        proc.stdin.write("\n")
        proc.stdin.write(json.dumps(_initialize(request_id=2)) + "\n")
        proc.stdin.flush()
        first = json.loads(proc.stdout.readline())
        second = json.loads(proc.stdout.readline())
        peak = _peak_mib(proc.pid)
    finally:
        proc.stdin.close()
        proc.wait(timeout=120)

    assert first.get("error", {}).get("code") == -32600, f"the over-long line was not refused: {first}"
    assert first.get("id") is None, f"a refusal with no request to answer must carry a null id: {first}"
    assert second.get("id") == 2 and "result" in second, (
        f"the stream lost its order after an over-long line: {second}")
    assert proc.returncode == 0, f"the session did not end cleanly: exit {proc.returncode}"
    assert peak is None or peak < line_mib, (
        f"a {line_mib} MiB line cost {peak:.1f} MiB of peak working set under a 1 MiB cap: the cap "
        "reads the line before it refuses it. The threshold is the line's own size, not a tuned "
        "constant: holding it costs at least that much (measured 85.3 MiB), a bounded read costs the "
        "interpreter's baseline and no more (measured 22.7 MiB).")


def test_the_surface_opens_no_socket_at_the_source():
    """R6's other half, at the source — **and only that half, which is what the name now says.**

    The old name claimed "no loop that outlives the call" and asserted nothing about loops: the body
    was, and is, a substring scan of this one file. The behavioural half is real but lives in
    `test_a_stdio_session_answers_initialize_and_tools_list_and_ends_on_eof`, where `_session` ends
    only when the process ends — a *non-daemon* thread or an open listener keeps it alive and the test
    fails by timeout. What this cannot see, stated so the pair is not overread: a daemon thread, a
    socket built from a computed name, a socket opened in any module this one imports, and anything
    spelled differently. It is a lint with a reason, not a proof.
    """
    assert MCP.is_file(), f"the surface does not exist: {MCP}"
    text = MCP.read_text(encoding="utf-8")
    for forbidden in ("import socket", "socket.", ".listen(", ".bind(", "socketserver", "http.server",
                      "threading", "Thread(", "asyncio"):
        assert forbidden not in text, (
            f"R6 forbids a server or a loop that outlives the call: `{forbidden}` appears in {MCP.name}")


# --- the request handler, where the error paths live --------------------------


def _mcp():
    """The module itself, for the cases that are cheaper to call than to spawn."""
    sys.path.insert(0, str(REPO))
    from keelcheck import mcp

    return mcp


def test_handle_rejects_shapes_it_cannot_answer():
    mcp = _mcp()
    cases = [
        ([1, 2, 3], -32600, "a request must be a JSON object"),
        ({"jsonrpc": "2.0", "id": 1}, -32600, "`method` string"),
        ({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": []}, -32602,
         "`params` must be an object"),
        ({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "nope"}}, -32602,
         "no tool named"),
        ({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
          "params": {"name": "audit", "arguments": "not-an-object"}}, -32602, "must be an object"),
    ]
    for request, code, fragment in cases:
        answer = mcp.handle(request)
        assert answer and answer["error"]["code"] == code, f"{request!r} -> {answer!r}"
        assert fragment in answer["error"]["message"], f"{request!r} -> {answer!r}"


def test_handle_answers_a_notification_with_nothing():
    mcp = _mcp()
    assert mcp.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    # A request *without* an id is not a notification the protocol defines, but it must not be answered
    # as if it had one either: no id, no response.
    assert mcp.handle({"jsonrpc": "2.0", "method": "tools/list"}) is None


def test_a_tool_that_raises_is_an_error_result_and_not_a_traceback():
    mcp = _mcp()
    mcp.TOOL_HANDLERS["boom"] = lambda arguments: 1 / 0
    try:
        answer = mcp.handle(_call("boom", {}))
    finally:
        del mcp.TOOL_HANDLERS["boom"]
    assert "error" not in answer, f"a failing tool became a protocol error: {answer}"
    result = answer["result"]
    assert result["isError"] is True, result
    assert "the tool failed" in result["content"][0]["text"], result
