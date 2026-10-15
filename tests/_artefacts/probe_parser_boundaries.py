"""Probe the R1 parser and the hash rule from outside, through `python -m keelcheck.charter` and `git`.

Artefact of measurement, not a test. Three families (Gilbert, 2026-10-14):

  A. a wish a naive parser swallows silently
  B. a `checked-by` cell that is an empty string rather than an absent cell
  C. a gate hash over a file whose worktree line endings differ

Nothing here imports `keelcheck/`; every answer is read off the CLI, the same surface an audit would use.

`git clone` cannot run under this sandbox (msys fails to create its named objects), so the fresh
checkout is reproduced with `checkout-index`, which applies the same smudge filter a clone would.

Run from anywhere:  python tests/_artefacts/probe_parser_boundaries.py
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]  # keelcheck/
ROOT = REPO.parent / ".assay-tmp" / "parser-boundaries"

GIT_ENV = {
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
}

HEADER = "| # | requirement | enforced-by | checked-by | state |"


def charter(rows: list[str], header: str = HEADER) -> str:
    return (
        "# Charter - probe\n\n## The frozen original\n\n> probe\n\n"
        "## What it is for\nx\n\n## What it is good at\nx\n\n"
        "## Problems the human and the agent agreed on\nx\n\n"
        "## Requirements\n\n" + header + "\n|---|---|---|---|---|\n"
        + "\n".join(rows)
        + "\n\n## Permissions\nnone\n\n## Scopes\nproject\n"
    )


def run_parser(path: Path, json_out: bool = True) -> subprocess.CompletedProcess:
    args = [sys.executable, "-m", "keelcheck.charter", str(path)] + (["--json"] if json_out else [])
    return subprocess.run(
        args, cwd=REPO, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


def probe(name: str, text: str, marker: str) -> str:
    path = ROOT / f"{name}.md"
    path.write_text(text, encoding="utf-8")
    proc = run_parser(path)
    render = run_parser(path, json_out=False)
    try:
        doc = json.loads(proc.stdout)
    except Exception:  # noqa: BLE001 - a non-charter answer is a result too
        return f"{name:<26} exit={proc.returncode} not-a-charter: {proc.stdout.strip()[:80]}"
    return (
        f"{name:<26} exit={proc.returncode} reqs={len(doc['requirements'])} "
        f"wishes={doc['wishes']} asserted={doc['asserted_enforcement']} "
        f"in-json={marker in proc.stdout} in-report={marker in render.stdout}"
    )


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          env={**os.environ, **GIT_ENV})


def fresh_checkout(src: Path, dst: Path, autocrlf: str) -> None:
    """Reproduce a fresh `git clone` checkout without the sandboxed msys transport."""
    if dst.exists():
        shutil.rmtree(dst, ignore_errors=True)
    dst.mkdir(parents=True)
    git(src, "--work-tree", str(dst), "-c", f"core.autocrlf={autocrlf}", "checkout-index", "-a", "-f")


def make_repo(name: str, gate_bytes: bytes, *, attributes: str | None,
              autocrlf: str) -> tuple[Path, str]:
    repo = ROOT / name
    if repo.exists():
        shutil.rmtree(repo, ignore_errors=True)
    repo.mkdir(parents=True)
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "t")
    git(repo, "config", "user.email", "t@example.invalid")
    git(repo, "config", "core.autocrlf", autocrlf)
    if attributes is not None:
        (repo / ".gitattributes").write_bytes(attributes.encode("ascii"))
    (repo / "tools").mkdir()
    (repo / "tools" / "gate.py").write_bytes(gate_bytes)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "gate")
    return repo, git(repo, "rev-parse", "HEAD:tools/gate.py").stdout.strip()


def cp(cwd: Path, *args: str) -> str:
    r = git(cwd, *args)
    return (r.stdout + r.stderr).strip()


def main() -> int:
    global ROOT
    ROOT.mkdir(parents=True, exist_ok=True)
    # a fresh run dir per process: a sandboxed dir cannot always be removed, so never reuse one
    ROOT = ROOT / f"run-{os.getpid()}"
    ROOT.mkdir(parents=True, exist_ok=True)
    head = git(REPO, "rev-parse", "--short", "HEAD").stdout.strip()
    print(f"# parser and hash boundaries - keelcheck@{head}")
    print(f"# python {sys.version.split()[0]}; {cp(REPO, '--version')}")
    print(f"# host core.autocrlf = {cp(REPO, 'config', '--get', 'core.autocrlf') or '(unset)'}\n")

    print("## A. a wish a naive parser swallows silently\n")
    print(probe("A1-empty-id-row",
                charter(["|  | the pod must stop itself | \u2014 | \u2014 | draft |"]),
                "the pod must stop itself"))
    print(probe("A2-unknown-id-header",
                charter(["| R1 | the pod must stop itself | \u2014 | \u2014 | draft |"],
                        header="| Rule | requirement | enforced-by | checked-by | state |"),
                "the pod must stop itself"))
    print(probe("A3-check-only-sentence",
                charter(["| R9 | nothing is published | \u2014 | the user's word first | checked |"]),
                "the user's word first"))
    print(probe("A4-truncated-row",
                charter(["| R1 | the pod must stop itself | \u2014 |"]),
                "the pod must stop itself"))
    print(probe("A5-negative-space",
                charter(["| R1 | the pod must stop itself | \u2014 | \u200b | met |"]),
                "the pod must stop itself"))
    print()

    print("## B. checked-by cells that are not the empty string but carry nothing\n")
    print(f"{'label':<22} {'cell repr':<16} is_wish  enforcement  in-report")
    for label, cell in [
        ("empty string", ""),
        ("single space", " "),
        ("tab", "\t"),
        ("em dash", "\u2014"),
        ("n/a", "n/a"),
        ("zero-width space", "\u200b"),
        ("word joiner", "\u2060"),
        ("BOM / ZWNBSP", "\ufeff"),
        ("non-breaking space", "\u00a0"),
        ("&nbsp; entity", "&nbsp;"),
        ("backticks only", "``"),
        ("asterisks only", "**"),
        ("quotes only", "\"\""),
        ("empty parens", "()"),
    ]:
        text = charter([f"| R1 | the pod must stop itself | \u2014 | {cell} | met |"])
        path = ROOT / "B.md"
        path.write_text(text, encoding="utf-8")
        proc = run_parser(path)
        render = run_parser(path, json_out=False)
        try:
            doc = json.loads(proc.stdout)
            r = doc["requirements"][0]
            in_report = bool(cell.strip()) and cell in render.stdout
            print(f"{label:<22} {cell!r:<16} {str(r['is_wish']):<7}  {r['enforcement']:<12} {in_report}")
        except Exception:  # noqa: BLE001
            print(f"{label:<22} {cell!r:<16} exit={proc.returncode} {proc.stdout.strip()[:50]}")
    print()

    print("## C. a gate hash over a file whose worktree line endings differ\n")
    lf = b"print('gate')\n"
    crlf = b"print('gate')\r\n"
    h_lf, h_crlf = (hashlib.sha256(b).hexdigest() for b in (lf, crlf))
    print(f"raw sha256(LF bytes)   = {h_lf}")
    print(f"raw sha256(CRLF bytes) = {h_crlf}")
    print(f"raw hashes differ      = {h_lf != h_crlf}\n")

    for label, attrs, autocrlf in [
        ("repo with eol=lf rule", "* text=auto eol=lf\n", "true"),
        ("repo with no rule", None, "true"),
    ]:
        repo, blob = make_repo("gate-" + label.split()[-2].replace("=", ""), lf,
                               attributes=attrs, autocrlf=autocrlf)
        (repo / "tools" / "gate.py").write_bytes(crlf)  # same content, CRLF worktree
        wh = (repo / "tools" / "gate.py").read_bytes()
        with_path = cp(repo, "hash-object", "--path=tools/gate.py", "tools/gate.py")
        no_path = cp(repo, "hash-object", "tools/gate.py")
        status = cp(repo, "status", "--porcelain")
        diff = cp(repo, "diff", "--stat")
        print(f"### {label}  (.gitattributes={attrs!r}, core.autocrlf={autocrlf})")
        print(f"  worktree CRLF              = {wh.endswith(bytes([13,10]))}")
        print(f"  raw sha256(worktree)       = {hashlib.sha256(wh).hexdigest()}")
        print(f"  matches raw sha256(LF)     = {hashlib.sha256(wh).hexdigest() == h_lf}")
        print(f"  committed blob oid         = {blob}")
        print(f"  hash-object --path=...     = {with_path}  (== blob: {with_path == blob})")
        print(f"  hash-object (no --path)    = {no_path}  (== blob: {no_path == blob})")
        print(f"  git status --porcelain     = {status!r}")
        print(f"  git diff --stat            = {diff!r}")
        fresh = ROOT / (repo.name + "-checkout")
        fresh_checkout(repo, fresh, autocrlf)
        fbytes = (fresh / "tools" / "gate.py").read_bytes()
        # hash the fresh file through the source repo, so the repo's attributes and core.autocrlf apply
        fpath = cp(repo, "hash-object", "--path=tools/gate.py", str(fresh / "tools" / "gate.py"))
        print(f"  fresh checkout (autocrlf={autocrlf}) CRLF = {fbytes.endswith(bytes([13,10]))}  "
              f"raw sha256 == LF sha: {hashlib.sha256(fbytes).hexdigest() == h_lf}  "
              f"hash-object --path == blob: {fpath == blob}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
