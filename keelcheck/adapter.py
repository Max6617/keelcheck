"""R5's fourth surface: the harness hook adapter, Claude Code first (R5, R6).

A **thin, per-event translator for the locked artefacts**. The harness runs this command at a lifecycle
event (`PreToolUse`), hands it that harness's event JSON on stdin, and reads a decision from its exit code
and stdout: allow (exit 0, no output) or deny (exit 2, plus the harness's own decision field) when the
event would write something the charter has locked — the charter file whose gate table *is* the lock, any
path a ratified row names, and the run record.

It is not the audit. It runs on every tool call, so it is deterministic, local and cheap, and it
deliberately runs no gate and no suite: that is `keelcheck gate run`, at commit time. Its whole job is the
rule this project already lives by — *a model may write a gate, a model may never weaken one* — moved to
the moment before the write instead of the audit after it. It re-implements nothing: the decision comes
from the same charter parsing, anchored-table read and git-normalized hashing the CLI already uses.

**Failure is closed.** An unparseable payload, an event this build does not know, a payload for a tool
this build is installed for that carries neither a path nor a command it can read, an unreadable charter,
a local read that outlives the bound or any internal error *denies*, and the installer writes the
harness's own fail-closed setting beside the command, so the harness does not fail open around a crashed
adapter. This is the one place the adapter is deliberately stronger than the pre-commit hook, which fails
open by absence.

**Inside R6.** No process of ours persists: the harness starts the adapter for one event, it reads stdin,
decides, writes stdout, exits. Nothing binds a socket or listens. The only persistent effect is a
best-effort `kind: "adapter"` append to the existing record **on a deny** — and the append must never be
the reason a deny fails.

**The call is bounded twice, and ours fires first.** The harness's own hook timeout is the outer bound,
and a *timed-out command hook* is documented as one that does not block the tool call — so a stall here
would fail open exactly where this surface is meant to be closed. `--timeout` (default
`DEFAULT_TIMEOUT`) bounds every local `git` read the decision makes, and an expired bound **denies**: the
harness never gets to give up on us first. The reads are real subprocesses (`git rev-parse`,
`git show`, `git config`, `git hash-object`), which is why the bound has to reach `gitcmd` rather than
sit in a loop here.

**Stated, not hidden:** this is a guardrail, not an enforcement boundary. A rewrite through an indirect
path (a script, a heredoc, `python -c`) is not caught by a path-and-verb heuristic, and a harness the user
disables runs no adapter at all. The pre-commit hook catches what reaches a commit, and the audit is still
what reports a missing record when either is bypassed.

Ruled points: Claude Code first; `install`
defaults to `--project` and prints the path and a one-line diff before touching anything; the record line
is `kind: "adapter"`, best-effort, carrying no anchor; and the adapter fails closed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import gitcmd, normalize, record
from .audit import Audit, CHARTER_NAME, load_charter, load_reference
from .output import emit

__all__ = ["main", "decide", "install", "locked_paths", "HARNESSES", "DEFAULT_TIMEOUT"]

HARNESSES = ("claude-code",)
#: The event this build installs for. Anything else is refused as an unknown event rather than guessed at.
KNOWN_EVENT = "PreToolUse"
#: The tools whose `tool_input` this build must be able to read, and the matcher the installer writes.
#: One source of truth on purpose: the refusal for an unreadable payload is only honest if it covers
#: exactly the tools the settings file asks to see.
MATCHED_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit", "Bash")
MATCHER = "|".join(MATCHED_TOOLS)
#: Tool names whose `tool_input` names a path or a command. The heuristic is stated, not implied: a write
#: through an indirect path is not caught here, which the module docstring says plainly.
PATH_KEYS = ("file_path", "notebook_path", "path", "filePath")
COMMAND_KEYS = ("command", "cmd")
#: The bound, in seconds, on this adapter's own local reads (R6). Ten is orders of magnitude more than
#: those reads take on a warm machine and far inside any harness's hook timeout; what matters is that the
#: adapter answers first, not that it is fast.
DEFAULT_TIMEOUT = 10.0
#: The harness's own bound, written into the installed entry. Claude Code documents the handler field
#: `timeout` in seconds with a **600 s default** for a `command` hook, and a timed-out `PreToolUse` command
#: hook does not block — so the field has to be set, and set *above* `DEFAULT_TIMEOUT` so the adapter's own
#: denial normally fires first and this only catches a process that hangs before it can answer. 30 s is
#: three times our bound and far under the vendor's minutes; the installed launch's own cost was measured
#: rather than assumed — the pinned interpreter, `-E -X utf8`, one ordinary event, five runs **0.44, 0.47,
#: 0.49, 0.44, 0.56 s** (min 0.44, max 0.56) — so the interpreter's start is not the term that decides the
#: field, and 30 s is not tight. Source for the field and its 600 s default: Claude Code's hooks
#: reference, `code.claude.com/docs/en/hooks`.
HARNESS_TIMEOUT = 30
#: What a shell string must show *before* the locked path it names, for the command branch to refuse it.
#: The design calls that branch a path-and-verb heuristic (its section "The smallest deliverable, and
#: the acceptance test written first"), and this is the verb half — narrow on purpose, because reading a
#: locked artefact (`cat CHARTER.md`) and *running* one (`python tools/coverage.py`) are ordinary work this
#: surface must not block. A rewrite hidden behind something not listed here is the residual the module
#: docstring states, not a promise.
WRITE_TOKENS = (
    ">", ">>", "tee", "truncate", "sed -i", "perl -i", "dd ", "cp ", "mv ", "rm ", "del ", "copy ",
    "move ", "chmod ", "chown ", "touch ", "ln ", "patch ", "checkout ", "restore ", "Set-Content",
    "Add-Content", "Out-File", "New-Item", "open(", ".write(", ".writelines(",
)


def _settings_path(repo: Path, scope: str) -> Path:
    if scope == "global":
        return Path.home() / ".claude" / "settings.json"
    return repo / ".claude" / "settings.json"


def _audit(repo: Path) -> Audit:
    runs, context = record.record_paths(repo)
    return Audit(
        repo=repo,
        charter_path=repo / CHARTER_NAME,
        record_path=runs,
        review_context_path=context,
    )


def locked_paths(repo: Path | str) -> dict[str, str]:
    """The locked artefacts, repo-relative and POSIX, mapped to what locks them.

    The charter file (its gate table is the lock), every path a ratified row names whatever its kind, and
    the run record. Built from the same `load_charter`/`load_reference` pair the audit uses, so the
    adapter cannot disagree with the audit about what is locked.
    """
    repo = Path(repo).resolve()
    locked: dict[str, str] = {CHARTER_NAME: "(the charter's gate table)"}
    runs, _ = record.record_paths(repo)
    try:
        locked[runs.relative_to(repo).as_posix()] = "(the run record)"
    except ValueError:  # a record outside the repository: it is locked, but not by a repo-relative name
        locked[runs.as_posix()] = "(the run record)"
    try:
        _, charter = load_charter(repo)
    except Exception:  # noqa: BLE001 - an unreadable charter is decided by the caller, which denies
        return locked
    audit = _audit(repo)
    audit.charter = charter
    try:
        audit.commit = gitcmd.head(repo)
    except gitcmd.GitError:
        audit.commit = None
    audit.reference = load_reference(repo, charter, audit)
    rows = audit.reference.gates if audit.reference is not None else []
    for row in rows:
        if row.path:
            locked[row.path.replace("\\", "/")] = row.name or "(unnamed row)"
    return locked


def _hashes(repo: Path, path: str, locked: dict[str, str], rows: list) -> tuple[str | None, str | None]:
    """(the ratified hash, the measured hash) for a locked path, each None where it does not apply."""
    ratified = None
    for row in rows:
        if row.path and row.path.replace("\\", "/") == path:
            ratified = row.hash
            break
    try:
        measured, _ = normalize.content_hash(repo, path)
    except Exception:  # noqa: BLE001 - a path that cannot be hashed is reported as such, not hidden
        measured = None
    return ratified, measured


def _targets(event: dict[str, Any]) -> tuple[list[str], list[str]]:
    """(paths this event names, shell strings it names) — kept apart because they are not the same thing.

    A `tool_input` value under :data:`PATH_KEYS` is a path and is read as one. A value under
    :data:`COMMAND_KEYS` is a whole shell command, whose text *contains* a path but is not one: reading it
    with the path branch is what let every `Bash` write through (see `_writes_path`).
    """
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return [], []
    # A key that is present but empty names nothing, so it does not count as "readable" either — see the
    # refusal in `_decide` for the payload that carries no readable key at all.
    paths = [tool_input[key] for key in PATH_KEYS
             if isinstance(tool_input.get(key), str) and tool_input[key].strip()]
    commands = [tool_input[key] for key in COMMAND_KEYS
                if isinstance(tool_input.get(key), str) and tool_input[key].strip()]
    return paths, commands


def _writes_path(command: str, locked: str) -> bool:
    """Does this shell string write `locked`?

    The write signal has to sit *before* the path it writes, which is how a shell spells a write:
    `echo x > tools/gate.py`, `rm -f tools/gate.py`, `cp other tools/gate.py`,
    `python -c "open('tools/gate.py','w')"`. Order is what keeps the ordinary work allowed —
    `python tools/coverage.py > run.log` names the locked script but redirects into *another* file,
    and `cat CHARTER.md` shows no write signal at all.
    """
    flat = command.replace("\\", "/")
    index = flat.find(locked.replace("\\", "/"))
    if index < 0:
        return False
    return any(token in flat[:index] for token in WRITE_TOKENS)


def _as_relative(target: str, repo: Path) -> str | None:
    """The repo-relative POSIX path a target names, or None when it names nothing in the repository."""
    if not target:
        return None
    candidate = Path(target)
    if not candidate.is_absolute():
        candidate = repo / candidate
    try:
        relative = candidate.resolve().relative_to(repo)
    except (ValueError, OSError):
        return None
    return relative.as_posix()


def _deny(repo: Path, candidate: str, locked: dict[str, str], command: str | None) -> dict:
    """The refusal for a named locked path: what locks it, its ratified hash and its measured one.

    The hashes are read on the way *out*, inside the caller's bound, and a failure to obtain them does
    not soften the denial: the refusal is about the write, and the numbers are what make it checkable.
    """
    rows = []
    try:
        _, charter = load_charter(repo)
        audit = _audit(repo)
        audit.charter = charter
        try:
            audit.commit = gitcmd.head(repo)
        except gitcmd.GitError:
            audit.commit = None
        audit.reference = load_reference(repo, charter, audit)
        rows = audit.reference.gates if audit.reference is not None else []
    except Exception:  # noqa: BLE001 - the denial does not depend on this succeeding
        rows = []
    ratified, measured = _hashes(repo, candidate, locked, rows)
    name = locked[candidate]
    if ratified and measured:
        detail = (f"its ratified hash is {ratified} and its measured hash is {measured}"
                  + ("" if ratified == measured else " -- they differ"))
    elif ratified:
        detail = f"its ratified hash is {ratified}, and its bytes could not be hashed here"
    else:
        detail = "it is the lock itself, not a hashed row"
    return {
        "locked": sorted(locked),
        "gate": name,
        "hashes": {"ratified": ratified, "measured": measured},
        "path": candidate,
        "command": command,
        "decision": "deny",
        "reason": (f"{candidate} is locked by `{name}`: {detail}. A gate may be changed only "
                   "by re-ratifying it in the charter, never by a write from here"),
    }


def _decide(event: dict, repo: Path) -> dict:
    """The decision itself, inside the caller's deadline. Split out so `decide` owns the bound."""
    locked = locked_paths(repo)
    base = {
        "locked": sorted(locked),
        "gate": None,
        "hashes": {"ratified": None, "measured": None},
        "path": None,
        "command": None,
    }
    if event.get("hook_event_name") not in (None, KNOWN_EVENT):
        return {**base, "decision": "deny",
                "reason": (f"the event is {event.get('hook_event_name')!r}, which this build does not "
                           "know: an adapter that cannot classify its event must not allow the write")}
    tool_input = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
    command = tool_input.get("command") if isinstance(tool_input.get("command"), str) else None

    paths, commands = _targets(event)
    for target in paths:
        relative = _as_relative(target, repo)
        candidates = [relative] if relative else []
        # A path that names nothing in this repository can still name a locked artefact inside it, so the
        # containment reading is kept for paths (a write to another checkout's `tools/gate.py` is refused).
        if relative is None:
            candidates = [known for known in locked if known in target.replace("\\", "/")]
        for candidate in candidates:
            if candidate and candidate in locked:
                return _deny(repo, candidate, locked, command)
    # A shell string is not a path: `Path("rm -f tools/gate.py").resolve()` is a perfectly good filename
    # that is not on any disk, which is why the whole command used to resolve to a relative path and fall
    # through to `allow`. `_writes_path` asks the question that matters instead.
    for text in commands:
        for known in locked:
            if _writes_path(text, known):
                return _deny(repo, known, locked, command)
    # Nothing readable at all, for a tool this build is installed for (or for an event that does not name
    # its tool, where nothing says the payload is someone else's): that is an allow waiting to happen if a
    # harness ever renames its keys, so it is a refusal instead — the same rule as an event this build
    # does not know. A tool this build is *not* installed for stays an allow: it is not ours to judge.
    tool = event.get("tool_name")
    if not paths and not commands and (tool in MATCHED_TOOLS or not isinstance(tool, str)):
        keys = ", ".join(sorted(tool_input)) if isinstance(tool_input, dict) and tool_input else "none"
        what = f"the event is for {tool!r}" if isinstance(tool, str) else "the event names no tool"
        return {**base, "decision": "deny", "reason": (
            f"{what} and carries no path and no command this build can read (tool_input keys: {keys}): "
            "an adapter that cannot find what an event touches must not allow it")}
    return {**base, "decision": "allow", "command": command}


def decide(event: dict, repo: Path | str, *, timeout: float | None = DEFAULT_TIMEOUT) -> dict:
    """The decision for one event, as data. No output, no record, no side effect.

    Pure on purpose: the harness shim (exit code, `hookSpecificOutput`) and the record append are applied
    by `main`, so this is the one place the decision is made and the one place a second surface must call
    if it wants the same answer.

    `timeout` bounds every local `git` read the decision makes (R6); `None` means no bound, which is the
    API caller's explicit choice and never the CLI's. An expired bound denies — see the module docstring
    for why the smaller bound has to be ours.
    """
    repo = Path(repo).resolve()
    try:
        with gitcmd.deadline(timeout):
            return _decide(event, repo)
    except gitcmd.GitTimeout as exc:
        return {
            "locked": [],
            "gate": None,
            "hashes": {"ratified": None, "measured": None},
            "path": None,
            "command": None,
            "decision": "deny",
            "reason": (f"the adapter's {timeout}s bound on its local reads expired ({exc}), so it denies "
                       "rather than keep the harness waiting: a write to a locked artefact must not "
                       "proceed on a read that did not finish"),
        }


def _hook_decision(decision: dict) -> dict:
    """Claude Code's framing of a decision: the field its `PreToolUse` hook reads."""
    return {
        "hookSpecificOutput": {
            "hookEventName": KNOWN_EVENT,
            "permissionDecision": decision["decision"],
            "permissionDecisionReason": decision.get("reason") or "",
        }
    }


def _record_refusal(repo: Path, decision: dict, event: dict) -> None:
    """The best-effort `kind: adapter` line. **Never** the reason a deny fails."""
    try:
        runs, _ = record.record_paths(repo)
        record.ensure_header(runs)
        record.append(runs, {
            "kind": "adapter",
            "at": record.now(),
            "decision": decision["decision"],
            "path": decision.get("path"),
            "command": decision.get("command"),
            "gate": decision.get("gate"),
            "hashes": decision.get("hashes"),
            "event": event.get("hook_event_name"),
        })
    except Exception:  # noqa: BLE001 - ruled: the append must never be the reason a deny fails
        pass


def one_event(harness: str, *, repo: Path | str | None = None, stdin=None, stdout=None,
              timeout: float | None = DEFAULT_TIMEOUT) -> int:
    """Read one event, decide, print the harness's decision, return the exit code."""
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    raw = stdin.read()
    target = Path(repo).resolve() if repo else None
    event: dict = {}
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("the payload is not a JSON object")
        event = parsed
        if target is None:
            cwd = event.get("cwd")
            target = Path(cwd).resolve() if isinstance(cwd, str) and cwd else Path.cwd()
        decision = decide(event, target, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 - fail closed: a gate that cannot read its event denies
        target = target or Path.cwd()
        decision = {"decision": "deny", "gate": None, "path": None, "command": None,
                    "locked": [], "hashes": {"ratified": None, "measured": None},
                    "reason": f"the adapter could not read its event ({exc}), so it denies"}
    if decision["decision"] == "deny":
        _record_refusal(target, decision, event)
        stdout.write(json.dumps(_hook_decision(decision), ensure_ascii=False) + "\n")
        stdout.flush()
        return 2
    return 0


def _has_our_command(entries: list, command: str) -> bool:
    """Is this installer's exact command already among these entries? (Idempotence, by identity.)"""
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for hook in entry.get("hooks") or []:
            if isinstance(hook, dict) and hook.get("command") == command:
                return True
    return False


def _without_our_command(entries: list, command: str) -> list:
    """The same entries with this installer's own hook removed — identity is the command string."""
    kept = []
    for entry in entries:
        if isinstance(entry, dict) and _has_our_command([entry], command):
            continue
        kept.append(entry)
    return kept


def _merged_hooks(existing: Any, ours: dict) -> dict:
    """Add our entries to the harness's existing hooks without dropping anyone else's.

    A settings file can hold other tools' hooks for the same event, so this appends rather than replaces:
    overwriting a foreign hook because `--force` was given would be a quiet change to someone else's
    permissions, which is the thing this surface exists to prevent. Installing twice changes no byte, by
    the identity of the command string — the same rule the shell hook installer uses for its marker.

    Ours is *dropped and re-added* rather than skipped when already present, because the entry's shape can
    change under an installed file: the harness's own `timeout` was added after the first installs, and an
    identity that only looked at the command would leave an old shape in place for ever. For an unchanged
    entry the result is byte-identical (ours was and is the last one).
    """
    hooks: dict = dict(existing or {}) if isinstance(existing, dict) else {}
    for event_name, new_entries in ours.items():
        command = new_entries[0]["hooks"][0]["command"] if new_entries else ""
        current = _without_our_command(list(hooks.get(event_name) or []), command)
        hooks[event_name] = current + list(new_entries)
    return hooks


def install(repo: Path | str, harness: str, *, scope: str = "project", force: bool = False,
            stdout=None) -> int:
    """Write the harness's own settings entry. Project by default; the path and diff are printed first."""
    stdout = sys.stdout if stdout is None else stdout
    repo = Path(repo).resolve()
    if harness not in HARNESSES:
        emit(f"keelcheck adapter: unknown harness {harness!r}; this build knows {', '.join(HARNESSES)}")
        return 2
    try:
        _, charter = load_charter(repo)
    except Exception as exc:  # noqa: BLE001 - an unauditable repository gets no adapter
        emit(f"keelcheck adapter: this repository cannot be audited ({exc}), so it gets no adapter")
        return 2
    if not charter.ratified_at:
        emit("keelcheck adapter: the charter names no `Ratified at:` line, so there is nothing to lock "
             "an edit against; a repository that cannot be audited gets no adapter")
        return 2

    path = _settings_path(repo, scope)
    command = _launch(repo, "adapter claude-code --repo " + str(repo).replace("\\", "/"))
    entry = {
        "hooks": {
            KNOWN_EVENT: [
                {
                    "matcher": MATCHER,
                    "hooks": [{"type": "command", "command": command, "timeout": HARNESS_TIMEOUT,
                               "onFailure": "block"}],
                }
            ]
        }
    }
    existing: dict = {}
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                existing = {}
        except (OSError, ValueError) as exc:
            emit(f"keelcheck adapter: {path} exists and is not readable JSON ({exc}); nothing written")
            return 2
    if existing.get("hooks") and not force:
        emit(f"keelcheck adapter: {path} already defines hooks, so it is not overwritten. "
             f"Re-run with --force to merge ours in and keep {path.name}.keel-backup")
        return 1

    merged = {**existing, "hooks": _merged_hooks(existing.get("hooks"), entry["hooks"])}
    stdout.write(f"keelcheck adapter install {harness} ({scope})\n")
    stdout.write(f"  file: {path}\n")
    stdout.write(f"  adds: hooks.{KNOWN_EVENT} -> {json.dumps(entry['hooks'][KNOWN_EVENT])}\n")
    stdout.flush()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        backup = path.with_name(path.name + ".keel-backup")
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8", newline="")
    path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
                    newline="")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        prog="keelcheck adapter",
        description=(
            "the harness hook adapter: one lifecycle event in on stdin, the harness's decision out "
            "(R5's fourth surface). Denies a write that would touch a locked artefact, and fails closed"
        ),
    )
    parser.add_argument(
        "words", nargs="*",
        help="`install <harness> [repo]` to write a settings entry, or `<harness> [repo]` to read one "
             "event from stdin (harness defaults to this build's first, claude-code)",
    )
    parser.add_argument("--repo", dest="repo_option", default=None,
                        help="repository the decision is about (default: the event's `cwd`)")
    parser.add_argument("--project", action="store_const", const="project", dest="scope",
                        help="write the project settings file (the default)")
    parser.add_argument("--global", action="store_const", const="global", dest="scope",
                        help="write the user settings file (~/.claude/settings.json), explicitly")
    parser.add_argument("--force", action="store_true",
                        help="install: merge into existing hooks, keeping a .keel-backup beside the file")
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT, metavar="S",
        help=(f"the bound, in seconds, on this adapter's own local reads (default: {DEFAULT_TIMEOUT:g}). "
              "It fires before the harness's own hook timeout on purpose: the harnesses document a "
              "timed-out command hook as one that does not block, so an expired bound denies here "
              "rather than letting the harness give up on us"),
    )
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        emit("keelcheck adapter: --timeout must be a positive number of seconds")
        return 2

    # The design's own grammar: `adapter install <harness> [--project|--global] [--force]` for the
    # installer, `adapter <harness>` for one event. `install` leads, so it is the word that decides.
    words = list(args.words)
    installing = bool(words) and words[0] == "install"
    if installing:
        words = words[1:]
    harness = words[0] if words else HARNESSES[0]
    repo = args.repo_option or (words[1] if len(words) > 1 else None)

    if harness not in HARNESSES:
        emit(f"keelcheck adapter: unknown harness {harness!r}; this build knows "
             f"{', '.join(HARNESSES)}")
        return 2
    if installing:
        return install(repo or ".", harness, scope=args.scope or "project", force=args.force)
    return one_event(harness, repo=repo, timeout=args.timeout)


def _launch(repo: Path, tail: str) -> str:
    """The hermetic launch, same shape as the hook installer's: pinned interpreter, no `PYTHON*` vote."""
    from .hook import launch_command

    return launch_command(repo, tail)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
