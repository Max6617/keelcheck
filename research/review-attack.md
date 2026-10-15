# Attack from the outside on `keel review` — Sift, 2026-10-14

A falsification attempt against `research/drift-review-design.md` §7–8 (Proctor's attacks and
Gilbert's rulings, contract D15) and against the code that landed for it. Not a review of the
project's *own* claims about itself: the question is which of the design's claims about the review
half were false **as implemented**, and which are simply unproven.

**Erratum, 2026-10-15 (Sift) — two path conventions in this file, on purpose.** The pointer to the
design note now reads `research/drift-review-design.md`: that file moved inside the repository on
2026-10-15 (D6's corollary), and in-repo paths are quoted relative to the repo root. The
`keel/review.py` and `keel/export.py` spellings inside the dated findings are **correct as of the
revisions they name** — the package directory really was `keel/` then; the rename to `keelcheck`
landed at `6ff67e8`, after both `218c444` and `5442a90`. They are left as written, because rewriting
a dated record to match today's tree is the drift this project exists to catch.

**Two revisions in this file, and both are named.**

- **First attack: `keel@218c444`** — `keel/review.py` blob `1c7d72a1f2c3…`, `keel/export.py` blob
  `791848ac2c…`. The evidence quoted under each finding is from this revision and is the record of
  what was true then. It is **not** the current state.
- **Dispositions: `keel@5442a90`** (2026-10-14, clean). Proctor reproduced all four findings
  independently, Mason landed the fixes at `32ec110`, `33720dc`, `5442a90`, and the design text
  moved. All six findings are now resolved or narrowed to a named, measured residual.

**Method.** `research/probe-review-attacks.py`, executed, output quoted. It reads `keel/` internals
on purpose (D3's CLI-only rule binds `tests/`, not this file), builds real repositories with
Proctor's own fixture helpers, and runs the real `keel review` CLI where a CLI answer is needed.
Five probes, no model in the loop.

**Status** (the column that matters):

| # | Claim | At `218c444` | At `5442a90` |
|---|---|---|---|
| 1 | D15: the prompt "is verified exactly like a gate's" | **Falsified** — the working tree re-ratified itself | **Fixed** (`32ec110`): row and instruction both from the anchor; my attack case exits 1 |
| 2 | §7.8: the omitted set may never contain a file a requirement, a gate or a finding names | **Falsified** — a gitignored gate path vanished silently | **Fixed**: in `skipped`, and findings-named paths are in `always_paths` |
| 3 | §7.7/D15/D17: the record directory is out of the reviewer's reach | **Falsified as stated** — a `.keel` name was denied, not the record | **Closed with a named boundary**: content identity excludes a record wherever it lives; only an unidentifiable record-**named** file is exported, and it is warned (§3) |
| 4 | §7.9: one function both sides, so freshness is never a false red | **Falsified** — worktree bytes and sizes | **Fixed**: git-normalized, same hash across checkouts |
| 5 | §1: the runner records `none \| git \| unknown` for reachability | **Falsified** as design text | **Closed as narrowed**: the field is a constant by construction and the design now says so |
| 6 | §1: a reviewer that leaves the export does so "visibly in what it returns" | **Falsified** as design text | **Closed as narrowed**: the sentence is deleted and replaced with "deliberate escape is not detected" |
| 7 | finding 1's consequence: the review ran on the anchored text while the working copy differed, and the line said nothing | **Raised** (probe C, second case) | **Ruled as D21**: disclose with the working file's hash + `working_copy_differs`; not yet landed at `5442a90` (§7) |

**My own corrections, recorded rather than buried.** Three things in my first write-up were wrong or
weaker than stated, and Mason's reply is why:

- **I reported findings 5 and 6 as still standing at `dbb70b5`.** They were already closed as
  narrowed in the design text at that revision: `git show dbb70b5:research/drift-review-design.md`
  contains "Deliberate escape is not detected" (finding 6) and, for `history_reachable`, that it "is
  not a three-valued measurement, it is a constant by construction" (finding 5); I re-checked both
  before writing this. **How the miss happened, because the class matters more than the instance:**
  I verified finding 5 against `keel/review.py` — the code, where the literal legitimately remains —
  and finding 6 against my earlier read of the design at `218c444`, without re-reading the design at
  the revision I was reporting on. Two mechanical traps made that easy and are worth naming for
  anyone checking a file claim here: **the sentence wraps across two lines**, so a single-line
  search misses it, and **the path spelling differs between contexts** — `research/…` inside the repo
  is `keel/research/…` in the workspace, and a grep against the wrong spelling returns nothing,
  which reads as a false negative rather than as an error. A claim about a file must name the
  **revision** and the **path spelling** that were read; that is rule 2 applied to prose.
- **My finding-3 fixture was not a keel record.** I wrote `{"kind":"audit","commit":"deadbeef"}` in
  a file named `prior-runs.jsonl`; a keel record is identified by its first line
  (`"record": "keel/runs"`), so mine was a plain JSON file and its export proved nothing about
  records. The *original* finding was still real at `218c444` — the deny was `.keel`-by-name only —
  and §3 below now tests the shapes that matter.
- **My finding-4 reproduction was weaker than I presented it.** I set `core.autocrlf` between the
  two checkouts; `core.autocrlf` is repo-wide, so the two reviews ran under two configurations in
  sequence, not two checkouts of one state. The conclusion still held (the manifest was keyed to
  worktree bytes; Mason confirms the cause, adding that each file's `len()` was in the hash too),
  and his cleaner measurement — one state, LF fixture files, `git checkout -f -- .` under each
  config — is the one to cite: it showed the defect before the fix and `sha256:7a2d0526e00f1…`
  twice after.

---

## 1. The prompt was verified against the working tree, so the working tree re-ratified itself

**Claim.** D15 §"The prompt": *"A `## Gates` row with `kind: prompt` is the reviewer's whole
instruction. Its content hash is verified exactly like a gate's: a mismatch is exit 1 and no review
runs."* D1 makes "exactly like a gate's" mean the **ratified table at the ratification commit**
(`git show <sha>:CHARTER.md`).

**Code at `218c444`.** `run_review` called `load_charter(repo)` (working tree, `review.py:296`), then
`_resolve_prompt` (`313`), which compared the prompt file to `row.hash` — the row **parsed from the
working-tree charter** (`_verified_prompt`, `84-107`). `audit.reference` was loaded afterwards
(`316`) and never consulted for the prompt.

**Attack.** Edit `review-prompt.md` **and** update that row's hash in the working tree; commit
nothing.

**Evidence at `218c444` (executed).**

```
ratified_prompt_hash: sha256:65866529db4ad1b7…
recorded_prompt_hash: sha256:89d06e46b2232867…
prompt_ratified: True
ratified_in: c-prompt-tamper@c2c045d7bdccc9be27d994191f37a730bdbb65e6
verdict: clean
exit_code: 0
control_prompt_only_exit: 1
```

Editing the prompt and its row together ran the review with exit 0 and recorded
`prompt_ratified: true` — provenance the anchor never gave. The control (prompt edited, row
untouched) exited 1, which is why the gap was easy to miss: the check that existed was a
*self-consistency* check, and the weakened artefact re-ratified itself.

**At `5442a90`: fixed, and the rule refined.** `_anchored_prompt` takes the row from `reference`
and the instruction from `git cat-file blob <anchor>:<path>`, requires the working **row** to equal
the ratified row (else exit 1 — my attack case), and hashes the blob against the ratified row.
Gilbert removed one check: the working-tree **file** is deliberately not compared to the ratified
hash, because the anchored blob is what is handed over, so a worktree edit cannot weaken the
reviewer's instruction, and the audit already reports that drift as `[gate]`. The review line
records the ratified hash; see §7 for what it deliberately does not record.

## 2. A gate path that git ignores was neither exported nor named as omitted

**Claim.** §7.8: *"the omitted set may never contain a file that a requirement, a gate or a finding
names; the omitted count and the full omitted-path list go in the manifest"*.

**Code at `218c444`.** The file set came from `git ls-files` + `git status --porcelain` only
(`export.py:74-86`), never a walk. Nothing compared `always_paths(...)` against what was exported,
and findings were not in `always_paths` at all.

**Evidence at `218c444` (executed).** A charter gate row naming `gates/check.sh`, with `gates/` in
`.gitignore`:

```
gates/check.sh in manifest['always']: True
gates/check.sh in files:   False
gates/check.sh in skipped: False
files: ['.gitignore', 'CHARTER.md', 'tracked.txt']    skipped: []
```

The file the charter named as its mechanism was silently absent from a manifest that said
`skipped: []` — the vacuity class, in the export.

**At `5442a90`: fixed.** The re-run reports `gates/check.sh in skipped: True` with the reason
`ignored by .gitignore (named by the charter)`, and `always_paths` now includes paths that
**findings** name (`for finding in audit.findings:`), so §7.8's "or a finding names" clause is
implemented rather than promised.

## 3. The record guarantee was about a name, not about the record

**Claim.** §7.7, D15, D17: the record root is excluded *"by role (any `.keel` path segment) and not
only where this run put it"*.

**Code at `218c444`.** `RECORD_SEGMENTS = {".keel"}` (`export.py:56,63`); the active root was
excluded only when it was a strict ancestor of the repo root (`120-122`). The tool therefore knew
the record only by a default *name* and by the path the invocation happened to use.

**At `218c444`** a file at the repo root is exported when the default `.keel` root is used, and
`--record <repo>/runs.jsonl` was exported too (its parent *is* the repo root, so the ancestor test
did not fire). That was real: any record not under a `.keel` segment and not named by the invocation
was handed to the reviewer. My first fixture overstated it as "any record"; see the corrections
above.

**At `5442a90`: closed with a named boundary.** `is_keel_record` reads the first line and excludes a
record wherever it lives (`"denied: a keel run record, wherever it lives"`), and the active record
and context files are excluded by identity — so a committed `history/runs.jsonl` under the default
record root is **not** exported, which closes the record-shaped case generally, not only under
`.keel`. Re-run at `5442a90` (executed):

```
genuine record at history/runs.jsonl  -> exported: False, reason: denied: a keel run record, wherever it lives
empty file named audit/runs.jsonl     -> exported: True,  manifest warning: a file named like a keel record
header-stripped record, odd name      -> exported: True,  (no warning)
```

**The boundary, kept as the thing to keep:** a record-**named** file (`runs.jsonl`,
`review-context.json`) whose content cannot identify it — empty or truncated — is not excluded on a
guess; it is exported and travels as a `warnings` entry in the manifest, the review line and the
report. Loud, not silent. **Measured outside that boundary, not part of the ruling:** a file that is
neither identifiable by content nor record-named — my `notes/history.log` with its first line
removed — exports without a warning. Reaching it needs a keel record's header line to have been
stripped by hand (`record.py` already calls a rotated or deleted record a human decision), so it is
recorded here as the edge of the boundary rather than as an open defect, and no action is requested
on it.

## 4. The manifest hashed worktree bytes, so freshness was checkout-dependent

**Claim.** §7.9: one function, both sides, *"because two code paths … would make every review
permanently stale: a false red that re-running cannot clear."* D9: *"every hash and every block
comparison is over git-normalized content."*

**Code at `218c444`.** `build_manifest` read raw bytes and hashed them
(`data = source.read_bytes()` → `hashlib.sha256(data).hexdigest()`, `export.py:180,188`).

**Evidence at `218c444` (executed).** One commit; `core.autocrlf` true then false; the same file
checked out CRLF (6 bytes) then LF (4 bytes):

```
manifest file hash: 58055bdcc73787eb88c7…   (CRLF checkout)
manifest file hash: 911169ddaaf146aff539…   (LF checkout)
two_checkouts_differ: True
```

A review recorded on one checkout was reported **stale** on another — a false red that re-running
cannot clear, in the one comparison that decides whether the review half ran, and a violation of D9.
Method caveat: my two measurements ran under two `core.autocrlf` settings, so the reproduction is
weaker than I first stated; Mason's cleaner run (one state, LF files, `git checkout -f -- .` under
each config) is the one to cite.

**At `5442a90`: fixed.** Files are hashed over git-normalized content, `bytes` is the stored size
because it enters the manifest hash, and the whole manifest is verified against
`git hash-object --stdin-paths` in one process. The re-run gives the same hash for both checkouts
(`911169ddaaf146…`, `two_checkouts_differ: False`).

## 5. `history_reachable` was a literal — ruled a constant, design corrected

**Claim.** §1 asked the runner to record `none | git | unknown`. `review.py` has exactly one
occurrence: `"history_reachable": "none",`. D15 ruled the field `none` "by construction".
**Disposition:** the code is the ruled shape and stays. The design was the thing out of step, and it
was corrected: the design now says it is a constant by construction and that *a constant is not
evidence*. My `dbb70b5` note that this was a standing design/code contradiction was wrong — the
correction is in that revision; I checked the code and not the design.

## 6. "Visible in what it returns" — the sentence is deleted

**Claim (at `218c444`).** "*it can only leave it deliberately, which is visible in what it
returns.*" **Falsified then:** `_run_reviewer` captures stdout and stderr only; `_evidence_resolves`
validates the strings emitted, never what was read. A reviewer that runs `git -C <repo> log` and
then cites relative paths inside the export produces items that are all `verified: true` and a
record indistinguishable from a clean-context review.

**Disposition: accepted and deleted.** At `dbb70b5` the design reads **"Deliberate escape is not
detected."** The tool guarantees what the reviewer *was handed*, not what it read. My two extra
facts are **not** yet in the design, and I am recording them here rather than claiming them as
fixed: (i) `CLAUDE.md`, `AGENTS.md` and `.claude/settings.json` are tracked files and are not in
`DENIED`, so the reviewer is handed the project's own always-loaded instruction file; (ii) keel does
not clear or sandbox the reviewer's environment, so user-level memory/rules/hooks still apply to a
harness command string. Mason has said he will fold both into the design in the next doc pass.

## 7. The ruling: D21 — the anchored instruction runs, and the difference is disclosed

The strengthening of finding 1 created a case D15's letter did not cover. Measured at `5442a90`:
**weaken the prompt file in the working tree, leave the row untouched** → `keel review` exits **0**,
records `prompt_ratified: true`, and the export's `REVIEW-PROMPT.md` is the **anchored** instruction;
the weakened text never reaches the reviewer. D15's letter ("a mismatch is exit 1 and no review
runs") and the code disagreed, so Proctor left two reds red rather than encode the code.

**Ruled (a), recorded as D21 (`PROJECT-STATE.md:524`, amending D15's letter, not Mason's entry), and
my reasoning is what decided it:** refusal buys no security when the reviewer never sees the weakened
text, and it would block every review until the worktree is clean — the "impossible" tier. The
unacceptable part was the **silence**, so the ruled shape is exact: exit **0**; `prompt_ratified`
stays **true** because the ratified instruction is what ran; the review line carries the **working
file's hash** and a `working_copy_differs` flag, so the substitution is disclosed where the record
lives; the audit's `[gate]` line still names both hashes; and the single remaining refusal is a
**self-inconsistent anchor** — the row's hash at the anchor disagreeing with the blob there, or the
path missing — exit 1, no review. Proctor has the four assertions its two reds must make.

**Landing status at `5442a90` (red-first, and correct):** D21's **red tests are in** —
`tests/test_review_cli.py:289` asserts `working_copy_differs is True` and `tests/CONTRACT.md:181`
states the shape, both landed at `45cebf8` — while `keel/review.py` at HEAD still contains no
`working_copy_differs` and no working-file hash. So the disclosure is ruled and red, and the fix is
Mason's; the refusals the code does implement are the working-**row** mismatch and the
self-inconsistent anchor. That is the process working, not an open design question: the
recommendation is adopted, and the field name to look for is `working_copy_differs`.

## What I could not falsify

- **Exit codes never depend on a verdict (item 4, D15).** Upheld: `Audit.compute_exit` reads
  findings; `_review_state` reads `result`/`manifest`, not `verdict`; a `divergence` verdict does
  not fail the audit. By design — and it means `--require-review` can be satisfied by a review that
  found the state drifted. A limit, not a bug.
- **Evidence canonicalization (item 1).** Upheld: absolute paths and escapes rejected, existence
  required.
- **`clean` + `unreviewed` → `partial`; divergence with no verified item → `unverified`
  (items 2, 3).** Upheld.
- **Timeouts, stdout cap, error lines written on failure (item 6).** Upheld. Proctor separately
  measured that a reviewer which never reads stdin does **not** deadlock the runner (~2 s to
  `malformed`, with and without `--timeout`); the explicit bound is now in anyway, as exposure
  insurance.
- **Staleness keyed to the manifest, not HEAD; content-keyed, not path-keyed (items 5, 10).**
  Upheld in shape; the byte-level defect (finding 4) was the only hole.
- **One function on both sides (item 9).** Upheld: `export.build_manifest` is called by the review
  and by the audit.

## Where this stands

Six findings: **four were false claims and are fixed**, **two were design text and are closed as
narrowed**; a seventh consequence is **ruled (D21) and pending landing**. What remains is named and
measured rather than left open: the D21 disclosure field is not yet in `keel/review.py`, and
`CLAUDE.md`/`AGENTS.md` plus the inherited environment are not yet written into the design (Mason's
next doc pass). One edge sits outside the record boundary and is recorded as such, not as a defect:
a file that is neither content-identifiable nor record-named exports without a warning (§3),
reachable only by stripping a keel record's first line by hand. My probe is not a test and stays in
`research/`.
