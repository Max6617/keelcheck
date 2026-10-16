"""List what a review actually exports. Scratch."""
import json
import os
import subprocess
import sys
from pathlib import Path

WS = Path(__file__).resolve().parents[3]  # <workspace>/keel/tests/_artefacts/<this file>
# The workspace root is derived from this file, never hardcoded: a recorded artefact must not
# carry a machine's layout, and these scripts write recorded artefacts.
sys.path.insert(0, str(WS / "keel" / "tests"))
import _support  # noqa: E402

ROOT = WS / ".assay-tmp" / "exportlist"
if ROOT.exists():
    import shutil
    shutil.rmtree(ROOT, ignore_errors=True)
ROOT.mkdir(parents=True)
r = ROOT / "repo"
r.mkdir()
_support.write(r / "tracked.txt", "hello\n")
_support.write(r / "review-prompt.md", "prompt\n")
_support.keel_hash = None
# minimal charter: no gates needed for an export
import importlib  # noqa: E402
_support.write_charter(r, requirements=[("R1", "x", "code: a parser", "—", "met")])
sha = _support.init_repo(r)
_support.write_charter(r, requirements=[("R1", "x", "code: a parser", "—", "met")], ratified=sha)
_support.commit_all(r, "ratified")
stub = ROOT / "stub.py"
stub.write_text("import json,sys\nsys.stdin.read()\nprint(json.dumps("
                "{'verdict':'clean','items':[],'unreviewed':[],"
                "'coverage':{'files_seen':1,'files_total':1}}))\n", encoding="utf-8")
sys.path.insert(0, str(WS / "keel"))
proc = subprocess.run(
    [sys.executable, "-m", "keelcheck", "review", str(r), "--reviewer",
     f'"{sys.executable}" "{stub}"', "--json", "--prompt", str(r / "review-prompt.md")],
    cwd=str(WS / "keel"), capture_output=True, text=True, encoding="utf-8",
    env={**os.environ, "PYTHONIOENCODING": "utf-8"})
try:
    doc = json.loads(proc.stdout)
except Exception:
    print(proc.returncode, proc.stdout[:200], proc.stderr[:400])
    raise SystemExit(0)
tree = Path(doc["export"])
print(f"exit {proc.returncode}")
print(f"tree = {tree}")
for p in sorted(tree.rglob("*")):
    rel = p.relative_to(tree)
    print(f"  {'D' if p.is_dir() else 'F'} {rel}")
