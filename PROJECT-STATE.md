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

## The demonstration (why it is rentguard)

`rentguard/CHARTER.md` is a real charter with a frozen original, ten requirements and a wishes list, and
the by-hand audit of it found: no way to arm the guard over MCP, a guard that had never run against a real
machine and could stop a healthy pod, a cap that exists only while `watch` runs, no technical lock on
publishing, and an unexercised volume path. Every one became a closed defect with a commit and a test. If
the tool reproduces that on the first run, R7 is met and the README has its demo; if it does not, the
shortfall is the finding.
