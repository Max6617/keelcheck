"""The clean-context drift review (R4, D15), driven from outside with stub reviewers.

A stub command is a complete double: the reviewer is a command the caller names, split with
`shlex`, run once with the export tree as cwd and the prompt on stdin. None of this needs a model.

**Verification tests, not red-first.** Mason landed the half at `6810818` before these could be
written, so they land against a contract that was written down first (D15 in `../PROJECT-STATE.md`)
and are green on arrival unless the code and the ruling disagree — in which case the failure is
named here as the finding. The one property that keeps them honest is that the tool never decides
its exit code from a verdict: the presence of a review for the current state is mechanical, what it
says is not.

Every observable is the CLI (`keel review`, `keel audit`) and `runs.jsonl`, never `keel/` internals.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

import _support

REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]
CLEAN = {"verdict": "clean", "items": [], "unreviewed": [],
         "coverage": {"files_seen": 4, "files_total": 4}}


# --- fixtures -----------------------------------------------------------------


def _stub(scratch, name: str, payload=None, *, raw: str | None = None, code: str | None = None) -> str:
    """A reviewer command string. Stubs live outside the repo so they never enter the export."""
    path = scratch.parent / f"{scratch.name}-stub-{name}.py"
    if raw is not None:
        body = raw
    elif code is not None:
        body = code
    else:
        body = ("import json,sys\nsys.stdin.read()\n"
                f"print(json.dumps({json.dumps(payload)}))\n")
    _support.write(path, body)
    return f'"{sys.executable}" "{path}"'


def _repo(scratch, *, gate: bool = True, prompt: bool = True, review_required: bool = False):
    """An auditable repo with one passing gate and (by default) a ratified prompt row."""
    _support.write(scratch / "tracked.txt", "hello\n")
    rows = []
    if gate:
        _support.write(scratch / "tools" / "gate.py", "print('ok')\n")
        rows.append(("coverage", "tools/gate.py", _support.hash_file(scratch / "tools" / "gate.py")))
    if prompt:
        _support.write(scratch / "review-prompt.md", "review the state against the original\n")
        rows.append(("review-prompt", "review-prompt.md",
                     _support.hash_file(scratch / "review-prompt.md"), "prompt"))
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=rows,
                           review_required=review_required)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=rows, ratified=sha,
                           review_required=review_required)
    _support.commit_all(scratch, "ratified")
    if gate:
        _support.keel("gate", "run", str(scratch), "--timeout", "10")  # so the audit is clean apart from the review
    return scratch


def _review_lines(scratch, record=None) -> list[dict]:
    path = Path(record) if record else scratch / ".keel" / "runs.jsonl"
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()
            if l.strip() and json.loads(l).get("kind") == "review"]


def _review(scratch, command: str, *extra):
    """Every reviewer runs under an explicit short timeout.

    `DEFAULT_TIMEOUT` in `review.py` is 600 s, so an environmental hang would hold the whole suite for
    ten minutes before reporting `timeout`. A test must never wait on a default it does not need
    (Gilbert, 2026-10-14), so the bound is added here unless the caller sets one deliberately.
    """
    extra = tuple(extra)
    if "--timeout" not in extra:
        extra = (*extra, "--timeout", "20")
    return _support.keel("review", str(scratch), "--reviewer", command, "--json", *extra)


def _audit_json(scratch, *extra):
    proc = _support.audit(scratch, "--json", *extra)
    return proc, json.loads(proc.stdout)


# --- the state is always reported ---------------------------------------------


def test_the_review_state_is_always_reported_and_only_required_makes_it_divergence(scratch):
    """D15: the state is printed whether or not a review is required, and the missing line is
    divergence only when the charter says `Review: required` or the caller passes `--require-review`."""
    _repo(scratch)

    plain, plain_doc = _audit_json(scratch)
    assert plain.returncode == 0, f"an unrequired missing review changed the exit code:\n{_support.combined(plain)}"
    assert plain_doc["review"]["status"] == "missing", "the state is not reported when not required"

    required, required_doc = _audit_json(scratch, "--require-review")
    assert required.returncode == 1, "a required missing review did not fail the audit"
    assert required_doc["review"]["status"] == "missing"
    assert any(f["kind"] == "review" for f in required_doc["findings"]), "the finding is not named"


def test_a_charter_declaring_review_required_makes_a_missing_review_divergence(scratch):
    """The charter's own declaration, not only the flag."""
    _repo(scratch, review_required=True)

    missing, _ = _audit_json(scratch)
    assert missing.returncode == 1, "`Review: required` in the charter did not fail a missing review"

    assert _review(scratch, _stub(scratch, "clean", CLEAN)).returncode == 0
    fresh, doc = _audit_json(scratch)
    assert fresh.returncode == 0, f"a fresh review did not satisfy the charter:\n{_support.combined(fresh)}"
    assert doc["review"]["status"] == "fresh"


# --- verdicts ------------------------------------------------------------------


@pytest.mark.parametrize("label,payload,expected_exit,verdict", [
    ("clean", CLEAN, 0, "clean"),
    ("partial, unreviewed named", {**CLEAN, "unreviewed": ["the gate runner"]}, 1, "partial"),
    ("partial, coverage short", {**CLEAN, "coverage": {"files_seen": 1, "files_total": 4}}, 1, "partial"),
    ("divergence with a verified item", {**CLEAN, "verdict": "divergence",
     "items": [{"class": "missing", "subject": "R1", "evidence": "CHARTER.md", "why": "x",
                "confidence": "high"}]}, 1, "divergence"),
    ("divergence, evidence escapes", {**CLEAN, "verdict": "divergence",
     "items": [{"class": "shifted", "subject": "x", "evidence": "../../outside.md", "why": "x",
                "confidence": "low"}]}, 1, "unverified"),
])
def test_a_verdict_is_recorded_and_mapped_to_an_exit_code(scratch, label, payload, expected_exit, verdict):
    _repo(scratch)

    proc = _review(scratch, _stub(scratch, "v", payload))
    line = _review_lines(scratch)[-1]

    assert proc.returncode == expected_exit, (
        f"{label}: exit {proc.returncode}, wanted {expected_exit}\n{_support.combined(proc)}")
    assert line["result"] == "pass", f"{label}: the process result is not pass"
    assert line["verdict"] == verdict, f"{label}: verdict {line.get('verdict')!r}, wanted {verdict!r}"


@pytest.mark.parametrize("label,evidence,verified", [
    ("a file that is in the export", "CHARTER.md", True),
    ("a requirement id in the charter", "R1", True),
    ("a file that does not exist", "no-such-file.md", False),
    ("a requirement id that does not exist", "R999", False),
])
def test_evidence_is_checked_against_the_export_and_the_charter(scratch, label, evidence, verified):
    """D15: evidence must "resolve to a path in the export **or** a requirement id in the charter".
    A model's citation is checked, never trusted.

    Measured at `117ac7c`: `_inside_export` returns True for *any* relative string, because
    `Path.resolve()` does not require the target to exist and the only test is that the result sits
    under the export root. So `no-such-file.md` and `R999` both count as verified, and the id branch
    the ruling names is not implemented at all.
    """
    _repo(scratch)
    payload = {**CLEAN, "verdict": "divergence",
               "items": [{"class": "missing", "subject": "R1", "evidence": evidence,
                          "why": "x", "confidence": "high"}]}

    _review(scratch, _stub(scratch, "ev", payload))
    counts = _review_lines(scratch)[-1]["items"]

    assert counts["verified"] == (1 if verified else 0), (
        f"{label}: {evidence!r} was counted as verified evidence; a citation that resolves to "
        f"nothing is not evidence (counts={counts})")
    assert counts["unverified"] == (0 if verified else 1), f"{label}: counts={counts}"


# --- the reviewer failed, and it is recorded either way ------------------------


@pytest.mark.parametrize("label,stub_kwargs,expected_result", [
    ("a class outside the three", {"payload": {**CLEAN, "items": [{"class": "wrong", "subject": "x",
     "evidence": "CHARTER.md", "why": "x", "confidence": "low"}]}}, "malformed"),
    ("output that is not JSON", {"raw": "print('nope')\n"}, "malformed"),
    ("a non-zero exit", {"code": "import sys\nsys.exit(3)\n"}, "error"),
    ("a command that cannot start", {"command": '"/nonexistent/keel-stub-does-not-exist"'}, "error"),
    ("a timeout", {"code": "import time\ntime.sleep(30)\n", "extra": ("--timeout", "1")}, "timeout"),
])
def test_a_failed_review_is_recorded_and_exits_2(scratch, label, stub_kwargs, expected_result):
    """D15: every failure mode is recorded with its reason and exits 2 — the line is written in every
    case, so a failed review is a record, not an absence."""
    _repo(scratch)
    command = stub_kwargs.pop("command", None) or _stub(scratch, "f", **{k: v for k, v in stub_kwargs.items() if k != "extra"})
    extra = stub_kwargs.get("extra", ())

    proc = _review(scratch, command, *extra)
    lines = _review_lines(scratch)

    assert proc.returncode == 2, f"{label}: exit {proc.returncode}, wanted 2\n{_support.combined(proc)}"
    assert lines, f"{label}: no review line was written"
    assert lines[-1]["result"] == expected_result, f"{label}: {lines[-1].get('result')!r}"
    assert lines[-1].get("reason"), f"{label}: the failure has no reason"


# --- freshness, and the two round trips ----------------------------------------


def test_a_review_is_fresh_then_stale_on_one_byte_then_fresh_again(scratch):
    """Items 9 and 10: one manifest function on both sides, and staleness keyed to the state's
    content — so a state that changes away and back hashes the same as the older review."""
    _repo(scratch)
    assert _review(scratch, _stub(scratch, "clean", CLEAN)).returncode == 0
    fresh_manifest = _review_lines(scratch)[-1]["manifest"]

    fresh, doc = _audit_json(scratch, "--require-review")
    assert fresh.returncode == 0 and doc["review"]["status"] == "fresh", (
        f"review-then-audit is not fresh:\n{_support.combined(fresh)}")

    _support.write(scratch / "tracked.txt", "hellp\n")
    stale, stale_doc = _audit_json(scratch, "--require-review")
    assert stale.returncode == 1, "a one-byte change left the review fresh"
    assert stale_doc["review"]["status"] == "stale"
    out = _support.combined(stale)
    assert fresh_manifest in out, "the stale report does not name the recorded manifest"
    assert stale_doc["review"].get("manifest"), "the stale report does not carry the current manifest"

    _support.write(scratch / "tracked.txt", "hello\n")
    again, doc = _audit_json(scratch, "--require-review")
    assert again.returncode == 0 and doc["review"]["status"] == "fresh", (
        "reverting the state did not restore freshness (item 10's caveat)")


def test_a_failed_review_never_satisfies_require_review(scratch):
    _repo(scratch)
    assert _review(scratch, _stub(scratch, "boom", code="import sys\nsys.exit(3)\n")).returncode == 2

    proc, doc = _audit_json(scratch, "--require-review")

    assert proc.returncode == 1, "a failed review satisfied a required one"
    assert doc["review"]["status"] == "failed"


def test_a_partial_review_still_satisfies_require_review(scratch):
    """Pinned because it is easy to assume the opposite: presence is mechanical, the verdict is not.
    A partial review *happened* for this state, so it satisfies a required one and says `partial`."""
    _repo(scratch, review_required=True)
    assert _review(scratch, _stub(scratch, "partial", {**CLEAN, "unreviewed": ["the hook installer"]})).returncode == 1

    proc, doc = _audit_json(scratch)

    assert doc["review"]["line"]["verdict"] == "partial", doc["review"]
    assert doc["review"]["status"] == "fresh", (
        "a partial review is a review that happened; only its verdict is uncertain")
    assert proc.returncode == 0, (
        f"a partial review failed a required one; presence is mechanical, the verdict is not:\n"
        f"{_support.combined(proc)}")


# --- the prompt is a hashed artefact ------------------------------------------


def test_a_working_tree_prompt_edit_cannot_weaken_the_review(scratch):
    """Gilbert's ruling (2026-10-14): the instruction handed over is the **anchored blob**, so an
    edit to the working copy cannot weaken a review — it cannot reach the reviewer at all. The edit
    is `[gate]` drift the audit names, not a review fact.

    The file *and its row* edited together is the other rule and is still refused
    (`test_the_prompt_is_verified_against_the_ratified_table_not_the_working_tree`).
    """
    _repo(scratch)
    ratified_text = (scratch / "review-prompt.md").read_text(encoding="utf-8")
    _support.write(scratch / "review-prompt.md", "a weakened instruction\n")

    proc = _review(scratch, _stub(scratch, "clean", CLEAN))

    assert proc.returncode == 0, _support.combined(proc)
    line = _review_lines(scratch)[-1]
    assert line["prompt_ratified"] is True
    tree = Path(line["export"])
    assert (tree / "REVIEW-PROMPT.md").read_text(encoding="utf-8") == ratified_text, (
        "the reviewer was handed the weakened working copy instead of the anchored instruction")

    # D21(iii): the difference travels with the record instead of being silent
    assert line.get("working_copy_differs") is True, (
        f"the line does not disclose that the working copy differs: {sorted(line)}")
    working_hash = _support.hash_file(scratch / "review-prompt.md")
    assert working_hash in json.dumps(line), (
        "the line does not carry the working file's hash, so the disclosure cannot be checked "
        f"against the file it is about ({working_hash})")

    _, doc = _audit_json(scratch)
    assert any(f["kind"] == "gate" and "review-prompt" in f["subject"] for f in doc["findings"]), (
        "the working-tree prompt edit is not named as drift by the audit")


def test_a_self_inconsistent_anchor_is_refused(scratch):
    """D21(iv): the refusal that stays. If the ratified row's hash does not match the prompt blob at
    the ratified commit, the anchor contradicts itself and no review runs — exit 1, no line."""
    _support.write(scratch / "tracked.txt", "hello\n")
    _support.write(scratch / "review-prompt.md", "the ratified instruction\n")
    bogus = "sha256:" + "0" * 64  # well-formed and wrong: the row and its own blob disagree
    rows = [("review-prompt", "review-prompt.md", bogus, "prompt")]
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=rows)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=rows, ratified=sha)
    _support.commit_all(scratch, "ratified with a row that contradicts its own blob")

    proc = _review(scratch, _stub(scratch, "clean", CLEAN))

    assert proc.returncode == 1, (
        f"a self-inconsistent anchor ran a review: exit {proc.returncode}\n{_support.combined(proc)}")
    assert not _review_lines(scratch), "a review was recorded against a self-inconsistent anchor"


def test_an_unratified_prompt_runs_and_is_recorded_as_such(scratch):
    """With no ratified prompt row, `--prompt` is an unlocked instruction — visible as such."""
    _repo(scratch, gate=False, prompt=False)
    path = _support.write(scratch.parent / f"{scratch.name}-prompt.md", "an unlocked instruction\n")

    proc = _review(scratch, _stub(scratch, "clean", CLEAN), "--prompt", str(path))

    assert proc.returncode == 0, f"{_support.combined(proc)}"
    assert _review_lines(scratch)[-1]["prompt_ratified"] is False, "the unlocked prompt is not visible"


def test_with_no_prompt_at_all_the_review_cannot_run_honestly(scratch):
    _repo(scratch, gate=False, prompt=False)

    proc = _review(scratch, _stub(scratch, "clean", CLEAN))

    assert proc.returncode == 2, f"exit {proc.returncode}, wanted 2\n{_support.combined(proc)}"


# --- kinds, and what defeats vacuity ------------------------------------------


def test_an_unknown_kind_is_a_gate_divergence(scratch):
    _repo(scratch, gate=False, prompt=False)
    _support.write(scratch / "tools" / "weird.py", "print('weird')\n")
    rows = [("weird", "tools/weird.py", _support.hash_file(scratch / "tools" / "weird.py"), "banana")]
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=rows)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=rows, ratified=sha)
    _support.commit_all(scratch, "unknown kind")

    proc, doc = _audit_json(scratch)

    assert proc.returncode == 1
    assert any(f["kind"] == "gate" and "weird" in f["subject"] for f in doc["findings"]), doc["findings"]


def test_only_gate_rows_defeat_vacuity(scratch):
    """A prompt row is not a runnable gate: it does not satisfy the hash half, and it is not run."""
    _repo(scratch, gate=False, prompt=True)

    run = _support.keel("gate", "run", str(scratch), "--json")
    proc, doc = _audit_json(scratch)

    assert run.returncode == 1, "a prompt row was treated as a runnable gate"
    assert any(f["kind"] == "vacuity" for f in doc["findings"]), (
        f"a prompt row defeated vacuity:\n{doc['findings']}")


# --- the reviewer is a command, never a shell ----------------------------------


def test_the_reviewer_string_is_not_run_through_a_shell(scratch):
    """D15: `shlex`, no shell. If a shell were used, the trailing `touch` would run."""
    _repo(scratch)
    marker = scratch.parent / f"{scratch.name}-SHELL-MARKER"
    command = f'"{sys.executable}" -c pass; touch "{marker}"'

    proc = _review(scratch, command)

    assert not marker.exists(), "the reviewer command was run through a shell"
    assert proc.returncode == 2, "a command that cannot do its job did not exit 2"


# --- what the reviewer was handed ---------------------------------------------


def test_the_export_has_no_history_and_no_secrets(scratch):
    """R4/W2: the reviewer's reach is the mechanism. No `.git`, the record root excluded, the
    deny-list applied, and `history_reachable: none` recorded."""
    _repo(scratch)
    _support.write(scratch / ".env", "SECRET=1\n")
    _support.write(scratch / "private.pem", "-----BEGIN KEY-----\n")
    _support.git(scratch, "add", "-A")
    _support.commit_all(scratch, "secrets")

    assert _review(scratch, _stub(scratch, "clean", CLEAN)).returncode == 0
    line = _review_lines(scratch)[-1]
    tree = Path(line["export"])
    names = {p.name for p in tree.iterdir()}

    assert line.get("history_reachable"), "the record states nothing about the reviewer's reach"
    assert not (tree / ".git").exists(), "the export ships .git"
    assert "CHARTER.md" in names, "the export does not ship the charter"
    assert ".env" not in names, "the export ships a secret file"
    assert "private.pem" not in names, "the export ships a key file"


def test_the_export_carries_the_prompt_the_reviewer_was_told_to_follow(scratch):
    """D15 names the export's contents: the current state "plus `REVIEW-PROMPT.md`,
    `FROZEN-ORIGINAL.md`, `MECHANICAL-FINDINGS.txt` and `KEEL-MANIFEST.json`", and §2 says the prompt
    "is *in the export*, so what the reviewer was told is part of what was handed over".

    The prompt here lives **outside** the repository, so the only way it can be in the export is if
    the runner writes it. Measured at `117ac7c`: the export has `FROZEN-ORIGINAL.md`,
    `MECHANICAL-FINDINGS.txt` and `KEEL-MANIFEST.json`, and no `REVIEW-PROMPT.md` — the instruction
    reaches the reviewer on stdin and is not part of what was handed over.
    """
    _repo(scratch, gate=False, prompt=False)
    instruction = "review this state against the frozen original\n"
    outside = _support.write(scratch.parent / f"{scratch.name}-outside-prompt.md", instruction)

    assert _review(scratch, _stub(scratch, "clean", CLEAN), "--prompt", str(outside)).returncode == 0
    tree = Path(_review_lines(scratch)[-1]["export"])

    assert (tree / "REVIEW-PROMPT.md").is_file(), (
        "the export does not carry the instruction the reviewer was given, so what it was told is "
        f"not part of what was handed over (files: {sorted(p.name for p in tree.iterdir())})")
    assert instruction.strip() in (tree / "REVIEW-PROMPT.md").read_text(encoding="utf-8")


def test_a_committed_record_directory_is_never_exported(scratch):
    """Gilbert's export finding, fixed in `e9ec9a1` before this test was written — named rather than
    hidden. A record directory that has been **committed** is otherwise a tracked file like any other,
    and the reviewer must not be handed prior audits, prior verdicts or the history it exists to be
    denied. The record is denied *by role*, not only by where this run put it."""
    _repo(scratch)  # the gate run wrote .keel/runs.jsonl
    _support.git(scratch, "add", "-A")
    _support.commit_all(scratch, "commit the prior record")
    outside = scratch.parent / f"{scratch.name}-records"
    outside.mkdir()

    proc = _review(scratch, _stub(scratch, "clean", CLEAN), "--record", str(outside))

    assert proc.returncode == 0, _support.combined(proc)
    line = _review_lines(scratch, record=outside / "runs.jsonl")[-1]
    tree = Path(line["export"])
    manifest = (tree / "KEEL-MANIFEST.json").read_text(encoding="utf-8")

    assert not (tree / ".keel" / "runs.jsonl").exists(), (
        "the export ships a committed prior run record — the reviewer can read the history it is "
        "supposed to be blind to")
    assert "denied: record directory" in manifest, (
        f"the manifest does not record the denial (manifest: {manifest[:300]})")


def test_the_vacuity_message_names_what_was_actually_tested(scratch):
    """Gilbert's requirement on `18023d9`: assert the **message**, not only the exit code. keel's own
    audit printed `gates ratified: 1` and `no gate is declared or ratified` in the same report, so a
    reader could not tell what the hash half had actually checked."""
    _repo(scratch, gate=False, prompt=True)  # the ratified table holds a prompt row and no gate

    _, doc = _audit_json(scratch)
    vacuity = [f for f in doc["findings"] if f["kind"] == "vacuity"]
    assert vacuity, "a repo whose only ratified row is a prompt is not reported as vacuous"
    message = vacuity[0]["message"]
    assert "prompt row" in message, f"the message does not name the prompt rows: {message!r}"
    assert "no executable gate" in message, f"the message does not say what is missing: {message!r}"

    # and when the working charter declares a gate that was never ratified, say that instead
    anchor = re.search(r"Ratified at:\s*([0-9a-f]{7,40})",
                       (scratch / "CHARTER.md").read_text(encoding="utf-8")).group(1)
    _support.write(scratch / "tools" / "gate2.py", "print('ok')\n")
    rows = [("review-prompt", "review-prompt.md",
             _support.hash_file(scratch / "review-prompt.md"), "prompt"),
            ("coverage", "tools/gate2.py", _support.hash_file(scratch / "tools" / "gate2.py"))]
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=rows, ratified=anchor)

    _, doc = _audit_json(scratch)
    message = [f for f in doc["findings"] if f["kind"] == "vacuity"][0]["message"]

    assert "declared in the working charter and not ratified" in message, (
        f"an unratified executable gate is not named as such: {message!r}")


# --- the prompt can come from another repository (R7) --------------------------


def test_a_prompt_can_be_taken_from_another_repositorys_ratified_table(scratch):
    """R7: a review of the read-only rentguard input can name keel's own ratified prompt, and the
    record says which repository and anchor the prompt was verified against — an unlocked instruction
    is for the case where nothing is ratified, not for this one."""
    source = scratch.parent / f"{scratch.name}-prompt-source"
    _support.write(source / "tracked.txt", "hello\n")
    _support.write(source / "review-prompt.md", "the ratified instruction\n")
    rows = [("review-prompt", "review-prompt.md",
             _support.hash_file(source / "review-prompt.md"), "prompt")]
    _support.write_charter(source, requirements=REQUIREMENTS, gates=rows)
    sha = _support.init_repo(source)
    _support.write_charter(source, requirements=REQUIREMENTS, gates=rows, ratified=sha)
    _support.commit_all(source, "ratified")
    _repo(scratch, gate=False, prompt=False)  # the reviewed repo has no prompt of its own

    proc = _review(scratch, _stub(scratch, "clean", CLEAN), "--prompt-repo", str(source))

    assert proc.returncode == 0, _support.combined(proc)
    line = _review_lines(scratch)[-1]
    assert line["prompt_ratified"] is True, "a prompt taken from a ratified table is not marked ratified"
    assert line.get("ratified_in"), "the record does not name where the prompt was ratified"
    assert source.name in line["ratified_in"] and sha[:7] in line["ratified_in"], (
        f"the record names something else: {line['ratified_in']!r}")


def test_a_working_tree_edit_in_the_prompt_repository_cannot_weaken_the_review(scratch):
    """Same rule across repositories: `--prompt-repo` hands over the anchored blob of the repository
    the prompt was ratified in, so a working-tree edit there does not reach the reviewer either."""
    source = scratch.parent / f"{scratch.name}-prompt-source2"
    _support.write(source / "tracked.txt", "hello\n")
    _support.write(source / "review-prompt.md", "the ratified instruction\n")
    rows = [("review-prompt", "review-prompt.md",
             _support.hash_file(source / "review-prompt.md"), "prompt")]
    _support.write_charter(source, requirements=REQUIREMENTS, gates=rows)
    sha = _support.init_repo(source)
    _support.write_charter(source, requirements=REQUIREMENTS, gates=rows, ratified=sha)
    _support.commit_all(source, "ratified")
    _repo(scratch, gate=False, prompt=False)
    _support.write(source / "review-prompt.md", "weakened instruction\n")

    proc = _review(scratch, _stub(scratch, "clean", CLEAN), "--prompt-repo", str(source))

    assert proc.returncode == 0, _support.combined(proc)
    line = _review_lines(scratch)[-1]
    assert line["prompt_ratified"] is True and source.name in line["ratified_in"]
    exported = (Path(line["export"]) / "REVIEW-PROMPT.md").read_text(encoding="utf-8")
    assert exported.strip() == "the ratified instruction", (
        f"the reviewer was handed the weakened working copy: {exported!r}")


# --- the export's limits, and where it goes ------------------------------------


def test_a_capped_export_still_carries_every_path_a_row_or_the_charter_names(scratch):
    """Design item 8, the honesty property rather than a limit: the cap may omit files, never a path
    a requirement, a gate row or the charter names. A capped review that reads clean is the cap used
    as a hiding place.

    `big.bin` sorts before `tools/gate.py`, so the byte cap trips on the big file — the gate script
    is exactly the path a naive cap drops first, and it is a path a gate row names.
    """
    _repo(scratch)
    _support.write(scratch / "big.bin", "x" * (21 * 1024 * 1024))
    _support.git(scratch, "add", "-A")
    _support.commit_all(scratch, "over the byte cap")

    assert _review(scratch, _stub(scratch, "clean", CLEAN)).returncode in (0, 1)
    line = _review_lines(scratch)[-1]
    tree = Path(line["export"])

    assert line["truncated"] is True, (
        f"a 21 MB repository did not trip the cap ({line['bytes']} bytes recorded)")
    assert (tree / "tools" / "gate.py").is_file(), (
        "the cap omitted a path a gate row names: the reviewer was told the review was clean while "
        "it was never shown the mechanism")
    assert (tree / "CHARTER.md").is_file(), "the cap omitted the charter"


def test_the_export_goes_where_the_caller_says(scratch):
    """`--export DIR` is cheap surface nothing covered."""
    _repo(scratch)
    target = scratch.parent / f"{scratch.name}-export-dir"

    proc = _review(scratch, _stub(scratch, "clean", CLEAN), "--export", str(target))

    assert proc.returncode == 0, _support.combined(proc)
    tree = Path(_review_lines(scratch)[-1]["export"])
    assert target in tree.parents or tree == target, f"the export went to {tree}, not under {target}"
    assert (tree / "CHARTER.md").is_file()


def test_output_over_one_megabyte_is_malformed(scratch):
    """D15 caps the reviewer's stdout at 1 MB; over it the output is `malformed`, never parsed."""
    _repo(scratch)
    command = _stub(scratch, "huge", code="print('x' * (1024 * 1024 + 100))\n")

    proc = _review(scratch, command)
    line = _review_lines(scratch)[-1]

    assert proc.returncode == 2, f"exit {proc.returncode}, wanted 2"
    assert line["result"] == "malformed", f"over-cap output was read as {line['result']!r}"
    assert "byte" in (line.get("reason") or "").lower(), (
        f"the reason does not name the cap: {line.get('reason')!r}")


# --- Sift's outside attack, independently reproduced (218c444) ------------------


def test_the_prompt_is_verified_against_the_ratified_table_not_the_working_tree(scratch):
    """D15: the prompt's hash is "verified exactly like a gate's" — and a gate's is verified against
    the table **at the ratification commit** (D1), never against the working tree.

    Measured at `218c444`: edit the prompt *and* its working-tree row hash together, commit nothing,
    and the review exits 0 recording `prompt_ratified: true` with `ratified_in: <repo>@<anchor>` —
    provenance the anchor never gave. The control (prompt edited, row untouched) does exit 1, which
    is why the gap reads as covered: the check that exists is self-consistency.
    """
    _repo(scratch)
    _support.write(scratch / "review-prompt.md", "a weakened instruction\n")
    weakened = _support.hash_file(scratch / "review-prompt.md")
    text = (scratch / "CHARTER.md").read_text(encoding="utf-8")
    ratified = re.search(r"review-prompt\.md\s*\|\s*(sha256:[0-9a-f]{64})", text).group(1)
    _support.write(scratch / "CHARTER.md", text.replace(ratified, weakened))

    proc = _review(scratch, _stub(scratch, "clean", CLEAN))
    lines = _review_lines(scratch)

    assert proc.returncode == 1, (
        "a prompt re-ratified in the working tree ran, and the reviewer was handed the weakened "
        f"instruction:\n{_support.combined(proc)}")
    assert not lines or lines[-1].get("prompt_ratified") is not True, (
        "the review line carries provenance the anchor never gave")


def test_a_path_a_gate_row_names_is_never_silently_absent_from_the_export(scratch):
    """§7.8 / D15: the cap may not omit a path a requirement, a row or the charter names, and every
    omission is listed with a reason. Measured at `218c444`: a gitignored gate path sits in the
    manifest's `always`, in neither `files` nor `skipped`, and `skipped: []` reports a clean export
    while the mechanism the charter rests on is gone — the vacuity class, inside the export."""
    _support.write(scratch / ".gitignore", "gates/\n")
    _support.write(scratch / "gates" / "check.sh", "#!/bin/sh\nexit 0\n")
    _support.write(scratch / "tracked.txt", "hello\n")
    rows = [("check", "gates/check.sh", _support.hash_file(scratch / "gates" / "check.sh"))]
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=rows)
    sha = _support.init_repo(scratch)  # .gitignore keeps gates/ out of the commit
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=rows, ratified=sha)
    _support.commit_all(scratch, "ratified")
    outside = _support.write(scratch.parent / f"{scratch.name}-instruction.md", "instruction\n")

    proc = _review(scratch, _stub(scratch, "clean", CLEAN), "--prompt", str(outside))
    assert proc.returncode == 0, _support.combined(proc)
    tree = Path(_review_lines(scratch)[-1]["export"])
    manifest = json.loads((tree / "KEEL-MANIFEST.json").read_text(encoding="utf-8"))
    named = "gates/check.sh"

    assert named in manifest.get("always", []), (
        f"the manifest does not list the path a gate row names at all: {sorted(manifest)}")

    def paths(entries):
        return {e if isinstance(e, str) else e.get("path") for e in entries}

    assert named in paths(manifest.get("files", [])) or named in paths(manifest.get("skipped", [])), (
        f"{named} is named by a gate row and is in neither the exported files nor the skipped list: "
        f"files={manifest.get('files')} skipped={manifest.get('skipped')}")


def test_a_review_of_an_unratified_charter_records_a_null_anchor(scratch):
    """Gilbert's ruling for R7 (option b, D4 untouched): D12 forbids an unanchored **audit**, but an
    unanchored **review** runs and records `ratified: null` — the prompt's own ratification is
    independent of the audited charter's anchor, and freshness is the manifest, not the anchor.

    Measured at `bcf4bf5`: `keel review ../rentguard` exits 2 in 0 s, so the demonstration's own
    frozen input cannot be reviewed at all. The faithful copy was the interim evidence; this is the
    fix.
    """
    _support.write(scratch / "tracked.txt", "hello\n")
    _support.write_charter(scratch, requirements=REQUIREMENTS)  # no `Ratified at:` line, no rows
    _support.init_repo(scratch)
    outside = _support.write(scratch.parent / f"{scratch.name}-instruction.md", "instruction\n")

    proc = _review(scratch, _stub(scratch, "clean", CLEAN), "--prompt", str(outside))
    lines = _review_lines(scratch)

    assert proc.returncode == 0, (
        f"a review of a charter that names no anchor did not run:\n{_support.combined(proc)}")
    assert lines, "no review line was written"
    assert lines[-1]["ratified"] is None, (
        f"the unanchored review claims an anchor: {lines[-1]['ratified']!r}")
    assert lines[-1]["prompt_ratified"] is False, "an unlocked --prompt is not marked unratified"


def test_the_record_does_not_claim_a_history_free_reviewer(scratch):
    """Sift's finding 5 and Gilbert's ruling for the demonstration: §1 promised `none | git | unknown`
    and the field was a literal `none`.

    What keel can prove is that the **export** has no `.git`. It cannot observe what a command the
    caller names loads from its own harness — the demonstration's reviewer is Claude Code, which reads
    the user's configuration and may carry user-level memory or project files. So the record must say
    `unknown`, or `none` reads as a measurement and is a constant.
    """
    _repo(scratch)

    assert _review(scratch, _stub(scratch, "clean", CLEAN)).returncode == 0
    line = _review_lines(scratch)[-1]

    assert line["history_reachable"] == "unknown", (
        f"the record claims {line['history_reachable']!r} for a caller-named command: the export's "
        ".git-lessness is provable, the reviewer's own context is not")


def test_the_export_never_hands_the_reviewer_the_active_record_file(scratch):
    """D17/D15: the record is out of the reviewer's reach *by role*. Measured at `218c444`:
    `--record <repo>/prior-runs.jsonl` is exported, because the active-root exclusion fires only when
    the record root is a strict ancestor of the repository — and `record_paths` deliberately accepts
    any file or directory, so the tool cannot assume it lives under `.keel`."""
    _repo(scratch)
    record = scratch / "prior-runs.jsonl"
    record.write_text("", encoding="utf-8")
    _support.git(scratch, "add", "-A")
    _support.commit_all(scratch, "commit a prior record at the root")

    proc = _review(scratch, _stub(scratch, "clean", CLEAN), "--record", str(record))

    assert proc.returncode == 0, _support.combined(proc)
    line = _review_lines(scratch, record=record)[-1]
    tree = Path(line["export"])

    assert not (tree / "prior-runs.jsonl").exists(), (
        "the active record file was handed to the reviewer: it can read the prior runs it exists to "
        "be blind to")


def test_the_manifest_is_the_same_for_one_state_under_both_autocrlf_configs(scratch):
    """§7.9 and D9: every hash is over git-normalized content, and one function serves both sides, so
    a legitimate difference in checkout form must not produce a false red.

    **Substitute evidence, and why.** Two clones would be the natural shape, but `git clone` spawns
    git's `sh`, which cannot start on this host. `core.autocrlf` is also repo-wide, so a linked
    worktree is not a second checkout either — setting the config there rewrites the shared config.
    So the property is measured on **one state under both configurations**: same commit, the config
    flipped, the worktree re-checked out with `git checkout -f -- .` before each review, and one
    manifest hash required from both.

    The fixture is written LF (`_support.write`), so the blobs are LF and `autocrlf=true` is what
    materialises CRLF — the asymmetry this test exists to survive.
    """
    _repo(scratch, prompt=False)
    prompt = _support.write(scratch.parent / f"{scratch.name}-instruction.md", "instruction\n")

    observed = {}
    for autocrlf in ("false", "true"):
        _support.git(scratch, "config", "core.autocrlf", autocrlf)
        # git skips rewriting files it believes unchanged, so force the smudge per configuration
        (scratch / "tracked.txt").unlink()
        _support.git(scratch, "checkout", "-f", "--", "tracked.txt")
        bytes_now = (scratch / "tracked.txt").read_bytes()
        observed[autocrlf] = bytes_now
        assert _review(scratch, _stub(scratch, f"clean-{autocrlf}", CLEAN), "--prompt",
                       str(prompt)).returncode == 0

    assert observed["true"].endswith(b"\r\n") and not observed["false"].endswith(b"\r\n"), (
        f"precondition: the two configurations did not produce different worktree bytes: {observed}")

    lines = _review_lines(scratch)
    manifests = [line["manifest"] for line in lines][-2:]

    assert manifests[0] == manifests[1], (
        f"one state yields two manifest hashes ({manifests[0][:16]} vs {manifests[1][:16]}), so a "
        "review is stale on any checkout with the other line-ending configuration — D9's class, and "
        "the false red that re-running cannot clear")
