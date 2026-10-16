"""Run the drift review at the three pre-fix revisions (D7's other end). One Claude Code call each."""
import subprocess, sys
from pathlib import Path

WS = Path(__file__).resolve().parents[3]  # <workspace>/keel/tests/_artefacts/<this file>
# The workspace root is derived from this file, never hardcoded: a recorded artefact must not
# carry a machine's layout, and these scripts write recorded artefacts.
KEEL, RG, TMP = WS / "keel", WS / "rentguard", WS / ".assay-tmp" / "r7"
WRAPPER = KEEL / "tests" / "_artefacts" / "claude-reviewer.py"
PY = sys.executable
for rev in ("bd63920", "ce69cea", "c512125"):
    wt = TMP / f"rg-{rev}"
    subprocess.run(["git", "-C", str(RG), "worktree", "add", "--detach", str(wt), rev], capture_output=True)
    cmd = f'"{PY}" "{WRAPPER}"'
    # A minimal env (PATH alone) broke the reviewer on the 2026-10-16 re-record: the Claude CLI is a
    # Bun binary and needs %SystemRoot% before it will make a network request, so every call came back
    # "no JSON object in the reviewer's output" with that sentence in claude's stderr. The reviewer's
    # *context* is what has to be clean (R4) — its environment is not, and starving it is not isolation.
    proc = subprocess.run(
        [PY, "-m", "keelcheck", "review", str(wt), "--reviewer", cmd, "--prompt-repo", str(KEEL),
         "--record", str(TMP / f"pre-{rev}.jsonl"), "--timeout", "600", "--json"],
        cwd=str(KEEL), capture_output=True, text=True, encoding="utf-8",
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    out = KEEL / "tests" / "_artefacts" / f"assay_r7_drift_pre_{rev}.json"
    out.write_text(proc.stdout, encoding="utf-8")
    print(f"{rev}: exit {proc.returncode}, saved {out.name}", flush=True)
    subprocess.run(["git", "-C", str(RG), "worktree", "remove", "--force", str(wt)], capture_output=True)