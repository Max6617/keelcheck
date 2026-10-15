# Where gates can actually sit, per harness

Deliverable 1 for keel. Written by Sift, 2026-10-14. **All primary sources fetched 2026-10-14**;
all three subagents' claims are excluded from this file (their work is the other two deliverables).

*Second pass, 2026-10-14 20:40:* re-read every source in §8 directly, confirmed §1–§4 and the
protection claims in §5, and extended §5 with the required-check **trigger** rules ([GHT], [GHSC])
that the first draft did not carry. Two source keys added: [GHT], [GHSC]. Nothing previously
reported was found wrong.

Source keys, full URLs in §6. Every claim below carries the key of the document it came from.
Where I could not verify something it says so; where a conclusion is mine and not a quoted
document line it is marked **[inference]**.

---

## 0. The question and the honest frame

keel's R5 orders the integration surfaces "git hook first, CLI second, MCP third, harness hook
adapter last". That ordering is about *reach*, and reach is real: a git hook is the only surface
that exists in every repository regardless of which agent is driving it [GH]. This file answers a
different question, the one that decides what R2 can claim: **for each surface, can a violation be
blocked, and can the block itself be quietly removed?**

Three facts frame everything else:

1. Every agent-harness hook family (Claude Code, Codex, Cursor) now has the *same* contract:
   a committed JSON config, a script, **exit 2 or a JSON `permissionDecision: "deny"` to block**,
   and **everything else fails open** ([CC], [CX], [CU]). A single adapter shape could target all
   three; the harness adapter is not three integrations, it is roughly one.
2. In all three, the config that decides whether the hook runs (and the hook body) is **writable by
   the same agent the hook is meant to constrain** ([CC] `disableAllHooks`, [CU] `.cursor/hooks.json`,
   [CX] `[features].hooks = false`). A gate the subject can switch off is a detector, not a lock.
3. The only surfaces that are not under the local agent's control are **server-side git hooks**
   (`pre-receive`, `update`) [GH] and **branch protection / required checks** on the host [GHB].
   Both need a host, and the charter says no server. That is the real cost of R6.

**Working vocabulary.** *Fail closed* = the violation is refused when the gate cannot run. *Fail
open* = the violation proceeds and only a log line records it. Almost everything here fails open.

---

## 1. Claude Code hooks

Config: `settings.json` at user, project (`.claude/settings.json`, committable), local
(`.claude/settings.local.json`, gitignored), managed policy, plugin, skill/subagent frontmatter;
hook entries **merge across levels rather than replacing each other** [CC].

**Can genuinely block.** `PreToolUse` can block a tool call before it runs, by `exit 2` or by
`hookSpecificOutput.permissionDecision: "deny"`; `UserPromptSubmit` and `UserPromptExpansion` can
reject a prompt; `Stop`/`SubagentStop` can send the agent back to work; `WorktreeCreate` fails
creation on any non-zero exit [CC]. Hooks also run inside subagents on their tool events [CC].

**Cannot block.** Events with no decision control at all: `Setup`, `Notification`, `SessionEnd`,
`PostCompact`, `InstructionsLoaded`, `StopFailure`, `CwdChanged`, `DirectoryAdded`, `FileChanged`
[CC]. `PermissionRequest` ignores exit 2 entirely (deny through the JSON `decision` object) and
`PermissionDenied` ignores exit code and stderr [CC]. A tool call from a hosted tool path is outside
this at all **[inference from [CX]'s equivalent table — Claude Code's doc does not print such a
table]**.

**Fail open or closed.** Fail open by default, in four independent ways:

- exit 1 (the conventional Unix failure code) is a **non-blocking error**: the action goes ahead
  [CC]. The doc's own warning: *"Without valid JSON on stdout, Claude Code treats exit code 1 as a
  non-blocking error… If your hook is meant to enforce a policy, use `exit 2`."* [CC]
- a hook that **cannot start** (mistyped path, not executable, `127`) is a non-blocking error [CC].
- **invalid JSON or schema-validation failure** is a non-blocking error [CC].
- a **timeout** cancels the hook and, on `PreToolUse`, "A timed-out hook… doesn't block the tool
  call… don't count on a stalled hook to act as a gate" [CC].

Fail-closed is opt-in: `onFailure: "block"` makes a failed *command* hook block the action, doing
"what exit code 2 does on that event" [CC]. (An Agent SDK callback hook that times out blocks
`PreToolUse` — the opposite of a command hook [CC].)

**The kill switch.** `"disableAllHooks": true` in a settings file, or
`claude --settings '{"disableAllHooks": true}'` for one run, which "takes precedence over project
and local settings"; there is no way to disable an individual hook [CC]. The precedence itself is
confirmed independently by the settings page, where command line is level 2 above project local,
shared project and user [CC-SETTINGS]. `disableAllHooks` cannot disable managed-policy hooks;
`allowManagedHooksOnly` in managed settings can block user, project, local and plugin hooks [CC].
A project-committed hook, therefore, is one CLI flag away from silence.

**What a violation looks like from outside.** The gate's stderr is surfaced to the model as e.g.
`PreToolUse:Bash hook error: […/no-rm.sh]: Blocked: rm commands are not allowed` [CC]; a skipped
gate produces no such notice unless `onFailure: "block"` was set, in which case the same text
appears as a block. The run is recorded in the debug log, not the transcript (exit 0) [CC].

---

## 2. Codex hooks

Config: `hooks.json` or inline `[hooks]` in `config.toml`, at `~/.codex/`, `<repo>/.codex/`, or
plugin; *all* matching sources run and higher-precedence layers do not replace lower ones [CX].
Project-local hooks load only when the project `.codex/` layer is trusted [CX]; the configuration
reference states the same boundary from the config side — a project marked
`trust_level = "untrusted"` makes Codex skip project-scoped `.codex/` layers, "including
project-local config, hooks, and rules" [CX-CFG].

**The trust-review property — the single most interesting line in this whole file.** "Before a
non-managed hook can run, Codex requires you to review and trust the exact hook definition. Codex
**records trust against the hook's current hash**, so new or changed hooks are marked for review and
skipped until trusted." [CX] A changed hook is *skipped*, not silently run. That is hash-pinned
approval of a hook body, shipped in a mainstream harness — close to what R2 wants, but it pins the
hook's *execution*, it does not audit the repository against a frozen original, and `--dangerously-bypass-hook-trust`
exists as an escape hatch for automation [CX]. Enterprise policy can pin it: `allow_managed_hooks_only = true`
plus `[features].hooks = true` in `requirements.toml`, with scripts delivered out of band by MDM [CX].

**Can genuinely block.** `PreToolUse` (Bash, `apply_patch`/Edit/Write, MCP tools, and other local
function tools) — `permissionDecision: "deny"`, the legacy `decision: "block"`, or `exit 2` with the
reason on stderr [CX]. `PermissionRequest` can allow/deny an approval request; any matching `deny`
wins [CX]. `UserPromptSubmit` blocks a prompt. `PreCompact`/`PostCompact` can stop compaction.
`Stop`/`SubagentStop` continue the agent instead of stopping [CX].

**Cannot block.** Hosted tools such as `WebSearch` do not use the local function-tool hook path [CX].
The doc's own summary: *"Some specialized tool paths can opt out of the default hook path. Treat tool
hooks as a useful guardrail, not a complete enforcement boundary."* [CX] `PostToolUse` "can't undo
side effects from a tool that already ran" [CX]. Background (`async: true`) hooks "can't block,
approve, rewrite, or otherwise control the operation that triggered them" [CX].

**Fail open or closed.** Fail open, and the documentation is unusually explicit about it: a
`PreToolUse` hook returning an **unsupported** field marks the hook run as failed, reports the error,
and *continues the tool call* [CX]. For managed MCP hooks: "an explicit supported denial can block an
action, but a `PreToolUse` callback error, timeout, or malformed response can fail the hook without
blocking the tool" [CX]. Default timeout 600 s for most hooks; `SessionEnd`/`Interrupt` 1 s, max 3 s [CX].

**The kill switch.** `[features] hooks = false` in `config.toml` turns hooks off; `codex_hooks` is a
deprecated alias [CX]. Admins can force them back on with `[features].hooks = true` in
`requirements.toml` [CX].

**What a violation looks like from outside.** Tool call refused and the hook's reason handed to the
model; on a failed-but-not-denied hook, an error is reported for that hook run and the call continues
[CX]. Untrusted hooks appear at startup with a warning telling you to open `/hooks` [CX].

---

## 3. Cursor hooks

Config: `hooks.json` at project (`<project>/.cursor/hooks.json`, committable) or user
(`~/.cursor/hooks.json`); plugins too; cloud agents load project hooks, not user hooks [CU]. Hooks
are spawned processes, JSON in on stdin, JSON out on stdout [CU]. Cursor also loads Claude Code
hooks via its third-party-hooks compatibility layer [CU].

**Can genuinely block.** Permission hooks: `beforeShellExecution`, `beforeMCPExecution`,
`beforeReadFile`, `beforeTabFileRead`, `subagentStart`, `preToolUse`; `beforeSubmitPrompt` can block
prompt submission; `stop`/`subagentStop` can auto-continue [CU].

**Cannot block.** `sessionStart` — "runs as fire-and-forget; the agent loop does not wait for or
enforce a blocking response"; the schema accepts `continue`/`user_message` "but current callers do
not enforce them. Session creation is not blocked even when `continue` is `false`" [CU]. `sessionEnd`
is fire-and-forget, response logged not used [CU]. `preCompact` "cannot block or modify the
compaction behavior" [CU]. `afterFileEdit`/`afterShellExecution` are observational [CU]. Cloud agents
"sometimes begin in a read-only environment… Hooks do not run during those turns" [CU].

**Fail open or closed.** Mixed, and this is the clearest fail-open/fail-closed statement of the
three harnesses. Exit 0 → use the JSON; **exit 2 → block**; **"Other exit codes - Hook failed,
action proceeds (fail-open by default)"** [CU]. For permission hooks, **invalid JSON or a
schema-mismatched response blocks the action** — so garbage fails closed *there* [CU]. Crashes,
timeouts and non-2-ones "fail open by default: Cursor logs the failure and allows the action
through. Set `failClosed: true` on the hook definition to block on those failures too." [CU]
Response merging across sources: "any `deny` wins over `ask`" [CU].

**The kill switch.** Delete or edit `.cursor/hooks.json` and reload (Cursor watches the file) [CU].
There is no managed-hook lock documented for local use; team/enterprise hooks exist only on
Enterprise plans and are distributed from the dashboard [CU].

**What a violation looks like from outside.** The permission decision's `user_message` (shown in
client) and `agent_message` (sent to the agent) [CU]; the Hooks output channel in **Customize**
shows configured and executed hooks and errors [CU].

---

## 4. Git hooks

Two families with very different strength. This distinction is the core of the recommendation.

### 4.1 Client-side: `pre-commit`, `pre-push`

**Can genuinely block.** Non-zero exit aborts the command: `pre-commit` "causes the `git commit`
command to abort before creating a commit" [GH]; `pre-push` non-zero and "`git push` will abort
without pushing anything" [GH].

**Cannot block / bypasses, all from the git docs themselves:**

- `pre-commit` "can be bypassed with the `--no-verify` option" [GH]. `commit-msg` and
  `pre-merge-commit` likewise [GH].
- `pre-push` is toggled by `--no-verify`: "The default is `--verify`, giving the hook a chance to
  prevent the push. With `--no-verify`, the hook is bypassed completely." [GP]
- **One documented exception:** `prepare-commit-msg` — "it is **not** suppressed by the `--no-verify`
  option. A non-zero exit means a failure of the hook and aborts the commit." The same paragraph
  adds the caveat: "It should not be used as a replacement for the pre-commit hook." [GH]
- A hook without the executable bit "is ignored" [GH] — silent, no message.
- The default hooks directory **is inside `$GIT_DIR`** (`$GIT_DIR/hooks`), changeable only via
  `core.hooksPath` [GH]. A `.githooks/` directory committed to the working tree is therefore not
  where git looks; the binding is a config value or a copy into `$GIT_DIR`, and neither is cloned
  with the repository **[inference from [GH]: nothing under `$GIT_DIR` is a tracked file]**.
- `reference-transaction` hook exit status "is ignored for any state except for the 'preparing' and
  'prepared' states" [GH]. `post-commit`, `post-merge`, `post-checkout` cannot affect the outcome
  (post-checkout only forwards its exit status) [GH].

**Fail open or closed.** Fail open on every axis that matters: uninstalled, non-executable, mistyped,
wrong `core.hooksPath`, `--no-verify`, or a commit made by a tool that writes objects directly. The
gate itself only fails closed in the one narrow case where it runs and exits non-zero.

**What a violation looks like from outside.** A refused commit/push with the hook's stderr text. A
*bypassed* gate looks like nothing at all — that is the point, and it is why R2's hash check must not
depend on the hook having run.

### 4.2 Server-side: `pre-receive`, `update`

**Can genuinely block, and the pusher cannot opt out.** `pre-receive` — "Its exit status determines
the success or failure of the update… If the hook exits with non-zero status, none of the refs will
be updated." `update` runs per ref; "Exiting with a non-zero status prevents `git receive-pack` from
updating that ref." [GH] `git push --no-verify` toggles only the *client* pre-push hook [GP], so it
does not reach these. Output from both is forwarded to the pusher's `send-pack` [GH].

**Cannot block.** A person with filesystem access to the server repository, or a push to a different
remote that has no such hook. Not available at all without controlling the host.

**Fail open or closed.** Fail closed *on the transport path*: the push is rejected. Scope is one
repository on one host, and maintaining the hook is out of band.

### 4.3 What a violation looks like from outside

`pre-receive`/`update` rejections arrive as `remote: …` lines and a failed push. A commit that
reached a protected branch anyway (bypass) is invisible from the client — it must be found by
comparing refs to the gate's recorded decisions.

---

## 5. CI: the merge gate (GitHub Actions + branch protection)

**Can genuinely block a merge.** Required status checks "must have a `successful`, `skipped`, or
`neutral` status before collaborators can make changes to a protected branch"; with "Require branches
to be up to date before merging" (the default, "strict") the head must be current with the base [GHB].
`Lock branch` makes the branch read-only [GHB]. `Require signed commits` restricts pushes to verified
signatures, and an unsigned commit must be rebased and force-pushed [GHB].

**Cannot block.** A local commit — CI sees nothing until a push happens. And the enforcement has
several documented holes:

- "By default, the restrictions of a branch protection rule **don't apply to people with admin
  permissions**… or custom roles with the 'bypass branch protections' permission." A separate
  setting, **Do not allow bypassing the above settings**, applies them to admins too [GHB].
- **"Any person or integration with write permissions to a repository can set the state of any
  status check in the repository"**, unless the check is pinned to a specific app as the expected
  source [GHB]. A second GitHub document states the same rule in its own words — "Anyone with write
  permissions to a repository can set the state for any status check in the repository" — and adds
  that organization owners and users with push access can create checks and commit statuses through
  the API [GHSC]. A model with a write token can therefore *set the gate green* rather than weaken
  the workflow.
- Only a single branch protection rule can apply to a branch at a time [GHB]. Rulesets lift that,
  but are a separate feature.
- `Allow force pushes` and `Allow deletions` are opt-out switches; enabling force pushes "will not
  override any other branch protection rules" but does let history be rewritten [GHB].

**The trigger rules decide whether a check counts at all.** A required check is satisfied only by a
workflow run triggered by `push`, `pull_request`, `pull_request_review`, `pull_request_target`,
`deployment`, or `deployment_status`; a run started any other way — `workflow_dispatch` on the head
branch is the documented example — "do[es] not appear in the pull request's checks section", and
"even if the checks pass for the head commit, they do not satisfy a required status check" [GHT].
Required checks must also pass on the **latest commit SHA**; checks from earlier commits don't
satisfy the requirement [GHT].

**Two ways to skip, opposite outcomes — the most fine-grained hole on this surface.** A *workflow*
skipped by path or branch filtering, or by a skip instruction in the commit message, leaves its
associated checks "in a 'Pending' state and block[s] merging" — fail closed [GHT]. A *job* skipped
by a conditional does the opposite: "A job is skipped by a conditional → The job reports 'Success'"
[GHT]. So a required job guarded by `if: false`, or by a condition that is false on this branch,
turns the gate green without running anything. This is the CI analogue of Claude Code's
`onFailure: "continue"`: the default is not to fail, and an absent run only means *blocked* when
someone arranged it to.

**Fail open or closed.** Fail **closed for the merge** when configured correctly and the bypass
settings are left off. Fail **open for everything else**: local work, the window before the push,
a graded job neutered by a conditional [GHT], and any path that an admin or a write-token holder
uses.

**What a violation looks like from outside.** A refused merge with the host's own message, e.g.
`remote: error: GH006: Protected branch update failed for refs/heads/main. / remote: error: Changes
have been requested.` [GHB] A status check that was set green by a third party shows in the merge box
with its author, which is why pinning the expected app matters [GHB].

**[Flagged, not verified]** That a pull request can weaken the workflow that grades it (workflow
files live in the repo, so a PR can edit `.github/workflows/*.yml`). I did not find a doc line that
states this either way in this session. Treat it as unverified and test it before relying on the
opposite. **[inference, unverified]**

---

## 6. Comparison table

| surface | blocks a real action? | who can switch it off | default failure mode | needs a host? | source |
|---|---|---|---|---|---|
| Claude Code `PreToolUse` | yes, the tool call | the agent: `disableAllHooks`, `--settings`, editable settings file | **open** (exit≠0/2, no-start, bad JSON, timeout) unless `onFailure: "block"` | no | [CC] |
| Codex `PreToolUse` | yes, the tool call | the agent: `[features] hooks = false` | **open** (unsupported field, MCP error/timeout) | no | [CX] |
| Cursor `before*` | yes, the action | the agent: edit `.cursor/hooks.json` | **open** on crash/timeout/non-2; **closed** on invalid JSON for permission hooks; `failClosed: true` to close the rest | no | [CU] |
| git `pre-commit`/`pre-push` | yes, the commit/push | the agent: `--no-verify`, chmod, `core.hooksPath`, no install | **open** | no | [GH],[GP] |
| git `prepare-commit-msg` | yes, the commit, **and not suppressed by `--no-verify`** (doc discourages relying on it) | the agent: chmod/remove/uninstall | open if absent | no | [GH] |
| git `pre-receive`/`update` | yes, the push, **not bypassable by the pusher** | whoever owns the server repository | closed on the transport path | **yes** | [GH],[GP] |
| CI required checks | yes, the merge | admins by default; anyone with a write token can set a check's state; a conditional `if:` on the graded job reports Success | closed for merges when bypass is off and the workflow is trigger-eligible; **open** when the graded job is skipped by a conditional | **yes** | [GHB],[GHSC],[GHT] |

Two observations the table forces:

1. **No local surface is a lock.** Every local gate is a detector that a local agent with write
   access can silence in one documented step. The strongest property keel can honestly claim from a
   local surface is *"a weakening becomes visible and named at the next audit"*, not *"a weakening
   is impossible"*.
2. **The three harness adapters are one adapter.** Claude Code, Codex and Cursor share the block
   contract (exit 2 / JSON deny / fail-open otherwise) and two of them (Cursor, and Codex via
   `CLAUDE_PLUGIN_ROOT` compatibility [CX]) deliberately mirror Claude Code. The adapter is thin
   glue over one contract, which is exactly the "last, optional" position R5 gives it.

---

## 7. Recommendation: keel's first integration surface

**Confirmed: git hook first, as the charter orders — but the recommendation is a redefinition of
what "first" buys, not an endorsement of the ordering as an enforcement claim.**

R5 says "git hook first, CLI second, MCP third, harness hook adapter last". The research supports
that ordering for *reach and cost*, and contradicts it for *strength*. Ship it with these five
decisions made:

**(a) The hook is the deliverable; the audit is the enforcement.** Install `pre-commit` and
`pre-push`, both calling `keel audit --hook`, exiting non-zero on a violation [GH]. Accept that
`--no-verify` bypasses `pre-push` completely [GP]. Do not describe the hook as enforcement of R2 in
the README. Describe it as the surface that makes the audit cheap to run; the *finding* is the
enforcement. This matches the charter's own tier list: hooks are tier 3 (intercepted), and tier 3 is
"strong per harness, absent elsewhere" [INTENT-LOOP.md §four tiers].

**(b) The ratified hashes must be anchored to a commit, not to a working-tree file.** This is the
one design question the charter leaves open in R2 and it decides whether the hash check means
anything. If the ratified list of gate hashes lives only in a working-tree file, an agent can edit
the gate and the recorded hash in the same two writes and the audit passes — the exact failure the
rule exists to prevent. The anchor must be a **ratification commit**: on ratification, keel records
the approved hash list in a commit whose message names the decision, and the audit re-computes each
gate's `git hash-object` and compares it against the ratified list **as of the latest ratification
commit**, not against the working tree. Then weakening a gate requires a new commit, and a new commit
is visible. This is also what makes project-state rule 2 ("a count only counts when it names a
commit") apply to hashes and not only to counts. **Question for Gilbert (design, R2): is the
ratification commit the anchor, or does the charter's frozen original file carry the hashes?** I
recommend the commit, because the charter file itself is editable in the working tree.

**(c) Put a *second* gate in `prepare-commit-msg`, and test the claim before trusting it.** The git
docs state `prepare-commit-msg` is not suppressed by `--no-verify` and its non-zero exit aborts the
commit [GH] — the only client-side hook family documented that way. The same paragraph says not to
use it as a replacement for `pre-commit` [GH], so treat this as an **additive** check whose one job
is to notice that the gate pair did not run, and have Proctor's adversarial set try to skip it
(`--no-verify`, `-n`, `GIT_INDEX_FILE`, a commit made by a tool that writes objects directly, a
merge commit, an amend). If it holds up, it is the cheapest way to make "quietly skipped" hard;
if it does not, the fallback is (d).

**(d) Every gate run appends a record, and a missing record is a finding.** Because a bypass is
invisible from outside (§4.1), the only honest way to detect a skipped gate is a record that will be
absent. Each audit run appends `{commit, gates_expected, gates_run, result, keel_version}` to an
append-only log. A commit with no record, or a record with fewer gates than the ratified set, is
reported by the next audit as *missing*, in the audit's own three-class vocabulary. This does not
need a server and does not violate R6.

**(e) Harness adapters last, and as one adapter, not three.** When they come: target the common
contract — command hook, JSON in on stdin, `exit 2` or `permissionDecision: "deny"`, fail open
otherwise — and set the fail-closed flag where each harness offers one (`onFailure: "block"` [CC],
`failClosed: true` [CU]). Map the whole thing onto `keel audit --hook` so there is one code path.
Do not build the MCP surface as enforcement: an MCP call returns a value, it cannot block anything,
and R6 already frames it as "a call that returns".

**What to tell the user in the README, in one line:** keel cannot stop a determined local agent from
weakening a gate; it can guarantee that the weakening is named at the next audit, against a commit,
with a record of what ran. If that sentence feels too weak, the escalation is a host-side surface
(§4.2, §5) and that is a scope change, not an implementation detail.

**Open question for Gilbert (design).** R2 currently reads "the audit fails when a hash differs from
the ratified one". It does not say *where the ratified one lives*. (b) proposes the ratification
commit. Whoever owns the charter should answer that before Mason writes the hash comparison, because
the answer changes what the parser must read.

---

## 8. Sources (all retrieved 2026-10-14)

- **[CC]** Claude Code, *Hooks reference* — <https://code.claude.com/docs/en/hooks> (Markdown twin
  <https://code.claude.com/docs/en/hooks.md>).
- **[CX]** Codex, *Hooks* — <https://learn.chatgpt.com/docs/hooks.md>.
- **[CX-CFG]** Codex, *Configuration Reference* — <https://learn.chatgpt.com/docs/config-file/config-reference.md>
  (used for `trust_level = "untrusted"` skipping project hooks, and for `allow_managed_hooks_only`
  / pinned `[features]` in `requirements.toml`; `sandbox_mode` and `approval_policy` were read but
  are not cited above).
- **[CU]** Cursor, *Hooks* — <https://cursor.com/docs/hooks.md>.
- **[GH]** Git, *githooks* — <https://git-scm.com/docs/githooks> (manual as of git 2.54.0/2.55.0).
- **[GP]** Git, *git-push* — <https://git-scm.com/docs/git-push>.
- **[GHB]** GitHub Docs, *About protected branches* —
  <https://raw.githubusercontent.com/github/docs/main/content/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches.md>
  (rendered: <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches>).
- **[GHSC]** GitHub Docs, *Status checks* (reference page; a **separate document** from [GHB], so its
  agreement on the write-permission rule is a second source and not a re-read) —
  <https://raw.githubusercontent.com/github/docs/main/content/pull-requests/reference/status-checks.md>.
- **[GHT]** GitHub Docs, *Troubleshooting required status checks* —
  <https://raw.githubusercontent.com/github/docs/main/content/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks.md>.
- **[CC-SETTINGS]** Claude Code, *Settings files and precedence* — <https://code.claude.com/docs/en/settings.md>
  (used only to confirm that `--settings` is a precedence level above project and local files, per
  §1's kill-switch paragraph).
- **[INTENT-LOOP.md]** keel workspace, `INTENT-LOOP.md` §"The four tiers of enforcement".

### Flagged as not verified / not covered

- That a PR can edit the workflow that grades it (§5, marked **[inference, unverified]**). What *is*
  verified is the adjacent fact that a required check is only satisfied by an eligible trigger event
  [GHT]; whether the workflow file that runs for `pull_request` is taken from the merge ref (and so
  editable by the PR) was **not** confirmed from a doc line this session.
- Whether Claude Code can block *hosted* tool calls (the doc has no equivalent of Codex's
  tool-coverage table; I inferred nothing either way there).
- No primary source was read for GitLab CI, Jenkins, or Buildkite; the CI section is GitHub-only and
  should not be generalised. Same for other git hosts' branch protection.
- Release dates/versions for the Cursor and Claude Code hook features were not established; nothing
  here depends on them.
