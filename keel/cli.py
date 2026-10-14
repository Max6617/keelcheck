"""The keel command line: a bounded run that exits (R6).

No daemon, no server, no listening socket. Every command reads files, prints a report
and returns.
"""

from __future__ import annotations

import sys

from . import __version__
from .charter import main as charter_main

USAGE = """keel -- charter and audit

usage: keel <command> [options]

commands:
  charter <path>    parse a charter, report the requirements that name no mechanism (R1)

  keel charter --help   for that command's options
"""


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE, end="")
        return 0
    if argv[0] in ("-V", "--version", "version"):
        print(f"keel {__version__}")
        return 0

    command, rest = argv[0], argv[1:]
    if command == "charter":
        return charter_main(rest)

    print(f"keel: unknown command: {command}\n", file=sys.stderr)
    print(USAGE, end="", file=sys.stderr)
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
