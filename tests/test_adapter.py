r"""R5's fourth surface, the harness hook adapter (Claude Code first) — red before `adapter.py` existed.

The acceptance test is the design's own (section "The smallest
deliverable, and the acceptance test written first"): a recorded
Claude Code `PreToolUse` payload whose `tool_input` names a path a ratified gate row names must exit
**2**, print `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", …}}`
with a reason naming the gate and both hashes, and append a `kind: "adapter"` line to the record naming
the path, the command and the decision. The same payload unparseable **also denies**, because a gate that
cannot read its event must not allow the edit. Its two companions prove the surface is not merely noisy:
an ordinary payload exits 0 with no output, and one editing an unlocked file exits 0.

**Fixtures are written to Claude Code's documented `PreToolUse` schema, not captured from a live
session**, and the difference is named rather than glossed: `{REPO}` stands in for the absolute path a
real session carries and the test substitutes it.

**A capture was attempted, twice, on 2026-10-16, and this host blocks it — measured, not assumed.** In a
scratch repository outside this checkout, with a hook whose command appends its stdin to a file, `claude
-p` ran and did its own work, and its answer said the shell tools had failed with `EPERM: operation not
permitted` when they tried to start `powershell.exe`/`bash.exe`. With the hook installed through
`--settings` and `onFailure: "block"`, the same session reported `Hook failed to run (PreToolUse:Write):
EPERM: operation not permitted, uv_spawn 'C:\Program Files\Git\bin\bash.exe'` — so **no hook process ran
and no payload arrived**. Command hooks go through Git Bash on Windows, and this agent's process sandbox
denies that spawn (the documented piped-stdio boundary). `--debug-file` inside the workspace does work and
records that the hook failed, but it does not record the payload, and the session transcript is written
outside the workspace.

What the real payloads' *keys* are is uncaptured here, not unknown: real sessions on this machine carry
`Bash` with `tool_input.command` (beside `description`, sometimes `timeout`/`run_in_background`), `Write`
with `tool_input.file_path` and `.content`, and `Edit` with `tool_input.file_path`, `.old_string`,
`.new_string` and `.replace_all` in their transcripts' tool calls — the same object Claude Code hands a
hook as `tool_input`. Every one of those keys is in `PATH_KEYS` or `COMMAND_KEYS`.

The adapter is a guardrail, not an enforcement boundary (the design says so in that same section, and so
do the
harnesses): a rewrite through an indirect path is not caught by a path-and-verb heuristic. These tests
pin what the surface does, not what it promises.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import _support

REPO = _support.REPO
FIXTURES = REPO / "tests" / "_artefacts" / "adapter" / "claude-code"
REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]


def _repo(scratch) -> Path:
    """A ratified charter whose gate row names `tools/gate.py` and whose prompt row names a file."""
    _support.write(scratch / "tracked.txt", "hello\n")
    _support.write(scratch / "tools" / "gate.py", "print('ok')\n")
    _support.write(scratch / "review-prompt.md", "review the state against the original\n")
    gates = [
        ("coverage", "tools/gate.py", _support.hash_file(scratch / "tools" / "gate.py")),
        ("review-prompt", "review-prompt.md",
         _support.hash_file(scratch / "review-prompt.md"), "prompt"),
    ]
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, gates=gates, ratified=sha)
    _support.commit_all(scratch, "ratified")
    return scratch


def _payload(name: str, repo: Path) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8").replace("{REPO}", repo.as_posix())


def _pythonpath(*extra: Path) -> str:
    """The checkout (and any shim directory) ahead of whatever the environment already had.

    Not a replacement: under the coverage gate the parent's `PYTHONPATH` carries the child tracer's
    bootstrap, so a test that overwrote it would run its children **unmeasured** — a measurement of the
    test rather than of the code. `extra` leads so a shim can be found first when a case needs one.
    """
    parts = [str(part) for part in (*extra, REPO)]
    inherited = os.environ.get("PYTHONPATH", "")
    if inherited:
        parts.append(inherited)
    return os.pathsep.join(parts)


def _adapter(repo: Path, name: str, *extra: str, env_extra: dict | None = None):
    """One event through the adapter, the way a harness runs it: payload on stdin, decision on stdout.

    `PYTHONPATH` carries the checkout because a harness runs the adapter with the interpreter the
    *installer* pinned; here the test starts `python -m` directly from the repository under test, so the
    package has to be importable from somewhere.
    """
    return subprocess.run(
        [sys.executable, "-m", "keelcheck", "adapter", "claude-code", *extra],
        input=_payload(name, repo), capture_output=True, text=True, encoding="utf-8",
        cwd=str(repo), timeout=120,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(REPO),
             **(env_extra or {})},
    )


def _adapter_lines(repo: Path) -> list[dict]:
    path = repo / ".keel" / "runs.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and json.loads(line).get("kind") == "adapter"]


# --- the acceptance contract --------------------------------------------------


def test_a_payload_naming_a_ratified_gate_is_denied_and_recorded(scratch):
    repo = _repo(scratch)
    done = _adapter(repo, "deny-rewrites-a-gate-script.json")
    out = done.stdout.strip()

    assert done.returncode == 2, (
        f"a write to a path a ratified gate row names was not denied:\n{done.stdout}\n{done.stderr}")
    decision = json.loads(out)
    hook = decision.get("hookSpecificOutput", {})
    assert hook.get("hookEventName") == "PreToolUse", f"wrong hook event name: {decision}"
    assert hook.get("permissionDecision") == "deny", f"not a deny: {decision}"
    reason = hook.get("permissionDecisionReason", "")
    assert "coverage" in reason, f"the reason does not name the gate: {reason}"
    # The design's wording: the reason names the gate *and both hashes*, so a reader can see whether the
    # file still matches what was ratified without opening anything else.
    assert reason.count("sha256:") >= 2, f"the reason does not carry both hashes: {reason}"

    lines = _adapter_lines(repo)
    assert lines, "a refusal left no `kind: adapter` line in the record"
    line = lines[-1]
    assert "tools/gate.py" in json.dumps(line), f"the line does not name the path: {line}"
    assert line.get("decision") == "deny", f"the line does not name the decision: {line}"
    assert "ratified" not in line, (
        f"the adapter line carries an anchor field, which it must not: {line}")


def test_a_payload_editing_the_charter_is_denied(scratch):
    repo = _repo(scratch)
    done = _adapter(repo, "deny-edits-the-charter-gate-row.json")
    assert done.returncode == 2, (
        f"the charter, whose gate table is the lock, was editable:\n{done.stdout}\n{done.stderr}")
    assert json.loads(done.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_a_shell_command_writing_a_ratified_gate_is_denied_and_recorded(scratch):
    """The design's first acceptance case, in that same section: a *command* writes a path a
    ratified row names. Both `Write` fixtures cover the path-key branch, so this is the branch a
    stranger's session hits first — a `Bash` payload naming the file inside the command string."""
    repo = _repo(scratch)
    done = _adapter(repo, "deny-rewrites-a-gate-script-with-a-shell-command.json")
    out = done.stdout.strip()

    assert done.returncode == 2, (
        f"a shell command writing a ratified gate was not denied:\n{done.stdout}\n{done.stderr}")
    hook = json.loads(out)["hookSpecificOutput"]
    assert hook.get("permissionDecision") == "deny", f"not a deny: {hook}"
    reason = hook.get("permissionDecisionReason", "")
    assert "coverage" in reason, f"the reason does not name the gate: {reason}"
    assert reason.count("sha256:") >= 2, f"the reason does not carry both hashes: {reason}"

    lines = _adapter_lines(repo)
    assert lines, "the refusal left no `kind: adapter` line in the record"
    line = lines[-1]
    assert line.get("path") == "tools/gate.py", f"the line does not name the path: {line}"
    assert "tools/gate.py" in (line.get("command") or ""), (
        f"the line does not carry the command that was refused: {line}")


def test_an_ordinary_payload_is_allowed_in_silence(scratch):
    repo = _repo(scratch)
    done = _adapter(repo, "allow-ordinary.json")
    assert done.returncode == 0, f"an ordinary payload was not allowed:\n{done.stdout}\n{done.stderr}"
    assert done.stdout.strip() == "", f"an allow printed something: {done.stdout!r}"
    assert not _adapter_lines(repo), "an allow was recorded; only refusals are worth keeping"


def test_an_unlocked_file_is_allowed(scratch):
    repo = _repo(scratch)
    payload = json.dumps({
        "hook_event_name": "PreToolUse", "cwd": str(repo), "tool_name": "Write",
        "tool_input": {"file_path": str(repo / "notes.md"), "content": "an unlocked file\n"},
    })
    done = subprocess.run(
        [sys.executable, "-m", "keelcheck", "adapter", "claude-code"],
        input=payload, capture_output=True, text=True, encoding="utf-8", cwd=str(repo), timeout=120,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(REPO)},
    )
    assert done.returncode == 0, f"an unlocked file was denied:\n{done.stdout}\n{done.stderr}"


def test_an_unparseable_payload_denies(scratch):
    repo = _repo(scratch)
    done = _adapter(repo, "malformed.json")
    assert done.returncode == 2, (
        f"a payload the adapter cannot read was allowed:\n{done.stdout}\n{done.stderr}")
    decision = json.loads(done.stdout)
    assert decision["hookSpecificOutput"]["permissionDecision"] == "deny", decision


def test_an_unknown_event_denies(scratch):
    repo = _repo(scratch)
    done = _adapter(repo, "unknown-event.json")
    assert done.returncode == 2, (
        f"an event the adapter does not know was allowed:\n{done.stdout}\n{done.stderr}")
    assert json.loads(done.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def _run_payload(repo: Path, payload: dict, *extra: str, env_extra: dict | None = None):
    """One event of any shape, the way a harness runs it: payload on stdin, decision on stdout."""
    return subprocess.run(
        [sys.executable, "-m", "keelcheck", "adapter", "claude-code", *extra],
        input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8",
        cwd=str(repo), timeout=120,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": _pythonpath(),
             **(env_extra or {})},
    )


def test_a_matched_tool_with_no_readable_input_denies(scratch):
    """An unreadable `tool_input` is not permission.

    The design's rule for an event the adapter cannot read (same section) applies to the payload's *keys*
    too: a harness (or a future version of this one) that renames `file_path`, or a hook someone wired to
    an event shape this build has never seen, would otherwise read as **allow** — and an allow is the one
    answer a lock must not give by accident. Both shapes are denied: a `tool_name` this build is
    installed for, and no `tool_name` at all (nothing then says the event is someone else's).
    """
    repo = _repo(scratch)
    for tool, keys in (
        ({"tool_name": "Write"}, {"filePathIsNowCalledSomethingElse": "tools/gate.py"}),
        ({}, {"whatever_this_is": "tools/gate.py"}),
    ):
        payload = {"session_id": "0f7c2b1e-0000-4000-8000-0000000000aa", "cwd": str(repo),
                   "hook_event_name": "PreToolUse", "tool_input": keys, **tool}
        done = _run_payload(repo, payload)
        assert done.returncode == 2, (
            f"a payload for {tool.get('tool_name', 'no named tool')} with no readable input was "
            f"allowed:\n{done.stdout}\n{done.stderr}")
        hook = json.loads(done.stdout)["hookSpecificOutput"]
        assert hook["permissionDecision"] == "deny", hook
        assert "no path and no command" in hook["permissionDecisionReason"], (
            f"the refusal does not say what could not be read: {hook}")


def test_a_tool_this_build_is_not_installed_for_is_still_allowed(scratch):
    """The boundary, stated rather than implied: the installer matches five tools, and a payload for
    another one — a matcher someone widened by hand — is not this build's to refuse."""
    repo = _repo(scratch)
    done = _run_payload(repo, {
        "session_id": "0f7c2b1e-0000-4000-8000-0000000000ab", "cwd": str(repo),
        "hook_event_name": "PreToolUse", "tool_name": "WebFetch",
        "tool_input": {"url": "https://example.invalid", "prompt": "summarise"},
    })
    assert done.returncode == 0, (
        f"a tool this adapter is not installed for was refused:\n{done.stdout}\n{done.stderr}")
    assert done.stdout.strip() == "", f"an allow printed something: {done.stdout!r}"


def test_a_deny_stands_when_the_record_cannot_be_written(scratch):
    """Ruled: the append must never be the reason a deny fails."""
    repo = _repo(scratch)
    keel_dir = repo / ".keel"
    keel_dir.mkdir(exist_ok=True)
    (keel_dir / "runs.jsonl").mkdir()  # a directory where the record file goes: the append must fail

    done = _adapter(repo, "deny-rewrites-a-gate-script.json")

    assert done.returncode == 2, (
        f"an unwritable record turned a deny into something else:\n{done.stdout}\n{done.stderr}")
    assert json.loads(done.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


# --- the bound on the adapter's own reads (R6) ---------------------------------


def test_a_hung_git_read_denies_instead_of_hanging(scratch, monkeypatch):
    """A read that never answers must end as a deny, not as a hook that hangs past the harness's bound.

    The child really does hang and a real `subprocess.run` really does kill it; what is substituted is
    *which* command hangs, because no test can make the host's `git` stall on demand. The refusal is the
    fail-closed direction, and the reason has to say that the bound is why, so a reader can tell a
    timeout from a file that could not be read.
    """
    repo = _repo(scratch)
    sys.path.insert(0, str(REPO))
    from keelcheck import adapter, gitcmd

    class HungGit:
        """`gitcmd`'s view of `subprocess`: every git read starts a child that never returns."""
        TimeoutExpired = subprocess.TimeoutExpired

        @staticmethod
        def run(command, **kwargs):
            return subprocess.run([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)

    monkeypatch.setattr(gitcmd, "subprocess", HungGit())
    event = json.loads(_payload("deny-rewrites-a-gate-script.json", repo))

    started = time.monotonic()
    decision = adapter.decide(event, repo, timeout=0.5)
    elapsed = time.monotonic() - started

    assert elapsed < 15, f"a hung read was waited on for {elapsed:.1f}s instead of the bound"
    assert decision["decision"] == "deny", f"a hung read allowed the write: {decision}"
    assert "bound on its local reads expired" in decision["reason"], (
        f"the refusal does not name the bound as the reason: {decision}")


def test_the_timeout_flag_is_plumbed_and_an_expired_bound_denies(scratch):
    """The flag reaches the decision, and a budget that is already spent refuses instead of reading.

    This case deliberately claims no more than that: with a millisecond the budget is spent before the
    first `git` starts, so the branch it pins is the one that refuses *without* starting a read (the
    reason says `never started`). The bound on a read that is already running is
    `test_a_hung_git_read_denies_instead_of_hanging` and
    `test_the_timeout_flag_bounds_a_running_read_through_the_cli`.
    """
    repo = _repo(scratch)
    done = _adapter(repo, "deny-rewrites-a-gate-script.json", "--timeout", "0.001")

    assert done.returncode == 2, (
        f"an expired bound did not deny:\n{done.stdout}\n{done.stderr}")
    hook = json.loads(done.stdout)["hookSpecificOutput"]
    assert hook["permissionDecision"] == "deny", hook
    reason = hook["permissionDecisionReason"]
    assert "bound on its local reads expired" in reason, f"the denial does not name the bound: {hook}"
    assert "never started" in reason, (
        f"this case is meant to pin the refusal without a read; it took another branch: {reason}")


def test_the_timeout_flag_bounds_a_running_read_through_the_cli(scratch):
    """The flag, end to end, on a read that *starts* and then outlives the bound.

    The other command-line case is satisfied by the refusal to start a read on an already-spent budget, so
    it says nothing about a read in flight. Here the reads really hang: `PYTHONPATH` carries a
    `sitecustomize` that points `gitcmd`'s subprocess seam at a child which sleeps, so the real
    `subprocess.run(timeout=...)` has to kill it. **The clock is the signal, and it has to be read against
    the *hang*, not against the bound:** the first read is `git rev-parse HEAD`, whose timeout
    `locked_paths` absorbs on purpose (a read that failed means "no commit known"), so the *next* read is
    the one whose refusal reaches the reason -- and it says `never started`, which is true of that read.
    With `timeout=None` that first read is not killed at all: it runs its full hang, and only then does the
    next read's spent-deadline check end the event. So the three numbers have to be ordered --
    **bound 3 s < assertion 15 s < hang 30 s** -- and that ordering is the whole test. Measured in a copy of
    the tree with both `timeout=budget` lines neutralised (an independent verifier's mutation): the case fails with
    `AssertionError: the run took 30.4s: a read that hangs 30 s was waited on instead of being bounded`,
    while unmutated the same case reads `1 passed in 4.02s` end to end. My first version of this case hung
    the child 12 s against a 20 s assertion, which the mutation *passed* -- the ordering had it backwards,
    and only running the mutation showed it. A fake
    `git` binary would be the other way to hang a read, and on Windows a `.cmd`/`.bat` stand-in cannot be
    found by `CreateProcess` -- measured, `git.bat` on `PATH` is simply skipped.
    """
    repo = _repo(scratch)
    shim = scratch / "hangpath"
    shim.mkdir()
    (shim / "sitecustomize.py").write_text(
        "import subprocess as _sp, sys as _sys\n"
        "from keelcheck import gitcmd as _gitcmd\n"
        "\n"
        "class _Hung:\n"
        "    TimeoutExpired = _sp.TimeoutExpired\n"
        "\n"
        "    @staticmethod\n"
        "    def run(command, **kwargs):\n"
        "        return _sp.run([_sys.executable, '-c', 'import time; time.sleep(30)'], **kwargs)\n"
        "\n"
        "_gitcmd.subprocess = _Hung()\n",
        encoding="utf-8", newline="\n",
    )
    payload = {
        "session_id": "0f7c2b1e-0000-4000-8000-0000000000bb", "cwd": str(repo),
        "hook_event_name": "PreToolUse", "tool_name": "Write",
        "tool_input": {"file_path": str(repo / "tools" / "gate.py"), "content": "exit 0\n"},
    }

    started = time.monotonic()
    done = _run_payload(repo, payload, "--timeout", "3",
                        env_extra={"PYTHONPATH": _pythonpath(shim)})
    elapsed = time.monotonic() - started

    assert done.returncode == 2, (
        f"a read that outlived the bound did not deny:\n{done.stdout}\n{done.stderr}")
    assert elapsed < 15, (
        f"the run took {elapsed:.1f}s: a read that hangs 30 s was waited on instead of being bounded")
    reason = json.loads(done.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "bound on its local reads expired" in reason, (
        f"the refusal does not name the bound: {reason}")


# --- the decision is data, not a side effect ----------------------------------


def test_decide_is_pure_and_returns_the_shared_shape(scratch):
    repo = _repo(scratch)
    sys.path.insert(0, str(REPO))
    from keelcheck import adapter

    event = json.loads(_payload("deny-rewrites-a-gate-script.json", repo))
    decision = adapter.decide(event, repo)

    assert decision["decision"] == "deny", decision
    assert decision["gate"] == "coverage", decision
    assert decision["locked"] and "tools/gate.py" in json.dumps(decision["locked"]), decision
    assert set(decision["hashes"]) == {"ratified", "measured"}, decision
    assert decision["hashes"]["ratified"] and decision["hashes"]["measured"], decision
    assert isinstance(decision["reason"], str) and decision["reason"], decision

    allow = adapter.decide(json.loads(_payload("allow-ordinary.json", repo)), repo)
    assert allow["decision"] == "allow", allow


# --- the installer: project by default, and it says what it will touch ---------


def test_install_defaults_to_the_project_and_prints_the_diff_before_writing(scratch):
    repo = _repo(scratch)
    done = _support.keelcheck("adapter", "install", "claude-code", str(repo))
    out = _support.combined(done)

    assert done.returncode == 0, out
    project = repo / ".claude" / "settings.json"
    assert str(project).replace("\\", "/") in out.replace("\\", "/"), (
        f"the project settings path is not printed before the write:\n{out}")
    assert "hooks" in out and "PreToolUse" in out, f"no one-line diff of the entry:\n{out}"
    assert project.is_file(), f"the settings were not written: {project}"

    settings = json.loads(project.read_text(encoding="utf-8"))
    entry = json.dumps(settings)
    assert "PreToolUse" in entry and "onFailure" in entry, (
        f"the entry is not fail-closed: {settings}")
    assert "settings.json" in entry or "adapter" in entry, settings
    # The global file must not be touched, and not even named as where this landed: compare against the
    # global settings *path*, not the home directory, which is a prefix of every scratch repo's path.
    global_settings = (Path.home() / ".claude" / "settings.json").as_posix()
    assert global_settings not in out.replace("\\", "/"), f"the default install named the global file:\n{out}"
    assert not (Path.home() / ".claude" / "settings.json").exists() or str(project) != str(
        Path.home() / ".claude" / "settings.json"), "the default install wrote the global file"


def test_the_installed_entry_sets_the_harness_timeout_above_ours(scratch):
    """The harness's own bound, ruled on an independent reviewer's sourced fetch.

    Claude Code documents the handler field `timeout` in seconds, **600** by default for a `command`
    hook, and a timed-out `PreToolUse` command hook does not block — so leaving the field out means the
    vendor's minutes-long default is what stands between a hung adapter and an open tool call. Ours has
    to sit strictly above the adapter's own bound, so the adapter's own denial normally fires first and
    this field only catches a process that hangs before it can answer.
    """
    repo = _repo(scratch)
    done = _support.keelcheck("adapter", "install", "claude-code", str(repo))
    assert done.returncode == 0, _support.combined(done)

    settings = json.loads((repo / ".claude" / "settings.json").read_text(encoding="utf-8"))
    handler = settings["hooks"]["PreToolUse"][0]["hooks"][0]
    sys.path.insert(0, str(REPO))
    from keelcheck import adapter

    assert handler["type"] == "command" and "adapter claude-code" in handler["command"], handler
    assert handler["onFailure"] == "block", f"the entry is not fail-closed: {handler}"
    assert handler["timeout"] == 30, f"the harness bound is not set: {handler}"
    assert handler["timeout"] > adapter.DEFAULT_TIMEOUT, (
        f"the harness bound must sit above the adapter's own ({adapter.DEFAULT_TIMEOUT}s): {handler}")


def test_force_upgrades_our_own_entry_in_place(scratch):
    """An install made before the harness bound existed carries our command and not the field.

    `--force` is that user's upgrade path, and it must not leave two copies of our hook on the event: the
    entry is dropped and re-added by the identity of its command, not merely skipped for being present.
    """
    repo = _repo(scratch)
    settings_path = repo / ".claude" / "settings.json"
    first = _support.keelcheck("adapter", "install", "claude-code", str(repo))
    assert first.returncode == 0, _support.combined(first)

    old = json.loads(settings_path.read_text(encoding="utf-8"))
    for handler in old["hooks"]["PreToolUse"][0]["hooks"]:
        handler.pop("timeout", None)
    settings_path.write_text(json.dumps(old, indent=2) + "\n", encoding="utf-8", newline="")

    again = _support.keelcheck("adapter", "install", "claude-code", str(repo), "--force")
    assert again.returncode == 0, _support.combined(again)
    merged = json.loads(settings_path.read_text(encoding="utf-8"))
    entries = merged["hooks"]["PreToolUse"]
    ours = [entry for entry in entries if "adapter claude-code" in json.dumps(entry)]
    assert len(entries) == 1 and len(ours) == 1, f"the upgrade left a duplicate entry: {merged}"
    assert ours[0]["hooks"][0]["timeout"] == 30, f"the upgrade did not restore the field: {ours[0]}"


def test_the_global_write_happens_only_when_asked_and_keeps_a_foreign_entry_as_backup(scratch):
    repo = _repo(scratch)
    home = scratch / "fake-home"
    (home / ".claude").mkdir(parents=True, exist_ok=True)
    foreign = home / ".claude" / "settings.json"
    # A foreign *hooks* block is the thing not overwritten implicitly: someone else's hook, in the field
    # this installer writes. A tool's own top-level settings are merged around either way.
    foreign.write_text(json.dumps({
        "someOtherTool": {"x": 1},
        "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "other"}]}]},
    }), encoding="utf-8")
    env = {"USERPROFILE": str(home), "HOME": str(home)}

    refused = _support.keelcheck("adapter", "install", "claude-code", str(repo), "--global",
                                 env_extra=env)
    assert refused.returncode != 0, (
        f"a foreign hooks block was overwritten:\n{_support.combined(refused)}")
    untouched = json.loads(foreign.read_text(encoding="utf-8"))
    assert untouched["hooks"]["PreToolUse"][0]["hooks"][0]["command"] == "other", (
        "the foreign hook was modified without --force")

    forced = _support.keelcheck("adapter", "install", "claude-code", str(repo), "--global", "--force",
                                env_extra=env)
    assert forced.returncode == 0, _support.combined(forced)
    merged = json.loads(foreign.read_text(encoding="utf-8"))
    assert "someOtherTool" in merged, f"--force dropped the tool's own settings: {merged}"
    blob = json.dumps(merged)
    assert "keelcheck" in blob, f"--force wrote no keelcheck hook: {merged}"
    assert "other" in blob, f"--force dropped the foreign hook instead of keeping both: {merged}"
    backups = list((home / ".claude").glob("*.keel-backup*"))
    assert backups, f"--force kept no backup beside {foreign}"


def test_installing_twice_changes_no_byte_and_keeps_a_foreign_hook(scratch):
    """Idempotence by the identity of the command string, the way the shell hook uses its marker."""
    repo = _repo(scratch)
    project = repo / ".claude" / "settings.json"
    project.parent.mkdir(parents=True, exist_ok=True)
    project.write_text(json.dumps({
        "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
            {"type": "command", "command": "someone-elses-hook"}]}]}
    }), encoding="utf-8")

    forced = _support.keelcheck("adapter", "install", "claude-code", str(repo), "--force")
    assert forced.returncode == 0, _support.combined(forced)
    first = project.read_text(encoding="utf-8")

    again = _support.keelcheck("adapter", "install", "claude-code", str(repo), "--force")
    assert again.returncode == 0, _support.combined(again)
    assert project.read_text(encoding="utf-8") == first, "installing twice changed the settings file"

    merged = json.loads(first)
    blob = json.dumps(merged)
    assert "someone-elses-hook" in blob, f"the foreign hook was dropped: {merged}"
    assert "keelcheck" in blob, f"no keelcheck hook was written: {merged}"
    assert blob.count("keelcheck") == json.dumps(merged).count("keelcheck"), "counting twice is a no-op"


def test_an_unknown_harness_is_refused():
    done = _support.keelcheck("adapter", "some-other-harness")
    assert done.returncode == 2, _support.combined(done)
    assert "claude-code" in _support.combined(done), (
        "the refusal does not name the harnesses that exist")
