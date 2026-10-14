# keel — artefact map

Which file holds which quantity, whether it exists, and how each claim was measured. Kept by **Folio**.
Started while the repository was one file, on purpose: a map written early is only honest if it names
what is missing, and it stays honest only if it is re-measured rather than remembered.

**Snapshot:** keel **HEAD `b81c374ad362824dcbc45cc9cc5a4f13a3407d46`** (`main`, 9 commits), the
demonstration repository rentguard at **`ad2e88015a5acaf7a7519a2fb4e2b76a5aca8622`** (75 commits),
measured **2026-10-14, 20:31–20:55 Europe/Vienna**, Python 3.12.6 on this host. Every row names the file
that holds the quantity; a count names the revision it was taken at (rule 2 in `keel/PROJECT-STATE.md`
lines 14–15). Numbers I did not re-measure are labelled **quoted**. The tree moved once during the pass —
two untracked files appeared under `tests/_artefacts/` (F5) — so read each row as an observation at the
moment it was taken, not as a claim about the working tree now.

## How to read this

- **Status** is `on disk`, `in progress` or `missing`. Committed vs untracked is part of it: at this
  snapshot the untracked paths are `README.md`, `docs/`, and two files that landed under
  `tests/_artefacts/` while this page was being written (`probe_parser_boundaries.py` and its captured
  output — Proctor's lane). `git status --porcelain` is the measurement, and it read `?? README.md` and
  `?? docs/` alone for most of the pass; the last two arrived at the end and are named rather than
  silently folded in.
- **`external:`** marks a cited path that lives outside the repository. D6 (`keel/PROJECT-STATE.md`
  lines 131–138) rules that a path cited by a project file must resolve inside the repo, and that a
  document existing only outside is cited this way and treated as unverifiable by the audit.
- A count of lines is counted from newline bytes with Python. The previous snapshot of this map used
  PowerShell's `Measure-Object -Line`, which **undercounts on this host** — it reported 93 lines for a
  127-line file. Those numbers are corrected below and the mistake is named rather than deleted (F7).

## 1. keel's own artefacts

| # | quantity | file that holds it | status | how it was measured |
|---|---|---|---|---|
| A1 | The charter — the one file a human reads | `keel/CHARTER.md`, 8607 bytes, 127 lines | on disk, committed at `b81c374`; the whole file differs from the freeze commit | `git show ae375c6:CHARTER.md` is 99 lines / 6418 bytes; `git status` clean for this file |
| A2 | The frozen original — the user's verbatim words plus the recommendation they accepted | `keel/CHARTER.md` lines 12–22 | on disk; **never edited**; verified | the frozen-original block is 530 bytes, sha256 `093a271b4c150594dceeaf51ebbcb0a5c2329118ba16239c14481bf2fffc94c2`, byte-identical at `ae375c6`, at HEAD `b81c374` and in the worktree |
| A3 | The approval, in the user's words | `keel/CHARTER.md` line 6 | on disk, committed | quoted there; `keel/PROJECT-STATE.md` lines 32–36 |
| A4 | Requirements R1–R9 with `enforced-by` / `checked-by` / state | `keel/CHARTER.md` lines 86–96 | on disk, committed; all still `draft` except R9 | the table's own `state` column |
| A5 | Wishes W1–W2, the struck wish, and the strike's trace | `keel/CHARTER.md` lines 98–116 | on disk, committed | W1 lines 105–107, W2 lines 109–111, the struck wish and its trace lines 113–116 |
| A6 | The ratification line and the "no gates ratified yet" rule | `keel/CHARTER.md` lines 26–29 | on disk, committed | line 26 records `Ratified at:` `ae375c6`; lines 28–29 rule that a gate-less input reports *vacuous* |
| A7 | Decisions D1–D9, the rule set, the lanes, the revision of record | `keel/PROJECT-STATE.md`, 17442 bytes, 211 lines | on disk, committed (D6 moved the binding record into the repo) | `git ls-files`; D6 at lines 131–138 |
| A8 | `enforced-by` / `checked-by` / neither = wish semantics | `keel/CHARTER.md` lines 82–84, and `external:INTENT-LOOP.md` lines 29–40 | on disk — in the repo, and in an external input | `INTENT-LOOP.md` sits at the workspace root, outside the repo |
| A9 | Prior-art record (ECC, Spec Kit; why the surviving claim is "the join") | `external:ECC-ASSESSMENT.md`, 65 lines, workspace root | on disk, **outside the repository** | D6's `external:` form; read in full |
| A10 | Charter parser (R1) | `keel/keel/charter.py` 17192 bytes / 465 lines, `keel/keel/cli.py` 44 lines, `__init__.py`, `__main__.py` | on disk, committed, runs | `git diff --stat 489f47d..HEAD -- keel/ pyproject.toml` is empty — the package is unchanged since `489f47d` |
| A11 | Gate scripts with ratified content hashes (R2) | — | **missing** | no `## Gates` heading in `keel/CHARTER.md` or `rentguard/CHARTER.md` (searched); the parser reports 0 gate hashes declared |
| A12 | The audit / gate runner (R3) | — | **missing** | `python -m keel audit --help` → `keel: unknown command: audit`, exit 1 |
| A13 | Clean-context drift review (R4) and its input file | `.keel/review-context.json` (named in `keel/CHARTER.md` line 91) | **missing** | no `.keel/` directory exists in `keel/` |
| A14 | Git hook installer (R5) | — | **missing** | `keel/keel/cli.py` lines 34–40 dispatch `charter` only |
| A15 | MCP surface (the shape R6 bounds) | — | **missing** | same file |
| A16 | Tests | `keel/tests/`: `CONTRACT.md` (46 lines), `conftest.py` (79), `_scratch.py` (109), `_support.py` (140), `test_audit_cli.py` (237), `test_charter_silent_wish.py` (118), `test_cli_encoding.py` (36), `_artefacts/` | on disk, committed; **red by design** | `python -m pytest -q -p no:cacheprovider tests/test_audit_cli.py tests/test_charter_silent_wish.py tests/test_cli_encoding.py` → **13 failed, 16 passed in 9.81s** at `b81c374` |
| A17 | Coverage tool (R8 names `tools/coverage.py`) | — in keel | **missing in keel** | `rentguard/tools/coverage.py` is the demonstration repository's; keel has no `tools/` |
| A18 | Gates-per-harness research, cited by D2 | `external:research/gates-per-harness.md`, workspace root | on disk, **outside the repository** | D6 rules that `research/` moves under the repo; at `b81c374` it has not |
| A19 | README | `keel/README.md`, 11854 bytes, 176 lines | on disk, **untracked draft — not published** | `git status --porcelain`; measured after this rewrite |
| A20 | This map | `keel/docs/ARTEFACT-MAP.md` | on disk, **untracked** | `git status --porcelain` |
| A21 | Packaging | `keel/pyproject.toml`, 795 bytes / 28 lines | on disk, committed, **never installed** | entry point `keel = "keel.cli:main"` line 22; `requires-python = ">=3.10"` line 9; no dependencies line 19 |
| A22 | The append-only gate run record (D3, D8/A3) | `.keel/runs.jsonl` | **missing** | no `.keel/` directory exists |
| A23 | A git remote | `keel/.git/config` | **none configured** | `git remote -v` prints nothing |
| A24 | The R7 mechanical assay artefact | `keel/tests/_artefacts/R7-demonstration-mechanical-2026-10-14.md`, 60 lines | on disk, committed | its numbers are pinned to `fbd9837` and it says so |

## 2. The demonstration's inputs (rentguard) — revision of record

| quantity | file / revision | status | source |
|---|---|---|---|
| The demonstration repository | `rentguard/`, HEAD `ad2e8801…`, 75 commits, 2026-10-14 20:04:24 +0200 | on disk; **worktree modified**: ` M tests/_artefacts/missing_lines_2026-10-14.txt` | `git -C rentguard log`, `git status` |
| rentguard's frozen original, R1–R10, W1–W4 | `rentguard/CHARTER.md`, 91 lines, 5821 bytes | on disk, committed; **byte-identical to keel's snapshot** `tests/_artefacts/rentguard-CHARTER-a72e7c4.md` — both sha256 `046fa7d91a3a…` | both files hashed |
| The revision rentguard's numbers are pinned to | `rentguard/CHARTER.md` line 30: *"Re-measured at `74b9f7a` (clean worktree, 189 passed / 0 failed, 45 subtests…)"* | the revision exists and is an ancestor of HEAD | **quoted, not re-measured** |
| The revisions R7 names, and the fixes they precede | `keel/CHARTER.md` line 94 names `bd63920`, `ce69cea`, `c512125`, `310f449`; D7 (`keel/PROJECT-STATE.md` lines 140–155) pairs them with `590c58e`, `d5fdaea`, `da51005` | all seven SHAs named above exist in `rentguard` and are ancestors of its HEAD | `git cat-file -t`, `git merge-base --is-ancestor` |
| The five by-hand defects | named **twice, differently** — see F6 | on disk | `keel/PROJECT-STATE.md` line 43 and lines 207–211; `tests/_artefacts/R7-demonstration-mechanical-2026-10-14.md` lines 23–33 |

## 3. What the parser half reproduces today — measured at keel `b81c374`

Run from the keel repository:

```
python -X utf8 -m keel charter ../rentguard/CHARTER.md     # exit 0
python -X utf8 -m keel charter CHARTER.md                  # exit 0
```

| input | requirements | wishes by the R1 rule | asserted enforcement | required sections |
|---|---|---|---|---|
| `rentguard/CHARTER.md` | 10 | R2, R4, R8 (3) | R5, R9 (2) | 5/6 — `problems` missing |
| `keel/CHARTER.md` | 9 | 0 | 0 | 6/6 |

Against the five by-hand defects, the parser finds **2 clearly** (rentguard R8 — the absent publishing
lock; R9 — the cap that exists only while `watch` runs), **1 as a symptom** (R2: a row whose state says
`met` and which names no mechanism), and **misses 2** (W4, the guard that could stop a healthy pod,
which lives in code; W3, the unexercised volume path, which is prose in the wishes section). That score
is the R7 artefact's, lines 23–33, at `fbd9837`; the run at `b81c374` produces the same output because
the package is unchanged since `489f47d`.

## 4. Findings, each with the file it lives in

**F1 — the audit does not exist, so R7's pair of runs cannot be produced.** `keel/CHARTER.md` line 94
commits the tool to an audit at four revisions; D7 (`keel/PROJECT-STATE.md` lines 140–155) defines it as
a pair; A11, A12, A13 and A22 are all `missing`. The parser's own artefact says the same at lines 40–42.

**F2 — both charters declare zero gates, so the mechanical half is vacuous by keel's own rule.**
Measured: no `## Gates` heading in either charter. `keel/CHARTER.md` lines 28–29 already state that an
audit which verifies nothing is a divergence and must not exit 0.

**F3 — rentguard is no longer the clean, frozen input D4 declared it to be.** D4
(`keel/PROJECT-STATE.md` lines 105–112) says `rentguard/` is read-only evidence while it is R7's input.
D7 names `310f449` as rentguard's HEAD; rentguard is now at `ad2e880`, 75 commits, and its worktree
carries one modified file. Its `CHARTER.md` is unchanged (byte-identical to the snapshot) and every
revision R7 names still exists — but "read-only evidence" and a dirty worktree are not the same
sentence, and D4 is Gilbert's ruling to revisit.

**F4 — the suite cannot be collected from the repository root.** `python -m pytest -q
-p no:cacheprovider` → **2 collection errors, exit 2**, on two mode-0700 `pytest-cache-files-*`
directories at the `keel/` root. They are not in `.gitignore` (6 lines), and `git status` cannot read
them — it skips them with a warning, so they are invisible to the diff and fatal to a plain `pytest`.
Naming the three test modules works (13 failed / 16 passed). The fix belongs to Proctor (`tests/`) or to
`.gitignore` (packaging, Gilbert's lane); this map names it and does not patch it.

**F5 — the files in my lane are untracked, and the tree moved during the writing pass.** `README.md` and
`docs/` are untracked; committing is Gilbert's lane (rule 1), so they stay untracked until he says
otherwise. An earlier draft of this page said they were the *only* untracked paths — true when measured,
false within the hour: `tests/_artefacts/probe_parser_boundaries.py` and its captured output (a
PowerShell error transcript, UTF-16, 1104 bytes) landed while the page was being written. `tests/` is
Proctor's lane and the files are his; they are named here because a map that claims what is untracked has
to re-measure, not remember.

**F6 — "the five by-hand defects" is two different lists.** `keel/PROJECT-STATE.md` line 43 names R2,
R4, W1, W3, W4. The R7 artefact's table (lines 25–33) names the MCP arming (rentguard R2), the guard
that could stop a healthy pod (W4), the cap that exists only while `watch` runs (W1), the absent
publishing lock (W2) and the unexercised volume path (W3). The lists differ in one slot: **R4 versus
W2**. Both are real defects in `rentguard/CHARTER.md` (R2 line 36, R4 line 38, R8 line 42, R9 line 43,
W1 lines 48–53, W2 lines 55–57, W3 lines 59–65, W4 lines 67–74); the count "five" agrees, the membership
does not. An audit that must name what it reproduced cannot be written against an ambiguous input, so
this needs a ruling — and it is the class of drift the project exists to catch.

**F7 — a correction to this map's own previous snapshot.** The earlier revision of this page reported
`CHARTER.md` as "committed 71 lines; working tree 104 lines / 6753 bytes". Those counts came from
PowerShell `Measure-Object -Line`, which undercounts here — it reports 93 lines for a file that holds
127. Measured correctly, from newline bytes: the freeze commit `ae375c6` holds **99 lines / 6418 bytes**
and the current file **127 lines / 8607 bytes**, and the corrected numbers are in A1. The earlier page's
committed-line count is demonstrably wrong against `git show`; its working-tree byte count cannot be
re-measured now, because that working tree no longer exists. Recorded because a map whose counts come
from an unreliable tool is the failure it documents.

**F8 — a citation inside the charter does not resolve as written.** `keel/CHARTER.md` line 103 records
D1 as being "in `keel-project-state.md`". That path exists at the workspace root as a pointer to
`keel/PROJECT-STATE.md`, but it does not resolve inside the repository — and D6's own corollary
(`keel/PROJECT-STATE.md` lines 136–138) says a path cited by a project file must resolve inside the repo,
with anything outside cited as `external:`. The charter's living part is Gilbert's file, so this is a
finding, not a patch. It is small, and it is the exact failure mode D6 was written about.

## 5. Not covered here

- Per-requirement fulfilment of keel's own R1–R9 — that is the audit's job (A12), which does not exist.
- Everything in the wider workspace that is not keel (`parked/`, `paper/`, `grok/`, `gpu/`, `research/`, …).
- Whether a stranger would find it useful — that is W1 in `keel/CHARTER.md` lines 105–107, and neither
  this map nor the README has a mechanism for it.
