"""The review command: start a reviewer with no history, and record what it was handed (R4).

This is the half that makes keel different from its neighbours, and it is deliberately small: the
reviewer is a **command the caller names**, run once with the export as its working directory and the
prompt on its stdin, and its answer is one JSON object that is validated mechanically before anything
is recorded. No model is needed to test any of it (a stub command is a complete test double), and no
model decides an exit code: a review that did not happen is a *missing record*, exactly like a
bypassed hook, and only the audit turns that into divergence -- and only when a review is required.

Exit codes:

    0   a review was recorded and its verdict was clean
    1   a review was recorded and its verdict was divergence, partial or unverified; or the
        ratified prompt's content no longer matches its hash (a weakened instruction is not a
        review)
    2   the review could not run honestly: no charter, no anchor, no prompt, the export could not
        be written, the record could not be written, or the reviewer failed, timed out, or did not
        return a usable object

The design is `research/drift-review-design.md`; the contract is D15.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
from pathlib import Path

from . import export, gitcmd, normalize, record
from .audit import Audit, AuditError, CHARTER_NAME, load_charter, load_reference, run_audit
from .charter import Charter, Gate
from .output import emit, emit_err

__all__ = ["main", "run_review", "validate_output"]

DEFAULT_TIMEOUT = 600.0
MAX_STDOUT = 1024 * 1024
CLASSES = ("missing", "unrequested", "shifted")
VERDICTS = ("clean", "divergence")


def prompt_row(charter: Charter) -> Gate | None:
    """The ratified prompt: a row of the gate table with ``kind: prompt`` (D15)."""
    for row in charter.gates:
        if row.kind == "prompt":
            return row
    return None


def split_command(command: str) -> list[str]:
    """The caller's command as argv. Not a shell: nothing here is expanded or interpreted.

    ``shlex`` in posix mode eats Windows path separators, and in non-posix mode it keeps the
    quoting characters, so the quotes are removed here after a non-posix split. The caller writes
    one string; keel never sees a shell.
    """
    if os.name == "nt":
        parts = shlex.split(command, posix=False)
        return [p[1:-1] if len(p) >= 2 and p[0] == p[-1] == '"' else p for p in parts]
    return shlex.split(command)


def _run_id(manifest: dict) -> str:
    """The export directory's name: the manifest it holds, and the process that wrote it.

    The manifest prefix makes the directory self-describing -- a record can never point at another
    review's tree, because the name says which state it holds, and that is the part Proctor pins
    inside a single review. The pid is what distinguishes two reviews of the same state started in
    the same second: they are separate processes, so a clock or a counter would not (Proctor's
    finding, landed as named hardening).
    """
    digest = str(manifest.get("manifest_sha256", "")).removeprefix("sha256:")[:12]
    return f"review-{digest or 'unknown'}-{os.getpid()}"


def _hash_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _anchored_prompt(
    owner_repo: Path, working: Charter, reference: Charter | None, label: str
) -> dict | None:
    """The prompt as **ratified at the anchor**, or None when that repository has no ratified prompt.

    Sift's finding, and Gilbert's ruling on it: reading the row from the working charter is a
    *self-consistency* check, so editing the prompt and its row together re-ratified the instruction
    in the working tree. Ratification is a property of the anchored revision, exactly like the gate
    table (D1, D12): the row comes from ``git show <anchor>:CHARTER.md`` and the instruction itself is
    the prompt's **blob at that commit**. The working tree must still agree; when it does not, the
    review refuses rather than handing over a weakened instruction.
    """
    if reference is None:
        return None
    ratified_row = prompt_row(reference)
    if ratified_row is None:
        return None
    if not ratified_row.path:
        return {"exit": 1, "error": "the ratified prompt row names no path"}
    if ratified_row.malformed_hash:
        return {
            "exit": 1,
            "error": f"the ratified prompt row's hash {ratified_row.hash!r} is not sha256:<64 hex>",
        }
    working_row = prompt_row(working)
    if (
        working_row is None
        or working_row.path != ratified_row.path
        or working_row.hash != ratified_row.hash
    ):
        return {
            "exit": 1,
            "error": (
                "rule 2 of the prompt check: the working charter's prompt row is not the ratified one "
                f"(working: {working_row.path + ' ' + working_row.hash if working_row else '(none)'}; "
                f"ratified: {ratified_row.path} {ratified_row.hash}); a working-tree edit of the table "
                "does not re-ratify an instruction (D1, D12, D15)"
            ),
        }
    anchor = working.ratified_at or ""
    blob = gitcmd.blob_bytes(owner_repo, anchor, ratified_row.path)
    if blob is None:
        return {
            "exit": 1,
            "error": (
                "rule 2 of the prompt check: the prompt "
                f"{ratified_row.path} does not exist at the anchor {anchor}"
            ),
        }
    digest = "sha256:" + hashlib.sha256(blob).hexdigest()
    if digest != ratified_row.hash:
        return {
            "exit": 1,
            "error": (
                "rule 2 of the prompt check: the prompt's blob at "
                f"{anchor} hashes {digest}, but the ratified row records {ratified_row.hash}; the row "
                "and the artefact at the anchor disagree (fix the row at the anchor)"
            ),
        }
    # Deliberately **not** checked here: whether the working-tree *file* still hashes to the ratified
    # row. The instruction handed over is the anchored blob, so a worktree edit cannot weaken it, and
    # the audit already reports that drift as `[gate]`. Gilbert's split: rule 1 is "no ratified row
    # anywhere plus --prompt", which runs and is recorded `prompt_ratified: false`; rule 2 is "a
    # ratified row exists and the artefact at the anchor disagrees", which refuses. Checking the
    # worktree file here made a fixture's checkout-configured line endings look like a weakened
    # instruction and blocked the manifest red behind a refusal.
    return {
        "text": blob.decode("utf-8", errors="replace"),
        "path": ratified_row.path,
        "hash": ratified_row.hash,
        "ratified": True,
        "ratified_in": label,
    }


def _resolve_prompt(
    repo: Path,
    working: Charter,
    reference: Charter | None,
    explicit: str | None,
    prompt_repo: str | None = None,
) -> dict:
    """The prompt text, its path, its hash, whether it is ratified, and where it was ratified.

    The audited repository's own ratified row wins. ``--prompt-repo`` is for an input whose charter
    cannot be edited -- rentguard is read-only evidence (D4) -- and its prompt is anchored in *that*
    repository the same way. ``--prompt`` is the last resort and is recorded unratified.
    """
    owned = _anchored_prompt(
        repo, working, reference, f"{repo.name}@{working.ratified_at or '?'}"
    )
    if owned is not None:
        return owned
    if prompt_repo:
        owner = Path(prompt_repo).resolve()
        try:
            _, owner_working = load_charter(owner)
        except AuditError as exc:
            return {"exit": 2, "error": f"--prompt-repo {owner}: {exc}"}
        owner_audit = Audit(
            repo=owner,
            charter_path=owner / CHARTER_NAME,
            record_path=owner / ".keel" / "runs.jsonl",
            review_context_path=owner / ".keel" / "review-context.json",
        )
        owner_audit.charter = owner_working
        try:
            owner_audit.commit = gitcmd.head(owner)
        except gitcmd.GitError as exc:
            return {"exit": 2, "error": f"--prompt-repo {owner}: git cannot name HEAD: {exc}"}
        owner_reference = load_reference(owner, owner_working, owner_audit)
        anchored = _anchored_prompt(
            owner,
            owner_working,
            owner_reference,
            f"{owner.name}@{owner_working.ratified_at or '?'}",
        )
        if anchored is None:
            return {
                "exit": 2,
                "error": f"--prompt-repo {owner} ratifies no prompt row (a `kind: prompt` row)",
            }
        return anchored
    if not explicit:
        return {
            "error": (
                "no review prompt is ratified in the charter's gate table (a `kind: prompt` row), "
                "no --prompt-repo was given either, and no --prompt was given; a review cannot run "
                "honestly without one (D15)"
            )
        }
    path = Path(explicit)
    if not path.is_file():
        return {"error": f"no such prompt file: {explicit}"}
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        rel = str(path.resolve().relative_to(repo)).replace("\\", "/")
    except ValueError:
        rel = str(path)
    return {"text": text, "path": rel, "hash": _hash_text(text), "ratified": False, "ratified_in": None}


def _run_reviewer(command: list[str], tree: Path, timeout: float) -> dict:
    """Start the reviewer once, with the export as cwd and the prompt on stdin.

    The prompt reaches the reviewer as a **file**, not through a pipe this process has to write:
    ``stdin=open(REVIEW-PROMPT.md)`` gives the child a real handle it can read or ignore. Writing the
    prompt through a pipe is the shape that hangs on Windows -- a child that never drains its stdin
    leaves the parent blocked in the write past any timeout, and the run is then recorded as
    `timeout` where `malformed` is the truth (Gilbert's report; measured: with the file, a reviewer
    that prints and ignores stdin returns in about 0.2 s).

    What is recorded is bounded: stdout is capped by `MAX_STDOUT` in validation, and the reason keeps
    the first 500 characters of stderr. Both are still buffered in full by `capture_output`, which is
    named in D15 as the one uncapped part of this path.
    """
    if not command:
        return {"result": "error", "exit": None, "stdout": "", "reason": "empty reviewer command"}
    try:
        handle = open(tree / "REVIEW-PROMPT.md", "r", encoding="utf-8", errors="replace")
    except OSError as exc:  # pragma: no cover - write_export just wrote it
        return {"result": "error", "exit": None, "stdout": "", "reason": f"no prompt in the export: {exc}"}
    try:
        with handle:
            proc = subprocess.run(
                command,
                cwd=str(tree),
                stdin=handle,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
    except subprocess.TimeoutExpired:
        return {"result": "timeout", "exit": None, "stdout": "", "reason": f"timed out after {timeout:g}s"}
    except OSError as exc:
        return {"result": "error", "exit": None, "stdout": "", "reason": f"could not start {command[0]}: {exc}"}
    if proc.returncode != 0:
        detail = (proc.stderr or "").strip()[:500]
        return {
            "result": "error",
            "exit": proc.returncode,
            "stdout": proc.stdout or "",
            "reason": f"the reviewer exited {proc.returncode}: {detail or '(no stderr)'}",
        }
    return {"result": "pass", "exit": 0, "stdout": proc.stdout or "", "reason": (proc.stderr or "").strip()}


def _evidence_resolves(tree: Path, evidence: str, requirement_ids: set[str]) -> bool:
    """D15: evidence resolves to a **file in the export** or to a **requirement id in the charter**.

    A citation that resolves to nothing is not evidence: `Path.resolve()` does not require the target
    to exist, so containment alone counted every relative string as verified (Proctor measured it).
    """
    if not evidence:
        return False
    if evidence in requirement_ids:
        return True
    if Path(evidence).is_absolute():
        return False
    try:
        target = (tree / evidence).resolve()
        root = tree.resolve()
    except OSError:  # pragma: no cover - unreadable path components
        return False
    if target != root and root not in target.parents:
        return False
    return target.exists()


def validate_output(stdout: str, tree: Path, requirement_ids: set[str]) -> dict:
    """Validate the reviewer's one JSON object. Returns a record dict, or {'error': ...}."""
    if len(stdout) > MAX_STDOUT:
        return {"error": f"the reviewer's output is over {MAX_STDOUT} bytes"}
    text = stdout.strip()
    if not text:
        return {"error": "the reviewer returned nothing on stdout"}
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"error": f"the reviewer's output is not one JSON object: {exc.msg}"}
    if not isinstance(obj, dict):
        return {"error": "the reviewer's output is not a JSON object"}
    verdict = obj.get("verdict")
    if verdict not in VERDICTS:
        return {"error": f"verdict must be one of {VERDICTS}, not {verdict!r}"}
    items = obj.get("items", [])
    if not isinstance(items, list):
        return {"error": "items must be a list"}
    unreviewed = obj.get("unreviewed")
    if not isinstance(unreviewed, list):
        return {"error": "unreviewed must be present as a list, even when empty"}

    counts = {name: 0 for name in CLASSES}
    counts.update({"verified": 0, "unverified": 0})
    cleaned: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            return {"error": "every item must be an object"}
        kind = item.get("class")
        if kind not in CLASSES:
            return {"error": f"item class must be one of {CLASSES}, not {kind!r}"}
        evidence = str(item.get("evidence") or "")
        if not evidence:
            return {"error": f"item {item.get('subject')!r} has no evidence"}
        verified = _evidence_resolves(tree, evidence, requirement_ids)
        counts[kind] += 1
        counts["verified" if verified else "unverified"] += 1
        cleaned.append(
            {
                "class": kind,
                "subject": str(item.get("subject") or ""),
                "evidence": evidence,
                "verified": verified,
                "why": str(item.get("why") or ""),
                "confidence": str(item.get("confidence") or ""),
            }
        )

    coverage = obj.get("coverage") or {}
    if not isinstance(coverage, dict):
        return {"error": "coverage must be an object with files_seen and files_total"}
    seen, total = coverage.get("files_seen"), coverage.get("files_total")
    partial = bool(unreviewed) or (
        isinstance(seen, int) and isinstance(total, int) and seen < total
    )
    if verdict == "clean" and partial:
        verdict = "partial"
    elif verdict == "divergence" and counts["verified"] == 0:
        verdict = "unverified"
    return {
        "verdict": verdict,
        "items": cleaned,
        "counts": counts,
        "unreviewed": [str(entry) for entry in unreviewed],
        "coverage": {"files_seen": seen, "files_total": total},
    }


def run_review(
    repo: Path | str,
    *,
    reviewer: str,
    prompt: str | None = None,
    prompt_repo: str | None = None,
    record_path: Path | str | None = None,
    export_root: Path | str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict:
    """Run one review and record it. Returns a report dict with an ``exit`` code."""
    repo = Path(repo).resolve()
    runs, context_path = record.record_paths(repo, record_path)
    audit = Audit(
        repo=repo,
        charter_path=repo / CHARTER_NAME,
        record_path=runs,
        review_context_path=context_path,
    )
    try:
        _, charter = load_charter(repo)
    except AuditError as exc:
        return {"exit": 2, "error": str(exc)}
    audit.charter = charter
    if not charter.ratified_at:
        return {
            "exit": 2,
            "error": (
                "the charter names no ratification commit (`Ratified at:`), so a review has no "
                "anchor to record against: not auditable (D12, D15)"
            ),
        }
    try:
        audit.commit = gitcmd.head(repo)
    except gitcmd.GitError as exc:
        return {"exit": 2, "error": f"git cannot name HEAD: {exc}"}

    audit.reference = load_reference(repo, charter, audit)
    chosen = _resolve_prompt(repo, charter, audit.reference, prompt, prompt_repo)
    if "error" in chosen:
        return {"exit": chosen.get("exit", 2), "error": chosen["error"]}

    manifest = export.build_manifest(audit)
    if not manifest["files"]:
        return {
            "exit": 2,
            "error": (
                "the export would contain no files, so the review would be a review of nothing; "
                "refusing rather than recording a clean verdict over an empty tree (D15)"
            ),
        }
    mechanical = run_audit(repo, record_path=runs, write=False)
    findings = mechanical.render()
    root = Path(export_root) if export_root else runs.parent / _run_id(manifest)
    try:
        tree = export.write_export(
            audit,
            manifest,
            root,
            prompt_text=chosen["text"],
            frozen_original=charter.frozen_original,
            findings=findings,
        )
    except OSError as exc:
        return {"exit": 2, "error": f"the reviewer's export could not be written: {exc}"}

    command = split_command(reviewer)
    run = _run_reviewer(command, tree, timeout)
    review: dict | None = None
    requirement_ids = {r.id for r in charter.requirements}
    if run["result"] == "pass":
        review = validate_output(run["stdout"], tree, requirement_ids)
        if "error" in review:
            run["result"] = "malformed"
            run["reason"] = review["error"]
            review = None

    context_hash = _hash_text(chosen["text"] + charter.frozen_original + findings)
    line = {
        "kind": "review",
        "at": record.now(),
        "commit": audit.commit,
        "ratified": charter.ratified_at,
        "manifest": manifest["manifest_sha256"],
        "context": context_hash,
        "prompt": chosen["hash"],
        "prompt_path": chosen["path"],
        "prompt_ratified": chosen["ratified"],
        "ratified_in": chosen.get("ratified_in"),
        "command": command,
        "exit": run["exit"],
        "result": run["result"],
        "history_reachable": "none",
        "export": str(tree),
        "files": manifest["count"],
        "bytes": manifest["bytes"],
        "truncated": manifest["truncated"],
    }
    if run["reason"]:
        line["reason"] = run["reason"]
    if review is not None:
        line.update(
            {
                "verdict": review["verdict"],
                "items": review["counts"],
                "unreviewed": review["unreviewed"],
                "coverage": review["coverage"],
                "claims": review["items"],
            }
        )
    try:
        record.ensure_header(runs)
        record.append(runs, line)
    except OSError as exc:
        return {"exit": 2, "error": f"the review could not be recorded: {exc}"}

    if run["result"] != "pass":
        return {"exit": 2, "error": run["reason"], "line": line, "export": str(tree)}
    verdict = review["verdict"] if review else "unverified"
    return {
        "exit": 0 if verdict == "clean" else 1,
        "line": line,
        "review": review,
        "export": str(tree),
        "manifest": manifest["manifest_sha256"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="keel review",
        description=(
            "start a reviewer with no history -- a .git-less export of the current state against "
            "the frozen original -- and record what it was handed (R4)"
        ),
    )
    parser.add_argument("repo", nargs="?", default=".", help="repository to review (default: .)")
    parser.add_argument(
        "--reviewer",
        required=True,
        help=(
            "the command to start, as one string; it is run with the export as its working "
            "directory and the prompt on its stdin, and must print one JSON object (D15)"
        ),
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help=(
            "prompt file when the charter ratifies none; recorded as unratified, because an "
            "unlocked instruction is not a locked one"
        ),
    )
    parser.add_argument(
        "--prompt-repo",
        default=None,
        help=(
            "a repository whose ratified charter holds the prompt row, for an input whose own "
            "charter cannot be edited (D4); the record then names where the prompt was ratified"
        ),
    )
    parser.add_argument("--record", default=None, help="where the run record lives (D4/A3)")
    parser.add_argument("--export", dest="export_root", default=None, help="where the export goes")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="seconds for the reviewer")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    result = run_review(
        args.repo,
        reviewer=args.reviewer,
        prompt=args.prompt,
        prompt_repo=args.prompt_repo,
        record_path=args.record,
        export_root=args.export_root,
        timeout=args.timeout,
    )

    if args.json:
        emit(json.dumps(result, indent=2, ensure_ascii=False))
        return result.get("exit", 2)

    line = result.get("line")
    if line is not None:
        emit(f"review: {line.get('verdict') or line.get('result')}  ({line.get('result')})")
        emit(f"  command:  {' '.join(line['command'])}")
        origin = line["prompt_path"] + (
            f" (ratified in {line['ratified_in']})" if line.get("prompt_ratified") else " (UNRATIFIED)"
        )
        emit(f"  prompt:   {origin}")
        emit(f"  manifest: {line['manifest']}")
        emit(f"  export:   {line['export']}  ({line['files']} files, {line['bytes']} bytes"
             + (", partial: over the cap" if line.get("truncated") else "") + ")")
        if line.get("items"):
            counts = line["items"]
            emit("  counts:   " + ", ".join(f"{k} {v}" for k, v in counts.items()))
        for item in line.get("claims", []):
            flag = "" if item["verified"] else "  [evidence-missing]"
            emit(f"    {item['class']:<12} {item['subject']}: {item['why']}{flag}")
        if line.get("unreviewed"):
            emit("  unreviewed: " + "; ".join(line["unreviewed"]))
    if result.get("error"):
        emit_err(f"keel review: {result['error']}")
    return result.get("exit", 2)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
