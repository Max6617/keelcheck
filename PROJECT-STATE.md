# keel — project state and coordination (written by Gilbert, 2026-10-14 ~19:20)

**Canonical copy lives in the repository it governs** — `keel/PROJECT-STATE.md`. The workspace-root
`keel-project-state.md` is a pointer to this file and carries no rules (D6). Read this before acting on keel.
The project is the charter-and-audit tool: one frozen human-approved original, requirements that name their
mechanism or are marked wishes, hashed gates, and an audit that reports divergence from the original.

## Rule set (binding, same as rentguard's)

1. **One writer per file.** `keel/` package + `pyproject.toml` + the CLI → Mason. `tests/` → Proctor.
   `docs/`, `README.md` → Folio. `research/`, design notes → Sift. `CHARTER.md`, this file, and
   packaging commits → Gilbert. A finding goes to the owner as a message; it is not patched into someone
   else's file.
2. **A count only counts when it names a commit.** A working-tree count is a measurement of a moving
   target; say so when you report one.
3. **Red first.** A test for a named failure exists before the fix lands.
4. **Nothing by message that a file can carry.** Rulings, corrections and scope changes go into files;
   idle Bots get silence.
5. **No publication, no spend.** Both need the user (publishing) or Gilbert (money) first.
6. **Bring design questions to Gilbert, not the user.** Only money, scope changes, credentials, a model
   choice, or headline-worthiness go to the user.

## What is frozen and what is not

- `CHARTER.md`'s **frozen original** is the user's verbatim words of 2026-10-14 plus the recommendation
  they accepted. It is never edited. Later clarifications are **appended as new requirements**.
- Everything else in that file — the requirement states, the wishes — is living state and gets re-measured
  at each audit, the way rentguard's was.

## Revision of record

- **The charter is approved and frozen**, commit `ae375c6`, the repository's first commit. The user read it
  on 2026-10-14 and asked for one change in their words: "wish 2 you can throw away but the ret is good".
  That wish (publishing has no lock) was struck **before** freezing and the trace kept in the file; R9 keeps
  the rule as a `checked-by` rather than a wish. **The frozen original has never been edited** — the change
  was in the living part, which is the distinction the format exists to make.
- No code yet at freezing, though Mason's parser landed the same evening at `489f47d`
  (`python -m keel charter <path>`); against `rentguard/CHARTER.md` at `rentguard@a72e7c4` it finds 3 wishes
  by the R1 rule (rentguard R2, R4, R8) plus 2 `enforced-by` cells that name no artefact (R5, R9).
- Charter edits after the finding, 2026-10-14, in the **living** part only: the "agreed problems" section
  added (6/6 sections now) and R4's mechanism named as an artefact. The frozen original is untouched.
- The first audit is the demonstration: **rentguard**, whose charter is `rentguard/CHARTER.md` and whose
  by-hand audit found five real defects (R2, R4, W1, W3, W4 there). Reproducing that finding is R7.

## Lanes and the first assignment for each

- **Mason** — build it: the charter parser (R1), the gate runner and hashes (R2), the git hook installer
  (R5). Start with the parser and its tests, because everything else reads the format it defines.
- **Proctor** — verify it adversarially: the tests that would catch a charter tool lying about itself —
  a requirement with neither mechanism nor check passing silently, a gate whose hash can be edited without
  the audit failing, an audit that reports success when the gate was skipped. Then run the rentguard
  demonstration independently.
- **Sift** — research and design: where gates can actually sit per harness (Claude Code hooks, Codex,
  pre-commit, CI) with what each can and cannot block, from primary sources; a prior-art check on the
  *join* rather than the neighbours; a check that the working name is not taken for a developer tool.
- **Folio** — the artefact map and the README outline a stranger needs: what it is, why the frozen original
  matters, the 60-second demo on a real repository, and what it deliberately does not do.

## Decisions of record

- **D1 — where the ratified gate hash lives (2026-10-14, Sift's question; ruled here).** Not the working-tree
  charter file: the audit reads the ratified hash from the **ratification commit**, via
  `git show <ratification-sha>:CHARTER.md`, and records that SHA here. The charter is frozen at `ae375c6`,
  so that is the reference commit until a human-approved amendment says otherwise; the SHA stays in this
  file and in the charter's living state. Working-tree hashes are forgeable in the same two writes the rule
  exists to prevent, so they are the *measured* side, never the *reference* side. A commit named by hash also
  satisfies rule 2 — every comparison names a commit.
  Residual risk, stated rather than smoothed over: whoever can rewrite history or repoint the recorded SHA
  can move the anchor. Both show up as divergence in the audit's own output, neither is an agent nudge, so
  they are out of the local threat model and belong to a human check (R9's class), not to code.
  A gate file whose hash differs from the ratified one fails the audit; a gate that never ran appears as a
  **missing run record** in the append-only record, because a local hook is a detector and not a lock
  (Sift, `research/gates-per-harness.md`).

- **D2 — R5's git hooks are reach, not enforcement (2026-10-14, accepting Sift's finding).** Every local
  surface can be silenced by the agent it constrains, and each harness documents how (`disableAllHooks`,
  `--no-verify` on `pre-commit` and `pre-push`). So R5's order stands as *reach* — git hook first, CLI
  second, MCP third, harness adapter last — and the guarantee moves into the audit: ratified hashes anchored
  to a commit (D1), plus an append-only run record in which a bypass appears as a **missing** record. The
  one adapter R5 puts last is one adapter, not three, because the three hook families share one contract
  (block = `exit 2` or JSON `permissionDecision: "deny"`; everything else fails open). The
  `prepare-commit-msg` idea is additive and stays with Proctor's adversarial set until tested, not asserted.

- **D3 — red-first ordering, and the contract the red test is written against (2026-10-14, Mason's question;
  ruled here).**`tests/` is Proctor's file, so **the red test lands there first**, committed and failing
  against the current `keel/`, and the group hears its commit id; Mason's fix follows and the fix commit is
  the one that turns it green. Mason does not commit test code under `tests/`; a reproduction he needs while
  building stays in his own scratch and is not committed as a test. To keep this from serialising into a
  stall, the *contract* is ruled here so Proctor can write the red test in parallel with Mason's
  implementation, and the test may use only these observables — never `keel/` internals:

  - `python -m keel audit <path-to-repo>` is the entry point.
  - Exit **0**: the audit ran, no divergence. Wishes may exist and are reported; they do not change the code.
  - Exit **1**: divergence — a ratified gate's file hash differs from `git show ae375c6:CHARTER.md` (D1), a
    named gate has **no run record**, or a required charter section is missing.
  - Exit **2**: the audit could not run honestly (charter unparseable, ratification commit unreadable), or
    `--fail-on-wish` was given and wishes exist.
  - The run record is `.keel/runs.jsonl`, append-only, one JSON object per run: gate name, gate file, its
    hash at that moment, the commit, and the exit status. A bypass is a **missing** line, never a wrong one.

  Renaming the entry point or moving the record is a contract change: it goes into this file first, and
  Proctor is told, so the red test is never written against a guess. Mason may still propose a different
  shape — as a counter-proposal here, before the red test is written, not by shipping it.

- **D4 — `rentguard/` is read-only evidence for as long as it is R7's demonstration input (2026-10-14).**
  Nobody edits it, including to fix a defect the tool finds there: editing the input after the by-hand audit
  would move the target R7 is measured against. Findings about it are reported, not patched. The fixes the
  tool finds on us go into **keel's own** artefacts — which is what happened: R1's format names an "agreed
  problems" section and neither charter had one, so keel's `CHARTER.md` now has it (6/6) and rentguard keeps
  its 5/6 as the finding. Likewise keel's own R4 cell said its mechanism in prose that named no artefact, so
  the cell now names `.keel/review-context.json`; W2 stays as written, because the file makes the runner's
  honesty visible without proving the reviewer had no history.

- **Pins, not reds (2026-10-14).** Mason landed the parser at `489f47d` with no red test in front of it,
  because `tests/` is not his file — a process miss, named rather than hidden. The backfill is Proctor's and
  is labelled a **pin**, not a red test: it locks the parser's current answers so a later change cannot move
  them silently — the three R1 wishes on `rentguard/CHARTER.md` (R2, R4, R8), R9's state-column-says-wish
  case, and keel's own 0-wishes result before the two cells above were tightened. A pin is green on landing
  and says so; calling a backfilled test "red-first" would be the exact laundering this project exists to
  catch.

- **D5 — the anchor is the frozen-original *block*, not the whole file (2026-10-14, answering Folio's
  "the freeze is already dirty").** The living part of `CHARTER.md` is *expected* to change — requirement
  states are re-measured at every audit — so a working-tree `M CHARTER.md` is not a violation and must never
  be reported as one. The audit extracts the **frozen original** section and diffs it byte-for-byte against
  the same section at `ae375c6`; a difference there is the failure, and nothing else in the file is. That is
  why the reference and the working tree may differ today without anything being wrong: the reference side is
  a block, not a snapshot of the file. R3's `enforced-by` cell now names this, because until it did, the
  requirement that protects the original named no mechanism — the tool's own defect, found by Folio on us.

- **D6 — the binding record lives inside the repository it governs (2026-10-14, Folio's finding).**The
  rulings were at the workspace root while the repo is `keel/`, so the tool could not see the decisions that
  bind it. Canonical is now `keel/PROJECT-STATE.md`, committed; the workspace-root `keel-project-state.md` is
  a pointer with no rules in it (two copies of a living record would drift, which is the failure this project
  exists to catch). Corollary for cited paths: a path cited by a project file must resolve **inside the
  repo**; a document that exists only outside is cited as `external:<workspace path>` and the audit reports
  it as unverifiable rather than letting it pass — `INTENT-LOOP.md` and `ECC-ASSESSMENT.md` are inputs and
  are cited that way. Sift's `research/` lane moves under the repo the same way, so `research/…` resolves.

- **D7 — what R7's demonstration is, now that rentguard's HEAD is 310f449 (2026-10-14, Folio's finding).**
  R7 as first written ("reproduce the defects that were found by hand") is not satisfiable at HEAD: the
  charter there already reads R2 met and W4 fixed, because the fixes are ancestors of it. Two revisions, one
  pair of runs, and that pair is the evidence:

  1. At the revision **immediately before each fix**, the audit reports that defect as divergence:
     `bd63920` (MCP arming → `590c58e`), `ce69cea` (idle clamp → `d5fdaea`), `c512125` (volume transport →
     `da51005`). This is the half that proves the detector works rather than the charter's prose being read
     back.
  2. At rentguard HEAD `310f449`, the audit reports what is **still** divergence — the cap that exists only
     while `watch` runs (W1) and the absent technical lock on publishing — and does **not** report the three
     closed ones as open.

  R7's row in the charter now carries this, so "reproduce" means the pair, not a claim that a single run at
  HEAD rediscovers history. The fifth by-hand defect (the unexercised volume path) is a wish in prose, not a
  requirement row: the parser's miss there is the README's demo half, exactly as Folio measured.

- **D8 — A1–A3 ruled, and an audit that verifies nothing is not clean (2026-10-14, Proctor's red set and the
  R7 score).** This corrects D3's exit table, which is the point of D3's own rule that a contract change
  lands in this file first.

  - **A1 — confirmed.** A gate is a row `| gate | path | hash |` under `## Gates`; the path is
    repo-relative (D6); the hash is `sha256:<64 hex>` computed over the script's bytes; the reference table
    is the one at the ratified commit. A malformed or missing hash is a **divergence**, never a skip.
  - **A2 — the pointer is named twice, and nowhere is it trusted alone.** The ratified commit is written as
    `Ratified at: <sha>` in the charter's living state **and** as the first line of `.keel/runs.jsonl`; the
    audit exits **1** when the two disagree, when the named SHA is not an ancestor of HEAD, or when its
    frozen-original block differs from the working tree's (D5). A charter with no `Ratified at:` line is not
    auditable: exit **2**, never 0. Two copies is what makes a single silent edit visible, and "edit both"
    stays the documented human-check residual from D1.
  - **A3 — confirmed, plus one correction.** Records are `.keel/runs.jsonl` (append-only, one JSON object per
    run, written even when the run fails) and `.keel/review-context.json`. The record is **tracked by git**,
    so a deleted line is a diff rather than a secret. It lives in the audited repo by default — but D4 keeps
    `rentguard/` read-only, so the audit takes `--record <path>` and the demonstration records into keel's
    own tree.
  - **Vacuity is a finding, not a clean run.** An audit that finds zero ratified gates must say so as a named
    divergence and must not exit 0. Proctor measured exactly this on rentguard: 0 gate hashes, so the
    hash-checking half verified nothing.
  - **The report prints all four columns.** A row whose only mechanism is `checked-by` is a **human check**,
    never silence: keel's own R9 is a sentence, and a report that reads "0 wishes, 0 asserted" while a
    sentence is the only guard on publishing is the render lying about the charter.
  - **`--json` is UTF-8 regardless of console codepage.** The cp1252 failure on R5's arrow breaks the
    machine-readable path, which is the one the run record consumes — a real bug, not a cosmetic one.
  - **R7 is scored per half, because the audit is two halves (R3).** Mechanical: hash changed after
    ratification, a gate with no run record, a missing section, vacuous enforcement. Clean-context drift
    review: undeclared divergence. Proctor's attribution stands — R8 and R9 declared, R2 symptomatic (a
    `met` claim with nothing behind it), **W4 and W3 drift-review only** (they live in code and in prose, not
    in a requirement row). The user's words are still honoured — "the audit found five real defects" — because
    the drift review is part of the audit by R3's own wording; what is refused is the claim that the
    mechanical half found them.

- **D9 — every hash and every block comparison is over git-normalized content (2026-10-14, measured; hand it
  to Proctor).** The host's system gitconfig sets `core.autocrlf=true`, so a fresh clone checked CRLF into the
  worktree: before the fix `CHARTER.md` in a clone had **127 CRLF lines** and the frozen-original block hashed
  `4bb314d0…` instead of `376f11a4…`. Any comparison of raw worktree bytes against `git show` bytes — D5's
  block diff, R2's gate hash, Proctor's `_support.hash_file` — would therefore report a false divergence on
  every Windows checkout, in exactly the rule the tool exists for. Fixed and verified: `.gitattributes`
  `* text=auto eol=lf` (committed at `7f73812`) and `core.autocrlf=false` in this repo; a fresh clone now
  reports `w/lf` and 0 CRLF. Second lesson from the same fix: the first `.gitattributes` (`98fea4f`) was
  written with a UTF-8 BOM, which silently stopped its first rule from matching — the clone still came out
  CRLF while the rule looked present. Rules are hashed artefacts too; a BOM is enough to make one decorative.
  Implementation note: prefer `git hash-object`/`git cat-file` over `hashlib` on worktree bytes, and pin the
  finding with a test that checks out with `core.autocrlf=true` forced.

## The demonstration (why it is rentguard)

`rentguard/CHARTER.md` is a real charter with a frozen original, ten requirements and a wishes list, and
the by-hand audit of it found: no way to arm the guard over MCP, a guard that had never run against a real
machine and could stop a healthy pod, a cap that exists only while `watch` runs, no technical lock on
publishing, and an unexercised volume path. Every one became a closed defect with a commit and a test. If
the tool reproduces that on the first run, R7 is met and the README has its demo; if it does not, the
shortfall is the finding.
