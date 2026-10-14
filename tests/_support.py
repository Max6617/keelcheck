"""Shared builders for the tests. Not product code, not collected by pytest.

**D3 says the tests use only the CLI observables, never `keel/` internals.** This file exists so the
few things that are *not* yet ruled live in exactly one place: see ``ASSUMPTIONS`` below. When
Gilbert rules them, this is the only file that changes.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

#: keel/tests/_support.py -> keel/tests -> keel/ -> workspace/
REPO = Path(__file__).resolve().parents[1]
WORKSPACE = REPO.parent
KEEL_CHARTER = REPO / "CHARTER.md"

#: The demonstration input. `rentguard/CHARTER.md` is D4's read-only evidence and lives outside this
#: repository, so the suite cannot read it in a clone: the byte-identical snapshot below is what the
#: pins use, and a test fails if the live file ever drifts from it. Source: `rentguard@a72e7c4`,
#: working tree clean at `rentguard@310f449` (CHARTER.md unchanged since a72e7c4).
RENTGUARD_CHARTER = REPO / "tests" / "_artefacts" / "rentguard-CHARTER-a72e7c4.md"
RENTGUARD_CHARTER_LIVE = WORKSPACE / "rentguard" / "CHARTER.md"

FROZEN_SENTINEL = "FROZEN-ORIGINAL-SENTINEL"

#: Things D1/D3 leave open, assumed here and flagged to Gilbert. One edit to this file changes every
#: test when they are ruled.
#:   A1  a gate is declared in the charter as  | gate | path | hash |  under a `## Gates` heading.
#:   A2  the ratification commit is named in the charter's living state as
#:       "Ratified at: `<sha>`"; the reference hash is read with `git show <sha>:CHARTER.md` (D1).
#:   A3  `keel audit <repo>` writes `.keel/runs.jsonl` (append-only) and `.keel/review-context.json`.
ASSUMPTIONS = ("A1 gates table", "A2 ratification commit line", "A3 record paths")


def write(path: Path, text: str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def charter_text(*, frozen: str = FROZEN_SENTINEL, requirements=(), gates=(),
                 ratified: str | None = None, omit_sections=()) -> str:
    """A complete charter: all six required sections, so a baseline has no other divergence.

    requirement tuples: (id, text, enforced_by, checked_by, state)
    gate tuples:        (name, path, hash)
    """
    req_rows = "\n".join("| {} | {} | {} | {} | {} |".format(*r) for r in requirements)
    parts = ["# Charter — demo", "", "## The frozen original", "", f"> {frozen}", ""]
    if ratified is not None:
        parts += [f"Ratified at: `{ratified}`", ""]
    parts += [
        "## What it is for", "the demo purpose", "",
        "## What it is good at", "the demo strength", "",
        "## Problems the human and the agent agreed on", "the demo problem", "",
        "## Requirements", "",
        "Every requirement names its mechanism or is a wish.", "",
        "| # | requirement | enforced-by | checked-by | state |",
        "|---|---|---|---|---|",
        req_rows,
        "",
        "## Permissions", "none", "",
        "## Scopes", "project", "",
    ]
    if gates:
        gate_rows = "\n".join("| {} | {} | {} |".format(*g) for g in gates)
        parts += ["## Gates", "", "| gate | path | hash |", "|---|---|---|", gate_rows, ""]
    text = "\n".join(parts) + "\n"
    for section in omit_sections:
        text = _drop_section(text, section)
    return text


def _drop_section(text: str, heading_fragment: str) -> str:
    lines = text.splitlines()
    kept: list[str] = []
    dropping = False
    for line in lines:
        if line.startswith("## "):
            dropping = heading_fragment.lower() in line.lower()
        if not dropping:
            kept.append(line)
    return "\n".join(kept) + "\n"


def write_charter(root, **kwargs) -> Path:
    return write(Path(root) / "CHARTER.md", charter_text(**kwargs))


def hash_bytes(data: bytes) -> str:
    """The content hash a charter records for a gate script.

    **Normalized, not raw (D9).** The host sets ``core.autocrlf=true``, so a fresh checkout on Windows
    writes CRLF into the worktree while the blob — and therefore any ratified hash read back through
    git — is LF. A hash over raw worktree bytes would report a divergence that is not one, on every
    Windows checkout, in exactly the rule the tool exists for. Git's own text normalization is
    CRLF -> LF; this is that, and it is the same value ``git hash-object --path=`` returns.
    """
    return "sha256:" + hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def hash_file(path: Path) -> str:
    return hash_bytes(Path(path).read_bytes())


# --- git ----------------------------------------------------------------------


def git(root, *args) -> subprocess.CompletedProcess:
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, env=env)


def init_repo(root, *, commit: bool = True) -> str:
    """Make ``root`` a git repository with everything committed; returns HEAD's sha."""
    git(root, "init", "-q")
    git(root, "config", "user.name", "t")
    git(root, "config", "user.email", "t@example.invalid")
    if not commit:
        return ""
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "charter")
    return git(root, "rev-parse", "HEAD").stdout.strip()


def commit_all(root, message: str) -> str:
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)
    return git(root, "rev-parse", "HEAD").stdout.strip()


# --- the audit CLI ------------------------------------------------------------


def audit(root, *extra, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Run `python -m keel audit <root>` the way a user would, capturing both streams as UTF-8."""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", **(env_extra or {})}
    return subprocess.run(
        [sys.executable, "-m", "keel", "audit", str(root), *extra],
        cwd=REPO, capture_output=True, text=True, encoding="utf-8", env=env,
    )


def combined(proc: subprocess.CompletedProcess) -> str:
    return (proc.stdout or "") + (proc.stderr or "")


# --- the parser CLI -----------------------------------------------------------


def charter_cli(path, *, json_out: bool = True, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Run `python -m keel.charter <path>` the way a user would (R1's own surface, no internals)."""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", **(env_extra or {})}
    args = [sys.executable, "-m", "keel.charter", str(path)] + (["--json"] if json_out else [])
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True, encoding="utf-8", env=env)
