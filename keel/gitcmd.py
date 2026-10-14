"""The git plumbing keel depends on (D1, D9).

Git is not a convenience here, it is the reference side: the ratified gate table is read
with ``git show <sha>:CHARTER.md`` (D1) and every content hash is verified against
``git hash-object`` so that the bytes hashed are the bytes git would store (D9).

Read-only on purpose: nothing in this module writes to the object database, the index or
the worktree. The only write keel makes anywhere is the run record, and that is a plain
file (see :mod:`keel.record`).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

__all__ = [
    "GitError",
    "autocrlf",
    "hash_object",
    "head",
    "is_ancestor",
    "is_repo",
    "object_format",
    "run",
    "show",
]


class GitError(RuntimeError):
    """A git command the audit cannot do without returned non-zero."""


def run(repo: Path | str, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run ``git -C <repo> <args>``, capturing both streams as UTF-8."""
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip() or f"exit {proc.returncode}"
        raise GitError(f"git {' '.join(args)}: {detail}")
    return proc


def is_repo(repo: Path | str) -> bool:
    return run(repo, "rev-parse", "--git-dir", check=False).returncode == 0


def head(repo: Path | str) -> str:
    """The commit the audit measures against."""
    return run(repo, "rev-parse", "HEAD").stdout.strip()


def is_ancestor(repo: Path | str, sha: str) -> bool:
    return run(repo, "merge-base", "--is-ancestor", sha, "HEAD", check=False).returncode == 0


def show(repo: Path | str, sha: str, path: str) -> str | None:
    """The bytes of ``path`` at ``sha`` as text, or None when that revision has no such file."""
    proc = run(repo, "show", f"{sha}:{path}", check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout


def object_format(repo: Path | str) -> str:
    """``sha1`` or ``sha256`` -- what ``git hash-object`` prints."""
    proc = run(repo, "rev-parse", "--show-object-format", check=False)
    value = proc.stdout.strip()
    return value if value in ("sha1", "sha256") else "sha1"


def autocrlf(repo: Path | str) -> str | None:
    """The effective ``core.autocrlf`` for this repository, or None when unset.

    The host's system config sets ``true`` (measured, D9), which is the reason a raw
    worktree byte comparison reports a false divergence on every Windows checkout.
    """
    proc = run(repo, "config", "--get", "core.autocrlf", check=False)
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip().lower()
    return value or None


def hash_object(repo: Path | str, relpath: str) -> str:
    """``git hash-object`` of ``relpath``, with git's own filters (CRLF, clean) applied.

    This is the arbiter the Python normalization is checked against: the object id a repo
    would store, computed by git rather than by our reading of its rules.
    """
    return run(repo, "hash-object", "--", relpath).stdout.strip()
