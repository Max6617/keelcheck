"""The keelcheck command line: a bounded run that exits (R6).

No daemon, no server, no listening socket. Every command reads files, prints a report and
returns.

    keelcheck charter <path>      parse a charter; a requirement naming no mechanism is a wish (R1)
    keelcheck audit   <repo>      hash-locked gates, the frozen original, the wishes (R2, R3)
    keelcheck gate    run <repo>  run the ratified gates and record the run (R2)
    keelcheck gate    hash <path> the hash a gate row records, over git-normalized content (D9)
"""

from __future__ import annotations

import sys

from . import __version__
from .audit import main as audit_main
from .charter import main as charter_main
from .gate import main as gate_main
from .hook import main as hook_main
from .mcp import main as mcp_main
from .output import emit, emit_err
from .review import main as review_main

USAGE = """keelcheck -- charter and audit

usage: keelcheck <command> [options]

commands:
  charter <path>      parse a charter, report the requirements that name no mechanism (R1)
  audit <repo>        audit a repository against its ratified charter (R2, R3)
  gate run <repo>     run the ratified gates and record the run (R2)
  gate hash <path>    the content hash a gate row records (R2, D9)
  review <repo>       start a reviewer with no history and record what it was handed (R4)
  hook install <repo> install the pre-commit hook that runs the ratified gates (R5)
  hook status <repo>  report which hooks are installed (R5)
  mcp                 an MCP session on stdin/stdout: a bounded call that returns (R5, R6)

  keelcheck <command> --help   for that command's options
"""


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        emit(USAGE)
        return 0
    if argv[0] in ("-V", "--version", "version"):
        emit(f"keelcheck {__version__}")
        return 0

    command, rest = argv[0], argv[1:]
    if command == "charter":
        return charter_main(rest)
    if command == "audit":
        return audit_main(rest)
    if command == "gate":
        return gate_main(rest)
    if command == "review":
        return review_main(rest)
    if command == "hook":
        return hook_main(rest)
    if command == "mcp":
        return mcp_main(rest)

    emit_err(f"keelcheck: unknown command: {command}\n")
    emit_err(USAGE)
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
