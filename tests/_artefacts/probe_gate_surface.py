"""Probe `keelcheck gate run` / `keelcheck gate hash` from outside. Scratch measurement, not a test.

Run: python .assay-tmp/gate-probe.py
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

WS = Path(__file__).resolve().parents[3]  # <workspace>/keel/tests/_artefacts/<this file>
# The workspace root is derived from this file, never hardcoded: a recorded artefact must not
# carry a machine's layout, and these scripts write recorded artefacts.
sys.path.insert(0, str(WS / "keel" / "tests"))
import _support  # noqa: E402

ROOT = WS / ".assay-tmp" / "gate-probe" / f"run-{os.getpid()}"
REQ = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]


def cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "keelcheck", *args],
        cwd=str(cwd or (WS / "keel")), capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(WS / "keel")},
    )


def repo(name, script_body, *, filename="tools/gate.py", name_gate="coverage"):
    root = ROOT / name
    root.mkdir(parents=True, exist_ok=True)
    p = _support.write(root / filename, script_body)
    digest = _support.hash_file(p)
    gates = [(name_gate, filename, digest)]
    _support.write_charter(root, requirements=REQ, gates=gates)
    sha = _support.init_repo(root)
    _support.write_charter(root, requirements=REQ, gates=gates, ratified=sha)
    _support.commit_all(root, "ratified")
    return root, digest


def divergences(proc):
    return [ln.strip() for ln in _support.combined(proc).splitlines() if ln.strip().startswith("[")]


def audit(root, *extra):
    return cli("audit", str(root), *extra)


print(f"# gate surface probe - keelcheck@{subprocess.run(['git','-C',str(WS / 'keel'),'rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip()}")
ROOT.mkdir(parents=True, exist_ok=True)

# 1. a skipped gate: does an audit run heal the missing gate record?
r, _ = repo("passing", "print('ok')\n")
first = audit(r)
second = audit(r)
run = cli("gate", "run", str(r))
third = audit(r)
print("\n## 1. a passing gate")
print(f"  audit #1          exit {first.returncode}  {divergences(first)}")
print(f"  audit #2 (no run) exit {second.returncode}  {divergences(second)}")
print(f"  gate run          exit {run.returncode}  {_support.combined(run).strip().splitlines()[:2]}")
print(f"  audit #3 (after)  exit {third.returncode}  {divergences(third)}")

# 2. a gate that runs and fails
r, _ = repo("failing", "import sys\nprint('bad')\nsys.exit(1)\n")
run = cli("gate", "run", str(r))
after = audit(r)
print("\n## 2. a gate that runs and FAILS")
print(f"  gate run  exit {run.returncode}  {_support.combined(run).strip().splitlines()[:2]}")
print(f"  audit     exit {after.returncode}  {divergences(after) or 'NONE'}")

# 3. a gate that times out
r, _ = repo("slow", "import time\ntime.sleep(30)\n")
run = cli("gate", "run", str(r), "--timeout", "1")
after = audit(r)
print("\n## 3. a gate that times out")
print(f"  gate run  exit {run.returncode}  {_support.combined(run).strip().splitlines()[:2]}")
print(f"  audit     exit {after.returncode}  {divergences(after) or 'NONE'}")

# 4. --record as a directory
r, _ = repo("recdir", "print('ok')\n")
d = ROOT / "recdir-records"
d.mkdir(exist_ok=True)
audit_dir = audit(r, "--record", str(d))
gate_dir = cli("gate", "run", str(r), "--record", str(d))
print("\n## 4. --record <directory>")
print(f"  audit    exit {audit_dir.returncode}  wrote: {[p.name for p in d.iterdir()]}")
print(f"  gate run exit {gate_dir.returncode}  wrote: {[p.name for p in d.iterdir()]}")
print(f"  gate run says: {_support.combined(gate_dir).strip()[:160]}")

# 5. gate hash vs git, CRLF worktree
r, digest = repo("crlf", "print('ok')\n")
_support.git(r, "config", "core.autocrlf", "true")
(r / "tools" / "gate.py").write_bytes(b"print('ok')\r\n")
h = cli("gate", "hash", "tools/gate.py", "--repo", str(r))
git_oid = _support.git(r, "hash-object", "--path=tools/gate.py", "tools/gate.py").stdout.strip()
print("\n## 5. gate hash over a CRLF worktree")
print(f"  keelcheck gate hash = {h.stdout.strip()}")
print(f"  recorded hash  = {digest}")
print(f"  git blob oid   = {git_oid}")
print(f"  agree: keelcheck==recorded {h.stdout.strip() == digest}")

# 6. record line shapes
r, _ = repo("shapes", "print('ok')\n")
cli("gate", "run", str(r))
audit(r)
import json  # noqa: E402
lines = (r / ".keel" / "runs.jsonl").read_text(encoding="utf-8").splitlines()
print("\n## 6. record lines")
for line in lines:
    obj = json.loads(line)
    print(f"  {obj.get('kind'):<7} keys={sorted(obj)}")
