"""A commit through the **installed** hook, made **inside a coverage-gate run** (R5 x R8).

Gilbert, 2026-10-15: the nested-isolation test in `tests/test_coverage_gate.py` establishes that
`gate -> pytest -> target` keeps the parent's `PYTHONPATH`. It does **not** reach the child that
actually failed — on 2026-10-15 the same gate over the same suite at two commits disagreed (exit 0
and exit 1), and the failing run died inside this hook with `No module named keelcheck`. That chain is
one process deeper: **`gate -> pytest -> target -> git -> sh -> python -m keelcheck`**, and the hook
script resolves its own environment at *install* time, which is exactly what the nested test cannot
see. This file is that chain, executed.

What makes it a regression test rather than a rerun, in Gilbert's words:

1. **The hook is installed from the tree under test** — `python -m keelcheck hook install` with
   `cwd` at the repository root, so install-time path resolution is exercised rather than inherited.
2. **The commit is made inside a gate run** — the recorded document names the gate's own child-process
   variables, so a run of this file outside the gate cannot pass as if it had been inside one.

The document is written to `KEEL_HOOK_GATE_OUT` (default: a file under the temp dir) and is the only
observable `tests/test_coverage_gate.py` reads: exit 0 alone would also be produced by a skipped or
uncollected target, which is the "a gate that never ran is not a passing gate" class this project
exists to catch.

Named without a `test_` prefix so the normal suite never collects it; the gate is given its path
explicitly.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]  # tests/_artefacts/x.py -> tests -> repo root
sys.path.insert(0, str(REPO / "tests"))

import _support  # noqa: E402  (path above)

OUT = Path(
    os.environ.get("KEEL_HOOK_GATE_OUT")
    or (Path(tempfile.gettempdir()) / "keel-hook-under-gate.json")
)

HOOK = ".git/hooks/pre-commit"
REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]

#: The msys failure the suite already skips on, quoted so this file reports the same fact rather than
#: inventing a defect in the hook when git's own `sh` cannot start.
SH_REASON = (
    "git cannot start a hook on this host: its sh.exe fails with "
    "NtCreateDirectoryObject(...msys-2.0S5-...): 0xC0000022, measured with a trivial correct hook"
)


def _record(doc: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")


def _scratch(name: str) -> Path:
    """A writable scratch directory.

    **Never `mkdtemp` on this host**: it creates a mode-0700 directory the sandbox refuses to write
    into, so a fixture built there fails for a reason that has nothing to do with the hook.
    """
    root = Path(tempfile.gettempdir()) / f"keel-hook-under-gate-{name}-{os.getpid()}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


def _head(repo: Path) -> str:
    return _support.git(repo, "rev-parse", "HEAD").stdout.strip()


def _probe_git_sh() -> tuple[bool, str]:
    """Can git start *any* hook here? Probed with a trivial foreign hook, never one of ours, so a
    broken installer cannot make this return False and excuse its own tests."""
    root = _scratch("probe")
    try:
        _support.write(root / "f.txt", "x\n")
        _support.init_repo(root)
        _support.write(root / ".git" / "hooks" / "pre-commit", "#!/bin/sh\nexit 0\n")
        _support.write(root / "f.txt", "y\n")
        _support.git(root, "add", "-A")
        proc = _support.git(root, "commit", "-m", "probe")
        if proc.returncode == 0:
            return True, ""
        return False, f"{_support.combined(proc).strip()[-400:]}"
    except Exception as exc:  # noqa: BLE001 - any failure here means no hook can run at all
        return False, f"{type(exc).__name__}: {exc}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _fixture(name: str) -> Path:
    """An auditable repo: charter with one ratified gate, one commit, one staged change."""
    root = _scratch(name)
    script = _support.write(root / "tools" / "gate.py", "print('ok')\n")
    gates = [("coverage", "tools/gate.py", _support.hash_file(script))]
    _support.write_charter(root, requirements=REQUIREMENTS, gates=gates)
    sha = _support.init_repo(root)
    _support.write_charter(root, requirements=REQUIREMENTS, gates=gates, ratified=sha)
    _support.commit_all(root, "ratified")
    _support.write(root / "NOTES.md", "a change to commit\n")
    _support.git(root, "add", "-A")
    return root


def _inside_gate_run() -> dict:
    """What the gate set for this process, recorded so the commit is provably inside one."""
    return {
        "KEELCHECK_COVERAGE_CHILD": os.environ.get("KEELCHECK_COVERAGE_CHILD"),
        "KEELCHECK_COVERAGE_DIR": os.environ.get("KEELCHECK_COVERAGE_DIR"),
        "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
    }


def test_a_commit_through_the_installed_hook_lands_inside_a_gate_run():
    doc: dict = {
        "repo": str(REPO),
        "python": sys.executable,
        "inside_gate": _inside_gate_run(),
    }
    works, reason = _probe_git_sh()
    doc["git_sh_works"] = works
    doc["git_sh_reason"] = reason
    if not works:
        _record(doc)
        pytest.skip(f"{SH_REASON}; measured here as: {reason}")

    repo = _fixture("fixture")
    doc["repo_under_test"] = str(repo)

    installed = _support.keelcheck("hook", "install", str(repo))
    doc["install_returncode"] = installed.returncode
    doc["install_output"] = _support.combined(installed).strip()[-400:]
    doc["hook_installed"] = (repo / HOOK).exists()
    doc["hook_body"] = (repo / HOOK).read_text(encoding="utf-8") if doc["hook_installed"] else ""

    before = _head(repo)
    commit = _support.git(repo, "commit", "-m", "through the installed hook, inside a gate run")
    after = _head(repo)
    doc["head_before"] = before
    doc["head_after"] = after
    doc["commit_returncode"] = commit.returncode
    doc["commit_output"] = _support.combined(commit).strip()[-800:]
    _record(doc)

    assert doc["hook_installed"], (
        "no hook was installed, so a commit that landed would prove nothing:\n"
        f"{doc['install_output']}")
    assert commit.returncode == 0, (
        "the installed hook blocked a commit whose gate passes; a hook that cannot start blocks "
        f"*every* commit:\n{doc['commit_output']}")
    assert after != before, "the commit did not land, so nothing was enforced or verified"
