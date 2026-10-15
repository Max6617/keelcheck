"""The audit (R2, R3; D1, D5, D8).

One bounded run. It reads the charter, reads the **ratified** charter out of git (D1: the
working-tree hash is the measured side, never the reference side), compares every gate's
content hash, checks the frozen-original block byte for byte (D5), checks the pointer that
is written twice (A2), reads the append-only run record, writes what it would hand a
clean-context reviewer, and returns an exit code.

    exit 0   the audit ran, no divergence. Wishes are reported and do not change the code.
    exit 1   divergence: a gate's hash differs from the ratified one, a gate has no run
             record, a required section is missing, the frozen original moved, the pointer
             disagrees, or there is no ratified gate at all -- vacuity is a finding, not a
             clean run (D8).
    exit 2   the audit could not run honestly (no charter, unparseable charter, no git),
             or ``--fail-on-wish`` was given and wishes exist.

No daemon, no server, no listening socket (R6): this is a function that returns.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

from . import export, gitcmd, normalize, record
from .charter import Charter, CharterFormatError, Gate, named_repo_paths, parse_charter, render
from .output import emit, emit_err

__all__ = [
    "Audit",
    "AuditError",
    "Finding",
    "load_charter",
    "load_reference",
    "main",
    "run_audit",
]

EXIT_CLEAN = 0
EXIT_DIVERGENCE = 1
EXIT_CANNOT_RUN = 2

CHARTER_NAME = "CHARTER.md"
INVENTORY_LIMIT = 400
OUTPUT_TAIL = 2000


class AuditError(RuntimeError):
    """The audit cannot run honestly at all: no charter, no git, no commit."""


@dataclass
class Finding:
    """One divergence, named by kind and subject so the report can be read at a glance."""

    kind: str
    subject: str
    message: str

    def as_dict(self) -> dict:
        return {"kind": self.kind, "subject": self.subject, "message": self.message}

    def line(self) -> str:
        return f"  [{self.kind}] {self.subject}: {self.message}"


@dataclass
class Audit:
    repo: Path
    charter_path: Path
    record_path: Path
    review_context_path: Path
    commit: str = ""
    charter: Charter | None = None
    reference: Charter | None = None
    findings: list[Finding] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    gates: list[dict] = field(default_factory=list)
    record_objects: list[dict] = field(default_factory=list)
    fatal: str | None = None
    cannot_run: str | None = None
    fail_on_wish: bool = False
    require_review: bool = False
    review_state: dict | None = None
    exit_code: int = EXIT_CLEAN

    # --- reporting ------------------------------------------------------------

    @property
    def ratified_at(self) -> str | None:
        return self.charter.ratified_at if self.charter else None

    def add(self, kind: str, subject: str, message: str) -> None:
        self.findings.append(Finding(kind, subject, message))

    def compute_exit(self) -> int:
        """Divergence classes drive the code; wishes never do (D12).

        **Exit 2 dominates exit 1** (Gilbert's ruling, 2026-10-14): a run that could not establish its
        anchor did not do the job, so it must not be reported with the code that means it did. The
        findings are still printed -- `keelcheck audit ../rentguard`, a charter with no `Ratified at:`
        line, printed its divergences and exited 1, which D12 forbids. Vacuity is not special-cased
        here any more: without an anchor there is no reference to be vacuous about.
        """
        if self.fatal:
            return EXIT_CANNOT_RUN
        if self.fail_on_wish and self.charter is not None and self.charter.wishes:
            return EXIT_CANNOT_RUN
        if self.cannot_run:
            return EXIT_CANNOT_RUN
        if self.findings:
            return EXIT_DIVERGENCE
        return EXIT_CLEAN

    def render(self) -> str:
        out: list[str] = []
        out.append(f"keelcheck audit -- {self.repo}")
        out.append(f"commit:   {self.commit or '(unknown)'}")
        out.append(f"charter:  {self.charter_path}")
        out.append(f"ratified: {self.ratified_at or '(not named -- this charter is not auditable)'}")
        if self.fatal:
            out.append("")
            out.append(f"CANNOT RUN HONESTLY: {self.fatal}")
            out.append(f"exit: {self.exit_code}")
            return "\n".join(out)
        assert self.charter is not None
        ratified_rows = self.reference.gates if self.reference else []
        executable = [g for g in ratified_rows if g.kind == "gate"]
        out.append(
            f"sections: {len(self.charter.sections)}/6  requirements: "
            f"{len(self.charter.requirements)}  gates ratified: "
            f"{len(ratified_rows)} ({len(executable)} executable)  wishes: {len(self.charter.wishes)}"
        )
        out.append("")
        if self.findings:
            out.append(f"DIVERGENCES ({len(self.findings)})")
            out.extend(f.line() for f in self.findings)
        else:
            out.append("DIVERGENCES: none")
        if self.cannot_run:
            out.append(f"NOT AUDITABLE: {self.cannot_run}")
        if self.warnings:
            out.append("")
            out.append(f"WARNINGS ({len(self.warnings)})")
            out.extend(f"  {w}" for w in self.warnings)
        out.extend(self._review_lines())
        out.append("")
        out.append(f"exit: {self.exit_code}")
        out.append("")
        out.append(render(self.charter))
        return "\n".join(out)

    def _review_lines(self) -> list[str]:
        """The review half, always reported: fresh, stale, inconsistent, failed or missing (D15).

        Always printed, even when a review is not required: the reader has to be able to see that
        the drift half did not run, and a report that omits it reads as if it had.
        """
        state = self.review_state or {"status": "missing", "line": None}
        status = state.get("status")
        line = state.get("line") or {}
        out = ["", f"REVIEW (clean context, R4): {status}"]
        if status == "fresh":
            out.append(f"  command:  {' '.join(line.get('command', []))}")
            out.append(f"  verdict:  {line.get('verdict')}")
            counts = line.get("items") or {}
            if counts:
                out.append("  counts:   " + ", ".join(f"{k} {v}" for k, v in counts.items()))
            if line.get("unreviewed"):
                out.append("  unreviewed: " + "; ".join(str(u) for u in line["unreviewed"]))
            for item in line.get("claims", []):
                flag = "" if item.get("verified") else "  [evidence-missing]"
                out.append(f"    {item.get('class')}: {item.get('subject')} -- {item.get('why')}{flag}")
        elif status == "inconsistent":
            mismatch = line.get("coverage_mismatch") or {}
            out.append(
                f"  the recorded review claims {mismatch.get('claimed')!r} files where it was handed "
                f"{mismatch.get('handed')!r}, so it is not a review of this state: a verdict from a "
                "reviewer that was not looking at the export does not satisfy R4 (D15)"
            )
        elif status == "stale":
            out.append(
                f"  the recorded review covers {state.get('recorded')}; the state now hashes "
                f"{state.get('manifest')}"
            )
        elif status == "failed":
            out.append(
                f"  the last review attempt produced no verdict ({line.get('result')}): "
                f"{line.get('reason', '(no reason recorded)')}"
            )
        else:
            out.append(
                f"  no review line in {self.record_path.name}; run "
                '`keelcheck review <repo> --reviewer "<command>"` (D15)'
            )
        return out

    def as_dict(self) -> dict:
        return {
            "keelcheck": "audit/1",
            "repo": str(self.repo),
            "commit": self.commit,
            "charter": str(self.charter_path),
            "ratified_at": self.ratified_at,
            "exit": self.exit_code,
            "fatal": self.fatal,
            "not_auditable": self.cannot_run,
            "findings": [f.as_dict() for f in self.findings],
            "warnings": self.warnings,
            "review": self.review_state,
            "gates": self.gates,
            "record": str(self.record_path),
            "review_context": str(self.review_context_path),
            "charter_parsed": self.charter.as_dict() if self.charter else None,
        }

    # --- what the clean-context reviewer would be handed (R4) ------------------

    def review_context(self) -> dict:
        """The reviewer's inputs: the frozen original and the current state. No history.

        Deliberately excluded: the git log, commit messages, previous audit reports and any
        file *contents* other than the charter. The reviewer's value comes from not having
        the history that produced the current state, so this file is an inventory of paths
        and hashes, never a narrative of how the repository got here.
        """
        assert self.charter is not None
        return {
            "keelcheck": "review-context/1",
            "generated": record.now(),
            "repo": str(self.repo),
            "commit": self.commit,
            "charter": CHARTER_NAME,
            "ratified_at": self.ratified_at,
            "frozen_original": self.charter.frozen_original,
            "frozen_original_bytes": self.charter.frozen_original_bytes,
            "frozen_original_sha256": self.charter.frozen_original_sha256,
            "sections": self.charter.sections,
            "missing_sections": self.charter.missing_sections,
            "requirements": [r.as_dict() for r in self.charter.requirements],
            "wishes": [r.id for r in self.charter.wishes],
            "human_checks": [r.id for r in self.charter.human_checks],
            "asserted_enforcement": [r.id for r in self.charter.asserted_enforcement],
            "gates": self.gates,
            "divergences": [f.as_dict() for f in self.findings],
            "inventory": self.inventory(),
            "handed_over": (
                "the frozen original block, the working charter's living state, every gate "
                "hash and the mechanical findings; no git history, no commit messages, no "
                "file contents other than the charter"
            ),
            "excluded": ["git log", "commit messages", "previous audit reports", "file contents"],
        }

    def inventory(self) -> dict:
        """Tracked and untracked paths with sizes: the current state, not its history."""
        entries: list[dict] = []
        tracked: list[str] = []
        try:
            listing = gitcmd.run(self.repo, "ls-files", "-z")
            tracked = [p for p in listing.stdout.split("\0") if p]
        except gitcmd.GitError:
            tracked = []
        untracked: list[str] = []
        proc = gitcmd.run(self.repo, "status", "--porcelain", "-z", check=False)
        for chunk in proc.stdout.split("\0"):
            if chunk.startswith("?? "):
                untracked.append(chunk[3:])
        for rel in sorted(set(tracked) | set(untracked)):
            path = self.repo / rel
            try:
                size = path.stat().st_size
            except OSError:
                size = None
            entries.append({"path": rel, "bytes": size, "tracked": rel in tracked})
        truncated = len(entries) > INVENTORY_LIMIT
        return {
            "files": entries[:INVENTORY_LIMIT],
            "truncated": truncated,
            "count": len(entries),
        }


# --- shared loading -----------------------------------------------------------


def load_charter(repo: Path) -> tuple[Path, Charter]:
    """Read and parse ``<repo>/CHARTER.md``, or raise :class:`AuditError`."""
    charter_path = repo / CHARTER_NAME
    if not charter_path.is_file():
        raise AuditError(f"no {CHARTER_NAME} in {repo}")
    try:
        text = charter_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise AuditError(f"{charter_path} could not be read: {exc}") from exc
    try:
        return charter_path, parse_charter(text, path=charter_path)
    except CharterFormatError as exc:
        raise AuditError(f"not a charter: {exc}") from exc


def load_reference(repo: Path, charter: Charter, audit: Audit) -> Charter | None:
    """The charter as it stands at the ratified commit (D1/A2), and the anchor checks."""
    sha = charter.ratified_at
    if not sha:
        audit.cannot_run = (
            "the charter names no ratification commit (`Ratified at: <sha>`), so there is "
            "no reference side to compare against (A2): not auditable, never clean"
        )
        return None
    if not gitcmd.is_ancestor(repo, sha):
        audit.add(
            "anchor",
            sha,
            f"the ratified commit is not an ancestor of HEAD ({audit.commit}); the anchor "
            "has been rewritten or points at another branch",
        )
    kind = gitcmd.run(repo, "cat-file", "-t", sha, check=False).stdout.strip()
    if kind != "commit":
        audit.add(
            "anchor",
            sha,
            f"the ratified reference resolves to {kind or 'nothing'}, not a commit; an input "
            "that is not a commit is a divergence and is named (D11 F3)",
        )
    text = gitcmd.show(repo, sha, CHARTER_NAME)
    if text is None:
        audit.add("anchor", sha, f"{CHARTER_NAME} cannot be read at the ratified commit {sha}")
        return None
    try:
        return parse_charter(text, path=Path(f"{sha}:{CHARTER_NAME}"))
    except CharterFormatError as exc:
        audit.add("anchor", sha, f"the charter at the ratified commit is not a charter: {exc}")
        return None


# --- gate checks --------------------------------------------------------------


def _short(value: str) -> str:
    return value[:16] + "..." if value and len(value) > 19 else value


def _block_diff(old: str, new: str) -> str:
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    for i in range(max(len(old_lines), len(new_lines))):
        before = old_lines[i] if i < len(old_lines) else None
        after = new_lines[i] if i < len(new_lines) else None
        if before != after:
            return f"line {i + 1}: {before!r} -> {after!r}"
    return "the blocks differ only in surrounding whitespace"


def _change_detail(repo: Path, sha: str, gate: Gate, current: str) -> str:
    """What changed, in one line: the hashes, plus the size of the change when git can show it."""
    detail = f"its content hash changed since ratification ({_short(gate.hash)} -> {_short(current)})"
    if not sha or not gate.path:
        return detail
    old_text = gitcmd.show(repo, sha, gate.path)
    new_path = repo / gate.path
    if old_text is not None and new_path.is_file():
        before = old_text.splitlines()
        after = new_path.read_text(encoding="utf-8", errors="replace").splitlines()
        detail += f"; {len(before)} -> {len(after)} lines"
    return detail


def _gate_runs(audit: Audit, gate: Gate) -> list[dict]:
    """Recorded executions of this gate with the ratified content, oldest first."""
    name = gate.name or "(unnamed)"
    return [
        obj
        for obj in audit.record_objects
        if obj.get("kind") == "gate" and obj.get("gate") == name and obj.get("hash") == gate.hash
    ]


def _check_run_record(audit: Audit, gate: Gate, name: str) -> None:
    """A record proves the gate *executed*; the audit needs it to have *passed*.

    A failing, timed-out or errored run carries the ratified hash too, so accepting a line on
    kind, name and hash alone reported a repository whose only mechanism is red as clean.
    """
    runs = _gate_runs(audit, gate)
    if not runs:
        audit.add(
            "gate-record",
            name,
            f"no run record for this gate in {audit.record_path.name}: it has never been "
            "executed by `keelcheck gate run` (or the hook that calls it). A local hook is a "
            "detector, not a lock, so a bypass shows up as a missing record rather than a "
            "wrong one (D1, D3)",
        )
        return
    # The **latest** run speaks for the present state. `any(result == "pass")` read the history and
    # ignored the present, so a gate that passed once and fails now was reported clean: a pass is
    # evidence about the moment it ran, not about the state this audit is looking at (Sift's red,
    # 2026-10-15, `tests/test_gate_record_latest.py`). `_gate_runs` is oldest first, and its match on
    # the ratified hash means a run of *this* content.
    last = runs[-1]
    if last.get("result") == "pass":
        return
    exit_note = f", exit {last.get('exit')}" if last.get("exit") is not None else ""
    audit.add(
        "gate-record",
        name,
        f"the most recent recorded run of this gate did not pass "
        f"(result: {last.get('result')}{exit_note}, {last.get('at') or 'unknown time'}) in "
        f"{audit.record_path.name}; an earlier pass is evidence about that moment, not about the "
        "state this audit is looking at (D1, D3)",
    )


def _review_state(audit: Audit) -> dict:
    """Does a clean-context review cover the current state? (R4, D15.)

    Always reported, fatal only when a review is required. Freshness is the export *manifest*: the
    review records the manifest it handed over and the audit recomputes it with the same function
    (one function, both sides -- Proctor, design item 9). A line whose reviewer failed, timed out or
    returned something unusable is not a review, so `result` must be `pass`; and a line whose claimed
    file count disagrees with what the runner handed over is `inconsistent` -- recorded, printed, and
    not a review of this state (Sift's finding, 2026-10-15).
    """
    lines = [obj for obj in audit.record_objects if obj.get("kind") == "review"]
    if not lines:
        return {"status": "missing", "line": None, "manifest": None, "recorded": None}
    usable = [
        obj
        for obj in lines
        if obj.get("result") == "pass" and obj.get("verdict") != "inconsistent"
    ]
    if not usable:
        last = lines[-1]
        if last.get("verdict") == "inconsistent":
            return {
                "status": "inconsistent",
                "line": last,
                "manifest": None,
                "recorded": last.get("manifest"),
            }
        return {
            "status": "failed",
            "line": last,
            "manifest": None,
            "recorded": last.get("manifest"),
        }
    manifest = export.build_manifest(audit)
    current = manifest["manifest_sha256"]
    for obj in reversed(usable):
        if obj.get("manifest") == current:
            return {"status": "fresh", "line": obj, "manifest": current, "recorded": current}
    return {
        "status": "stale",
        "line": usable[-1],
        "manifest": current,
        "recorded": usable[-1].get("manifest"),
    }


def _anchor_moved(audit: Audit) -> None:
    """D12: the anchor moving is a human event, named once, not a re-measurement.

    The anchor value lives in exactly one place -- the charter's ``Ratified at:`` line. Each
    run entry records the anchor *it used*; when that differs from the previous entry's, the
    audit says so and exits 1. It fires once, because the entry this run appends carries the
    new value.
    """
    previous = None
    for obj in reversed(audit.record_objects):
        if obj.get("kind") in ("audit", "review"):
            previous = obj
            break
    if previous is None:
        return
    before = previous.get("ratified")
    after = audit.ratified_at
    if before != after:
        audit.add(
            "anchor-moved",
            "ratified",
            f"the anchor moved since the previous run: {before or '(none)'} -> "
            f"{after or '(none)'}; moving the anchor is a human event and not a "
            "re-measurement, so this is reported once and the entry this run appends carries "
            "the new value (D12)",
        )


def _resolves(audit: Audit, path: str) -> bool:
    """True when ``path`` names something that exists in the audited repository (D13).

    Checked at the audited revision and in the working tree, plus the two files **this run**
    writes: R4's cell names ``.keel/review-context.json``, which the audit produces, and D13
    is about a *borrowed* mechanism -- ``tools/coverage.py`` from another repository -- not
    about the tool's own output. The exception is the run's own two paths where the run
    actually put them, not their default names: with ``--record`` elsewhere the named file is
    not in the repository, and calling that built is the hole Proctor measured.
    """
    if (audit.repo / path).exists():
        return True
    if audit.commit and gitcmd.run(
        audit.repo, "cat-file", "-e", f"{audit.commit}:{path}", check=False
    ).returncode == 0:
        return True
    try:
        target = (audit.repo / path).resolve()
    except OSError:  # pragma: no cover - unreadable path components
        return False
    return any(
        written.resolve() == target
        for written in (audit.record_path, audit.review_context_path)
    )


def _check_enforced_by_paths(audit: Audit) -> None:
    """D13: a mechanism that does not resolve in the audited repo is a wish wearing its name."""
    assert audit.charter is not None
    for requirement in audit.charter.requirements:
        for path in named_repo_paths(requirement.enforced_by):
            if _resolves(audit, path):
                continue
            audit.add(
                "unbuilt",
                requirement.id,
                f"`enforced-by` names `{path}`, which does not resolve in the audited "
                f"repository (checked at HEAD {audit.commit or '(unknown)'} and in the "
                "working tree); a mechanism that does not exist is a wish wearing a "
                "mechanism's name (D13)",
            )


def check_gate(audit: Audit, gate: Gate, working: Gate | None) -> None:
    """One ratified gate: malformed hash, file, content hash, declaration, run record."""
    assert audit.reference is not None
    sha = audit.ratified_at or "(unnamed)"
    name = gate.name or "(unnamed)"
    entry = {
        "name": name,
        "path": gate.path,
        "ratified": gate.hash,
        "current": None,
        "status": "unknown",
    }
    audit.gates.append(entry)
    entry["kind"] = gate.kind

    if not gate.known_kind:
        entry["status"] = "unknown-kind"
        audit.add(
            "gate",
            name,
            f"kind {gate.kind!r} is not one of `gate`, `prompt`; an unknown kind is a divergence, "
            "never a skip (A1, D15)",
        )
    if gate.malformed_hash:
        entry["status"] = "malformed"
        audit.add(
            "gate",
            name,
            f"the ratified hash {gate.hash or '(empty)'!r} is not `sha256:<64 hex>`; a "
            "malformed hash is a divergence, never a skip (A1)",
        )
    if working is None:
        audit.add(
            "gate",
            name,
            f"this gate is in the ratified table at {sha} but not in the working charter; "
            "a ratified gate cannot be dropped by editing the working tree (D1)",
        )
    elif working.hash != gate.hash:
        audit.add(
            "gate",
            name,
            f"the working charter declares {_short(working.hash) or '(empty)'} but the "
            f"ratified table at {sha} records {_short(gate.hash)}; editing the working-tree "
            "hash does not re-ratify a gate (D1)",
        )

    path = gate.path or (working.path if working else "")
    if not path:
        entry["status"] = "no-path"
        audit.add("gate", name, "no gate file path is recorded (A1)")
    elif not (audit.repo / path).is_file():
        entry["status"] = "missing"
        audit.add("gate", name, f"the gate file {path} does not exist")
    else:
        try:
            current, warnings = normalize.content_hash(audit.repo, path)
        except FileNotFoundError:
            entry["status"] = "missing"
            audit.add("gate", name, f"the gate file {path} does not exist")
        except normalize.NormalizationError as exc:
            entry["status"] = "unverifiable"
            audit.add("gate", name, f"the content hash cannot be trusted: {exc}")
        else:
            entry["current"] = current
            audit.warnings.extend(f"{name}: {w}" for w in warnings)
            if current != gate.hash:
                entry["status"] = "changed"
                audit.add(
                    "gate",
                    name,
                    f"{path}: {_change_detail(audit.repo, sha if audit.ratified_at else "", gate, current)}",
                )
            else:
                entry["status"] = "locked"

    if gate.kind == "gate":
        _check_run_record(audit, gate, name)


def _table_commit(audit: Audit) -> str:
    """The commit that last touched the charter at the ratified revision: who moved the table."""
    sha = audit.ratified_at
    if not sha:
        return "(unknown)"
    proc = gitcmd.run(audit.repo, "log", "-1", "--format=%H", sha, "--", CHARTER_NAME, check=False)
    lines = [line for line in proc.stdout.strip().splitlines() if line]
    return lines[0] if lines else sha


def _gate_table_changes(audit: Audit) -> None:
    """D10: every change to the gate table since the last run record, named.

    Both copies of the pointer agreeing is not proof of approval: an edit that keeps the
    charter and the record consistent -- a re-ratified-looking hash that no human approved --
    passes A2 untouched. So the table itself is compared with the one the previous run
    recorded, and each change is printed with both hashes and the commit that made it.
    """
    previous = None
    for obj in reversed(audit.record_objects):
        if obj.get("kind") == "audit":
            previous = obj
            break
    if previous is None:
        return
    before = {
        g.get("name"): g.get("ratified", g.get("hash"))
        for g in previous.get("gates", [])
        if isinstance(g, dict)
    }
    reference_gates = audit.reference.gates if audit.reference is not None else []
    after = {g.name or "(unnamed)": g.hash for g in reference_gates}
    changed_at = _table_commit(audit)
    for name in sorted(set(before) | set(after)):
        old, new = before.get(name), after.get(name)
        if old == new:
            continue
        audit.add(
            "gate-table",
            name,
            f"the gate table changed since the run at {previous.get('commit') or '(unknown commit)'} "
            f"({previous.get('at') or 'unknown time'}): {old or '(not present)'} -> "
            f"{new or '(not present)'}; the table is read from {changed_at} (D10)",
        )


# --- the run ------------------------------------------------------------------


def run_audit(
    repo: Path | str,
    *,
    record_path: Path | str | None = None,
    fail_on_wish: bool = False,
    require_review: bool = False,
    write: bool = True,
) -> Audit:
    """Run the audit, write the record and the reviewer's input file, and return the result.

    ``write=False`` evaluates without touching the tree: the review command needs the mechanical
    findings for the reviewer's export and must not append an audit line of its own while doing it.
    """
    repo = Path(repo).resolve()
    runs, context = record.record_paths(repo, record_path)
    audit = Audit(
        repo=repo,
        charter_path=repo / CHARTER_NAME,
        record_path=runs,
        review_context_path=context,
        fail_on_wish=fail_on_wish,
        require_review=require_review,
    )

    try:
        _, charter = load_charter(repo)
    except AuditError as exc:
        audit.fatal = str(exc)
        audit.exit_code = audit.compute_exit()
        return audit
    audit.charter = charter

    for name in charter.missing_sections:
        audit.add(
            "missing-section",
            name,
            "a section R1's fixed format names is missing from the charter",
        )

    try:
        audit.commit = gitcmd.head(repo)
    except gitcmd.GitError as exc:
        audit.fatal = f"git cannot name HEAD: {exc}"
        audit.exit_code = audit.compute_exit()
        return audit

    audit.reference = load_reference(repo, charter, audit)

    objects, problems = record.read(runs)
    audit.record_objects = objects
    for problem in problems:
        audit.add("record", runs.name, f"{problem}")
    header = record.first_header(objects)
    if objects and header is None:
        audit.add(
            "record",
            runs.name,
            "the record has no header line, so its format and version are not declared",
        )
    _anchor_moved(audit)
    audit.review_state = _review_state(audit)
    if (charter.review_required or require_review) and audit.review_state["status"] != "fresh":
        declared = "the charter declares it" if charter.review_required else "--require-review"
        audit.add(
            "review",
            "clean-context",
            f"a clean-context review is required ({declared}) and the current state is "
            f"{audit.review_state['status']}: a review that did not happen is a missing record, "
            "not a wrong one (R4, D15)",
        )
    _check_enforced_by_paths(audit)
    for subject, message in charter.format_issues:
        audit.add("format", subject, message)

    reference_gates = audit.reference.gates if audit.reference is not None else []
    if audit.reference is not None:
        if audit.reference.frozen_original != charter.frozen_original:
            audit.add(
                "original",
                "frozen-original",
                f"the frozen-original block differs from the block at {charter.ratified_at}: "
                f"{audit.reference.frozen_original_bytes} -> {charter.frozen_original_bytes} bytes, "
                f"{_block_diff(audit.reference.frozen_original, charter.frozen_original)}",
            )
        _gate_table_changes(audit)

    reference_gate_rows = [g for g in reference_gates if g.kind == "gate"]
    if not reference_gate_rows:
        working_gate_rows = [g for g in charter.gates if g.kind == "gate"]
        ratified_prompts = [g for g in reference_gates if g.kind == "prompt"]
        anchor = charter.ratified_at or "(no anchor)"
        holds = (
            f"the ratified table at {anchor} holds {len(ratified_prompts)} prompt row(s) and no "
            "executable gate"
            if ratified_prompts
            else f"no gate is ratified at {anchor}"
        )
        declared = (
            f"{len(working_gate_rows)} executable gate(s) are declared in the working charter and "
            "not ratified"
            if working_gate_rows
            else "no executable gate is declared in the working charter either"
        )
        audit.add(
            "vacuity",
            "gates",
            f"{holds}, and {declared}; R2's gate is an executable script with a content hash, so "
            "the hash half of this audit verified nothing -- and an audit that verifies nothing is "
            "not a clean run (D8)",
        )

    if audit.reference is not None:
        working = {g.name: g for g in charter.gates}
        reference_names = {g.name for g in reference_gates}
        for gate in reference_gates:
            check_gate(audit, gate, working.get(gate.name))
        for gate in charter.gates:
            if gate.name not in reference_names:
                audit.add(
                    "gate-unratified",
                    gate.name or "(unnamed)",
                    f"declared in the working charter but not ratified at {charter.ratified_at}",
                )

    audit.exit_code = audit.compute_exit()

    if not write:
        return audit
    try:
        record.ensure_header(runs)
        record.append(
            runs,
            {
                "kind": "audit",
                "at": record.now(),
                "commit": audit.commit,
                "ratified": charter.ratified_at,
                "exit": audit.exit_code,
                "divergences": len(audit.findings),
                "gates": [
                    {
                        "name": g["name"],
                        "path": g["path"],
                        "hash": g["current"],
                        "ratified": g["ratified"],
                        "status": g["status"],
                    }
                    for g in audit.gates
                ],
            },
        )
        record.write_json(context, audit.review_context())
    except OSError as exc:
        audit.fatal = f"the run record could not be written: {exc}"
        audit.exit_code = audit.compute_exit()
    return audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="keelcheck audit",
        description=(
            "audit a repository against its ratified charter: hash-locked gates, the "
            "frozen original, the wishes (R1-R3)"
        ),
    )
    parser.add_argument("repo", nargs="?", default=".", help="repository to audit (default: .)")
    parser.add_argument(
        "--record",
        default=None,
        help=(
            "where the append-only run record goes (default: <repo>/.keel/runs.jsonl); the "
            "reviewer's input file is written beside it (D4/A3)"
        ),
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--require-review",
        action="store_true",
        help=(
            "a missing or stale clean-context review is divergence; the charter can also declare "
            "`Review: required` (D15)"
        ),
    )
    parser.add_argument(
        "--fail-on-wish",
        action="store_true",
        help="exit 2 when the charter contains a wish (opt-in; wishes are reported, not fatal)",
    )
    args = parser.parse_args(argv)

    # A directory is turned into <dir>/runs.jsonl inside record.record_paths, so `keelcheck audit`
    # and `keelcheck gate run` read the same argument the same way.
    audit = run_audit(
        args.repo,
        record_path=args.record,
        fail_on_wish=args.fail_on_wish,
        require_review=args.require_review,
    )

    if args.json:
        emit(json.dumps(audit.as_dict(), indent=2, ensure_ascii=False))
    else:
        emit(audit.render())
    return audit.exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
