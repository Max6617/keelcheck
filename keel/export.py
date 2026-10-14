"""The reviewer's export and its manifest (R4; design sections 2 and 7).

The reviewer must not be able to read the history, so it is not pointed at the repository: it is
pointed at a `.git`-less copy of the current state, with the frozen original, the mechanical
findings and one fixed prompt beside it. That makes clean context a property of the reviewer's
*reach* rather than a promise about its input (W2).

One function builds the manifest -- :func:`build_manifest` -- and **both sides call it**: the review
copies the files it lists, and the audit recomputes it to decide whether a recorded review still
covers the current state. Two code paths over the deny-list, the cap or the symlink policy would make
every review permanently stale, a false red that re-running cannot clear (Proctor, design item 9).
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from . import gitcmd

__all__ = [
    "DENIED",
    "MAX_BYTES",
    "MAX_FILES",
    "MANIFEST_NAME",
    "MANIFEST_KIND",
    "build_manifest",
    "deny_reason",
    "manifest_sha256",
    "write_export",
]

MANIFEST_KIND = "review/manifest/1"
MANIFEST_NAME = "KEEL-MANIFEST.json"
GENERATED = ("REVIEW-PROMPT.md", "FROZEN-ORIGINAL.md", "MECHANICAL-FINDINGS.txt")

#: Bound on what is handed to a third party, and on what this tool spends hashing it.
MAX_FILES = 2000
MAX_BYTES = 20 * 1024 * 1024

#: Names and shapes that never leave the repository, whatever the manifest would say otherwise.
DENIED = {
    "names": {".env", ".netrc", "credentials", "id_rsa", "id_ed25519"},
    "suffixes": (".pem", ".key", ".pfx", ".p12", ".keystore"),
    "prefixes": (".env.",),
    "dirs": {".ssh", ".aws", ".gnupg", ".git"},
}

#: The record directory, denied **by role** and not only by where this run put it. A repository
#: whose record is committed under `.keel/` and audited with `--record` elsewhere would otherwise
#: hand the reviewer prior audits, prior review verdicts and the history it exists to be denied
#: (Gilbert's finding, 2026-10-14). The active record root is excluded as well, because a record may
#: legitimately live somewhere else.
RECORD_SEGMENTS = {".keel"}


def deny_reason(rel: str) -> str | None:
    """Why this path must not be exported, or None when it may be."""
    name = rel.rsplit("/", 1)[-1]
    parts = rel.split("/")
    if RECORD_SEGMENTS.intersection(parts):
        return "denied: record directory (the reviewer is not given prior runs)"
    if name in DENIED["names"] or name.startswith(DENIED["prefixes"]):
        return "denied: credential name"
    if name.lower().endswith(DENIED["suffixes"]):
        return "denied: key material"
    if DENIED["dirs"].intersection(parts[:-1]) or name in DENIED["dirs"]:
        return "denied: secret directory"
    return None


def _repo_paths(repo: Path) -> tuple[list[str], list[str]]:
    """(tracked, untracked-but-not-ignored) repo-relative paths, from git -- never a walk."""
    tracked: list[str] = []
    listing = gitcmd.run(repo, "ls-files", "-z", check=False)
    if listing.returncode == 0:
        tracked = [p for p in listing.stdout.split("\0") if p]
    untracked: list[str] = []
    status = gitcmd.run(repo, "status", "--porcelain", "-z", check=False)
    if status.returncode == 0:
        for chunk in status.stdout.split("\0"):
            if chunk.startswith("?? "):
                untracked.append(chunk[3:])
    return tracked, untracked


def always_paths(audit) -> list[str]:
    """Paths the reviewer must always get: the anchor, the locked artefacts, named mechanisms.

    Nothing here depends on a finding, so the set is the same on both sides of the comparison and
    the manifest cannot disagree with itself (R4, design item 8).
    """
    assert audit.charter is not None
    found: list[str] = [audit.charter_path.name if audit.charter_path else "CHARTER.md"]
    for row in audit.charter.gates:
        if row.path:
            found.append(row.path)
    from .charter import named_repo_paths  # local: charter imports nothing from here

    for requirement in audit.charter.requirements:
        found.extend(named_repo_paths(requirement.enforced_by))
    return [p for p in dict.fromkeys(found) if p]


def select_paths(audit) -> dict:
    """The file set both sides agree on: under the record root excluded, deny-list applied, capped.

    Tracked files plus untracked-and-not-ignored ones -- the current state -- never a filesystem
    walk, never `.git`, never `.keel` (the record directory, denied by role), never the active
    record root (which is where the export itself is written), and never a denied name. The cap may
    not hide a file an artefact names (design item 8).
    """
    repo = audit.repo
    # The active record root is excluded only when it is *inside* the repository. A record path that
    # resolves above the repo must not exclude the whole repo -- that produced an empty manifest and a
    # "clean" review of nothing (found by Mason's own probe, 2026-10-14). `.keel` is denied by role
    # anyway, so a committed record is never exported whatever --record says.
    chosen_root = audit.record_path.parent.resolve()
    repo_root = repo.resolve()
    excluded_root = chosen_root if (chosen_root != repo_root and repo_root in chosen_root.parents) else None
    tracked, untracked = _repo_paths(repo)
    always = set(always_paths(audit))
    skipped: list[dict] = []
    candidates: list[tuple[str, bool]] = []
    for rel, is_tracked in [(p, True) for p in tracked] + [(p, False) for p in untracked]:
        rel = rel.replace("\\", "/")
        target = (repo / rel).resolve()
        if excluded_root is not None and (excluded_root in target.parents or target == excluded_root):
            continue
        reason = deny_reason(rel)
        if reason:
            skipped.append({"path": rel, "reason": reason})
            continue
        candidates.append((rel, is_tracked))

    ordered = sorted(candidates, key=lambda item: (item[0] not in always, item[0]))
    chosen: list[tuple[str, bool]] = []
    total = 0
    truncated = False
    for rel, is_tracked in ordered:
        size = 0
        try:
            size = (repo / rel).stat().st_size
        except OSError:
            skipped.append({"path": rel, "reason": "unreadable"})
            continue
        if rel not in always and (len(chosen) >= MAX_FILES or total + size > MAX_BYTES):
            truncated = True
            skipped.append({"path": rel, "reason": "over the cap"})
            continue
        chosen.append((rel, is_tracked))
        total += size
    return {"paths": chosen, "skipped": skipped, "truncated": truncated, "always": sorted(always)}


def manifest_sha256(files: list[dict]) -> str:
    """The state's identity: canonical JSON of the file list, sorted, hashes and sizes only."""
    canonical = json.dumps(
        sorted(files, key=lambda f: f["path"]),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_manifest(audit) -> dict:
    """The manifest of the current state. Called by the review *and* by the audit (item 9)."""
    selection = select_paths(audit)
    files: list[dict] = []
    skipped = list(selection["skipped"])
    for rel, is_tracked in selection["paths"]:
        source = audit.repo / rel
        if source.is_symlink():
            skipped.append({"path": rel, "reason": "symlink: never followed out of the export"})
            continue
        try:
            data = source.read_bytes()
        except OSError as exc:
            skipped.append({"path": rel, "reason": f"unreadable: {exc}"})
            continue
        files.append(
            {
                "path": rel,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "tracked": is_tracked,
            }
        )
    files.sort(key=lambda f: f["path"])
    return {
        "keel": MANIFEST_KIND,
        "files": files,
        "skipped": skipped,
        "truncated": selection["truncated"],
        "always": selection["always"],
        "count": len(files),
        "bytes": sum(f["bytes"] for f in files),
        "manifest_sha256": manifest_sha256(files),
    }


def write_export(
    audit,
    manifest: dict,
    export_root: Path,
    *,
    prompt_text: str,
    frozen_original: str,
    findings: str,
) -> Path:
    """Write the reviewer's directory: the tree, one prompt, the anchor, the mechanical findings.

    The reviewer runs with this tree as its cwd, so every path it can cite is one it was given, and
    the manifest is inside it as well: the reviewer can see exactly what it holds.
    """
    tree = Path(export_root) / "tree"
    if tree.exists():
        shutil.rmtree(tree, ignore_errors=True)
    tree.mkdir(parents=True, exist_ok=True)
    for entry in manifest["files"]:
        source = audit.repo / entry["path"]
        target = tree / entry["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    (tree / "REVIEW-PROMPT.md").write_text(prompt_text, encoding="utf-8", newline="\n")
    (tree / "FROZEN-ORIGINAL.md").write_text(
        frozen_original + "\n", encoding="utf-8", newline="\n"
    )
    (tree / "MECHANICAL-FINDINGS.txt").write_text(findings + "\n", encoding="utf-8", newline="\n")
    (tree / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    return tree
