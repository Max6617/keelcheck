"""The reviewer's export and its manifest (R4; design sections 2 and 7).

The reviewer must not be able to read the history, so it is not pointed at the repository: it is
pointed at a `.git`-less copy of the current state, with the frozen original, the mechanical
findings and one fixed prompt beside it. That makes clean context a property of the reviewer's
*reach* rather than a promise about its input (W2).

Four things this module has to get right, each of them a finding from an outside attack:

- **One manifest, one function, two sides.** :func:`build_manifest` is called by the review (to copy
  what it lists) *and* by the audit (to decide whether a recorded review still covers the current
  state). Two code paths over the deny-list, the cap or the symlink policy would make every review
  permanently stale.
- **The hashes are over git-normalized content** (D9). A manifest over raw worktree bytes gives one
  commit two identities across two checkouts, so a review recorded on one is reported stale on the
  other -- a false red that re-running cannot clear. `bytes` and `sha256` are both the *stored* size
  and hash, because both go into the manifest hash and a checkout-dependent field would move it.
  The whole manifest is then checked against ``git hash-object`` in one process.
- **The record is out of reach by identity, not by name.** The active record and context files are
  excluded wherever they live, a record-shaped file is excluded wherever it lives (its first line
  says what it is, which is what catches a *prior* record under another name or in another
  directory), and `.keel` stays denied by role as the base case.
- **A path an artefact names is never silently absent.** Nothing may be dropped without a reason in
  `skipped`: not by the cap, not by `.gitignore`, not by being missing. The manifest's job is to say
  what the reviewer did *not* get.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from . import gitcmd, normalize

__all__ = [
    "DENIED",
    "MAX_BYTES",
    "MAX_FILES",
    "MANIFEST_NAME",
    "MANIFEST_KIND",
    "always_paths",
    "build_manifest",
    "deny_reason",
    "is_keel_record",
    "manifest_sha256",
    "select_paths",
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

#: The record directory denied **by role**: a repository whose record is committed under `.keel/`
#: and audited with `--record` elsewhere would otherwise hand the reviewer prior audits and prior
#: review verdicts -- the history it exists to be denied.
RECORD_SEGMENTS = {".keel"}

#: What a keel record's first line says it is. A record under any other name or directory is still a
#: record, and "the record is out of reach" has to be true for every location the tool supports.
RECORD_MARKERS = ("keel/runs", "review-context/1")

#: The names a record has by default. A file with one of these names that cannot be identified by
#: content is exported and *named* in the manifest's `warnings` rather than excluded on a guess.
RECORD_NAMES = ("runs.jsonl", "review-context.json")


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


def is_keel_record(data: bytes) -> bool:
    """True when these bytes are a keel run record or a reviewer's context file, wherever they live."""
    first = data.split(b"\n", 1)[0].strip()
    if not first.startswith(b"{"):
        return False
    try:
        obj = json.loads(first.decode("utf-8", "replace"))
    except ValueError:
        return False
    if not isinstance(obj, dict):
        return False
    return obj.get("record") in RECORD_MARKERS or obj.get("keel") in RECORD_MARKERS


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
    """Paths the reviewer must always get, or be told about: the anchor, the locked artefacts, and
    every path a requirement, a row or a **finding** names (design item 8)."""
    assert audit.charter is not None
    from .charter import named_repo_paths  # local: charter imports nothing from here

    found: list[str] = [audit.charter_path.name if audit.charter_path else "CHARTER.md"]
    for row in audit.charter.gates:
        if row.path:
            found.append(row.path)
    for requirement in audit.charter.requirements:
        found.extend(named_repo_paths(requirement.enforced_by))
    for finding in audit.findings:
        found.extend(named_repo_paths(f"{finding.subject} {finding.message}"))
    return [p for p in dict.fromkeys(found) if p]


def select_paths(audit) -> dict:
    """The file set both sides agree on: what git lists, what the charter names, minus what must not
    leave, capped -- and every exclusion carries a reason.
    """
    repo = audit.repo
    repo_root = repo.resolve()
    tracked, untracked = _repo_paths(repo)
    known: dict[str, bool] = {p.replace("\\", "/"): True for p in tracked}
    known.update({p.replace("\\", "/"): False for p in untracked})
    always = always_paths(audit)
    skipped: list[dict] = []

    # Paths the charter names that git does not list at all: ignored, or absent. Neither may vanish
    # silently -- a gitignored gate path used to be in `always` and in neither `files` nor `skipped`.
    for rel in always:
        if rel in known:
            continue
        if (repo / rel).exists():
            skipped.append({"path": rel, "reason": "ignored by .gitignore (named by the charter)"})
        else:
            skipped.append({"path": rel, "reason": "named by the charter but not present"})

    # The record this run writes, and its context file, are excluded by identity wherever they are:
    # `--record <repo>/runs.jsonl` puts them in the tree, and an earlier version exported them.
    by_identity = set()
    for path in (audit.record_path, audit.review_context_path):
        try:
            by_identity.add(path.resolve())
        except OSError:  # pragma: no cover - unreadable path components
            continue

    candidates: list[tuple[str, bool]] = []
    for rel, is_tracked in known.items():
        try:
            target = (repo / rel).resolve()
        except OSError:  # pragma: no cover - unreadable path components
            continue
        if target in by_identity:
            skipped.append({"path": rel, "reason": "denied: the record this run writes"})
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
    _ = repo_root
    return {"paths": chosen, "skipped": skipped, "truncated": truncated, "always": always}


def manifest_sha256(files: list[dict]) -> str:
    """The state's identity: canonical JSON of the file list, sorted, hashes and sizes only.

    Every field in it is checkout-independent -- the sizes and hashes are the *stored* ones -- because
    a field that moves between checkouts moves the identity with it.
    """
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
    repo = audit.repo
    autocrlf = gitcmd.autocrlf(repo)
    algorithm = gitcmd.object_format(repo)
    files: list[dict] = []
    skipped = list(selection["skipped"])
    normalized: dict[str, bytes] = {}
    for rel, is_tracked in selection["paths"]:
        source = repo / rel
        if source.is_symlink():
            skipped.append({"path": rel, "reason": "symlink: never followed out of the export"})
            continue
        try:
            data = source.read_bytes()
        except OSError as exc:
            skipped.append({"path": rel, "reason": f"unreadable: {exc}"})
            continue
        if is_keel_record(data):
            skipped.append({"path": rel, "reason": "denied: a keel run record, wherever it lives"})
            continue
        stored = normalize.normalize_path(repo, rel, data, autocrlf=autocrlf)
        normalized[rel] = stored
        files.append(
            {
                "path": rel,
                "bytes": len(stored),
                "sha256": hashlib.sha256(stored).hexdigest(),
                "tracked": is_tracked,
            }
        )
    mismatch = normalize.verify_bulk(repo, normalized, autocrlf=autocrlf, algorithm=algorithm)
    if mismatch is not None:
        raise normalize.NormalizationError(mismatch)

    files.sort(key=lambda f: f["path"])
    exported = {f["path"] for f in files}
    explained = {entry["path"] for entry in skipped}
    for rel in selection["always"]:
        if rel not in exported and rel not in explained:
            skipped.append(
                {"path": rel, "reason": "named by the charter but neither exported nor explained"}
            )
    # The residual boundary, made loud rather than silent: a file *named* like a record that is not
    # this run's record and whose first line does not say what it is (an empty or truncated record)
    # cannot be identified by content, so it is exported and named here instead of being excluded on
    # a guess. A record with a first line is excluded above, wherever it lives.
    warnings = [
        {"path": entry["path"], "reason": f"a file named like a keel record ({RECORD_NAMES}): check "
                                          "whether the reviewer was handed prior runs"}
        for entry in files
        if entry["path"].rsplit("/", 1)[-1] in RECORD_NAMES
    ]
    return {
        "keel": MANIFEST_KIND,
        "files": files,
        "skipped": skipped,
        "warnings": warnings,
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
