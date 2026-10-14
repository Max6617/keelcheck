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


def _run_id() -> str:
    return "review-" + record.now().replace(":", "-")


def _hash_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _resolve_prompt(repo: Path, charter: Charter, explicit: str | None) -> dict:
    """The prompt text, its repo-relative path, its hash, and whether it is the ratified one."""
    row = prompt_row(charter)
    if row is not None:
        if not row.path or not (repo / row.path).is_file():
            return {"error": f"the ratified prompt {row.path or '(no path)'} does not exist"}
        try:
            current, _ = normalize.content_hash(repo, row.path)
        except (FileNotFoundError, normalize.NormalizationError) as exc:
            return {"error": f"the ratified prompt cannot be hashed: {exc}"}
        if row.malformed_hash or current != row.hash:
            return {
                "error": (
                    f"the prompt {row.path} changed since ratification ({row.hash or '(no hash)'} "
                    f"-> {current}); keel does not review against a weakened prompt (R2, D15)"
                ),
                "exit": 1,
            }
        return {
            "text": (repo / row.path).read_text(encoding="utf-8", errors="replace"),
            "path": row.path,
            "hash": current,
            "ratified": True,
        }
    if not explicit:
        return {
            "error": (
                "no review prompt is ratified in the charter's gate table (a `kind: prompt` row) "
                "and no --prompt was given; a review cannot run honestly without one (D15)"
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
    return {"text": text, "path": rel, "hash": _hash_text(text), "ratified": False}


def _run_reviewer(command: list[str], cwd: Path, stdin_text: str, timeout: float) -> dict:
    """Start the reviewer once, with the export as cwd and the prompt on stdin."""
    if not command:
        return {"result": "error", "exit": None, "stdout": "", "reason": "empty reviewer command"}
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            input=stdin_text,
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


def _inside_export(tree: Path, evidence: str) -> bool:
    """D15: evidence resolves inside the export, or it is not evidence."""
    if not evidence or Path(evidence).is_absolute():
        return False
    try:
        target = (tree / evidence).resolve()
        root = tree.resolve()
    except OSError:  # pragma: no cover - unreadable path components
        return False
    return target == root or root in target.parents


def validate_output(stdout: str, tree: Path) -> dict:
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
        verified = _inside_export(tree, evidence)
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

    chosen = _resolve_prompt(repo, charter, prompt)
    if "error" in chosen:
        return {"exit": chosen.get("exit", 2), "error": chosen["error"]}
    audit.reference = load_reference(repo, charter, audit)

    manifest = export.build_manifest(audit)
    mechanical = run_audit(repo, record_path=runs, write=False)
    findings = mechanical.render()
    root = Path(export_root) if export_root else runs.parent / _run_id()
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
    run = _run_reviewer(command, tree, chosen["text"], timeout)
    review: dict | None = None
    if run["result"] == "pass":
        review = validate_output(run["stdout"], tree)
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
    parser.add_argument("--record", default=None, help="where the run record lives (D4/A3)")
    parser.add_argument("--export", dest="export_root", default=None, help="where the export goes")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="seconds for the reviewer")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    result = run_review(
        args.repo,
        reviewer=args.reviewer,
        prompt=args.prompt,
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
        emit(f"  prompt:   {line['prompt_path']} ({'ratified' if line['prompt_ratified'] else 'UNRATIFIED'})")
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
