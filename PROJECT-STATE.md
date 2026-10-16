# keel — project state and coordination (written by Gilbert, 2026-10-14 ~19:20)

**Canonical copy lives in the repository it governs** — `keel/PROJECT-STATE.md`. The workspace-root
`keel-project-state.md` is a pointer to this file and carries no rules (D6). Read this before acting on keel.
The project is the charter-and-audit tool: one frozen human-approved original, requirements that name their
mechanism or are marked wishes, hashed gates, and an audit that reports divergence from the original.

## Rule set (binding, same as rentguard's)

1. **One writer per file.** `keel/` package + `pyproject.toml` + the CLI → Mason. `tests/` → Proctor.
   `docs/`, `README.md` → Folio. `research/`, design notes → Sift. `CHARTER.md` and packaging commits →
   Gilbert. **This file is the shared decision record:** anyone may append a numbered decision with their
   name on it, nobody edits another's entry, and Gilbert ratifies or overrules. The rule as first written
   made this file Gilbert's alone; D1–D9 were appended to it by others, so the rule was bent rather than
   followed. Rather than freeze the record behind one writer, the convention is now explicit — the bending
   is recorded here instead of hidden. A finding goes to the owner as a message; it is not patched into
   someone else's file.
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
- **What landed after the parser, 2026-10-14 (latest code commit `08771ce`):** the mechanical audit and the
  gate runner (`2006f46`: the reference gate table from `git show <sha>:CHARTER.md`, git-normalized hashes,
  the frozen block's byte length printed on both sides, all four columns, the gate-table change line,
  `[unbuilt]`); the review half (`keel review`, `6810818`: a `.git`-less export, one named reviewer command,
  one JSON object back, a `kind: review` line in `runs.jsonl`, and `--prompt-repo` for a prompt ratified in
  another repository); the pre-commit hook installer (`08771ce`); and the three defects its own probing found
  (`e9ec9a1` — the record directory denied by role, and evidence that must resolve to a file in the export or
  a requirement id; `18023d9` — the vacuity line now names the table it actually tested). Suite at
  `08771ce`: **84 passed, 3 failed**, the three being R5's tests that need git's own `sh`, which cannot start
  under this sandbox (`0xC0000022`).
- **The suite is green, verified from outside the work.** At `866912b`, in a clean worktree: **106 passed,
  1 skipped, 0 failed in 4:34** (Gilbert's run; Mason's own count agrees at the same commit). `tools/coverage.py`
  is in at that commit — 7,984 bytes, git-normalized `sha256:1f77ff07…`, and `.py` gates execute as
  `[sys.executable, <abs path>]` — but its **`DEFAULT_FLOOR` is `0.0`**, and the reason is better than the
  number: the first measurement came back **15.3%** because **the suite drives keel from outside** (D3 — the
  CLI is the observable), so `keel audit`, `keel review`, `keel gate` and `keel export` run in child
  processes that `sys.settrace` in the test process cannot see; `charter.py` measures 71.9% only because one
  test imports it in-process. The script therefore **refuses to report a number at all** — exit 2, naming the
  untouched modules — which is a failure the gate reports rather than a pass at 15%. So its row stays out of
  the charter, and the work that closes it is a tracer that follows child processes (`tools/sitecustomize.py`
  bootstrap, per-pid lines, parent merge). The floor follows the first *honest* measurement, rounded down, in
  the same commit, and the gate hash moves with the constant — a ratchet set from a blind measurement is the
  defect this project exists to catch.
- **The anchor and the first gate:** `Ratified at: 117ac7c`, moved from the freeze commit `ae375c6` at the
  user's word (D17). One ratified gate, `review-prompt`, `kind: prompt`. The mechanical half still reports
  **vacuity**, and correctly: a prompt is a locked instruction, not an executable gate. That clears when
  `tools/coverage.py` and the suite-and-coverage gate are declared and ratified (R8, D13, D19).
- **R7's mechanical half, dry-run 2026-10-14 ~23:10 (Gilbert), corrected by Proctor's reproduction the same
  evening.** An archive export is not auditable — the run ends `CANNOT RUN HONESTLY: git cannot name HEAD` — so
  each revision is read through a real repository (`git worktree add --detach <dir> <rev>`; `git clone` spawns
  `sh`, which cannot start in this session). At `bd63920` and at `310f449` the **divergence list is identical**:
  `[missing-section] problems`, `[vacuity] gates`, `NOT AUDITABLE` because rentguard's charter names no
  ratification commit, the review line missing, exit 2 — and neither revision names any of the five by-hand
  defects through it. **The reports are not identical below the divergences**: the living state moves between
  the two revisions (asserted enforcement 3 → 2; R2, R5, R6 and R10 change state and cells; R3's cell goes from
  prose to a backticked sha, which is *why* the asserted count drops) and **the mechanical half names none of
  that as divergence**. Proctor's per-half table (`c3526c6`; raw outputs in
  `tests/_artefacts/assay_r7_mechanical_two_revisions.txt`) scores it: three of the five appear only as *state
  classes* — R2's `met` is the one that is a lie, with R9 and R8 stating their gaps — two are invisible to it
  (W4, W3), and `problems` and vacuity are extra findings about the charter, not among the five. So the
  two-revision pair does **not** discriminate by itself, and **the drift review is what must name the rest**.
  R7's write-up makes the narrower sentence: the five scored per half with what neither half found named, never
  "the audit reproduces the by-hand audit".
- The first audit is the demonstration: **rentguard**, whose charter is `rentguard/CHARTER.md` and whose
  by-hand audit found five real defects there. The catalogue of record is **D11**: R2, **R4+W4 as one**
  finding, W1, W2, W3 — all six names, because this line first listed R2, R4, W1, W3, W4 and dropped W2.
  Reproducing that finding is R7.

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

- **D10 — D1–D9 ratified, with one addition and one process note (2026-10-14, Gilbert).** D1 answers Sift's R2
  question, and better than the shape I had drafted: the ratified gate table lives in the charter's *living*
  state, and the **reference** is that file at the ratification commit (`git show <sha>:CHARTER.md`). **I
  withdraw the separate registry file I was about to rule.** It would have added a second artefact whose
  honesty has to be maintained alongside the charter's, and it forfeits D5's block rule, which the charter
  already provides. One source, and rule 2 ("every comparison names a commit") falls out of it.

  **One addition, because both copies agreeing is not proof of approval.** A2 makes a single silent edit to
  either copy visible. What it does not catch is an edit to the gate table that keeps both copies consistent —
  a re-ratified-looking hash that no human approved. So the audit must also report, as a first-class line,
  **every change to the gate table since the last run record**: which gate, both hashes, and the commit that
  made the change. The tier stays honest and unchanged — the tool makes a weakened gate *loud*, never
  impossible — and that line is what "loud" means in practice.

  The rest are ratified as recorded: D2 (hooks are reach, not enforcement), D3 (red-first ordering with the
  contract fixed here first), D4 (rentguard is read-only evidence while it is R7's input), D5 (the anchor is
  the frozen-original *block*), D6 (the record lives inside the repository it governs), D7 (R7 is a
  two-revision pair), D8 (A1–A3, vacuity is a finding, the report prints all four columns), D9 (every
  comparison is over git-normalized content). Sift's two unverified flags stay labelled: whether a pull
  request can edit the workflow that grades it, and that the CI section covers GitHub only.

- **D11 — the by-hand catalogue pinned, the anchor measured, and one live defect found doing it (2026-10-14,
  from Folio's artefact map).** The map's real finding was a contradiction inside the record; four hygiene
  items came with it. Ruled here so the demo's claim is checkable before more is built on it.

  **F6 — "the five by-hand defects" is one catalogue, printed with all six names.** rentguard's own charter is
  the authority, and its W4 says in terms that it "is what R4's wish looked like once it was tested": **R4 and
  W4 are one finding in two stages, not two findings.** The five, as my by-hand reading of 2026-10-14 recorded
  them: (1) the MCP surface could not arm the guard — **R2**; (2) the guard was unproven and, tested, wrong —
  **R4 and W4**; (3) the cap exists only while `watch` runs — **W1** (R9); (4) publishing has no lock —
  **W2** (R8); (5) the volume path is unexercised — **W3**. Both existing lists each dropped a name: this
  file's (R2, R4, W1, W3, W4) lost **W2**, the R7 artefact's lost **R4**. Same count, different membership —
  which is why both read as fine. **Every listing prints all six names with the merge stated.** The artefact's
  measurements stand; its owner adds the catalogue as a dated note, because I will not put a second writer into
  a file that is being written.

  **F3 — the input moves; D4 binds the audit, not the dependency.** rentguard is at `ad2e880`, 75 commits, one
  modified file (`tests/_artefacts/missing_lines_2026-10-14.txt`, an evidence note, not product). D1 and D9
  already require reading revisions rather than the worktree, so a dirty checkout cannot reach a run. Explicit
  now: **an input that is not a commit exits 1 and is named.**

  **The artefact's own drift note, ruled the same way.** D7's "at rentguard HEAD `310f449`" names a moving
  thing. rentguard's code is now at `ad2e880` while its charter is unchanged, so the demonstration input is
  intact — the wording is not. **No input is ever named by a moving reference**: the demo names the four
  revisions in R7's cell (`bd63920`, `ce69cea`, `c512125`, `310f449`), and later rentguard commits change
  nothing about it.

  **F8 — a citation in a charter resolves inside the repository that holds it.** `keel/CHARTER.md` cited
  `keel-project-state.md`, which resolves only one directory above the repo: D6's own corollary, broken. The
  line sits in an appended decision note, living state, so it now reads `PROJECT-STATE.md`; the frozen block is
  byte-identical before and after.

  **F9 — found here while verifying F8, and it is live: the block the code anchors is not the block the record
  defines.** This file defines the frozen original as the user's verbatim words **plus the recommendation they
  accepted** — the sentence that carries the scope. `keel/charter.py`'s `_parse_frozen_original` collects only
  the first blockquote block, so `frozen_original` is **82 bytes** (the words alone, sha256
  `3c5b8b6a44e75d2eaa0e507c6f3ced57b486678f43271a2b8f580f30c0fb9e43`) where the definition of record is
  **553 bytes** (everything under the heading to the next `## `, heading included; sha256
  `376f11a44ebc140f705430a06df8df72f05ab59d2120f4a6e09db1a405e85716`). The recommendation is where the scope
  lives — "narrow to the join … keep using rentguard as the demonstration" — so an edit there would leave the
  audit reporting the frozen original intact: **the anchor covers less than the record says it covers, which is
  the vacuity class, on the tool's own anchor.** Ruled: the block is everything under the heading to the next
  `## `, heading included, **recorded beside its byte length** so a redefinition shows up as a length change
  rather than as a second defensible hash. Fixed by **Mason** in the parser, red test by **Proctor** (edit the
  recommendation line; the audit must report the frozen original moved). Folio's 530 bytes / `093a271b…` for
  the same block excluded the 23-byte heading line — a third definition, and the reason the length is recorded.

  **F4 — the repo could not be collected from its root.** Two mode-0700 `pytest-cache-files-*` directories sat
  at keel's root, invisible to `git status`. They are pytest's own transient cache directories and were gone
  after the first `pytest` run this turn, so Folio's exact combination — directories present, cache plugin on —
  can no longer be reproduced: plain `pytest --collect-only` at the root collects **34 tests, exit 0**.
  Recorded as **unreproduced**, not as fixed by me. The structural half was real and is closed —
  `pytest-cache-files-*/` is in `.gitignore`, because a 0700 directory under the root breaks a run on this
  host while `git status` says nothing.

  **F7 recorded as a counting caution:** `Measure-Object -Line` counted `README.md` as 141 lines and the map as
  128; the files are **176** and **152** — it drops blank lines silently. Counts a stranger will check are
  taken with `[IO.File]::ReadAllLines().Count`.

- **D12 — one anchor and a moving-anchor line; and Mason's five open readings settled (2026-10-14).** Mason
  refused D8's second copy of the anchor and he is right; D8's A2 is withdrawn, and with it the clause in D10
  that leaned on "a single silent edit to either copy".

  - **The anchor value lives in exactly one place** — the charter's `Ratified at:` line. A second copy cannot
    be kept honest: the run record is append-only, so a legitimate re-ratification would leave a first-line
    copy stale **forever** and the audit would fail permanently for a correct reason. What the record keeps is
    the anchor **used on that run**. When the anchor differs from the previous entry's, the audit prints
    `[anchor-moved]`, names both SHAs and exits 1, because moving the anchor is a human event and not a
    re-measurement; it fires once and the next entry carries the new anchor.
  - **The laundering path stays covered without the second copy:** to pass with a weakened gate the change
    must be committed and the pointer repointed, and that lights two independent lines — `[anchor-moved]` and,
    from D10, `[gate-table]` naming every gate-table change since the last run record.
  - **No `Ratified at:` line: exit 2**, never 0. Stands.
  - **The run object is per run, carrying a `gates` array, and is written after the evaluation.** D3's
    per-gate wording was mine and was wrong; a line written before the evaluation would satisfy its own
    "no run record" check.
  - **`.ok` and the exit code answer different questions.** `.ok` is the strict library property (False while
    any requirement is unbacked); the exit code is driven by divergence classes only, so wishes do not make a
    clean charter fail. Confirmed.
  - **Exit codes keep one meaning per number across commands.** A file that is not a charter — or is
    unreadable — is exit 2 in `keel charter` exactly as in `keel audit`: the tool could not do the job. A
    charter that parses and has findings (a missing section, a wish under `--fail-on-wish`) is exit 1.
  - **`keel.gates.ratify()`, if it exists, writes the `Ratified at:` line and nothing else.** Confirmed.
  - **F9's extraction rule is ratified as Mason refined it:** the anchor block is the heading line through the
    last non-blank line, trailing blanks dropped, ended by exactly one `\n`. D11's phrasing "to the next `## `"
    read literally is **554** bytes because it swallows the separator blank; the recorded value is 553 and
    Mason's rule is what produces it. Lengths are recorded in **bytes** — the 549 I reported earlier was
    characters of the same block (the em dashes are multibyte), not a third definition.
  - **One canonical spelling for the pointer:** a plain line `Ratified at: <sha>`. Other spellings are still
    parsed so a miss is never silent, but they are reported as `[format]`, because R1 says the format is
    fixed. Keel's own charter now carries the canonical line.
  - **The red/pin labelling is upheld:** F9's test is red at `eb3c0ec` for the trivial reason that
    `keel audit` does not exist there, and Mason says so rather than calling it red-first; the targeted
    witness is the `489f47d` measurement (82 bytes before, 553 after). Honesty about which side of a red a
    test is on is the point of rule 3.

- **D13 — "names an artefact" is a heuristic, and a mechanism that does not exist is a wish wearing its name
  (2026-10-14, found by running the parser on keel's own charter).** Two live examples, both in my lane and
  both now honest in `keel/CHARTER.md`:

  - **R7 passed the `ASSERTED ENFORCEMENT` check with a demo run in its `enforced-by` cell.** Running the
    audit at four revisions is what R1 calls a *check* — "a demo makes the state visible" — not a mechanism.
    It is now `enforced-by: —`, `checked-by: the audit run at the four revisions`. This is the same class as
    rentguard's R5 cell ("3 rentals, $0.0264"): evidence of a run is not a mechanism, and the parser only
    caught that one because the cell happened to hold no path.
  - **R8's cell named `tools/coverage.py` — rentguard's path, not keel's.** keel has no `tools/` directory at
    all. A mechanism borrowed from another repository passes any text heuristic and enforces nothing.

  Ruled, as an audit line beside D10's `[gate-table]`: **an `enforced-by` that names a repo path must resolve
  in the audited repo at the audited revision**, and a mechanism that does not resolve is reported
  `[unbuilt]` — the vacuity family, because a requirement whose mechanism does not exist is a wish wearing a
  mechanism's name. And the report must say which heuristic produced "0 asserted enforcement", so the human
  judges the claim instead of trusting the word. R1 catches a requirement with no mechanism; this catches a
  mechanism with no code.

- **D14 — D12 and D13 ratified, and the attribution defect they arrived with (2026-10-14, Gilbert).** D12 and
  D13 are ratified as they stand. D12's withdrawal of D8's A2 — and of the D10 clause that leaned on "a single
  silent edit to either copy" — is correct and better than what I ruled: the run record is append-only, so a
  second copy of the anchor would go stale forever on a legitimate re-ratification and fail the audit for a
  right reason. `[anchor-moved]` plus D10's `[gate-table]` line keep the laundering path covered without it.
  D13's `[unbuilt]` is the same family: a mechanism that does not resolve in the audited repo is a wish
  wearing a mechanism's name.

  **What they arrived without, and it is a live defect in this repository's process.** Neither entered a
  numbered decision with its author's name, which rule 1 requires, and neither can be attributed from git:
  `keel/.git/config` carries `user.name = Gilbert`, so **every commit here is authored "Gilbert" unless the
  committer overrides it**. `eb3c0ec` crossed `tests/` — Proctor's lane — and no one can say who wrote it, so
  Proctor read the log and reasonably reported it as mine. No turn in this conversation wrote it.
  `2006f46` shows the pattern that works (its author is "Max"). **Rule, effective now: commit with
  `git -c user.name=<Bot> -c user.email=<bot>@keel.local`**, and a numbered decision names its author in its
  body. The one-writer-per-file rule is unenforceable while the log cannot say who the writer was.

- **D16 — a mechanism cell names code that resolves in the *audited* repo; a file that only a run writes is
  evidence, not a mechanism (2026-10-14, Proctor's finding; `keel/CHARTER.md` R4 corrected).** (D15 stays
  reserved for the contract entry Mason was asked to append.) R4's `enforced-by` named
  `.keel/review-context.json`, which D13 resolves inside the audited repo — but that file is written under the
  **record root**, so whenever the record goes elsewhere (exactly what the rentguard demonstration forces, D4)
  keel's own R4 reported `[unbuilt]`, and was silent when the record defaulted. A divergence that depends on
  where the record was written trains a reader to ignore the finding, which is a gate already off.

  Ruled, and it generalises: an `enforced-by` names **code that resolves in the audited repo**; a file that
  exists only after a run is **evidence** and belongs in `checked-by` (rentguard's R5 lesson, D13); and a path
  whose location is a function of the invocation — anything under the record root — is not a mechanism at all.
  **Rejected:** naming the record path relative to the `--record` root inside the cell (that writes the
  invocation into the claim, and a claim true only sometimes is what `[unbuilt]` exists to catch), and accepting
  the conditional `[unbuilt]` as honest.

  The row now reads `enforced-by: —`, `checked-by: the drift report names `.keel/review-context.json`, written
  under the record root`, state **checked, not enforced**, with the part that exists (`keel/audit.py`) and the
  part that does not (the runner) both named in the state column. That is the truthful row until the runner is
  built, and it keeps a not-yet-built mechanism out of `enforced-by` the same way rentguard's R5 is kept out.

- **D15 — the review half's contract (2026-10-14, Mason; Gilbert's three rulings, the shapes recorded here
  before the code so Proctor's red tests are written against a contract and not a guess).** The rulings are:
  the review prompt is a **hashed artefact in the gate table with `kind: prompt`** (one table, one anchor, no
  second registry); the **missing-review line is always reported and fails only** when the charter declares
  `Review: required` or `--require-review` is passed; and the review line **shares `runs.jsonl`**. The shapes
  that follow are mine to propose and Gilbert's to overrule.

  - **Entry points.** `keel review <repo> --reviewer "<command>" [--prompt PATH] [--record PATH]
    [--export DIR] [--timeout S] [--json]`, and `keel audit <repo> [--require-review]` alongside the existing
    options. The reviewer is a **command the caller names** and keel never sees a shell: it is split with
    `shlex` and run with `cwd` = the export root and the prompt on its stdin. A stub command is a complete
    test double, so none of this needs a model.
  - **The prompt.** A `## Gates` row with `kind: prompt` is the reviewer's whole instruction. Its content
    hash is verified exactly like a gate's: a mismatch is exit 1 and no review runs, because a weakened
    instruction is not a review. `kind` is optional and defaults to `gate`; a `kind` outside `gate`/`prompt`
    is a `[gate]` divergence, never a skip. `keel gate run` runs `kind: gate` rows only, and only they can
    defeat vacuity. With no ratified prompt row, `--prompt PATH` runs the review recorded as
    `prompt_ratified: false` (an unlocked instruction, visible as such); with neither, exit 2.
  - **The export and its manifest.** The reviewer is pointed at `<export>/tree`, built by copy: the current
    state with no `.git`, plus `REVIEW-PROMPT.md`, `FROZEN-ORIGINAL.md`, `MECHANICAL-FINDINGS.txt` and
    `KEEL-MANIFEST.json`. `--export` defaults to `<record root>/review/review-<utc>/`. Tracked files plus
    untracked-and-not-ignored ones, never a filesystem walk; the record root is excluded **by role**
    (any `.keel` path segment) and not only where this run put it, because a committed record audited
    with `--record` elsewhere would hand the reviewer its own history (Gilbert's finding, fixed in
    `keel/export.py` after this entry); `.env*`, `*.pem`,
    `*.key`, `*.pfx`, `*.p12`, `*.keystore`, `id_rsa`, `id_ed25519`, `.netrc`, `credentials`, `.ssh/`,
    `.aws/`, `.gnupg/` are denied and listed as skipped; symlinks are never followed; the cap (2000 files /
    20 MB) may not omit a path a requirement, a row or the charter names. **One function, `export.build_manifest`,
    is called by both sides** — the review copies what it lists and the audit recomputes it for staleness —
    because two code paths over the deny-list, the cap or the symlink policy would make every review
    permanently stale.
  - **The reviewer's return.** Exactly one JSON object, at most 1 MB: `verdict`, `items[{class, subject,
    evidence, why, confidence}]`, `unreviewed`, `coverage{files_seen, files_total}`, `reviewer`. A class
    outside `missing`/`unrequested`/`shifted`, an item without evidence, non-JSON output, a non-zero exit, a
    timeout or a command that cannot start is recorded as `malformed`/`error`/`timeout` with the reason, and
    exits 2 — the review line is written in every case. Evidence is canonicalized against the export root;
    anything absolute or escaping it leaves the item **unverified**, counted separately from verified ones. A
    clean verdict with entries in `unreviewed` or with `files_seen < files_total` is recorded **partial**; a
    divergence with no verified item is recorded **unverified**.
  - **The record line.** `{"kind": "review", "at", "commit", "ratified", "manifest", "context", "prompt",
    "prompt_path", "prompt_ratified", "command", "exit", "result", "verdict", "items", "unreviewed",
    "coverage", "claims", "history_reachable", "export", "files", "bytes", "truncated"}` — one JSON object
    per line in `runs.jsonl`, appended after the reviewer returns. It carries the anchor it used, so
    `[anchor-moved]` compares the previous entry **whose kind is `audit` or `review`**, an explicit allowlist in `_anchor_moved` (`audit.py:467`) — amended in place 2026-10-15 after Sift read the code: the earlier wording, "any kind that carries an anchor", described a broader rule than the tool implements, and a new kind would have been inert without the sentence saying so (D12 amended):
    D10's `[gate-table]` still compares the last `audit` entry, because only audits carry a gate array.
    `history_reachable` is **`unknown`**, not `none` (amended 2026-10-14 after Sift's finding 5 and
    Gilbert's ruling for the demonstration): what the tool can prove is that the export holds no `.git`, no
    record and no prior report; what it cannot observe is the context of a command the caller names, and the
    demonstration's reviewer is a harness that loads the user's own configuration and memory. `none` would be a
    constant reading as a measurement.
  - **Exit codes.** `keel review`: 0 when a review was recorded with verdict `clean`; 1 when the recorded
    verdict is `divergence`, `partial` or `unverified`, and 1 when the ratified prompt no longer matches its
    hash; 2 when it could not run honestly (no charter, no anchor, no prompt, unwritable export or record, or
    the reviewer failed). `keel audit`: the review state is **always printed** (`fresh` / `stale` / `failed` /
    `missing`) and is a divergence only when required; freshness requires `result: pass` **and** a manifest
    equal to the current state's, so a failed or stale review never satisfies it. The reviewer's verdict never
    changes the mechanical exit code — a model never decides exit 0.
  - **Recommendation, not a change:** `.keel/review/` belongs in `.gitignore`. The export is per run, is
    never part of the manifest (the record root is excluded), and would otherwise show as untracked clutter
    in a repository whose record lives in its own tree.

- **D17 — the anchor moved, once, at the user's word: keel's first gate is ratified (2026-10-14).** The user
  approved re-pointing `Ratified at:` from the freeze commit `ae375c6` to `117ac7c`, the commit that carries
  the first gate row. Everything that made the anchor worth having was checked before the move: the
  frozen-original block is byte-identical at both commits (553 bytes, sha256
  `376f11a44ebc140f705430a06df8df72f05ab59d2120f4a6e09db1a405e85716`), so the move changes only which **gate
  table** is the reference, and the anchor is named in exactly one place (D12) — the charter line and this
  record agree, and `[anchor-moved]` reports the change once rather than letting it pass as a re-measurement.

  Why it needed the user and not me: D12 defines moving the anchor as a *human* event, because the anchor is
  where a person's approval sits. A Bot moving it to make its own audit green is the laundering path D1/D10
  exist to catch — with the tool's own repository as the demonstration.

  What the audit said before the move is the mechanism working unprompted on its own repository, first try:
  `[gate-unratified] review-prompt: declared in the working charter but not ratified at ae375c6`, with
  `gates ratified: 0` and the `[vacuity]` line. Declaring a gate *after* the anchor is declared, not ratified.

  Two consequences for the demonstration: R7's drift half runs with **keel's own** prompt, named explicitly
  and ratified here rather than in rentguard's read-only charter (D4), and the review line records which
  repository and anchor ratified it. And the export must exclude the record directory **by role** — any
  `.keel` path segment — not only the record root of the current invocation, or a repository that commits its
  record hands the reviewer its own history (Mason's lane; `export.py:106`).

- **D18 — a cell names the rule, not the value it resolves to today (2026-10-14, found while fixing R3; the same family
  as D16).** R3's `enforced-by` said the frozen-original block "is diffed against `ae375c6`" — true when written, and
  true after the anchor moved to `117ac7c` only by accident: the block is byte-identical at both commits, so nothing
  fired. A cell that names a moving value goes quietly stale and depends on an accident to stay true. It now names the
  rule — "diffed against the charter at the ratification anchor, the `Ratified at:` line" — and cannot rot when the
  anchor moves again. The test generalises and belongs with D16's: **if the value a cell names can change without the
  cell changing, the cell names the wrong thing.** The same test found R4's record path (D16) and this one.

- **D19 — the coverage gate's interface, stated before its red (2026-10-14, Mason).** Gilbert's order after
  R5 is `tools/coverage.py` plus a suite-and-coverage gate declared and ratified; that is what clears vacuity on
  keel, closes D13's `[unbuilt]` on R8 and gives keel the self-audit W1 needs. Proctor will not guess an
  interface, so this is the contract, in the shape D15 used.

  - **Surface:** `python tools/coverage.py [--min FLOAT] [--target FLOAT] [pytest args …]`, following
    rentguard's `tools/coverage.py` spelling rather than inventing a second one. `--min` is the floor.
  - **The floor is an argument, never ambient state.** Not an environment variable: that is state a test
    cannot pin, the team has already ruled against it, and `keel gate run` passes **no arguments** to a gate,
    so the gate's floor has to be the script's own default anyway. Not a floor file either: that is a second
    artefact whose honesty must be maintained alongside the charter's. The default is a constant in the
    script, which puts the floor inside the gate hash: **raising it is a gate change and needs
    re-ratification (R2)** — the ratchet is locked code, which is the point.
  - **The failing side is forced with `--min`:** `python tools/coverage.py --min 0.99` fails while the suite is
    green, so the gate cannot be confused with `exit 0`. Through `keel gate run` the gate always runs with its
    ratified default floor; the failing-side red runs the script directly, the way the hook tests run the
    installed hook's `exec` line directly while `sh` is unavailable here.
  - **The measurement:** the standard library, not the `coverage` module (not installed here, and there is no
    network): `sys.settrace` over the `keel/` package plus `trace._find_executable_linenos` for the executable
    set, with the suite run through `pytest.main`. A per-module table and a TOTAL, as rentguard's does.
  - **Exit codes:** 0 at or above the floor, 1 below it, 2 when it could not measure at all — no module body of
    ours was reached, which is the checkout-placement trap and is *diagnosed* rather than reported as 0.0%,
    because a hand-set floor would otherwise turn a broken measurement into a pass.
  - **Counts name a commit (rule 2):** the last line is
    `coverage X.X% (floor Y.Y% target Z.Z%) at <full sha> worktree clean|dirty`, so the number's provenance is
    in the number.
  - **The first floor value** is set from the first measurement, in the same commit that builds the script,
    rounded down; R8's 94% stays the *target*, and the charter's state column says whether it is met. The row
    is `| suite | tools/coverage.py | sha256:<64 hex> | gate |`, ratified like any gate — a fixture can carry
    its own row, so the red does not wait on keel's charter, which is Gilbert's.

- **D20 — D19 ratified as written (2026-10-14, Gilbert).** The three load-bearing choices are right and should
  not be relitigated when the red arrives: the floor is a **constant inside the script**, so raising it is a gate
  change that needs re-ratification rather than an edit nobody sees; the failing side is **forced with `--min`**,
  so the gate cannot be confused with `exit 0`; and an unmeasurable run is **exit 2**, diagnosed, because a
  hand-set floor would otherwise turn a broken measurement into a pass. Two notes for the build, not changes to
  it: `trace._find_executable_linenos` is private stdlib, so it is the exit-2 diagnosis that keeps a future
  Python honest, not the number the script prints; and the row `| suite | tools/coverage.py | sha256:<64 hex> |
  gate |` is mine to put in the charter once the hash is over the git-normalized blob — hand it to me rather
  than editing the charter, and the anchor move that follows is the user's by D12.

- **D21 — the review runs on the anchored instruction; a working-copy difference is disclosed, never silent
  (2026-10-14, Sift's question; amends D15's letter).** D15 said "a mismatch is exit 1 and no review runs".
  Measured at `dbb70b5`: weaken the prompt *file* in the working tree with the row and the anchor untouched, and
  `keel review` exits 0 while the reviewer receives the **anchored** text — the weakened text never reaches it,
  but the record said nothing about the difference. Ruled **(a), not (b)**: the anchored artefact *is* the
  instruction, so refusal buys no security and would block every review until the worktree is clean — the
  "impossible" tier INTENT-LOOP warns against. The unacceptable part was the silence, so the review line carries
  the **working file's hash** and a `working_copy_differs` flag, `prompt_ratified` stays `true` because the
  ratified instruction is what ran, and the audit's `[gate]` line still names both hashes. One refusal case
  remains: the anchor is **self-inconsistent** (the row's hash at the anchor does not match the blob at the
  anchor, or the path is missing there) — exit 1, no review.

## The demonstration (why it is rentguard)

`rentguard/CHARTER.md` is a real charter with a frozen original, ten requirements and a wishes list, and
the by-hand audit of it found: no way to arm the guard over MCP, a guard that had never run against a real
machine and could stop a healthy pod, a cap that exists only while `watch` runs, no technical lock on
publishing, and an unexercised volume path. Every one became a closed defect with a commit and a test. If
the tool reproduces that on the first run, R7 is met and the README has its demo; if it does not, the
shortfall is the finding.

## 2026-10-15 — the rename, the anchor, and R7's drift column (written by Gilbert, 23:2x)

- **The product is `keelcheck`.** Renamed end to end in `6ff67e8` (43 files plus the package directory) with
  two deliberate legacies so nothing narrows: the record marker still recognises pre-rename records, and a
  hook installed under the old name needs `hook install --force`. The `keel/` checkout directory and the
  `.keel/` record root keep their names on purpose.
- **The anchor moved to `688fce8` in `041689b`**, at Max's word on 2026-10-15, carrying two changes: the
  rename in the charter's prose, and the **coverage gate as the second ratified row**
  (`| suite | tools/coverage.py | sha256:c0b4c4ca… | gate |`, floor **0.83** from the first honest measurement,
  2031/2419, rounded down). The review prompt's hash moved with the rename (its manifest line), and the
  frozen-original block is byte-identical at 553 bytes. The audit now reads `gates ratified: 2 (1 executable)`,
  which is what ended the vacuity line.
- **The gate's suite timeout is a bound against a hang, not against slowness**: `8f6f8ed` raised it
  600 → 1800 s, because every run on this host recorded `timeout` while the suite was merely slow. The run
  record still has to be written on a **clean** tree — my own runs refused to start on a dirty one, on purpose.
- **R7's drift column: the completion claim was wrong, and an independent read corrected it.** The two held
  reviews ran at `ce69cea` and `c512125` on Max's released calls, and per the review JSONs the reviewer names
  **2 of 5** by-hand defects at `bd63920` and `ce69cea` and **1 of 5** at `c512125` — **D2, the guard proof,
  not D1, because that run reports the MCP fix** (Proctor's corrected wording) — and the **current** state
  names **1**, D2 again. So drift is **not met as
  written** on the current state (1, not none) and **met in part** at the pre-fix revisions (1–2, not 2
  across the board); the pre-fix pair adds the MCP-surface item where it was still missing. Verdict's
  write-up is `VERDICT-keel-r7-drift-column.md`, and it also found the demonstration file disagreeing with
  its own JSONs (`c512125` reads "0" there against 1 in the JSON), a false `history_reachable: unknown` for
  the current-state run (which records `"none"`), and the record carrying the failed 401 calls rather than
  the successful review lines. **R7's headline is a correction rather than a completion** — found by ordering
  the check rather than by trusting the claim, which is the whole point of the half that works.
- **The largest gap, found by Sift and measured** (`research/gap-review-half.md`): a four-line stub satisfied
  R4's presence check — it claimed 999,999 files in a 76-file export — because `validate_output` took the file
  counts from the reviewer's own JSON. Being closed by (i) comparing against the runner's manifest count and
  recording a disagreement as **inconsistent**, and (ii) a `kind: reviewer` gate row naming the accepted
  reviewer command, so a review from a different command is `[reviewer-unratified]` and satisfies nothing.
- **Next item taken: the MCP surface** — R5's third, absent until now: `python -m keelcheck mcp`, a stdlib
  stdio JSON-RPC server the client spawns, one call per invocation, exposing `audit`; no socket, and no gate
  hash moves. Reds first: the process exits on stdin EOF, and a diverging fixture returns as a tool *result*
  carrying exit 1 rather than as an MCP error.
- **Open, and stated as such:** the drift column names **2 of the 5** by-hand defects, not 5 of 5 — that is
  the result rather than a run to be re-cut; and the review half's prior-context and deliberate-escape
  residuals stay named rather than closed.
- **Ruling 2026-10-15 (Gilbert): recorded artefacts are evidence, so they are not rewritten — but new ones
  must not carry the host's absolute paths.** `tests/_artefacts/` ships 39 matches of the author's machine
  (`C:\Users\besen\.dsh\…`), which the R7 drift review called unrequested in rentguard's tree; the fix is not
  a rewrite, because a rewritten transcript is a falsified one. Instead: captures normalise the checkout root
  to a placeholder **at write time**, and the existing files stand as they are with one line saying whose
  machine they record. Pre-publication item, owned by whoever writes the artefact, not a live blocker.
- **Instance hazard, found and handled by Folio (2026-10-15):** a Bot runs a separate conversation per
  group, so the `keel — charter and audit` Folio and the Folio in its own chat were both editing `README.md`
  and `docs/ARTEFACT-MAP.md`. The own-chat instance found a fresher snapshot, read it, verified what it could
  measure and built on it rather than overwriting it — correct behaviour, and worth naming as a rule: **one
  Bot with two conversations is still one writer per file.** A lane that works in a group treats a parallel
  instance's write as another writer's and reads before writing; the alternative is two versions of one
  snapshot, which is the failure this project exists to catch.
- **Machine convention (B15 in `BOTTLENECKS.md`, Warden's record, 2026-10-15): heavy runs are serialised.**
  At most one whole-suite run, gate run under the tracer, or fit campaign at a time; the lane that needs the
  floor writes one line — lane, what, started, expected bound — and clears it, so a timing estimate is valid
  only while its own claim is the only one held. **A frozen log is not evidence of a live run**: check the
  process, because a killed run's log stops exactly where it stopped and looks identical to a hang. The
  reason this is a rule here rather than advice: the milestone's own record depends on a suite finishing
  inside a bound, and shared load is what turns a pass into a clock failure.

## 2026-10-15 — the pending gate change, and the order that closes the milestone (Gilbert)

- **The audit's live state, measured at `9e00e60` (`keelcheck audit .`, 4.8 s):** two divergences —
  `[gate] suite: … its content hash changed since ratification (sha256:c0b4c4ca1… -> sha256:b4a8ae1ef…)`
  and `[gate-record] suite: the recorded run of this gate did not pass (result: fail, timeout)`. Plus
  `REVIEW (clean context, R4): missing`, which is **reported and not required** (the charter's own word),
  so it is not a divergence and does not fail the audit. Those two are the whole distance to a clean audit.
- **The file behind the first one is a gate change, not housekeeping.** The working tree carries the 3.13
  tracer filter in `tools/coverage.py` (`{n for n in … if isinstance(n, int)}`): working tree
  `sha256:b4a8ae1e…` against HEAD and the ratified row at `sha256:c0b4c4ca…`. Ruling: it lands (Mason's
  lane, his commit) and the row moves in the same charter pass as the review prompt's new hash, under one
  re-ratification from Max.
- **Measured here, independent of Assay's rentguard measurement, and it cannot move the numbers:** over
  `keelcheck/` (13 files) on this host, **3.12.6** gives 2451 executable lines, raw keys 2451, `None` keys
  **0**; **3.13.15** gives the same **2451** integer lines, raw keys **2461**, `None` keys **10** (one each
  in 10 of the 13 files). Identical line numbers on both, one unhittable denominator entry per file on
  3.13, and the filter is a **no-op on 3.12** — the interpreter the gate run uses. Without it one tree
  prints two denominators 0.41 points apart; with it, one floor means one thing.
- **Read from the code, not assumed — where the ratified side comes from, and what that means for the
  run.** `load_reference` reads the charter **at `Ratified at:`** (`git show <anchor>:CHARTER.md`) and the
  gate file's bytes at that same commit; `_gate_runs` matches a recorded run by
  `obj["gate"] == name and obj["hash"] == gate.hash`, where `gate` is the **reference** row; and a
  working-tree row whose hash differs from the ratified table is its own divergence — *"editing the
  working-tree hash does not re-ratify a gate (D1)"*. So a passing run recorded at the **new** script hash
  satisfies `[gate-record]` the moment the anchor names a commit whose charter carries that hash, **with no
  second run**. That is why the run is taken first and the anchor move closes it.
- **What the re-ratification will look like in the record, so nobody reads it as breakage:** one commit
  carrying the new row values, then the anchor line pointing at it (`041689b` → `688fce8` is the shape); the
  first audit after that names the move and the table change —
  `[anchor-moved]` plus one `[gate-table]` per moved row — and the audit after *that* is clean. Honest and
  intended: the anchor moving is a human event, reported once.
- **Landed here and now: the prompt's denominator** — `ee70da3`, `review-prompt.md` rule 3, the
  `review-prompt` row's hash moving from `sha256:90df6ebc…` to
  `sha256:0e4b5764ab8c25f17105988a0094c4afe3ecbb45f8fd967d3a4ebf2debdf2e91`. Rule 3 named the fields but
  never fixed what they count, while the runner parks four of its own files in the directory it hands over
  (`REVIEW-PROMPT.md`, `FROZEN-ORIGINAL.md`, `MECHANICAL-FINDINGS.txt`, `KEELCHECK-MANIFEST.json`), so a
  two-file export read as six and an honest reviewer counting the directory was recorded `inconsistent` by
  `validate_output`'s `total != handed` check. The instruction gets stricter, and the row is a **proposal**
  until the anchor names it.
- **It happened, in the tool's own order — and the tool enforced the order (23:0x).** Mason's filter landed as
  `5b22dd1`; my charter pass landed as **`488c0e1`** — the two rows recomputed from the files rather than copied
  (`review-prompt` → `0e4b5764…`, `suite` → `b4a8ae1e…`), R4's citation made repo-relative with the adapter
  design named beside it, the adapter's two permissions written into Permissions — and `Ratified at:`
  **deliberately still names `688fce8`**, which is the content-then-word order that `688fce8` → `041689b`
  established. **My gate run was then refused, and the refusal is the finding:**
  `keelcheck gate run .` returned `gate suite: locked` — *"the gate's content does not match the ratified hash,
  and keelcheck does not run code that is not the ratified code (R2)"* — because the runner takes its gates from
  the charter **at `Ratified at:`**, not from the working tree. So the run cannot be taken early to make the
  word cheap; the word comes first, by construction. The audit at `488c0e1` reads **five divergences**, every
  one of them the pending ratification and one of them in D1's own words ("editing the working-tree hash does
  not re-ratify a gate") — the honest state to leave a night in: landed, unratified, and loud about it.
- **What closes the milestone, in order, on Max's word:** an anchor-move commit (`Ratified at: 688fce8 ->` the
  content commit, plus the sentence that records the move, nothing else — `041689b`'s shape), then
  `keelcheck gate run .` (~21 min quiet: 1274.59 s measured by Mason, 3600 s bound, and the forty-minute runs
  were three tracer suites contending rather than the suite's shape), then two audits — the first names the move
  once as `[anchor-moved]` plus one `[gate-table]` per moved row, the second should read zero divergences.
  Nothing else on this repository waits on anything.
- **The pass is final at three rows (`3d04f31`), and the audit says exactly what is left.** `review-prompt`
  `0e4b5764…`, `suite` **`973d639a…`** (Mason's thread fix `cc2b319`, the last thing that touches that file),
  and a third row — `reviewer`, `tests/_artefacts/claude-reviewer.py`, `8d5e6a5e…` — which landed *with* the code
  that reads it (`e3fee48`), because a row the audit could not act on would have been a fiction. The audit at the
  pass reads **six divergences, every one the pending ratification**: two rows declared but not ratified, two
  files whose content changed since ratification, the gate record whose newest run did not pass, and
  `[gate-unratified] reviewer: declared in the working charter but not ratified at 688fce8` — a check I did not
  know the tool had, and the one that makes the whole state fail-closed rather than silent. R4's cell now says
  which half is enforced (the command identity) and which is not (the runner that starts one).
  **So the word closes it**: an anchor-move commit naming the **then-current HEAD** — `3d04f31` is where the rows
  were set, and everything above it is state, the publish checklist and the licence, none of which touch the
  three gate files, so any later commit carries the same three rows and the reference reads them identically —
  then one gate run whose pass row is the only one at `973d639a…` and therefore the newest, then two audits.
- **Found by comparing our gate with rentguard's fix (`f832596`): a tracer sees only the thread that installed
  it.** `tools/coverage.py:189` and `tools/_child_trace.py:67` call `sys.settrace(tracer)` and nothing else,
  while `keelcheck/review.py:308-309` runs `_drain` on two daemon threads — package lines counted in the
  denominator that can never be hit, wrong in the direction nobody notices. Rentguard's gate carried the same
  bug and now calls `threading.settrace(tracer)` beside it, its own comment naming the threaded callers (the
  guard's stop, `run`'s session reader). **Ruling: the fix lands before the ratification, not after** — the
  `suite` row is still a proposal at `488c0e1` with the anchor at `688fce8`, so the row is updated once to
  whatever the final file hashes to; landing it after Max's word would spend a second re-ratification on one
  line. Mason owns it, with the before/after measurement named rather than a total alone.
- **The gap nobody has listed: there is no publish path for `keelcheck`.** Rentguard has a checklist, a
  sequence, a credential and a verify-the-ref-back step; this repository has the name decided (the registry
  shortlist, the user's word), the wheel building and installing into a clean venv (Scribe's measurement,
  `1274510`), and R9 saying the decision is the user's alone. What is missing is the same page rentguard has —
  preconditions, the exact commands, the credential (`$DSH_SECRET_<...>`, never in the chat), and the
  verification — and two things would make the README's claims true rather than aspirational before it is
  written: R5's third surface (the MCP call) and R7's demonstration closing. **Next user-facing artefact after
  those land, Scribe's shape**, not now: written today it would be stale by morning.

- **Ruling on the Â§7 objective, 2026-10-16 07:0x â€” Max chose (a), accept the flat zero, and "still stop
  everything".** The brief's options were (a) keep mod-113 and publish the probably-flat `M(t)`, (b)
  task-relevant features with a prereg amendment, (c) another head weight or horizon. His word: *"A but
  still stop everything."* So the line publishes the prereg's first falsifier and nothing further runs
  for it â€” **no grid rental, no re-shake, no frozen-head arm and no `--features off` control**, all of
  which were live options in the final hour. That last clause matters because the recommendation from
  this side was the $0 CPU controls and then (c-frozen) (`stage0/features/S7-C-PATH.md` Â§2), and the
  decision went against it; the file records that rather than reading as though the lane had chosen (a).
- **What (a) publishes, stated so no later page overreaches it:** `M(t) = 0` is measured and the
  instrument is valid (identity carry **128/128**, noise null **0/128**), and an **exact lossless
  rotation** of the code also scores **0/128** â€” so the honest sentence is *"the code did not present
  itself in the generator's basis; whether another objective would have produced separation is
  untested"*, **not** *"the model never used the features"*. The partial-RÂ² series says the readout's
  code content rose 0.093 â†’ 0.215 over the diverging shakedown run, which is the opposite of "never
  used". Sources: `stage0/features/results/basis_blindness_check.json`,
  `partial_r2_batchB-shakedown-lr1e-3-s1.json`.
- **The follow-on items, all unstarted by this ruling, for whoever resumes the line:** the two CPU
  controls that would settle whether Batch B's diverging trajectory is the injection or the cache path
  (one control with `--features off`, cache on, 40,000 steps), the re-shake that would re-price the
  bounds, and the bounds card itself (`max_hours_per_run` â‰¥ 15.79 h and `cap_usd` â‰¥ $24.02, both priced
  from the diverging run). They are recorded in `S7-C-PATH.md` Â§3â€“Â§4 and in `BOTTLENECKS.md` B16/B18,
  and they are not to be started on anyone's initiative.
- **Housekeeping, so the morning reader is not misled:** the night's goal window closed at 05:07 and the
  last file in this workspace moved at 00:25, so nothing has run since â€” no pods, no volumes, no
  accrual (pod-timing root **$9.96 of $22.50**, workspace root **$2.30 of $5.00**). rentguard is
  published at **`605564e`** and its CI run **`38814870047`** reads **completed / success** across all
  three interpreter legs; keel is clean at `27b446b` with nothing of its own outstanding; the only keel
  item still gated is the anchor move, which needs one line from Max in the keel room.

