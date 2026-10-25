"""The git plumbing keelcheck depends on (D1, D9).

Git is not a convenience here, it is the reference side: the ratified gate table is read
with ``git show <sha>:CHARTER.md`` (D1) and every content hash is verified against
``git hash-object`` so that the bytes hashed are the bytes git would store (D9).

Read-only on purpose: nothing in this module writes to the object database, the index or
the worktree. The only write keelcheck makes anywhere is the run record, and that is a plain
file (see :mod:`keelcheck.record`).

**Every read can be bounded** (`gitcmd.deadline`). `subprocess.run` with no timeout waits
forever on a `git` that never answers, and the surface that runs per tool call — the harness
adapter — must answer before the harness gives up on it, because the harnesses document a
timed-out *command* hook as one that does not block. The deadline is a context variable rather
than a parameter on every helper so that all of them share one budget per event, and an expired
budget raises :class:`GitTimeout` from the read itself rather than returning a partial answer.
"""

from __future__ import annotations

import contextlib
import contextvars
import subprocess
import time
from pathlib import Path

__all__ = [
    "GitError",
    "GitTimeout",
    "autocrlf",
    "deadline",
    "hash_object",
    "head",
    "is_ancestor",
    "is_repo",
    "object_format",
    "remaining",
    "run",
    "show",
]


class GitError(RuntimeError):
    """A git command the audit cannot do without returned non-zero."""


class GitTimeout(GitError):
    """A git read did not finish inside the caller's bound.

    Separate from :class:`GitError` only so a caller can say *which* happened: both end as a
    refusal at the adapter, but "git answered no" and "git never answered" are different facts
    about the repository and the record should carry the right one.
    """


#: `(a monotonic end, the bound it came from)` for the reads the *calling* thread starts, or None.
#: A ContextVar, not a parameter, so that a deadline set once by `adapter.decide` covers every
#: helper the decision calls — `head`, `show`, `is_ancestor`, `autocrlf`, `object_format` and
#: `hash_object` — without threading a new argument through all of them (and through the modules
#: that call them for their own reasons).
_DEADLINE: contextvars.ContextVar[float | None] = contextvars.ContextVar(
    "keelcheck_git_deadline", default=None
)


@contextlib.contextmanager
def deadline(seconds: float | None):
    """Bound every git read started inside this block by `seconds` from now (None = unbounded).

    One budget for the whole block, not one per call: a sequence of reads that together outlive the
    bound is a hang, and the point of the bound is the caller's wall clock.
    """
    token = _DEADLINE.set(None if seconds is None else time.monotonic() + seconds)
    try:
        yield
    finally:
        _DEADLINE.reset(token)


def remaining() -> float | None:
    """Seconds left of the caller's bound, or None when no bound is set."""
    end = _DEADLINE.get()
    return None if end is None else end - time.monotonic()


def _budget(args: tuple[str, ...]) -> float | None:
    """The timeout for one read, raising :class:`GitTimeout` when the bound has already run out."""
    left = remaining()
    if left is None:
        return None
    if left <= 0:
        raise GitTimeout(f"git {' '.join(args)} never started: the caller's bound had already expired")
    return left


def run(
    repo: Path | str, *args: str, check: bool = True, stdin: str | None = None
) -> subprocess.CompletedProcess:
    """Run ``git -C <repo> <args>``, capturing both streams as UTF-8.

    A read that outlives :func:`deadline` raises :class:`GitTimeout` rather than hanging, whatever
    `check` says: a timeout is not a non-zero exit and there is no honest `CompletedProcess` to
    return for a process that had to be killed.
    """
    budget = _budget(args)
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            input=stdin,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=budget,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitTimeout(
            f"git {' '.join(args)} did not finish within the caller's {budget:.3g}s bound"
        ) from exc
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


def hash_object_many(repo: Path | str, relpaths: list[str]) -> list[str]:
    """``git hash-object --stdin-paths``: git's own answer for a whole list, in one process.

    Measured on this host: the filters are applied exactly as for a single path (a CRLF file and
    its LF twin hash alike), so a manifest of any size can be verified in bulk instead of one
    subprocess per file.
    """
    if not relpaths:
        return []
    listing = run(repo, "hash-object", "--stdin-paths", stdin="\n".join(relpaths) + "\n")
    return [line.strip() for line in listing.stdout.splitlines() if line.strip()]


def blob_bytes(repo: Path | str, rev: str, path: str) -> bytes | None:
    """The bytes of ``path`` at ``rev``, or None when that revision has no such blob.

    The prompt is hashed from its blob at the anchor, not from the worktree: a working-tree edit of
    both the file and its row cannot re-ratify itself.
    Bounded like every other read here -- this one takes bytes rather than text, so it cannot go
    through :func:`run`, and a bound that missed it would be a bound with a hole in it.
    """
    budget = _budget(("cat-file", "blob", f"{rev}:{path}"))
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "blob", f"{rev}:{path}"],
            capture_output=True,
            timeout=budget,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitTimeout(
            f"git cat-file blob {rev}:{path} did not finish within the caller's {budget:.3g}s bound"
        ) from exc
    if proc.returncode != 0:
        return None
    return proc.stdout
