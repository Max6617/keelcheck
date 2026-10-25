# Changelog

Notable changes, newest first. Releases before 1.0 may change any interface.

## 0.1.0 — 2026-10-25

First public release.

keelcheck keeps one frozen, human-approved original per project — the charter — and audits the
repository against it. Every requirement in the charter must name the mechanism that enforces it or the
check that judges it; a requirement with neither is reported as a wish. Gates are recorded with content
hashes, and the audit reads the ratified table from the commit the charter names, never from the working
tree.

**What it does**

- `keelcheck charter <path>` parses a charter and reports its requirements, wishes, gates and anchor.
- `keelcheck audit <repo>` checks gate hashes against the ratified table, diffs the frozen original,
  reports missing sections, gate records that never passed, and vacuity. Exit 0 is clean, 1 is a
  divergence, 2 is a run that could not be honest.
- `keelcheck gate run <repo>` runs the ratified gates and records the run; `keelcheck gate hash <path>`
  prints the content hash a gate row records.
- `keelcheck review <repo> --reviewer "<command>"` runs a clean-context reviewer against a `.git`-less
  export and records what it was handed, classifying what it sees as missing, unrequested or shifted.
- `keelcheck hook install <repo>` installs the pre-commit hook that runs the gates; `hook status`
  reports what is installed.
- `keelcheck mcp` serves the audit over MCP on stdin/stdout, with no socket and no server.
- `keelcheck adapter install claude-code` writes the Claude Code `PreToolUse` settings entry, and
  `keelcheck adapter claude-code` answers one lifecycle event.

**Known limits**

- The review is a judgement by the command you name. It is not proof that the reviewer had no prior
  knowledge of the project.
- The adapter is a guardrail, not an enforcement boundary: indirect writes are not caught, and a harness
  with hooks disabled runs nothing.
- A local git hook can be bypassed; a bypass appears in the audit as a missing run record.
- A gate that runs and passes can still measure the wrong thing: the audit verifies the gate's bytes and
  its record, not the quality of what it measures.
- No CI is configured in the repository; no package is published; Claude Code is the only adapter target
  built so far.

**Requirements:** Python 3.10 or newer, git, and no runtime dependencies.
