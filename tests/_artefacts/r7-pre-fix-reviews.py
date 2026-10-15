"""Run the drift review at the three pre-fix revisions (D7's other end). One Claude Code call each."""
import subprocess, sys
from pathlib import Path

WS = Path(r"C:\Users\besen\.dsh\bot\workspace")
KEEL, RG, TMP = WS / "keel", WS / "rentguard", WS / ".assay-tmp" / "r7"
WRAPPER = KEEL / "tests" / "_artefacts" / "claude-reviewer.py"
PY = sys.executable
for rev in ("bd63920", "ce69cea", "c512125"):
    wt = TMP / f"rg-{rev}"
    subprocess.run(["git", "-C", str(RG), "worktree", "add", "--detach", str(wt), rev], capture_output=True)
    cmd = f'"{PY}" "{WRAPPER}"'
    proc = subprocess.run(
        [PY, "-m", "keelcheck", "review", str(wt), "--reviewer", cmd, "--prompt-repo", str(KEEL),
         "--record", str(TMP / f"pre-{rev}.jsonl"), "--timeout", "600", "--json"],
        cwd=str(KEEL), capture_output=True, text=True, encoding="utf-8",
        env={"PYTHONIOENCODING": "utf-8", "PATH": __import__("os").environ["PATH"]})
    out = KEEL / "tests" / "_artefacts" / f"assay_r7_drift_pre_{rev}.json"
    out.write_text(proc.stdout, encoding="utf-8")
    print(f"{rev}: exit {proc.returncode}, saved {out.name}", flush=True)
    subprocess.run(["git", "-C", str(RG), "worktree", "remove", "--force", str(wt)], capture_output=True)