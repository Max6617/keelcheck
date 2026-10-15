"""R5's first surface: the git hook (D2 -- reach, not enforcement).

A pre-commit hook is the one surface every repository and every harness shares, so it comes first;
the harness adapter comes last. It is *reach* and not a guarantee: `git commit --no-verify` defeats
any hook, which is why the audit reads the run record and a bypass shows up as a **missing** one
(D1, D2).

Three things make the installed hook honest:

- **It resolves the interpreter at install time** (an absolute path) and puts the package's import
  root on ``PYTHONPATH``. Git for Windows runs hooks through its own ``sh`` with the caller's PATH,
  and a hook that cannot start blocks *every* commit -- including one whose gates pass.
- **It carries a marker** (``# keelcheck-hook v1``). Without one, a second install would have to choose
  between overwriting a hook it did not write and refusing its own; the marker is what lets a foreign
  hook be refused and keelcheck's own be idempotent.
- **It refuses to install where the charter names no ratification commit.** A repository that cannot
  be audited gets no hook, because a hook that pretends to enforce is worse than none.

The hook body is written as bytes with LF endings: a CRLF after the shebang makes git's ``sh`` look
for ``/bin/sh\\r`` and silently never run the hook.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import keelcheck

from . import gitcmd
from .audit import AuditError, load_charter
from .output import emit, emit_err

__all__ = ["HOOK_NAMES", "INSTALLABLE", "MARKER", "hook_body", "hooks_dir", "install", "main", "status"]

MARKER = "# keelcheck-hook v1"
HOOK_NAMES = ("pre-commit", "pre-push")
#: Pre-push blocks a *push* on audit divergence; it is deliberately its own build and its own red
#: test, so this surface installs pre-commit only and says so rather than half-doing both.
INSTALLABLE = ("pre-commit",)


def hooks_dir(repo: Path | str) -> Path:
    """Where git would run hooks, honouring ``core.hooksPath``."""
    proc = gitcmd.run(repo, "rev-parse", "--git-path", "hooks", check=False)
    if proc.returncode != 0 or not proc.stdout.strip():
        return Path(repo) / ".git" / "hooks"
    found = Path(proc.stdout.strip().replace("\\", "/"))
    return found if found.is_absolute() else (Path(repo).resolve() / found)


def _sh(path: Path | str) -> str:
    """A path as the hook's POSIX shell should see it: forward slashes, no surprises."""
    return str(path).replace("\\", "/").replace('"', '\\"')


def hook_body(repo: Path | str, hook: str) -> str:
    """The installed script. Deterministic: the same repo and hook produce the same bytes.

    **The launch is hermetic, and that is measured rather than assumed.** 2026-10-15: two runs of the
    same gate over the same suite at the same commit disagreed (exit 0 and exit 1), and the failing
    one died inside this hook with `No module named keelcheck`. Probed directly: with `PYTHONHOME`
    set in the caller's environment, `python -m keelcheck` cannot start at all (`Python path
    configuration`, `PYTHONHOME = …`); with a foreign `keelcheck` earlier on `PYTHONPATH`, `python -m
    keelcheck` runs *that* package instead. The hook's failure mode is "every commit is blocked", so
    the caller's shell must not get a vote: `-E` ignores every `PYTHON*` variable, `-X utf8` replaces
    `PYTHONIOENCODING`, and the import root is pinned inside the command (`sys.path.insert(0, …)`)
    instead of reaching it through the environment. `PYTHONHOME` is unset, because it stops every
    python the hook starts -- the gate's own children included, which no flag on the hook's launch can
    reach. `PYTHONPATH` is still exported, for those children: the hook's *own* import no longer
    depends on it.
    """
    root = Path(keelcheck.__file__).resolve().parents[1]
    python = Path(sys.executable).resolve()
    command = "gate run" if hook == "pre-commit" else "audit"
    launch = (
        "import runpy, sys; "
        f"sys.path.insert(0, r'{_sh(root)}'); "
        "runpy.run_module('keelcheck', run_name='__main__')"
    )
    return (
        "#!/bin/sh\n"
        f"{MARKER} -- installed by keelcheck hook install. The lock is the charter's gate table, not\n"
        "# this file: change a gate by re-ratifying it, never by editing this hook.\n"
        "# The interpreter, the import root and the encoding are pinned in this command: a PYTHON*\n"
        "# variable in the caller's shell must not decide whether a commit is possible. PYTHONHOME is\n"
        "# unset because it stops *every* python this hook starts, its gate children included.\n"
        "unset PYTHONHOME\n"
        f'PYTHONPATH="{_sh(root)}"${{PYTHONPATH:+:$PYTHONPATH}}\n'
        "export PYTHONPATH\n"
        f'exec "{_sh(python)}" -E -X utf8 -c "{launch}" {command} "{_sh(repo)}"\n'
    )


def _write_hook(target: Path, body: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body.encode("utf-8"))  # bytes, LF: never text mode on Windows
    try:
        os.chmod(target, 0o755)
    except OSError:  # pragma: no cover - Windows has no such bit to set
        pass


def install(repo: Path | str, *, hook: str = "pre-commit", force: bool = False) -> dict:
    """Install the hook. Returns a report dict with an ``exit`` code."""
    repo = Path(repo).resolve()
    result = {"repo": str(repo), "hook": hook, "exit": 0, "action": None, "error": None,
              "path": None, "backup": None}
    if hook not in INSTALLABLE:
        result.update(
            exit=2,
            error=(
                f"{hook} is not installed by this build: pre-push blocks a push on audit "
                "divergence and is a separate mechanism with its own red test (R5)"
            ),
        )
        return result
    try:
        _, charter = load_charter(repo)
    except AuditError as exc:
        result.update(exit=2, error=str(exc))
        return result
    if not charter.ratified_at:
        result.update(
            exit=2,
            error=(
                "the charter names no ratification commit (`Ratified at:`); a repository that "
                "cannot be audited gets no hook, because a hook that pretends to enforce is worse "
                "than none (D12)"
            ),
        )
        return result

    target = hooks_dir(repo) / hook
    backup = target.with_name(target.name + ".keelcheck-backup")
    body = hook_body(repo, hook)
    result["path"] = str(target)
    if target.exists():
        existing = target.read_bytes()
        if MARKER.encode("utf-8") not in existing:
            if not force:
                result.update(
                    exit=1,
                    action="refused",
                    error=(
                        f"{target} already exists and was not written by keelcheck; it was not touched. "
                        f"Rerun with --force to keep it beside the new hook as {backup.name} (R5)"
                    ),
                )
                return result
            shutil.copyfile(target, backup)
            _write_hook(target, body)
            result.update(action="forced", backup=str(backup))
            return result
        if existing == body.encode("utf-8"):
            result.update(action="unchanged")
            return result
        _write_hook(target, body)
        result.update(action="updated")
        return result
    _write_hook(target, body)
    result.update(action="installed")
    return result


def status(repo: Path | str) -> dict:
    """What is installed where, without touching anything. A query: exit 0 either way."""
    repo = Path(repo).resolve()
    directory = hooks_dir(repo)
    hooks: dict[str, dict] = {}
    for name in HOOK_NAMES:
        target = directory / name
        backup = target.with_name(target.name + ".keelcheck-backup")
        if not target.exists():
            state = "not-installed"
        elif MARKER.encode("utf-8") in target.read_bytes():
            state = "installed"
        else:
            state = "foreign"
        hooks[name] = {
            "state": state,
            "path": str(target),
            "backup": str(backup) if backup.exists() else None,
            "installable": name in INSTALLABLE,
        }
    return {"repo": str(repo), "hooks_path": str(directory), "hooks": hooks, "exit": 0}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="keelcheck hook",
        description="install the git hook that runs the ratified gates, or report what is installed (R5)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    installer = sub.add_parser("install", help="install the pre-commit hook that runs the gates")
    installer.add_argument("repo", nargs="?", default=".", help="repository (default: .)")
    installer.add_argument(
        "--hook",
        default="pre-commit",
        choices=HOOK_NAMES,
        help="which hook to install (default: pre-commit; pre-push is a separate build)",
    )
    installer.add_argument(
        "--force",
        action="store_true",
        help="keep an existing hook beside the new one as <hook>.keelcheck-backup instead of refusing",
    )
    installer.add_argument("--json", action="store_true", help="machine-readable output")

    reporter = sub.add_parser("status", help="report which hooks are installed (read-only)")
    reporter.add_argument("repo", nargs="?", default=".", help="repository (default: .)")
    reporter.add_argument("--json", action="store_true", help="machine-readable output")

    args = parser.parse_args(argv)

    if args.command == "status":
        report = status(args.repo)
        if args.json:
            emit(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            emit(f"hooks: {report['hooks_path']}")
            for name, entry in report["hooks"].items():
                if entry["state"] == "installed":
                    emit(f"  {name}: installed (keelcheck-hook v1) -> {entry['path']}")
                elif entry["state"] == "foreign":
                    emit(f"  {name}: foreign hook present -> {entry['path']}")
                else:
                    emit(f"  {name}: not installed")
                if entry["backup"]:
                    emit(f"      backup kept: {entry['backup']}")
        return report["exit"]

    report = install(args.repo, hook=args.hook, force=args.force)
    if args.json:
        emit(json.dumps(report, indent=2, ensure_ascii=False))
        return report["exit"]
    if report["error"]:
        emit_err(f"keelcheck hook install: {report['error']}")
        return report["exit"]
    action = report["action"]
    if action == "unchanged":
        emit(f"{args.hook}: already installed, unchanged -> {report['path']}")
    elif action == "forced":
        emit(f"{args.hook}: installed -> {report['path']} (the previous hook is {report['backup']})")
    elif action == "updated":
        emit(f"{args.hook}: updated -> {report['path']}")
    else:
        emit(f"{args.hook}: installed -> {report['path']}")
    return report["exit"]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
