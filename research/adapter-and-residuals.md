# R5's fourth surface, and the two named residuals — Sift, 2026-10-15

Two design answers Gilbert asked for. The adapter is designed, not built; the residuals are classified as
closable or permanent. Sources for every harness claim are in `research/gates-per-harness.md` (`[CC]`
Claude Code, `[CX]` Codex, `[CU]` Cursor), all fetched from primary docs on 2026-10-14.

**Ruled (Gilbert, 2026-10-15), and folded in below rather than left as a message:**

1. **Claude Code first, on two independent reasons** — reach, and the fact that the team's own reviews
   run through `claude -p`. §"Which harness first".
2. **`adapter install` defaults to `--project`.** The global write exists and is never the default; the
   path is printed *before* it is touched, with a one-line diff of what it adds. A tool that audits
   permissions must not quietly widen them. §"The smallest deliverable".
3. **The `kind: "adapter"` line is ruled in**, on a deny, best-effort, with the fields named — and
   **the append must never be the reason a deny fails**. §"Staying inside R6".
4. **The residual split stands as written**: deliberate escape is *closable by deployment*, with only
   the "detectable from inside" claim permanent; the prior-context residual is a *permanent boundary of
   the method*. "Do not build a closure that is really a gesture." §"Part 2".

## Part 1 — the harness hook adapter

### What it is

The adapter is a **thin, per-event translator for the locked artefacts**: a command the coding harness
runs at a lifecycle event (Claude Code `PreToolUse`, Codex `PreToolUse`, Cursor `beforeShellExecution`
/ `preToolUse`), which reads that harness's event JSON on stdin and answers in that harness's own
vocabulary — allow (exit 0, no output) or deny (exit 2 and/or `permissionDecision: "deny"` / `permission:
"deny"`) — when the event would edit something the charter has locked: the charter file whose gate table
is the lock, any path a `kind: gate` or `kind: prompt` row names, and the run record. It is **not the
audit**: it runs on every tool call, so it must be deterministic, local and cheap, and it deliberately
does not run the gate suite (that is `keelcheck gate run`, at commit time, at `pre-commit`). Its whole
job is the rule the project already lives by — *a model may write a gate, a model may never weaken one* —
moved to the moment before the write instead of the audit after it. It re-implements nothing: the
decision comes from the same charter parsing, anchored-table read and git-normalized hashing the CLI
already uses, and the adapter exists only to map event JSON in and a decision out.

### Which harness first, and why: Claude Code

Three reasons, all from the primary sources in `gates-per-harness.md`, none from preference:

1. **Its contract is the one the others are copies of.** Cursor's own docs say exit code 2 "matches
   Claude Code behavior for compatibility" and Cursor ships a layer that loads Claude Code hooks
   verbatim; Codex sets `CLAUDE_PLUGIN_ROOT` / `CLAUDE_PLUGIN_DATA` for plugin-hook compatibility. An
   adapter written against Claude Code's event names and decision fields is the *template* the Codex and
   Cursor adapters become reductions of, so writing it first is not one harness — it is the contract.
2. **It is the only one of the three with a documented fail-closed switch for a *failed* hook**
   (`onFailure: "block"`). Codex has none — a `PreToolUse` hook returning an unsupported field "marks
   the hook run as failed … and continues the tool call" — and Cursor has `failClosed: true`, which the
   adapter wants but which is one flag, not a contract. A gate whose own crash fails open is the defect
   this design exists to avoid, so the first target is the harness where that cannot happen.
3. **The adapter must survive a hostile environment, and Claude Code's is documented best** — hook
   input schema, matcher semantics, timeouts, and the `disableAllHooks` kill switch, all of which the
   adapter's design has to answer for.

Second is **Codex**, because its event names and JSON shapes are the closest to Claude Code's and its
hook definitions are **hash-trusted** (Codex "records trust against the hook's current hash", skipping a
changed hook until re-trusted) — which is the adapter's own installation story, already shipped by
another project and worth matching rather than inventing. Third is **Cursor**, which is the least new
work because its compatibility layer may run the Claude Code adapter as-is (`failClosed: true` closes
its fail-open default). This ordering does not change R5's: the adapter is still last, and all three are
the same adapter with different field names.

**Ruled (2026-10-15): Claude Code is also the answer for the user's own workflow, and that is a second,
independent reason** — the team's own reviews run through `claude -p` (credentials re-authenticated
today), so the harness the adapter targets first is one this project can exercise on itself rather than
only an argument about reach among strangers. Two reasons landing on the same first choice is worth
recording, because the first one alone was about other people's environments.

### Staying inside R6 (no daemon, no server, a bounded call)

- **No process of ours persists.** The harness starts the adapter for one event; it reads stdin, decides,
  writes stdout, exits. keelcheck never binds a socket, never listens, and keeps no state in memory
  between events. The only persistent effect is a file append to the existing record — the same
  `.keel/runs.jsonl` (`record.append`), on a **deny** only, because a refused weakening attempt is
  exactly the event worth keeping. **Ruled (2026-10-15):** the line is `kind: "adapter"` and carries the
  event, the path, the gate row, both hashes and the decision — and it is **best-effort: the append must
  never be the reason a deny fails.** If the record cannot be written, the denial still happens. That
  sentence is the difference between a guardrail and a record keeper, and it is the rule for anything
  else this surface records later.
- **The adapter line cannot move the anchor, and that is already the code's answer rather than a new
  rule.** `_anchor_moved` picks the previous entry with an explicit allowlist — `obj.get("kind") in
  ("audit", "review")` (`keelcheck/audit.py:467`) — so a `kind: "adapter"` line is inert for
  `[anchor-moved]` with or without a `ratified` field. The adapter line therefore carries **no anchor**;
  the property to pin is a test (an adapter line between two audits produces no `[anchor-moved]`), not a
  numbered decision. Noted for the charter pass: D15 and design §8 describe the comparison as "the
  previous entry of *any kind that carries an anchor*", which is broader than the code's allowlist — the
  code is the safer reading, and the sentence is Gilbert's file and Mason's respectively.
- **The call is bounded by the harness, and bounded again by us.** Claude Code's `PreToolUse` hook
  timeout is the outer bound (seconds, not minutes); the adapter takes its own `--timeout` and refuses to
  run gates or the audit inside an event. It performs only local reads: the charter, the ratified table
  (one `git show`), and `git hash-object` on the locked paths.
- **Failure is closed.** An unparseable payload, an unreadable charter, or any internal error *denies* —
  and the install writes the harness's own fail-closed setting (`onFailure: "block"`, `failClosed: true`)
  alongside the command, so the harness does not fail open around a crashed adapter. This is the one
  place the adapter is deliberately stronger than the pre-commit hook, which fails open by absence.

### What it reuses verbatim, rather than re-implementing

**From the hook installer (`keelcheck/hook.py`)** — the hermetic launch and the install discipline:
the pinned interpreter and import root with `-E -X utf8`, `PYTHONHOME` unset, all for the reason its
docstring records (a caller's `PYTHON*` variables decided whether a commit was possible); the refusal to
install where the charter has no `Ratified at:` ("a repository that cannot be audited gets no hook");
and the marker/idempotence pattern — for a shell hook a comment line, for a JSON settings entry the
identity of the command string, refusing to overwrite a foreign entry unless `--force` keeps a backup.

**From the CLI** — the decision itself, not a copy of it: `audit.load_charter`, `audit.load_reference`
(the ratified table at the anchor), `charter.Gate.kind` and `.path`, `normalize.content_hash` /
`gitcmd.hash_object` (never a second normalization path — D9's whole lesson is that two paths drift),
`record.append`/`ensure_header`, `output.emit`/`emit_err`, and the existing `--json`/exit-code
conventions. The new surface is one module and one subcommand (`keelcheck adapter <harness>`), beside
`gate`/`audit`/`review`/`hook` in `cli.py`, and it calls the same functions they do.

**From the MCP server, in flight** — **one decision object, two framings.** The MCP tool and the adapter
must return the same JSON (`{"decision": "allow"|"deny", "reason": …, "locked": [...], "gate": …,
"hashes": {"ratified": …, "measured": …}}`), with transport and exit-code framing applied last: MCP
returns it, the adapter turns it into exit 2 plus the harness's field. If the MCP lands first, the
adapter's core is the MCP's `check` function and the adapter adds only the harness shim — there must not
be two decision functions, or the two surfaces will disagree in exactly the way a third checker of
locked artefacts must not.

### The smallest deliverable, and the acceptance test written first

**Deliverable:** `keelcheck/adapter.py` with a pure `decide(event: dict, repo) -> dict` and a
`keelcheck adapter <harness>` entry that reads one event, prints the harness's decision, and exits 0/2;
`keelcheck adapter install claude-code [--project|--global] [--force]`; a checked-in fixture directory of
**recorded real payloads** (`tests/_artefacts/adapter/claude-code/`: an allow, a deny that rewrites a
ratified gate script, a deny that edits the charter's gate row, and a malformed payload); and a docs
snippet showing the settings entry. No model, no harness and no network are needed to test any of it —
the same property that makes the review half testable makes this half testable.

**Ruled (2026-10-15), and it constrains the installer:** `--project` is the default and the global write
exists only when explicitly asked for as `--global`. The path that will be touched is printed **before**
it is touched, with a one-line diff of what the entry adds; nothing the adapter does writes to
`~/.claude/settings.json` implicitly, because a tool that audits permissions must not quietly widen
them. The flag is `--global`, not `--user`, so the one word a caller types says where it lands.

**The acceptance test I would write first (red before the fix, per rule 3):**

> Given a recorded Claude Code `PreToolUse` payload whose `tool_input.command` writes to a path a
> ratified gate row names, `keelcheck adapter claude-code` exits **2**, prints
> `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", …}}` with a
> reason naming the gate and both hashes, and appends a `kind: "adapter"` line to the record naming the
> path, the command and the decision. Given the same payload with an unparseable body, it **also denies**
> — a gate that cannot read its event must not allow the edit.

Two companion cases prove the surface is not merely noisy: an ordinary payload (`ls`, a read) exits 0
with no output, and a payload editing an *unlocked* file exits 0. The four cases together are the
contract: block the locked, allow the ordinary, fail closed on the unreadable, and record the refusal.

**Stated, not hidden:** the adapter is a *guardrail*, not an enforcement boundary — the harnesses say so
themselves (Codex: "Treat tool hooks as a useful guardrail, not a complete enforcement boundary"). A
command that rewrites a gate through an indirect path (a script, a generated heredoc, a `python -c`) is
not caught by a path-and-verb heuristic; a harness the user disables (`disableAllHooks`, `[features]
hooks = false`) runs no adapter at all. That is why the tier does not change: the adapter intercepts
earlier and cheaper, the pre-commit hook catches what reaches a commit, and the audit is still what
reports a **missing** record when either is bypassed.

## Part 2 — the two named residuals

### §5, the prior-context residual — a permanent boundary of the method

**What "closing" it would take.** The reviewer must demonstrably not know the project: a fresh execution
context with no session reuse and no auto-loaded memory or rules (the harness's own flags), a clean
credential or vendor, and a recorded attestation of those conditions. That is T3 in the design — a
container, another machine, another vendor — plus an environment the runner does not control at all.

**The measurement that would demonstrate it.** A differential experiment on one export: review it
(i) in a fresh session with memory and rules disabled, (ii) after the reviewer has been steeped in the
project's history (same harness, memory on, or a prior session), (iii) by a model with no project
exposure. Compare the three finding sets. If (i) and (ii) differ on the same bytes, the prior leaks and
is measurable; if (i) and (iii) agree, the substitution is bounded for that harness and that model. Note
what this measures: *susceptibility to a manipulated prior*, not the absence of one.

**Verdict: a permanent boundary, not pending work.** A hosted model's weights, the vendor's cache, and
the reviewer's own earlier sessions are outside any instrument the runner holds; a clean container
removes the *observable* conditions and cannot prove the *prior*. The honest form is the one already in
the design and in W2: the tool records what it handed over and under what conditions, and a human judges
the reviewer. Naming it permanent is stronger than leaving it looking like work, because it stops the
project promising a guarantee no local mechanism can give — and it is the same class as D1's
history-rewrite residual, which is also outside the local threat model.

### §1, the deliberate-escape residual — closable by deployment

**What "closing" it would take.** Confine the reviewer's *reads*, not its intentions: the T2 export
directory mounted into a container or VM that has **no path to the audited repository** and no ambient
credentials (the strongest form); or, weaker, a process sandbox that denies the repository path; or, as
detection rather than prevention, a supervisor that records the reviewer's file opens and reports any
path outside the export as a finding. The design already names the first as T3; what is missing is not a
mechanism but the decision to run the reviewer that way and to say so in the record.

**The measurement that would demonstrate it.** The same binary under two conditions: with the
confinement off, `git -C <repo> log` inside the reviewer succeeds; with it on, the same call fails
(no such path / permission denied) and the attempt is recorded — and the two runs' review records differ
in the field that says which confinement applied. A differential measurement is what makes this
"proved" rather than "asserted", in the same way the export's manifest made the reach claim provable.

**Verdict: closable, by deployment — a gap with a named mechanism, not a boundary.** It cannot be closed
*from inside the runner* (no local instrument sees the reviewer's reads; that part is permanent), but it
can be closed by running the reviewer somewhere the repository is not — and the design's own T3 exists
for exactly this. The deliverable, when someone wants it: one documented T3 recipe (container or a
second machine with only the export), one recorded field naming the confinement, and the differential
test above. The prior residual remains the permanent one.

### Ruled (Gilbert, 2026-10-15): the split stands exactly as written

Deliberate escape is **closable by deployment** — confined reads, proven by differential measurement —
with only the "detectable from inside" claim remaining permanent. The prior-context residual is a
**permanent boundary of the method**, because a hosted model's weights, its cache and its earlier
sessions are outside any local instrument. Naming it permanent is what stops this project promising a
guarantee it cannot give, and it is worth more than a mechanism that only looks like one: **do not build
a closure that is really a gesture.** No work item is created for the prior residual; it stays a named
boundary, and the conditions the runner *can* record remain the honest claim.

## Decided since drafting (Gilbert, 2026-10-15)

All three points I could not settle from research alone were ruled, and each is folded into the section
above rather than left here:

- **Which harness first** — Claude Code, on reach *and* on the team's own reviews running through
  `claude -p`. The lane note was right that only the user's workflow could settle it; the ruling is that
  both reasons point the same way.
- **Whether the installer may write outside the repository** — it may, but `--project` is the default,
  `--global` is explicit, and the path and a one-line diff are printed before anything is touched.
- **Whether an adapter refusal is recorded** — yes, `kind: "adapter"`, best-effort, and the append must
  never be the reason a deny fails.

One thing remains outside my lane and is not a design question: if these three are to be numbered in
`PROJECT-STATE.md`, that record is Gilbert's to write — I have not touched it.
