"""Probe `keelcheck review` / `keelcheck audit --require-review` from outside, with stub reviewers.

Scratch measurement. Run: python .assay-tmp/review-probe.py
"""
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

ROOT = WS / ".assay-tmp" / "review2" / f"run-{os.getpid()}"
KEEL = WS / "keel"
REQ = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]
CLEAN = {"verdict": "clean", "items": [], "unreviewed": [],
         "coverage": {"files_seen": 4, "files_total": 4}}


def cli(*args):
    return subprocess.run([sys.executable, "-m", "keelcheck", *args], cwd=str(KEEL),
                          capture_output=True, text=True, encoding="utf-8",
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"})


def stub(name, obj=None, *, raw=None, code=None):
    p = ROOT / "stubs" / f"{name}.py"
    p.parent.mkdir(parents=True, exist_ok=True)
    body = raw if raw is not None else (code or f"import json,sys\nsys.stdin.read()\nprint(json.dumps({json.dumps(obj)}))\n")
    p.write_text(body, encoding="utf-8")
    return f'"{sys.executable}" "{p}"'


def make_repo(name, *, gates=None, prompt=True, extra_rows=()):
    root = ROOT / name
    root.mkdir(parents=True, exist_ok=True)
    _support.write(root / "tracked.txt", "hello\n")
    _support.write(root / "tools" / "gate.py", "print('ok')\n")
    gate_hash = _support.hash_file(root / "tools" / "gate.py")
    rows = [("coverage", "tools/gate.py", gate_hash)]
    if prompt:
        _support.write(root / "review-prompt.md", "review the repo against the original\n")
        rows.append(("review-prompt", "review-prompt.md",
                     _support.hash_file(root / "review-prompt.md"), "prompt"))
    rows.extend(extra_rows)
    _support.write_charter(root, requirements=REQ, gates=rows)
    sha = _support.init_repo(root)
    _support.write_charter(root, requirements=REQ, gates=rows, ratified=sha)
    _support.commit_all(root, "ratified")
    cli("gate", "run", str(root))
    return root


def show(label, proc, keys=("exit", "error", "result", "verdict")):
    try:
        doc = json.loads(proc.stdout)
    except Exception:
        print(f"  {label:<34} exit {proc.returncode}  raw={(proc.stdout or proc.stderr).strip()[:120]}")
        return None
    line = doc.get("line") or {}
    bits = " ".join(f"{k}={str(doc.get(k))[:40]}" for k in keys if doc.get(k) not in (None, ""))
    if line:
        bits += (f" | line result={line.get('result')} verdict={line.get('verdict')} "
                 f"items={line.get('items')} prompt_ratified={line.get('prompt_ratified')} "
                 f"manifest={str(line.get('manifest'))[:10]}")
    print(f"  {label:<34} exit {proc.returncode}  {bits}")
    return doc


def audit_state(label, root, *extra):
    proc = cli("audit", str(root), "--json", *extra)
    try:
        doc = json.loads(proc.stdout)
    except Exception:
        print(f"  {label:<34} exit {proc.returncode}  raw={(proc.stdout or proc.stderr).strip()[:110]}")
        return proc
    review = doc.get("review")
    state = review.get("status") if isinstance(review, dict) else review
    print(f"  {label:<34} exit {proc.returncode}  review_state={state}  "
          f"findings={[f['kind'] for f in doc.get('findings', [])]}")
    return proc


print(f"# review probe - keelcheck@{subprocess.run(['git','-C',str(KEEL),'rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip()}")
ROOT.mkdir(parents=True, exist_ok=True)

print("\n## 1. the baseline: a clean repo with no review, not required")
base = make_repo("base")
audit_state("audit (review not required)", base)
audit_state("audit --require-review", base, "--require-review")

print("\n## 2. verdicts")
r = make_repo("verdicts")
for name, obj in [
    ("clean", CLEAN),
    ("partial unreviewed", {**CLEAN, "unreviewed": ["the gate runner"]}),
    ("partial coverage", {**CLEAN, "coverage": {"files_seen": 1, "files_total": 4}}),
    ("divergence verified", {**CLEAN, "verdict": "divergence",
                             "items": [{"class": "missing", "subject": "R1", "evidence": "CHARTER.md",
                                        "why": "x", "confidence": "high"}]}),
    ("divergence escaping", {**CLEAN, "verdict": "divergence",
                             "items": [{"class": "shifted", "subject": "x",
                                        "evidence": "../../outside.md", "why": "x", "confidence": "low"}]}),
    ("malformed class", {**CLEAN, "items": [{"class": "wrong", "subject": "x",
                                             "evidence": "CHARTER.md", "why": "x", "confidence": "low"}]}),
]:
    show(name, cli("review", str(r), "--reviewer", stub(name.replace(" ", "-"), obj), "--json",
                   "--record", str(ROOT / f"rec-{name.replace(' ', '-')}")))

print("\n## 3. reviewer failures")
show("not json", cli("review", str(r), "--reviewer", stub("notjson", raw="print('nope')\n"),
                     "--json", "--record", str(ROOT / "rec-notjson")))
show("exit 3", cli("review", str(r), "--reviewer", stub("e3", code="import sys\nsys.exit(3)\n"),
                   "--json", "--record", str(ROOT / "rec-e3")))
show("timeout", cli("review", str(r), "--reviewer", stub("slow", code="import time\ntime.sleep(30)\n"),
                    "--json", "--timeout", "1", "--record", str(ROOT / "rec-slow")))

print("\n## 4. freshness: fresh -> stale -> fresh  (one record location throughout)")
r = make_repo("fresh")
clean_cmd = stub("clean4", CLEAN)
show("review", cli("review", str(r), "--reviewer", clean_cmd, "--json"))
audit_state("audit --require-review (fresh)", r, "--require-review")
_support.write(r / "tracked.txt", "hellp\n")
audit_state("audit --require-review (1 byte)", r, "--require-review")
_support.write(r / "tracked.txt", "hello\n")
audit_state("audit --require-review (reverted)", r, "--require-review")

print("\n## 5. a failed review and a missing one")
r = make_repo("failed")
cli("review", str(r), "--reviewer", stub("e3b", code="import sys\nsys.exit(3)\n"))
audit_state("audit --require-review (failed)", r, "--require-review")
r = make_repo("missing")
audit_state("audit --require-review (missing)", r, "--require-review")

print("\n## 6. the prompt as a hashed artefact")
r = make_repo("prompt")
show("ratified prompt row", cli("review", str(r), "--reviewer", clean_cmd, "--json"))
_support.write(r / "review-prompt.md", "weakened instruction\n")
show("weakened prompt", cli("review", str(r), "--reviewer", clean_cmd, "--json"))
r = make_repo("noprompt", prompt=False)
_support.write(ROOT / "noprompt-prompt.md", "an unlocked instruction\n")
show("--prompt, nothing ratified",
     cli("review", str(r), "--reviewer", clean_cmd, "--json", "--prompt",
         str(ROOT / "noprompt-prompt.md")))
show("no prompt at all", cli("review", str(r), "--reviewer", clean_cmd, "--json"))

print("\n## 6b. an unknown kind")
r = make_repo("unknownkind", extra_rows=[])
_support.write(r / "tools" / "weird.py", "print('weird')\n")
rows = [("coverage", "tools/gate.py", _support.hash_file(r / "tools" / "gate.py")),
        ("weird", "tools/weird.py", _support.hash_file(r / "tools" / "weird.py"), "banana"),
        ("review-prompt", "review-prompt.md", _support.hash_file(r / "review-prompt.md"), "prompt")]
_support.write_charter(r, requirements=REQ, gates=rows)
sha = _support.init_repo(r)
_support.write_charter(r, requirements=REQ, gates=rows, ratified=sha)
_support.commit_all(r, "ratified with an unknown kind")
audit_state("unknown kind", r)

print("\n## 7. gates vs prompts: only gate rows defeat vacuity")
r = make_repo("promptonly", gates=None, prompt=True)
# rebuild with only the prompt row
rows = [("review-prompt", "review-prompt.md",
         _support.hash_file(r / "review-prompt.md"), "prompt")]
_support.write_charter(r, requirements=REQ, gates=rows)
sha = _support.init_repo(r)
_support.write_charter(r, requirements=REQ, gates=rows, ratified=sha)
_support.commit_all(r, "prompt only")
proc = cli("gate", "run", str(r), "--json")
try:
    doc = json.loads(proc.stdout)
    print(f"  gate run, prompt-only repo          exit {proc.returncode}  "
          f"error={str(doc.get('error'))[:60]} gates={[g.get('gate') for g in doc.get('gates', [])]}")
except Exception:
    print(f"  gate run exit {proc.returncode} raw={(proc.stdout or proc.stderr).strip()[:110]}")
audit_state("audit, prompt-only repo", r)
