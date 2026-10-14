"""Probe the fixes and the new D12/D13 behaviour from outside. Scratch measurement.

Run: python .assay-tmp/d12-d13-probe.py
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

WS = Path(r"C:\Users\besen\.dsh\bot\workspace")
sys.path.insert(0, str(WS / "keel" / "tests"))
import _support  # noqa: E402

ROOT = WS / ".assay-tmp" / "d12d13" / f"run-{os.getpid()}"
KEEL = WS / "keel"
REQ_OK = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]


def cli(*args):
    return subprocess.run([sys.executable, "-m", "keel", *args], cwd=str(KEEL),
                          capture_output=True, text=True, encoding="utf-8",
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"})


def kinds(proc):
    out = _support.combined(proc)
    return sorted(set(re.findall(r"\[([a-z-]+)\]", out))), out


def report(label, proc, extra=""):
    ks, out = kinds(proc)
    gate_lines = [l.strip() for l in out.splitlines() if "gate-record" in l or "unbuilt" in l
                  or "anchor" in l or "format" in l]
    print(f"  {label:<34} exit {proc.returncode}  classes={ks}")
    for line in gate_lines[:3]:
        print(f"      {line[:150]}")
    if extra:
        print(f"      {extra}")


def gated(root_name, body="print('ok')\n", *, gate="coverage", path="tools/gate.py",
          reqs=REQ_OK, runner="gate run"):
    root = ROOT / root_name
    script = _support.write(root / path, body)
    digest = _support.hash_file(script)
    gates = [(gate, path, digest)]
    _support.write_charter(root, requirements=reqs, gates=gates)
    sha = _support.init_repo(root)
    _support.write_charter(root, requirements=reqs, gates=gates, ratified=sha)
    _support.commit_all(root, "ratified")
    if runner:
        cli(*runner.split(), str(root))
    return root, digest


print(f"# D12/D13 + gate-result probe - keel@"
      f"{subprocess.run(['git','-C',str(KEEL),'rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip()}")
ROOT.mkdir(parents=True, exist_ok=True)
(ROOT / 'notacharter.md').write_text('# just a heading\n', encoding='utf-8')

print("\n## 1. a gate record only counts when it passed")
r, _ = gated("pass")
report("pass", cli("audit", str(r)))
r, _ = gated("fail", "import sys\nsys.exit(1)\n")
report("fail", cli("audit", str(r)))
r, _ = gated("timeout", "import time\ntime.sleep(30)\n", runner="gate run --timeout 1")
report("timeout", cli("audit", str(r)))
r, _ = gated("error", "print('not runnable')\n", path="tools/gate.txt")
report("error (non-.py gate)", cli("audit", str(r)))

print("\n## 2. --record <directory>")
r, _ = gated("recdir", runner="")
d = ROOT / "records"
d.mkdir(exist_ok=True)
run = cli("gate", "run", str(r), "--record", str(d))
aud = cli("audit", str(r), "--record", str(d))
report("gate run --record <dir>", run, f"files={sorted(p.name for p in d.iterdir())}")
report("audit --record <dir>", aud)

print("\n## 3. D12: the header, the anchor, [format]")
r, _ = gated("anchor", runner="")
cli("audit", str(r))
head = json.loads((r / ".keel" / "runs.jsonl").read_text(encoding="utf-8").splitlines()[0])
print(f"  header keys: {sorted(head)}  (no 'ratified': {'ratified' not in head})")
# move the anchor to a new commit
text = (r / "CHARTER.md").read_text(encoding="utf-8")
new_sha = _support.commit_all(r, "a second commit")
text = re.sub(r"(Ratified at:\s*`?)([0-9a-f]{7,40})", rf"\g<1>{new_sha}", text, count=1)
_support.write(r / "CHARTER.md", text)
_support.commit_all(r, "repoint the anchor")
report("after repointing (1st)", cli("audit", str(r)))
report("after repointing (2nd)", cli("audit", str(r)))

# non-canonical spelling -> [format]?
r, _ = gated("format", runner="")
t = (r / "CHARTER.md").read_text(encoding="utf-8")
t = re.sub(r"Ratified at: ([0-9a-f]{7,40})", r"- `Ratified at:` `\1`", t, count=1)
_support.write(r / "CHARTER.md", t)
_support.commit_all(r, "non-canonical pointer")
report("non-canonical pointer", cli("audit", str(r)))

# no pointer -> exit 2
r = ROOT / "nopointer"
_support.write_charter(r, requirements=REQ_OK)
_support.init_repo(r)
report("no pointer", cli("audit", str(r)))

print("\n## 4. D13: [unbuilt] and the carve-out")
for label, cell in [
    ("borrowed path", "code: tools/coverage.py"),
    ("other .keel file", "code: .keel/anything-else.json"),
    ("review-context (default)", "code: .keel/review-context.json"),
    ("runs.jsonl (default)", "code: .keel/runs.jsonl"),
    ("a directory", "code: tools/"),
]:
    r = ROOT / f"unbuilt-{label.replace(' ', '-')}"
    _support.write_charter(r, requirements=[("R8", "x", cell, "—", "met")])
    _support.init_repo(r)
    sha = (r / "CHARTER.md") and _support.git(r, "rev-parse", "HEAD").stdout.strip()
    _support.write_charter(r, requirements=[("R8", "x", cell, "—", "met")], ratified=sha)
    _support.commit_all(r, "ratified")
    report(label, cli("audit", str(r)))

print("\n## 4b. the carve-out when --record moves the record elsewhere")
r = ROOT / "carveout-elsewhere"
d2 = ROOT / "elsewhere"
d2.mkdir(exist_ok=True)
reqs = [("R8", "reviewer input exists", "code: .keel/review-context.json", "—", "met"),
        ("R9", "the record exists", "code: .keel/runs.jsonl", "—", "met")]
_support.write_charter(r, requirements=reqs)
_support.init_repo(r)
sha = _support.git(r, "rev-parse", "HEAD").stdout.strip()
_support.write_charter(r, requirements=reqs, ratified=sha)
_support.commit_all(r, "ratified")
report("--record elsewhere", cli("audit", str(r), "--record", str(d2)),
       f"files elsewhere={sorted(p.name for p in d2.iterdir())}  "
       f".keel exists={(r / '.keel').exists()}")

print("\n## 5. keel charter exit codes (D12)")
print(f"  clean charter        exit {cli('charter', str(ROOT / 'pass' / 'CHARTER.md')).returncode}")
print(f"  wish (rentguard)     exit {cli('charter', str(WS / 'rentguard' / 'CHARTER.md')).returncode}")
print(f"  not a charter        exit {cli('charter', str(ROOT / 'nopointer' / 'CHARTER.md' if False else ROOT / 'notacharter.md')).returncode}")
