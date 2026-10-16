"""Re-record the R7 drift artefacts — the three pre-fix revisions and the current state — one Claude Code
call each, against **cleaned copies** of the revisions they name.

Run from the keel checkout:  python tests/_artefacts/r7-pre-fix-reviews.py

Why cleaned copies: the reviewed revisions carry two UTF-16 PowerShell captures and three local paths in
`docs/VERIFICATION.md` that name the author's machine. The reviewer is truthful and *quotes* them, so a
recording made against the revision as it stands puts that path back into the artefact. The copy is the
revision minus those files, with the doc's path elided to `<workspace>`; nothing else is touched, and the
copy is committed in its own worktree so the artefact records the copy it actually reviewed.

What this does NOT do: rewrite a recorded artefact. A re-record is a new run of the same review, and the
older artefact is replaced by it rather than edited.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

WS = Path(__file__).resolve().parents[3]  # <workspace>/keel/tests/_artefacts/<this file>
# The workspace root is derived from this file, never hardcoded: a recorded artefact must not
# carry a machine's layout, and these scripts write recorded artefacts.
KEEL, RG, TMP = WS / "keel", WS / "rentguard", WS / ".assay-tmp" / "r7"
WRAPPER = KEEL / "tests" / "_artefacts" / "claude-reviewer.py"
PY = sys.executable

# What the cleaning removes / elides, named so a reader of the artefact can tell what the copy was.
CAPTURES = [
    "tests/_artefacts/assay_cli_fake_probe_2026-10-14.txt",
    "tests/_artefacts/assay_money_paths_2026-10-14.txt",
]
ELIDE_FROM, ELIDE_TO = str(WS), "<workspace>"
ELIDE_IN = "docs/VERIFICATION.md"

# revision, output name, annotated header?
RUNS = [
    ("bd63920", "assay_r7_drift_pre_bd63920.json", False),
    ("ce69cea", "assay_r7_drift_pre_ce69cea.json", False),
    ("c512125", "assay_r7_drift_pre_c512125.json", False),
    ("310f449", "assay_r7_drift_one_call_2026-10-16.json", True),
]


def clean_copy(wt: Path) -> list[str]:
    """The revision minus the machine: captures removed, the doc's local root elided."""
    changed = []
    for rel in CAPTURES:
        p = wt / rel
        if p.exists():
            subprocess.run(["git", "-C", str(wt), "rm", "-q", "--cached", rel], capture_output=True)
            p.unlink()
            changed.append(f"removed {rel}")
    doc = wt / ELIDE_IN
    if doc.exists():
        text = doc.read_text(encoding="utf-8")
        if ELIDE_FROM in text:
            n = text.count(ELIDE_FROM)
            doc.write_text(text.replace(ELIDE_FROM, ELIDE_TO), encoding="utf-8", newline="")
            changed.append(f"elided {n} local path(s) in {ELIDE_IN}")
    return changed


def review(wt: Path, rev: str) -> tuple[int, float, str]:
    # A minimal env (PATH alone) broke the reviewer on the 2026-10-16 re-record: the Claude CLI is a
    # Bun binary and needs %SystemRoot% before it will make a network request, so every call came back
    # "no JSON object in the reviewer's output" with that sentence in claude's stderr. The reviewer's
    # *context* is what has to be clean (R4) — its environment is not, and starving it is not isolation.
    cmd = f'"{PY}" "{WRAPPER}"'
    t0 = time.time()
    proc = subprocess.run(
        [PY, "-m", "keelcheck", "review", str(wt), "--reviewer", cmd, "--prompt-repo", str(KEEL),
         "--record", str(TMP / f"{rev}.jsonl"), "--timeout", "600", "--json"],
        cwd=str(KEEL), capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return proc.returncode, round(time.time() - t0, 1), proc.stdout


for rev, out_name, annotated in RUNS:
    wt = TMP / f"rg-{rev}"
    subprocess.run(["git", "-C", str(RG), "worktree", "remove", "--force", str(wt)], capture_output=True)
    add = subprocess.run(["git", "-C", str(RG), "worktree", "add", "--detach", str(wt), rev],
                         capture_output=True, text=True)
    if add.returncode != 0:
        print(f"{rev}: worktree failed: {add.stderr.strip()[:200]}", flush=True)
        continue
    changed = clean_copy(wt)
    subprocess.run(["git", "-C", str(wt), "add", "-A"], capture_output=True)
    subprocess.run(["git", "-C", str(wt), "-c", "user.name=Gilbert",
                    "-c", "user.email=gilbert@keel.local", "commit", "-q", "-m",
                    f"cleaned copy of rentguard@{rev}: local paths elided to <workspace>, capture logs removed"],
                   capture_output=True)
    copy_commit = subprocess.run(["git", "-C", str(wt), "rev-parse", "HEAD"],
                                 capture_output=True, text=True).stdout.strip()

    code, wall, body = review(wt, rev)
    out = KEEL / "tests" / "_artefacts" / out_name
    if annotated:
        try:
            parsed = json.loads(body)
            rv, line = parsed.get("review", {}), parsed.get("line", {})
            out.write_text(
                f"# R7 drift half - one Claude Code call, re-recorded {time.strftime('%Y-%m-%d')}\n"
                f"# Reviewer: claude -p via tests/_artefacts/claude-reviewer.py (wrapped for keel's "
                f"one-JSON-object contract)\n"
                f"# Input: a CLEANED COPY of rentguard@{rev} at {copy_commit[:12]} (git worktree; local "
                f"paths elided to\n#   <workspace>, the two UTF-16 capture logs removed - see "
                f"PROJECT-STATE.md, the path-hygiene entry).\n"
                f"# Prompt: --prompt-repo keel; prompt_ratified={line.get('prompt_ratified')}, "
                f"ratified_in={line.get('ratified_in')}\n"
                f"# Result: exit {parsed.get('exit')}, verdict {rv.get('verdict')}, counts "
                f"{rv.get('counts')}, coverage {rv.get('coverage', {}).get('files_seen')}/"
                f"{rv.get('coverage', {}).get('files_total')}, wall {wall}s.\n\n" + body,
                encoding="utf-8", newline="")
        except Exception as exc:  # noqa: BLE001
            out.write_text(body, encoding="utf-8", newline="")
            print(f"{rev}: annotation skipped ({exc})", flush=True)
    else:
        out.write_text(body, encoding="utf-8", newline="")

    print(f"{rev}: exit {code}, {wall}s, copy {copy_commit[:10]}, "
          f"cleaned=[{'; '.join(changed)}], saved {out.name}", flush=True)
    subprocess.run(["git", "-C", str(RG), "worktree", "remove", "--force", str(wt)], capture_output=True)
