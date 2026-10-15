"""Outside attack on keel's clean-context review (Sift, 2026-10-14).

Not product code and not a test: this probe reads ``keel/`` internals deliberately, which D3
forbids in ``tests/`` and nowhere else. It tests the claims in
``keel/research/drift-review-design.md`` sections 7-8 and in D15 against the code that landed
at ``6810818`` (plus the export fixes at ``e9ec9a1``/``8a63e68``).

Run from anywhere::

    python research/probe-review-attacks.py

Scratch repositories are made under ``<workspace>/.probe-tmp/<uuid>/`` and are disposable.

Every probe prints PASS/FAIL for the claim it attacks and the raw evidence. A FAIL here is a
finding against the design, not a bug in the probe.
"""

from __future__ import annotations

import hashlib
import json
import sys
import uuid
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]  # workspace/
REPO = WORKSPACE / "keel"  # the keel repository
sys.path.insert(0, str(REPO))  # `import keel`
sys.path.insert(0, str(REPO / "tests"))  # `import _support`

import _support  # noqa: E402
from keel import export  # noqa: E402
from keel.audit import Audit, load_charter  # noqa: E402

REQ = [("R1", "the parser exists", "code: the parser", "—", "**met**")]
SCRATCH = WORKSPACE / ".probe-tmp"
BASE = SCRATCH  # per-run directory; set in main()


def _audit(root: Path, *, record: Path | None = None) -> Audit:
    record = record or (root / ".keel" / "runs.jsonl")
    audit = Audit(
        repo=root,
        charter_path=root / "CHARTER.md",
        record_path=record,
        review_context_path=record.with_name("review-context.json"),
    )
    _, charter = load_charter(root)
    audit.charter = charter
    return audit


def _manifest(root: Path, *, record: Path | None = None) -> dict:
    return export.build_manifest(_audit(root, record=record))


def _repo(root: Path, rows, *, extra_files=(), gitignore: str | None = None) -> str:
    for rel, text in extra_files:
        _support.write(root / rel, text)
    if gitignore is not None:
        _support.write(root / ".gitignore", gitignore)
    _support.write(root / "tracked.txt", "hello\n")
    _support.write_charter(root, requirements=REQ, gates=rows)
    sha = _support.init_repo(root)
    _support.write_charter(root, requirements=REQ, gates=rows, ratified=sha)
    _support.commit_all(root, "ratified")
    return sha


def say(name: str, **kv) -> None:
    print(f"\n## {name}")
    for key, value in kv.items():
        print(f"   {key}: {value}")


# --- Probe A: is a record out of reach by identity, or only by name? -------------------------
def probe_a_record_identity() -> None:
    root = BASE / "a-record-identity"
    root.mkdir(parents=True, exist_ok=True)
    _support.write(root / "tracked.txt", "hello\n")
    # 1. a genuine prior record, under a non-default directory
    _support.write(
        root / "history" / "runs.jsonl",
        '{"at":"2026-10-14T00:00:00Z","kind":"header","record":"keel/runs","version":1}\n'
        '{"at":"2026-10-14T00:01:00Z","commit":"deadbeef","kind":"audit"}\n',
    )
    # 2. an empty file with a record's default name
    _support.write(root / "audit" / "runs.jsonl", "")
    # 3. a record with its first line stripped, under a name that is not a record's
    _support.write(root / "notes" / "history.log", '{"commit":"deadbeef","kind":"audit"}\n')
    rows = [("coverage", "tracked.txt", _support.hash_file(root / "tracked.txt"))]
    _support.write_charter(root, requirements=REQ, gates=rows)
    sha = _support.init_repo(root)
    _support.write_charter(root, requirements=REQ, gates=rows, ratified=sha)
    _support.commit_all(root, "ratified")

    manifest = _manifest(root)
    paths = [f["path"] for f in manifest["files"]]
    skipped = {s["path"]: s["reason"] for s in manifest["skipped"]}
    say(
        "A  is a record out of reach by identity (its first line) or only by name?",
        genuine_record_at_history=f"exported: {'history/runs.jsonl' in paths}  "
        f"reason: {skipped.get('history/runs.jsonl', '(not skipped)')}",
        empty_file_named_runs=f"exported: {'audit/runs.jsonl' in paths}  "
        f"reason: {skipped.get('audit/runs.jsonl', '(not skipped)')}",
        header_stripped_odd_name=f"exported: {'notes/history.log' in paths}  "
        f"reason: {skipped.get('notes/history.log', '(not skipped)')}",
        manifest_warnings=manifest.get("warnings"),
        note="The first line is the identity. A record that keeps it is excluded wherever it lives; "
        "one that has lost it, under a name that is not a record's, is exported and not named.",
    )


# --- Probe B: an always-path that git ignores vanishes without being named as skipped --------
def probe_b_ignored_always_path() -> None:
    root = BASE / "b-ignored-gate"
    root.mkdir(parents=True, exist_ok=True)
    gate_rel = "gates/check.sh"
    _support.write(root / gate_rel, "print('ok')\n")
    rows = [("coverage", gate_rel, _support.hash_file(root / gate_rel))]
    _repo(root, rows, gitignore="gates/\n")
    m = _manifest(root)
    paths = [f["path"] for f in m["files"]]
    skipped = [s["path"] for s in m["skipped"]]
    say(
        "B  a gate path that git ignores is neither exported nor reported as omitted",
        always=f"{gate_rel} in manifest['always']: {gate_rel in m['always']}",
        exported=f"{gate_rel} in files: {gate_rel in paths}",
        reported=f"{gate_rel} in skipped: {gate_rel in skipped}",
        files=paths,
        skipped=skipped,
        what_the_design_claims="section 7 item 8: the omitted set may never contain a file a "
        "requirement, a gate or a finding names",
    )


# --- Probe C: the prompt is verified against the working-tree row, not the ratified one -----
def probe_c_working_tree_prompt() -> None:
    root = BASE / "c-prompt-tamper"
    root.mkdir(parents=True, exist_ok=True)
    stub = BASE / "c-stub.py"
    _support.write(
        stub,
        "import json,sys\nsys.stdin.read()\n"
        "print(json.dumps({'verdict':'clean','items':[],'unreviewed':[],"
        "'coverage':{'files_seen':3,'files_total':3}}))\n",
    )
    _support.write(root / "tracked.txt", "hello\n")
    _support.write(root / "review-prompt.md", "REVIEW V1 -- the ratified instruction\n")
    ratified_rows = [
        ("review-prompt", "review-prompt.md", _support.hash_file(root / "review-prompt.md"), "prompt")
    ]
    _support.write_charter(root, requirements=REQ, gates=ratified_rows)
    sha = _support.init_repo(root)
    _support.write_charter(root, requirements=REQ, gates=ratified_rows, ratified=sha)
    _support.commit_all(root, "ratified")
    ratified_hash = ratified_rows[0][2]

    # The attack: change the prompt AND the row's hash in the working tree only. Nothing committed.
    _support.write(root / "review-prompt.md", "REVIEW V2 -- weakened after ratification\n")
    tampered_rows = [
        ("review-prompt", "review-prompt.md", _support.hash_file(root / "review-prompt.md"), "prompt")
    ]
    _support.write_charter(root, requirements=REQ, gates=tampered_rows, ratified=sha)

    cmd = f'"{sys.executable}" "{stub}"'
    proc = _support.keel("review", str(root), "--reviewer", cmd, "--json")
    line = {}
    record = root / ".keel" / "runs.jsonl"
    if record.is_file():
        for raw in record.read_text(encoding="utf-8").splitlines():
            obj = json.loads(raw)
            if obj.get("kind") == "review":
                line = obj

    # Control: change only the prompt file (row left at the ratified hash) -> must refuse.
    control = BASE / "c-control"
    control.mkdir(parents=True, exist_ok=True)
    _support.write(control / "tracked.txt", "hello\n")
    _support.write(control / "review-prompt.md", "REVIEW V1\n")
    crows = [("review-prompt", "review-prompt.md", _support.hash_file(control / "review-prompt.md"), "prompt")]
    _support.write_charter(control, requirements=REQ, gates=crows)
    csha = _support.init_repo(control)
    _support.write_charter(control, requirements=REQ, gates=crows, ratified=csha)
    _support.commit_all(control, "ratified")
    (control / "review-prompt.md").write_text("REVIEW V2\n", encoding="utf-8")
    cproc = _support.keel("review", str(control), "--reviewer", cmd, "--json")

    say(
        "C  the prompt check: working-tree edit of the file AND its row, vs the file only",
        ratified_prompt_hash=ratified_hash,
        recorded_prompt_hash=line.get("prompt"),
        prompt_ratified=line.get("prompt_ratified"),
        ratified_in=line.get("ratified_in"),
        verdict=line.get("verdict"),
        edit_file_and_row_exit=proc.returncode,
        edit_file_only_exit=cproc.returncode,
        note="At 218c444 the first case was exit 0 / prompt_ratified true (the finding). At "
        "dbb70b5 it is exit 1 and the second case is 0 with the anchored text substituted, which "
        "is Proctor's open D15 ruling; see research/review-attack.md section 7.",
        what_the_design_claims="D15: its content hash is verified exactly like a gate's; a "
        "mismatch is exit 1 and no review runs",
    )


# --- Probe D: history_reachable is a constant, not a measurement ----------------------------
def probe_d_history_reachable() -> None:
    text = (REPO / "keel" / "review.py").read_text(encoding="utf-8")
    assignments = [ln.strip() for ln in text.splitlines() if "history_reachable" in ln]
    say(
        "D  history_reachable is a literal, not one of none|git|unknown",
        lines_in_review_py=assignments,
        what_the_design_claims="section 1 asked for none|git|unknown; D15 ruled the field a constant "
        "by construction and the design text now says a constant is not evidence (corrected at "
        "dbb70b5). The code literal is the ruled shape, not a finding",
    )


# --- Probe E: the manifest hashes raw worktree bytes, not git-normalized content -------------
def probe_e_worktree_bytes() -> None:
    root = BASE / "e-crlf"
    root.mkdir(parents=True, exist_ok=True)
    _support.write(root / "text.txt", "a\nb\n")
    rows = [("coverage", "tracked.txt", "sha256:" + "0" * 64)]
    sha = _repo(root, rows)
    _support.git(root, "config", "core.autocrlf", "true")
    (root / "text.txt").unlink()
    _support.git(root, "checkout", "--", "text.txt")
    raw = (root / "text.txt").read_bytes()
    m = _manifest(root)
    got = next(f["sha256"] for f in m["files"] if f["path"] == "text.txt")
    lf = hashlib.sha256(b"a\nb\n").hexdigest()
    # The same commit, a second checkout with the other autocrlf setting.
    _support.git(root, "config", "core.autocrlf", "false")
    (root / "text.txt").unlink()
    _support.git(root, "checkout", "--", "text.txt")
    raw2 = (root / "text.txt").read_bytes()
    m2 = _manifest(root)
    got2 = next(f["sha256"] for f in m2["files"] if f["path"] == "text.txt")
    say(
        "E  the manifest hashes worktree bytes, so freshness is checkout-dependent (D9's class)",
        commit=_support.git(root, "rev-parse", "--short", "HEAD").stdout.strip(),
        checkout_autocrlf_true=f"{len(raw)} bytes, {'CRLF' if b'\r\n' in raw else 'LF'}, "
        f"manifest={got[:20]}...",
        checkout_autocrlf_false=f"{len(raw2)} bytes, {'CRLF' if b'\r\n' in raw2 else 'LF'}, "
        f"manifest={got2[:20]}...",
        two_checkouts_differ=got != got2,
        sha256_of_stored_lf=lf,
        what_the_design_claims="section 7 item 9: one function, both sides; a difference would "
        "make every review permanently stale -- and D9: every hash is over git-normalized content",
    )


def main() -> int:
    global BASE
    SCRATCH.mkdir(parents=True, exist_ok=True)
    BASE = SCRATCH / uuid.uuid4().hex
    BASE.mkdir()
    for name, fn in [
        ("A", probe_a_record_identity),
        ("B", probe_b_ignored_always_path),
        ("C", probe_c_working_tree_prompt),
        ("D", probe_d_history_reachable),
        ("E", probe_e_worktree_bytes),
    ]:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - a probe that cannot run must say so
            print(f"\n## {name}  PROBE ERROR: {type(exc).__name__}: {exc}")
    print(f"\nscratch: {BASE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
