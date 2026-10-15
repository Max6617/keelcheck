"""R5, the git hook installer, driven from outside. **Red first at `7371668`** — `keelcheck hook` does not
exist yet, so every test here fails at the guard.

The contract these are written against is Mason's, stated before the code (2026-10-14):

    keelcheck hook install [repo] [--hook pre-commit|pre-push|both] [--force]
    keelcheck hook status  [repo]

Pre-commit only in this file. Pre-push is a separate red: it has to block a *push* on audit
divergence, which needs a local bare remote, and one test does not get to cover two mechanisms.

The failures that matter most, in order, and why:

1. **The installed hook blocks a commit when a ratified gate fails** — and a passing gate lets it
   land. Without both halves the hook is decoration, and the tool claims enforcement it does not
   have. The passing half is also the guard: a block that happens because the fixture is broken
   passes the failing test for the wrong reason.
2. **The hook leaves the `kind: gate` record the audit reads.** A hook-run gate that leaves no record
   is indistinguishable from a bypass, so the audit would report the tool's own hook as a missing
   run. The test asserts the audit is *clean* after a hook-run commit, not merely that a line exists.
3. **An existing hook is never clobbered**, and `--force` keeps it beside the new one. This is the
   tier-1/tier-2 distinction in INTENT-LOOP: the installer must not be the thing that loses work.
4. **A repo with no anchor installs nothing and exits 2** — the same rule as everywhere else: a
   charter that cannot name its ratification commit cannot be audited, so its hook must not pretend.

Also pinned: idempotence (a second install changes no byte), a POSIX `#!/bin/sh` script with no CRLF
(git for Windows runs hooks through its own `sh`), and cwd-independence (a commit from a subdirectory
runs the hook).

`git commit --no-verify` defeats any pre-commit hook; that is D2's documented residual, not a test —
hooks are reach, not enforcement.
"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

import _support

REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]
HOOK = ".git/hooks/pre-commit"


# --- can git start a hook on this host? ---------------------------------------


def _git_sh_works() -> bool:
    """True when git can actually run a hook here.

    git for Windows runs hooks through its own ``sh``, and under this host's sandbox ``sh.exe`` cannot
    create its named objects (``NtCreateDirectoryObject(...msys-2.0S5-...): 0xC0000022``), so *every*
    hook fails to start. Probed with a trivial, correct, foreign hook — never with one of ours, so a
    broken installer cannot make this return False and skip its own tests.
    """
    try:
        root = Path(tempfile.mkdtemp(prefix="keelcheck-sh-probe-"))
    except OSError:  # pragma: no cover - the writable-root policy in conftest owns this
        return False
    try:
        _support.write(root / "f.txt", "x\n")
        hook = root / ".git" / "hooks" / "pre-commit"
        # init_repo commits once, before the hook exists
        _support.init_repo(root)
        _support.write(hook, "#!/bin/sh\nexit 0\n")
        _support.write(root / "f.txt", "y\n")
        _support.git(root, "add", "-A")
        return _support.git(root, "commit", "-m", "probe").returncode == 0
    except Exception:  # noqa: BLE001 - any failure here means no hook can run
        return False
    finally:
        shutil.rmtree(root, ignore_errors=True)


_GIT_SH = _git_sh_works()
_SH_REASON = (
    "git cannot start a hook on this host: its sh.exe fails with "
    "NtCreateDirectoryObject(...msys-2.0S5-...): 0xC0000022, measured with a trivial correct hook. "
    "The git-level half of R5 is not verifiable here; the hook command itself is tested directly in "
    "test_the_hook_command_runs_the_gates_and_records_them and "
    "test_the_hook_command_does_not_need_python_on_the_path."
)
needs_git_sh = pytest.mark.skipif(not _GIT_SH, reason=_SH_REASON)


def _hook_repo(scratch, gate_body: str = "print('ok')\n", *, anchor: bool = True):
    """An auditable repo with one gate, a charter, and one staged change ready to commit."""
    script = _support.write(scratch / "tools" / "gate.py", gate_body)
    digest = _support.hash_file(script)
    gates = [("coverage", "tools/gate.py", digest)]
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates,
                           ratified=sha if anchor else None)
    _support.commit_all(scratch, "ratified")
    _support.write(scratch / "NOTES.md", "a change to commit\n")
    _support.git(scratch, "add", "-A")
    return scratch, digest


def _head(repo) -> str:
    return _support.git(repo, "rev-parse", "HEAD").stdout.strip()


# --- the guard ----------------------------------------------------------------


def test_the_hook_command_exists(scratch):
    """Without this, a 'commit was blocked' assertion could pass because git refused for its own
    reason, and a 'commit landed' assertion could pass because no hook was ever installed."""
    proc = _support.keelcheck("hook", "--help")
    assert proc.returncode == 0, f"`keelcheck hook --help` failed: {_support.combined(proc)[-400:]}"
    assert "hook" in _support.combined(proc).lower()
    assert _support.keelcheck("hook", "install", "--help").returncode == 0


# --- 1. the hook does something -----------------------------------------------


@needs_git_sh
def test_the_installed_hook_blocks_a_commit_when_a_ratified_gate_fails(scratch):
    repo, _ = _hook_repo(scratch, "import sys\nprint('bad')\nsys.exit(1)\n")
    installed = _support.keelcheck("hook", "install", str(repo))
    assert installed.returncode == 0, f"install failed:\n{_support.combined(installed)}"
    before = _head(repo)

    commit = _support.git(repo, "commit", "-m", "should be blocked")

    assert commit.returncode != 0, (
        f"a commit landed while the ratified gate fails:\n{_support.combined(commit)}")
    assert _head(repo) == before, "the commit was created despite a failing gate"


@needs_git_sh
def test_the_installed_hook_lets_a_commit_land_when_the_gate_passes(scratch):
    """The control for the test above: same fixture, passing gate. If this fails too, the block was
    git's and not the hook's."""
    repo, _ = _hook_repo(scratch, "print('ok')\n")
    assert _support.keelcheck("hook", "install", str(repo)).returncode == 0
    before = _head(repo)

    commit = _support.git(repo, "commit", "-m", "should land")

    assert commit.returncode == 0, (
        f"a commit was blocked although the gate passes:\n{_support.combined(commit)}")
    assert _head(repo) != before, "the commit did not land"


# --- 2. the hook's run is the record the audit reads --------------------------


@needs_git_sh
def test_a_hook_run_satisfies_the_audits_run_record_check(scratch):
    """The hook must leave a `kind: gate` line with `result: pass`, or the audit reads the tool's own
    hook as a bypass. The observable is the audit's exit code, not the record's contents."""
    repo, _ = _hook_repo(scratch, "print('ok')\n")
    assert _support.keelcheck("hook", "install", str(repo)).returncode == 0
    assert _support.git(repo, "commit", "-m", "through the hook").returncode == 0

    lines = [json.loads(l) for l in (repo / ".keel" / "runs.jsonl").read_text(
        encoding="utf-8").splitlines() if l.strip()]
    gate_runs = [o for o in lines if o.get("kind") == "gate"]

    assert gate_runs, "the hook left no gate run record"
    assert any(o.get("result") == "pass" for o in gate_runs), f"no passing run recorded: {gate_runs}"

    proc = _support.audit(repo)
    assert proc.returncode == 0, (
        f"the audit still reports the hook's own run as a missing record:\n{_support.combined(proc)}")


# --- 3. never clobber an existing hook ----------------------------------------


def test_an_existing_hook_is_never_clobbered(scratch):
    repo, _ = _hook_repo(scratch)
    existing = repo / HOOK
    existing.parent.mkdir(parents=True, exist_ok=True)
    _support.write(existing, "#!/bin/sh\necho mine\n")
    before = existing.read_bytes()

    proc = _support.keelcheck("hook", "install", str(repo))

    assert proc.returncode == 1, f"the install did not refuse:\n{_support.combined(proc)}"
    assert "pre-commit" in _support.combined(proc), "the refusal does not name the file"
    assert existing.read_bytes() == before, "the existing hook was modified"


def test_force_keeps_the_old_hook_beside_the_new_one(scratch):
    repo, _ = _hook_repo(scratch)
    existing = repo / HOOK
    existing.parent.mkdir(parents=True, exist_ok=True)
    _support.write(existing, "#!/bin/sh\necho mine\n")
    before = existing.read_bytes()

    proc = _support.keelcheck("hook", "install", str(repo), "--force")

    assert proc.returncode == 0, f"--force failed:\n{_support.combined(proc)}"
    backup = repo / (HOOK + ".keelcheck-backup")
    assert backup.is_file(), "the old hook was not kept"
    assert backup.read_bytes() == before, "the backup is not the old hook"
    assert existing.read_bytes() != before, "the new hook was not installed"


# --- 4. nothing to install into -----------------------------------------------


def test_a_repo_with_no_anchor_installs_nothing_and_exits_2(scratch):
    repo, _ = _hook_repo(scratch, anchor=False)

    proc = _support.keelcheck("hook", "install", str(repo))

    assert proc.returncode == 2, f"exit {proc.returncode}, wanted 2\n{_support.combined(proc)}"
    assert not (repo / HOOK).exists(), "a hook was installed into a repository that cannot be audited"


# --- mechanical properties ----------------------------------------------------


def test_installing_twice_changes_no_byte(scratch):
    repo, _ = _hook_repo(scratch)
    assert _support.keelcheck("hook", "install", str(repo)).returncode == 0
    hook = repo / HOOK
    first = hashlib.sha256(hook.read_bytes()).hexdigest()

    proc = _support.keelcheck("hook", "install", str(repo))

    assert proc.returncode == 0, f"the second install failed:\n{_support.combined(proc)}"
    assert hashlib.sha256(hook.read_bytes()).hexdigest() == first, "the second install rewrote the hook"
    assert hook.read_text(encoding="utf-8", errors="replace").strip(), "the hook is empty"


def test_the_installed_hook_is_a_posix_script_without_crlf(scratch):
    """git for Windows runs hooks through its own `sh`: a CRLF after the shebang makes the interpreter
    path `/bin/sh\\r`, and the hook silently never runs."""
    repo, _ = _hook_repo(scratch)
    assert _support.keelcheck("hook", "install", str(repo)).returncode == 0

    raw = (repo / HOOK).read_bytes()

    assert raw.startswith(b"#!/bin/sh"), f"the hook does not start with a POSIX shebang: {raw[:60]!r}"
    assert b"\r\n" not in raw, "the hook has CRLF line endings; git's sh will not run it reliably"


@needs_git_sh
def test_the_hook_runs_when_the_commit_is_made_from_a_subdirectory(scratch):
    """A hook that assumes the invoking cwd is the repository root blocks or misrecords commits made
    from anywhere else."""
    repo, _ = _hook_repo(scratch, "import sys\nsys.exit(1)\n")
    assert _support.keelcheck("hook", "install", str(repo)).returncode == 0
    sub = repo / "sub"
    _support.write(sub / "file.txt", "x\n")
    _support.git(repo, "add", "-A")
    before = _head(repo)

    commit = _support.git(sub, "commit", "-m", "from a subdirectory")

    assert commit.returncode != 0, (
        f"a failing gate did not block a commit made from a subdirectory:\n{_support.combined(commit)}")
    assert _head(repo) == before


@needs_git_sh
def test_a_passing_commit_lands_when_python_is_not_on_the_path(scratch):
    """git for Windows runs hooks through its own `sh` with whatever PATH it inherits. A hook that
    invokes a bare `python`/`keelcheck` then fails to start, and a failing hook blocks **every** commit —
    including one in a repo whose gates pass. The observable is the passing case: a stripped PATH must
    still let the commit land, which means the installer resolved the interpreter at install time.

    Polarity matters: a hook that never runs would also let this commit land, so it is only meaningful
    next to `test_the_installed_hook_blocks_a_commit_when_a_ratified_gate_fails`.
    """
    repo, _ = _hook_repo(scratch, "print('ok')\n")
    assert _support.keelcheck("hook", "install", str(repo)).returncode == 0
    before = _head(repo)
    path = os.pathsep.join(
        p for p in os.environ.get("PATH", "").split(os.pathsep) if p and "python" not in p.lower())

    commit = subprocess.run(
        ["git", "commit", "-m", "through the hook without python on PATH"],
        cwd=repo, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PATH": path},
    )

    assert commit.returncode == 0, (
        "the hook could not start without python on PATH, so it blocked a commit whose gates pass:\n"
        f"{_support.combined(commit)}"
    )
    assert _head(repo) != before, "the commit did not land"


# --- the hook body, without git's sh ------------------------------------------


def _hook_argv(repo) -> tuple[list[str], str | None]:
    """The command and PYTHONPATH the installed hook would run, read out of the file it wrote."""
    text = (repo / HOOK).read_text(encoding="utf-8")
    argv: list[str] = []
    pythonpath = None
    for line in text.splitlines():
        if line.startswith("PYTHONPATH="):
            pythonpath = line.split("=", 1)[1].split("${")[0].strip().strip('"')
        elif line.startswith("exec "):
            argv = shlex.split(line[len("exec "):])
    return argv, pythonpath


def _run_hook_body(repo, *, path: str | None = None):
    argv, pythonpath = _hook_argv(repo)
    assert argv, "the installed hook has no `exec` line"
    env = {**os.environ}
    if pythonpath:
        env["PYTHONPATH"] = pythonpath
    if path is not None:
        env["PATH"] = path
    return subprocess.run(argv, cwd=repo, capture_output=True, text=True, encoding="utf-8", env=env)


def test_the_hook_command_runs_the_gates_and_records_them(scratch):
    """What git would execute, executed directly: the hook's own exit status is the whole decision
    git makes on it. Passing → 0 and a `kind: gate` record with `result: pass`, which is what makes
    the audit clean afterwards."""
    repo, _ = _hook_repo(scratch, "print('ok')\n")
    assert _support.keelcheck("hook", "install", str(repo)).returncode == 0

    proc = _run_hook_body(repo)

    assert proc.returncode == 0, f"the hook command failed on a passing gate:\n{_support.combined(proc)}"
    lines = [json.loads(l) for l in (repo / ".keel" / "runs.jsonl").read_text(
        encoding="utf-8").splitlines() if l.strip()]
    assert any(o.get("kind") == "gate" and o.get("result") == "pass" for o in lines), (
        "the hook command left no passing gate record, so the audit would read it as a bypass")
    assert _support.audit(repo).returncode == 0, "the audit does not accept the hook's own record"


def test_the_hook_command_exits_non_zero_on_a_failing_gate(scratch):
    repo, _ = _hook_repo(scratch, "import sys\nsys.exit(1)\n")
    assert _support.keelcheck("hook", "install", str(repo)).returncode == 0

    proc = _run_hook_body(repo)

    assert proc.returncode != 0, "a failing gate produced exit 0; git would let the commit through"


def test_the_hook_command_does_not_need_python_on_the_path(scratch):
    """The PATH hazard without git: the interpreter and the import root are absolute in the body."""
    repo, _ = _hook_repo(scratch, "print('ok')\n")
    assert _support.keelcheck("hook", "install", str(repo)).returncode == 0
    path = os.pathsep.join(
        p for p in os.environ.get("PATH", "").split(os.pathsep) if p and "python" not in p.lower())

    proc = _run_hook_body(repo, path=path)

    assert proc.returncode == 0, (
        "the hook command needs python on PATH, so it would block every commit:\n"
        f"{_support.combined(proc)}")


def test_the_hook_body_carries_the_marker_and_absolute_paths(scratch):
    """The marker is what makes idempotence and never-clobber compatible at all; the absolute paths
    are what make the hook independent of git's environment."""
    repo, _ = _hook_repo(scratch)
    assert _support.keelcheck("hook", "install", str(repo)).returncode == 0

    text = (repo / HOOK).read_text(encoding="utf-8")
    argv, pythonpath = _hook_argv(repo)

    assert "# keelcheck-hook v1" in text, (
        "the hook has no marker, so a second install cannot tell its own hook from a foreign one")
    assert argv and Path(argv[0]).is_absolute(), f"no absolute interpreter: {argv[:1]}"
    assert pythonpath and Path(pythonpath).is_absolute(), f"no absolute import root: {pythonpath!r}"


def test_the_installer_honours_core_hookspath(scratch):
    """The installer resolves the hooks directory through git, so a repository that moves it must get
    the hook where git will look for it — and nowhere else."""
    repo, _ = _hook_repo(scratch)
    _support.git(repo, "config", "core.hooksPath", ".githooks")

    proc = _support.keelcheck("hook", "install", str(repo))

    assert proc.returncode == 0, _support.combined(proc)
    assert (repo / ".githooks" / "pre-commit").is_file(), (
        "the hook did not go to core.hooksPath, so git would never run it")
    assert not (repo / HOOK).exists(), "the hook was written to the default directory as well"
