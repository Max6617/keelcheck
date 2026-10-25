"""Shared builders for the tests. Not product code, not collected by pytest.

**D3 says the tests use only the CLI observables, never `keelcheck/` internals.** This file exists so the
few things that are *not* yet ruled live in exactly one place: see ``ASSUMPTIONS`` below. When
The maintainer rules them, this is the only file that changes.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

#: keel/tests/_support.py -> keel/tests -> keel/ (the checkout, which keeps its name) -> workspace/
REPO = Path(__file__).resolve().parents[1]
WORKSPACE = REPO.parent
KEELCHECK_CHARTER = REPO / "CHARTER.md"

#: The demonstration input. `rentguard/CHARTER.md` is D4's read-only evidence and lives outside this
#: repository, so the suite cannot read it in a clone: the byte-identical snapshot below is what the
#: pins use, and a test fails if the live file ever drifts from it. It was taken from a clean
#: working tree at a pinned revision, and the live CHARTER.md had not changed since then.
RENTGUARD_CHARTER = REPO / "tests" / "_artefacts" / "rentguard-CHARTER-a72e7c4.md"
RENTGUARD_CHARTER_LIVE = WORKSPACE / "rentguard" / "CHARTER.md"

FROZEN_SENTINEL = "FROZEN-ORIGINAL-SENTINEL"

#: The shapes D1/D3 left open; ruled by D8 and kept in one place so a change moves every test at once.
#:   A1  a gate is declared in the charter as  | gate | path | hash |  under a `## Gates` heading.
#:   A2  the ratification commit is named in the charter's living state as
#:       "Ratified at: `<sha>`", and again as the record's first line; the audit exits 1 if the two
#:       disagree. The reference block is read with `git show <sha>:CHARTER.md` (D1, D8).
#:   A3  `keelcheck audit <repo>` writes `.keel/runs.jsonl` (append-only) and `.keel/review-context.json`;
#:       `--record <path>` moves the record (needed because D4 keeps rentguard/ read-only).
ASSUMPTIONS = ("A1 gates table", "A2 ratification pointer, named twice", "A3 record paths")


def write(path: Path, text: str) -> Path:
    """Write fixture bytes as **LF**, whatever the host's text-mode default is.

    `Path.write_text` translates `\\n` to `\\r\\n` on Windows, so every fixture file used to be CRLF in
    the worktree while git stored whatever was committed — which is exactly the class D9 exists for,
    and it produced a false red in the manifest test (a CRLF blob committed under `autocrlf=false`
    genuinely differs from the LF a later checkout materialises). Fixtures write the bytes a checkout
    of them would have.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def charter_text(*, frozen: str = FROZEN_SENTINEL, requirements=(), gates=(),
                 ratified: str | None = None, omit_sections=(), review_required: bool = False) -> str:
    """A complete charter: all six required sections, so a baseline has no other divergence.

    requirement tuples: (id, text, enforced_by, checked_by, state)
    gate tuples:        (name, path, hash)

    **The ratification pointer goes in a `## Ratification` section at the end, never between the
    frozen heading and the next heading.** D11 (F9) makes the anchor the whole frozen *section*
    (heading to the next heading), so a pointer written inside that span would itself be anchored —
    and because the pointer is added *after* the ratification commit, every fixture would carry a
    spurious `[original]` divergence. That is the false signal this placement avoids; a real charter
    (`keel/CHARTER.md`) has the same shape.
    """
    req_rows = "\n".join("| {} | {} | {} | {} | {} |".format(*r) for r in requirements)
    parts = ["# Charter — demo", "", "## The frozen original", "", f"> {frozen}", ""]
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
        # D15: a `## Gates` row may carry a fourth column, `kind`, which defaults to `gate`. The
        # column is emitted only when a fixture uses it, so the three-column shape stays the default.
        wide = any(len(g) == 4 for g in gates)
        header = "| gate | path | hash | kind |" if wide else "| gate | path | hash |"
        rule = "|---|---|---|---|" if wide else "|---|---|---|"
        gate_rows = "\n".join("| " + " | ".join(str(x) for x in g) + " |" for g in gates)
        parts += ["## Gates", "", header, rule, gate_rows, ""]
    if ratified is not None:
        # D12: one canonical spelling, a plain line. Other spellings still parse, so a fixture that
        # used one would keep working and quietly stop testing the format.
        parts += ["## Ratification", "", f"Ratified at: {ratified}", ""]
    if review_required:
        # D15: the charter's own declaration that a missing review is divergence, canonical spelling.
        parts += ["## Review", "", "Review: required", ""]
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
    """Run `python -m keelcheck audit <root>` the way a user would, capturing both streams as UTF-8."""
    return keelcheck("audit", str(root), *extra, env_extra=env_extra)


def keelcheck(*args, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Run any `python -m keelcheck ...` command the way a user would, with UTF-8 stdio pinned."""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", **(env_extra or {})}
    return subprocess.run(
        [sys.executable, "-m", "keelcheck", *args],
        cwd=REPO, capture_output=True, text=True, encoding="utf-8", env=env,
    )


def combined(proc: subprocess.CompletedProcess) -> str:
    return (proc.stdout or "") + (proc.stderr or "")


# --- the parser CLI -----------------------------------------------------------


def charter_cli(path, *, json_out: bool = True, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Run `python -m keelcheck.charter <path>` the way a user would (R1's own surface, no internals)."""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", **(env_extra or {})}
    args = [sys.executable, "-m", "keelcheck.charter", str(path)] + (["--json"] if json_out else [])
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True, encoding="utf-8", env=env)
