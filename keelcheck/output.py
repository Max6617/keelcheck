"""UTF-8 output for the CLI (D8).

The machine-readable report must not depend on the console code page. Measured at
`489f47d`: ``python -m keelcheck charter ../rentguard/CHARTER.md --json`` exited 1 with
``UnicodeEncodeError: 'charmap' codec can't encode character '\\u2192'`` on a cp1252
console, because the arrow in rentguard R5's text cannot be encoded there. The record
consumes that path, so it is a defect and not a cosmetic one.

Every line the CLI prints goes through here. When the stream has a ``.buffer`` (a real
console, or pytest's capture) the text is written as UTF-8 bytes; otherwise it is written
as text. No ``ensure_ascii`` workaround: the tool's own output should be readable in the
language the charters are written in.
"""

from __future__ import annotations

import sys
from typing import IO


def _write(stream: IO, text: str) -> None:
    buffer = getattr(stream, "buffer", None)
    if buffer is None:
        stream.write(text)
        stream.flush()
        return
    try:
        stream.flush()
    except (ValueError, OSError):  # pragma: no cover - closed or detached stream
        pass
    buffer.write(text.encode("utf-8"))
    buffer.flush()


def emit(text: str = "") -> None:
    """Print ``text`` to stdout as UTF-8, with a trailing newline."""
    _write(sys.stdout, text if text.endswith("\n") else text + "\n")


def emit_err(text: str = "") -> None:
    """Print ``text`` to stderr as UTF-8, with a trailing newline."""
    _write(sys.stderr, text if text.endswith("\n") else text + "\n")
