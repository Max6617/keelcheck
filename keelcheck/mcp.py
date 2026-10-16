"""The MCP surface: a bounded stdio call that returns (R5 third, R6).

`keelcheck mcp` speaks JSON-RPC 2.0, one object per line, on stdin and stdout. It is a **call, not a
service**: it opens no socket, binds nothing, starts no thread and holds no state between requests, and
when stdin closes the process exits. R6 says "an MCP call that returns", and the shape that satisfies it
is exactly this one — the stdio transport, spawned by the client, where the client decides how long the
session lives by how long it keeps the pipe open.

That is also why this file has no `socket`, no `listen`, no `bind` and no HTTP: a network MCP server
would be a listening socket, which R6 forbids, so the stdio transport is not a preference here but the
only shape the charter allows.

    keelcheck mcp            # one session on stdin/stdout, ends at EOF

Protocol, in brief: `initialize` answers with the protocol version, `serverInfo` and the `tools`
capability; `tools/list` names the tools; `tools/call` runs one. A tool's *finding* is a result, never a
protocol error — an audit that reports divergences answers `isError: false` with the exit code inside the
text, because that is what the caller asked for. Notifications (no `id`) are never answered, which the
protocol requires.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable, TextIO

from . import __version__
from .audit import run_audit
from .output import emit_err

#: The MCP revision this surface speaks. A client that wants another one still gets a usable answer:
#: `initialize` echoes this and the client decides whether it can proceed.
PROTOCOL_VERSION = "2024-11-05"

#: One request may not be larger than this. The bound exists because the input is a pipe from another
#: process: an unbounded read is how a bounded call stops being bounded.
MAX_REQUEST_BYTES = 1024 * 1024

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602

TOOLS: list[dict[str, Any]] = [
    {
        "name": "audit",
        "description": (
            "Audit a repository against its ratified charter: hash-locked gates, the frozen original, "
            "the wishes and the review state. Returns the report and the exit code the audit would "
            "have returned from a shell (0 clean, 1 divergence, 2 cannot run)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "repository to audit (default: .)"},
                "record": {
                    "type": "string",
                    "description": "where the run record goes (default: <repo>/.keel/runs.jsonl)",
                },
            },
            "required": [],
        },
    },
]


def _audit_tool(arguments: dict[str, Any]) -> dict[str, Any]:
    """The `audit` tool: the mechanical half's report, plus the exit code a shell would have seen."""
    repo = arguments.get("repo") or "."
    record = arguments.get("record")
    audit = run_audit(repo, record_path=record)
    text = audit.render()
    if not text.endswith("\n"):
        text += "\n"
    # An MCP result cannot carry a process exit code, and a divergence is not an error, so the code
    # travels in the text: the caller reads it exactly as it would read `echo $?`.
    text += f"exit: {audit.exit_code}\n"
    return {"content": [{"type": "text", "text": text}], "isError": False}


TOOL_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {"audit": _audit_tool}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def handle(request: Any) -> dict[str, Any] | None:
    """One request in, at most one response out. `None` means a notification, which is not answered."""
    if not isinstance(request, dict):
        return _error(None, INVALID_REQUEST, "a request must be a JSON object")
    request_id = request.get("id")
    method = request.get("method")
    if not isinstance(method, str):
        return _error(request_id, INVALID_REQUEST, "a request needs a `method` string")
    # A request without an `id` is a notification, whatever its method: the protocol forbids answering
    # it, and a client that gets an unsolicited response desynchronises. (JSON-RPC still allows an
    # `id: null` on a *parse* or *invalid-request* error, which is why the two checks above run first.)
    if request_id is None:
        return None

    if method == "initialize":
        return _result(
            request_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "keelcheck", "version": __version__},
            },
        )
    if method == "tools/list":
        return _result(request_id, {"tools": TOOLS})
    if method == "tools/call":
        params = request.get("params")
        params = {} if params is None else params
        if not isinstance(params, dict):
            return _error(request_id, INVALID_PARAMS, "`params` must be an object")
        name = params.get("name")
        handler = TOOL_HANDLERS.get(name) if isinstance(name, str) else None
        if handler is None:
            return _error(request_id, INVALID_PARAMS, f"no tool named {name!r}")
        arguments = params.get("arguments")
        arguments = {} if arguments is None else arguments
        if not isinstance(arguments, dict):
            return _error(request_id, INVALID_PARAMS, "`arguments` must be an object")
        try:
            return _result(request_id, handler(arguments))
        except Exception as exc:  # noqa: BLE001 - a failing tool is reported, never a traceback
            return _result(
                request_id,
                {
                    "content": [{"type": "text", "text": f"the tool failed: {exc}"}],
                    "isError": True,
                },
            )
    if request_id is None:
        return None
    return _error(request_id, METHOD_NOT_FOUND, f"unknown method {method!r}")


def serve(stdin: TextIO, stdout: TextIO) -> int:
    """Answer requests until stdin closes. Returns the process exit code for the session."""
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        if len(line) > MAX_REQUEST_BYTES:
            responses = [_error(None, INVALID_REQUEST, f"a request may not exceed {MAX_REQUEST_BYTES} bytes")]
        else:
            try:
                request = json.loads(line)
            except json.JSONDecodeError as exc:
                responses = [_error(None, PARSE_ERROR, f"not JSON: {exc.msg}")]
            else:
                answer = handle(request)
                responses = [] if answer is None else [answer]
        for response in responses:
            stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        stdout.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="keelcheck mcp",
        description=(
            "speak MCP on stdin/stdout: a bounded call that returns, with no socket and no server "
            "(R5, R6). The session ends when stdin closes."
        ),
        epilog="tools: audit",
    )
    parser.parse_args(argv)
    return serve(sys.stdin, sys.stdout)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
