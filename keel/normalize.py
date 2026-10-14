"""Git-normalized content, and the hash taken over it (D9).

Measured on this host: the system ``gitconfig`` sets ``core.autocrlf=true``, so a fresh
clone checks ``CHARTER.md`` out with 127 CRLF lines and the frozen-original block hashed
``4bb314d0...`` instead of ``376f11a4...``. Any comparison of raw worktree bytes against
``git show`` bytes therefore reports a false divergence on exactly the rule this tool
exists for (D9). So the hash is taken over the content **git would store**, never over the
bytes on disk.

Two layers, and the second one is the point:

1. This module implements git's text detection and CRLF conversion for the attributes that
   matter (``text``, ``-text``/``binary``, ``text=auto``, and the ``core.autocrlf``
   fallback). It is a reading of git's rules, so it can be wrong.
2. Every hash is verified against ``git hash-object`` -- the object id git itself would
   store for that path, with its own filters. If the two disagree (an exotic attribute, a
   clean filter, a lone CR), the hash is refused rather than approximated: the audit says
   it could not run honestly instead of reporting a number it cannot vouch for.

A ``.gitattributes`` that starts with a UTF-8 BOM is *not* stripped here: git does not
strip it either, which is how the first rule in ``98fea4f`` became decorative while
looking present. It is reported as a warning instead (D9).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import gitcmd

__all__ = [
    "Attributes",
    "DEAD_RULE_WARNING",
    "NormalizationError",
    "attributes_for",
    "content_hash",
    "hash_of",
    "normalize_bytes",
]

BINARY_SNIFF_BYTES = 8000
BOM = b"\xef\xbb\xbf"
DEAD_RULE_WARNING = (
    "a .gitattributes file starts with a UTF-8 BOM, which git does not strip, "
    "so its first rule does not match"
)


class NormalizationError(RuntimeError):
    """keel cannot prove that the bytes it hashed are the bytes git would store."""


@dataclass
class Attributes:
    """The attribute values that decide whether line endings are normalized."""

    text: str | None = None  # "true" | "false" | "auto" | None (unspecified)
    warnings: list[str] = field(default_factory=list)


# --- .gitattributes -----------------------------------------------------------


def _pattern_to_regex(pattern: str) -> re.Pattern | None:
    """Translate one .gitattributes pattern to a regex over a base-relative path.

    The subset git uses: ``*`` (not across ``/``), ``**`` (across), ``?``, a leading ``/``
    anchoring to the attributes file's directory, and -- for a pattern with no slash -- a
    match against the basename at any depth. A trailing-space pattern is left alone; git's
    quoting rules are not reproduced and an unparsable pattern matches nothing.
    """
    if not pattern or "\\" in pattern:
        return None
    anchored = pattern.startswith("/")
    body_src = pattern[1:] if anchored else pattern
    has_slash = "/" in body_src
    out: list[str] = []
    i = 0
    while i < len(body_src):
        char = body_src[i]
        if char == "*":
            if body_src.startswith("**", i):
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
        elif char == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(char))
        i += 1
    body = "".join(out)
    prefix = "" if (anchored or has_slash) else "(?:.*/)?"
    try:
        return re.compile(prefix + body + r"\Z")
    except re.error:  # pragma: no cover - escape() cannot produce this
        return None


def _sources(repo: Path, relpath: str) -> list[tuple[Path, Path]]:
    """(attributes file, the directory it anchors to), highest precedence first.

    Git's order: ``$GIT_DIR/info/attributes``, then ``.gitattributes`` in the file's own
    directory and walking up to the repository root.
    """
    rel = Path(relpath)
    found: list[tuple[Path, Path]] = []
    parts = list(rel.parent.parts)
    while parts:
        base = Path(*parts)
        found.append((repo / base / ".gitattributes", base))
        parts.pop()
    found.append((repo / ".gitattributes", Path()))
    found.append((repo / ".git" / "info" / "attributes", Path()))
    return found


def _parse_token(token: str) -> tuple[str, str] | None:
    if token.startswith("-"):
        return token[1:].lower(), "false"
    if token.startswith("!"):
        return token[1:].lower(), "unspecified"
    if "=" in token:
        key, value = token.split("=", 1)
        return key.strip().lower(), value.strip().lower()
    return token.strip().lower(), "true"


def attributes_for(repo: Path | str, relpath: str) -> Attributes:
    """Resolve ``text`` for ``relpath`` the way git would, plus any dead-rule warning."""
    repo = Path(repo)
    result = Attributes()
    for attr_file, base in _sources(repo, relpath):
        if not attr_file.is_file():
            continue
        raw = attr_file.read_bytes()
        if raw.startswith(BOM) and DEAD_RULE_WARNING not in result.warnings:
            result.warnings.append(f"{attr_file}: {DEAD_RULE_WARNING}")
        text = raw.decode("utf-8", errors="replace")
        try:
            rel_to_base = str(Path(relpath).relative_to(base)) if str(base) != "." else relpath
        except ValueError:
            continue
        for line in reversed(text.splitlines()):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            fields = line.split()
            if len(fields) < 2:
                continue
            regex = _pattern_to_regex(fields[0])
            if regex is None or not regex.match(rel_to_base):
                continue
            for token in fields[1:]:
                parsed = _parse_token(token)
                if parsed is None:
                    continue
                key, value = parsed
                if key == "binary":
                    # git's macro: -diff -merge -text
                    if result.text is None:
                        result.text = "false"
                    continue
                if key == "text" and result.text is None and value != "unspecified":
                    result.text = value
            break  # the last matching line in this file wins, and we walk backwards
    return result


# --- normalization ------------------------------------------------------------


def _is_binary(data: bytes) -> bool:
    """Git's own test: a NUL byte in the first 8000 bytes."""
    return b"\0" in data[:BINARY_SNIFF_BYTES]


def normalize_bytes(data: bytes, *, text: str | None, autocrlf: str | None) -> bytes:
    """The content git would store for a worktree file with these bytes.

    Only the direction that matters for hashing is implemented: the checkin (clean)
    conversion, ``CRLF -> LF``. The checkout direction is what ``eol=`` controls and it
    cannot change what is stored.
    """
    if text == "false":
        return data
    if text == "true":
        return data.replace(b"\r\n", b"\n")
    if text == "auto":
        return data if _is_binary(data) else data.replace(b"\r\n", b"\n")
    # No attribute: git falls back to core.autocrlf for files it detects as text.
    if autocrlf in ("true", "input") and not _is_binary(data):
        return data.replace(b"\r\n", b"\n")
    return data


def hash_of(data: bytes, algorithm: str = "sha256") -> str:
    """The recorded form: ``sha256:<64 hex>`` over git-normalized content (D8 A1)."""
    return f"{algorithm}:" + hashlib.new(algorithm, data).hexdigest()


def _git_blob_id(data: bytes, algorithm: str) -> str:
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.new(algorithm, header + data).hexdigest()


def content_hash(repo: Path | str, relpath: str) -> tuple[str, list[str]]:
    """The gate hash of ``relpath``: git-normalized, verified against git.

    Returns (``sha256:<hex>``, warnings). Raises :class:`NormalizationError` when git's own
    object id for the path disagrees with this module's reading, rather than returning a
    hash that might not be the content git stores.
    """
    repo = Path(repo)
    path = repo / relpath
    if not path.is_file():
        raise FileNotFoundError(relpath)
    data = path.read_bytes()
    attributes = attributes_for(repo, relpath)
    normalized = normalize_bytes(
        data, text=attributes.text, autocrlf=gitcmd.autocrlf(repo)
    )
    algorithm = gitcmd.object_format(repo)
    try:
        git_id = gitcmd.hash_object(repo, relpath)
    except gitcmd.GitError as exc:
        raise NormalizationError(f"git hash-object failed for {relpath}: {exc}") from exc
    ours = _git_blob_id(normalized, algorithm)
    if git_id != ours:
        raise NormalizationError(
            f"{relpath}: this module reads the file as {ours[:12]}..., git stores it as "
            f"{git_id[:12]}... (attributes, a clean filter, or a line ending git handles "
            "differently); refusing to hash content it cannot vouch for"
        )
    return hash_of(normalized), attributes.warnings
