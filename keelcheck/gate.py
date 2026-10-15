"""The gate runner (R2): execute the ratified gates, and record that they ran.

R2 says a gate is a script recorded in the charter with a content hash. Two halves follow
from that, and they are deliberately different commands:

``keelcheck gate run``
    the **runner**. It refuses to execute a gate whose content hash differs from the
    ratified one -- running unratified code is the thing the lock exists to prevent -- and
    it is the only producer of the ``kind: "gate"`` run records the audit reads. A local
    hook is a detector, not a lock (D2), so the runner's record is what makes a bypass
    visible as a *missing* record rather than a wrong one (D1).

``keelcheck gate hash``
    the authoring half: the recorded form (``sha256:<64 hex>``) of a script's content,
    taken over the bytes git would store (D9). This is what a charter row records when a
    gate is ratified.

No daemon, no server, no listening socket (R6): a bounded subprocess per gate and a return.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import gitcmd, normalize, record
from .audit import Audit, AuditError, CHARTER_NAME, OUTPUT_TAIL, load_charter, load_reference
from .charter import Gate
from .output import emit, emit_err

__all__ = ["main", "run_gate_command", "hash_command"]

#: Seconds per gate, overridable with `--timeout`. **It protects against a gate that never returns,
#: not against slowness**, because the hook runs these gates on every commit: a hang must become a
#: recorded failure rather than a committer staring at a shell. It was 600 s, and that turned a slow
#: machine into a false red -- measured 2026-10-15 on one host, the coverage gate ran the suite under
#: the tracer in 451.84 s in one run (3 failed, 113 passed) and exceeded 600 s in the next, so the
#: bound sat inside the noise of the thing it bounds. The slowest gate here is the suite under a
#: tracer, and a machine twice as slow as this one is not misbehaving; `--timeout` is for tightening
#: it deliberately.
DEFAULT_TIMEOUT = 1800.0
PASS = "pass"
FAIL = "fail"
LOCKED = "locked"
MISSING = "missing"
UNVERIFIABLE = "unverifiable"
TIMEOUT = "timeout"
ERROR = "error"
PYTHON_SUFFIXES = (".py", ".pyw")


def _tail(text: str, limit: int = OUTPUT_TAIL) -> str:
    text = text.strip()
    return text if len(text) <= limit else "..." + text[-limit:]


def _run_one(repo: Path, path: Path, timeout: float) -> tuple[int | None, str, str]:
    """Run one gate script. Returns (exit status or None, result, captured output)."""
    absolute = (repo / path).resolve()
    command = [sys.executable, str(absolute)] if absolute.suffix in PYTHON_SUFFIXES else [str(absolute)]
    try:
        proc = subprocess.run(
            command,
            cwd=str(repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        captured = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        return None, TIMEOUT, f"timed out after {timeout:g}s\n{captured}"
    except OSError as exc:
        return None, ERROR, f"could not execute {absolute}: {exc}"
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, (PASS if proc.returncode == 0 else FAIL), output


def run_gate_command(
    repo: Path | str,
    *,
    record_path: Path | str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> tuple[list[dict], int, str | None]:
    """Run every ratified gate, record each run, and report. Returns (results, exit, error)."""
    repo = Path(repo).resolve()
    runs, context = record.record_paths(repo, record_path)
    audit = Audit(
        repo=repo,
        charter_path=repo / CHARTER_NAME,
        record_path=runs,
        review_context_path=context,
    )
    try:
        _, charter = load_charter(repo)
    except AuditError as exc:
        return [], 2, str(exc)
    audit.charter = charter
    try:
        audit.commit = gitcmd.head(repo)
    except gitcmd.GitError as exc:
        return [], 2, f"git cannot name HEAD: {exc}"

    audit.reference = load_reference(repo, charter, audit)
    for finding in audit.findings:
        emit_err(f"keelcheck gate run: {finding.line().strip()}")
    if audit.reference is None:
        return [], 2, audit.cannot_run or "the ratified charter could not be read"
    gate_rows = [g for g in audit.reference.gates if g.kind == "gate"]
    if not gate_rows:
        return [], 1, (
            "no ratified gate: the hash half of this repository verifies nothing, so "
            "there is nothing to run (vacuity is a finding, not a clean run -- D8)"
        )

    results: list[dict] = []
    for gate in gate_rows:
        results.append(_check_and_run(audit, gate, runs, timeout))

    exit_code = 0 if results and all(r["result"] == PASS for r in results) else 1
    try:
        record.ensure_header(runs)
        for result in results:
            record.append(runs, result)
    except OSError as exc:
        return results, 2, f"the run record could not be written: {exc}"
    return results, exit_code, None


def _check_and_run(audit: Audit, gate: Gate, runs: Path, timeout: float) -> dict:
    name = gate.name or "(unnamed)"
    entry = {
        "kind": "gate",
        "at": record.now(),
        "gate": name,
        "path": gate.path,
        "hash": None,
        "ratified": gate.hash,
        "commit": audit.commit,
        "exit": None,
        "result": LOCKED,
    }
    if gate.malformed_hash:
        entry["reason"] = f"the ratified hash {gate.hash or '(empty)'} is not sha256:<64 hex> (A1)"
        return entry
    if not gate.path or not (audit.repo / gate.path).is_file():
        entry["result"] = MISSING
        entry["reason"] = f"the gate file {gate.path or '(none)'} does not exist"
        return entry
    try:
        current, warnings = normalize.content_hash(audit.repo, gate.path)
    except normalize.NormalizationError as exc:
        entry["result"] = UNVERIFIABLE
        entry["reason"] = str(exc)
        return entry
    entry["hash"] = current
    if warnings:
        entry["warnings"] = warnings
    if current != gate.hash:
        entry["reason"] = (
            "the gate's content does not match the ratified hash, and keelcheck does not run "
            "code that is not the ratified code (R2)"
        )
        return entry
    status, result, output = _run_one(audit.repo, Path(gate.path), timeout)
    entry["exit"] = status
    entry["result"] = result
    if output.strip():
        entry["output"] = _tail(output)
    return entry


def hash_command(repo: Path | str, path: str) -> tuple[str | None, list[str], str | None]:
    """The recorded hash of one gate script. Returns (hash, warnings, error)."""
    repo = Path(repo).resolve()
    candidate = Path(path)
    absolute = candidate if candidate.is_absolute() else repo / candidate
    try:
        relative = absolute.resolve().relative_to(repo)
    except ValueError:
        return None, [], f"{path} is outside the repository {repo} (D6: paths resolve inside it)"
    try:
        digest, warnings = normalize.content_hash(repo, str(relative).replace("\\", "/"))
    except FileNotFoundError:
        return None, [], f"no such file: {path}"
    except normalize.NormalizationError as exc:
        return None, [], str(exc)
    return digest, warnings, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="keelcheck gate",
        description="run the ratified gates, or compute the hash a gate row records (R2)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run every ratified gate and record the run")
    run.add_argument("repo", nargs="?", default=".", help="repository (default: .)")
    run.add_argument("--record", default=None, help="where the run record goes (default: <repo>/.keel/runs.jsonl)")
    run.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                     help=f"seconds per gate (default: {DEFAULT_TIMEOUT:g})")
    run.add_argument("--json", action="store_true", help="machine-readable output")

    digest = sub.add_parser("hash", help="print the recorded content hash of a script")
    digest.add_argument("path", help="script path, relative to the repository or absolute")
    digest.add_argument("--repo", default=".", help="repository the path resolves in (default: .)")
    digest.add_argument("--json", action="store_true", help="machine-readable output")

    args = parser.parse_args(argv)

    if args.command == "hash":
        value, warnings, error = hash_command(args.repo, args.path)
        for warning in warnings:
            emit_err(f"keelcheck: warning: {warning}")
        if error:
            emit_err(f"keelcheck gate hash: {error}")
            return 2
        if args.json:
            emit(json.dumps({"path": args.path, "hash": value, "warnings": warnings}, ensure_ascii=False))
        else:
            emit(value or "")
        return 0

    results, exit_code, error = run_gate_command(
        args.repo, record_path=args.record, timeout=args.timeout
    )
    if args.json:
        emit(json.dumps({"gates": results, "exit": exit_code, "error": error}, indent=2, ensure_ascii=False))
    else:
        if error:
            emit_err(f"keelcheck gate run: {error}")
        for result in results:
            detail = f" exit {result['exit']}" if result["exit"] is not None else ""
            emit(f"gate {result['gate']}: {result['result']}{detail}")
            if result["result"] in (FAIL, TIMEOUT, ERROR, LOCKED, MISSING, UNVERIFIABLE):
                if result.get("reason"):
                    emit(f"    {result['reason']}")
                if result.get("output"):
                    emit(f"    output: {result['output']}")
        if results:
            emit(f"exit: {exit_code}")
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
