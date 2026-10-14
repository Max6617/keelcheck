# keel — artefact map

Which file holds which quantity, whether it exists, and how each claim was measured. Kept by **Folio**.

**Snapshot — every number on this page belongs to one revision.** keel
**HEAD `fa6fb87f365e8b56a23341efbfeec29c70c1a8a4`** (`main`, 40 commits), the demonstration repository
rentguard at **`eef6bdbff5d5ac5784f73b1c6395203a6d19f811`** (82 commits, clean), measured
**2026-10-14, 22:26–22:45 Europe/Vienna**, Python 3.12.6 on this host. Only `docs/ARTEFACT-MAP.md` was
modified at the start of the pass — this file, being rewritten. The tree has moved **continuously**
tonight (`b81c374` → `9e89f86` → `78dfc0bc` → `53ea564` → `1b65a53` → `fa6fb87`, and rentguard
`310f449` → `ad2e880` → `a1848ef` → `c59d6a84` → `eef6bdb`), so read every row as an observation at that
stamp, never as a claim about the working tree now. Re-measure before quoting; the commands are named.

## How to read this

- **Status** is `on disk`, `in progress` or `missing`; committed vs untracked is part of it. Only
  `docs/ARTEFACT-MAP.md` is being edited at this stamp; the rest of the worktree is clean.
- **`external:`** marks a cited path outside the repository, per D6 (`keel/PROJECT-STATE.md` lines 131–138).
- Counts are newline bytes counted with Python. D11 records the caution (lines 285–287): PowerShell's
  `Measure-Object -Line` drops blank lines and undercounted an earlier revision of this very map.

## 1. keel's own artefacts

| # | quantity | file that holds it | status | how it was measured |
|---|---|---|---|---|
| A1 | The charter — the one file a human reads | `keel/CHARTER.md`, 9735 bytes, 142 lines | on disk, committed; the whole file differs from the freeze commit | `git show ae375c6:CHARTER.md` was 99 lines / 6418 bytes |
| A2 | The frozen original — the user's words **and** the recommendation they accepted | `keel/CHARTER.md` lines 12–22 | on disk, committed; **never edited** | `keel charter CHARTER.md` prints **553 bytes**, sha256 `376f11a44ebc140f705430a06df8df72f05ab59d2120f4a6e09db1a405e85716`. The anchor rule is D12's (lines 313–317): heading line through the last non-blank line, trailing blanks dropped, one `\n`. An earlier revision of this map printed 530 bytes / `093a271b…` — that excluded the 23-byte heading line, the third definition D11 F9 records |
| A3 | The approval, in the user's words | `keel/CHARTER.md` line 6 | on disk, committed | quoted there; `PROJECT-STATE.md` lines 32–36 |
| A4 | Requirements R1–R9 with `enforced-by` / `checked-by` / state | `keel/CHARTER.md` lines 91–101 | on disk, committed | R3 now names the anchor *rule* rather than a sha (D18); R4 is `checked, not enforced`, its mechanism moved out of `enforced-by` by D16 |
| A5 | Wishes W1–W2, the struck wish, its trace | `keel/CHARTER.md` lines 113–131 | on disk, committed | the strike's trace at lines 128–131 |
| A6 | The ratification line — the single anchor | `keel/CHARTER.md` line 26: `Ratified at: \`117ac7c\`` | on disk, committed; **moved once, at the user's word** | `keel charter` reports `ratified at: 117ac7c`; the move is D17 (`PROJECT-STATE.md` lines 453–473) and the spelling ruling is D12 |
| A7 | Decisions D1–D20, the rule set, the lanes, the revision of record | `keel/PROJECT-STATE.md`, 46453 bytes, 531 lines | on disk, committed | D14 line 359, D16 line 376, D15 line 396, D17 line 453, D18 line 475, D19 line 483, D20 line 514 |
| A8 | `enforced-by` / `checked-by` / neither = wish semantics | `keel/CHARTER.md` lines 87–89 and `external:INTENT-LOOP.md` lines 29–40 | on disk, in the repo and in an external input | `INTENT-LOOP.md` sits at the workspace root |
| A9 | Prior-art record (ECC, Spec Kit; why the claim is "the join") | `external:ECC-ASSESSMENT.md`, 65 lines, workspace root | on disk, outside the repository | D6's `external:` form |
| A10 | The charter parser (R1) | `keel/keel/charter.py`, 31841 bytes, 806 lines | on disk, committed, runs | `keel charter` output in §3 |
| A11 | **The audit (R2, R3)** | `keel/keel/audit.py`, 33471 bytes, 845 lines | on disk, committed, runs — exit 0/1/2 | `keel audit` output in §3; it checks every gate hash against the ratified table, diffs the frozen block with its byte length, reports vacuity, `[gate-table]` changes (D10), `[anchor-moved]` (D12) and `[unbuilt]` (D13), and prints the review state |
| A12 | The gate runner and the hash authoring half (R2) | `keel/keel/gate.py`, 9319 bytes, 242 lines | on disk, committed, runs | `gate run` executes `kind: gate` rows only and refuses a hash mismatch; `gate hash` prints the recorded hash over git-normalized bytes (D9) |
| A13 | The run record and the reviewer's input (D3, D8, D12, D15) | `keel/keel/record.py`, 5856 bytes, 155 lines | on disk, committed | the header no longer carries the anchor (D12 implemented — see §3); audit, gate and review objects carry the anchor they used |
| A14 | Git-normalized hashing (D9) | `keel/keel/normalize.py`, 9164 bytes, 238 lines | on disk, committed | `keel gate hash keel/cli.py` = `sha256:d00cdcd7…`, matching the file's own hash |
| A15 | **The clean-context review half (R3, R4, D15)** | `keel/keel/review.py` 19353 bytes / 482 lines, `keel/keel/export.py` 9598 bytes / 236 lines, `keel/review-prompt.md` 2656 bytes / 58 lines | on disk, committed, runs — but has never been run | `keel review --help` exit 0; the prompt's hash is the ratified gate row (A18); no `kind: "review"` line exists in any record yet |
| A16 | The git hook installer (R5) | `keel/keel/hook.py`, 9752 bytes, 237 lines | on disk, committed, runs | `keel hook install <repo>` / `hook status <repo>`, both in `keel --help`; this host cannot start git's own `sh` for the hook tests (D19, lines 498–499) |
| A17 | The CLI surface (R6) | `keel/keel/cli.py`, 2297 bytes, 68 lines | on disk, committed; **five** commands plus the `hook` pair | `keel --help`, exit 0, §3 |
| A18 | The ratified gate table | `keel/CHARTER.md` lines 103–111 — one row: `review-prompt`, `review-prompt.md`, `sha256:1f8b54b07bbe…`, `kind: prompt` | on disk, committed, **1 gate ratified** | `keel charter CHARTER.md` → `gates: 1 declared`; the audit's `[vacuity]` names it as a prompt row, not an executable gate |
| A19 | The clean-context design note | `keel/research/drift-review-design.md`, 16894 bytes, 248 lines | on disk, committed; superseded in part by D15 | `git ls-files` |
| A20 | MCP surface (the shape R6 bounds) | — | **missing** | not in `keel/`; R5's order puts it third |
| A21 | Tests | `keel/tests/`: `test_review_cli.py` (534 lines), `test_audit_cli.py` (466), `test_hook_cli.py` (394), `test_gate_cli.py` (187), `test_parser_boundaries.py` (179), `test_charter_silent_wish.py` (118), `test_cli_encoding.py` (36), `_support.py` (176), `conftest.py` (79), `_scratch.py` (109), `CONTRACT.md` (170), `_artefacts/` | on disk, committed; **green in a clean tree** | a `git archive` of `fa6fb87`: **93 passed, 6 skipped in 270.59s**, exit 0. The 6 skips are the R5 hook tests (D19, lines 498–499). See F4 for the worktree run |
| A22 | Coverage tool (R8 names `tools/coverage.py`) | — in keel | **missing; interface ruled** | `keel/CHARTER.md` line 100 admits the mechanism is unbuilt; the interface and its three load-bearing choices are D19/D20 (`PROJECT-STATE.md` lines 483–522) |
| A23 | Packaging | `keel/pyproject.toml`, 795 bytes, 28 lines | on disk, committed, **never installed** | entry point `keel = "keel.cli:main"`; `requires-python = ">=3.10"`; no dependencies |
| A24 | README and this map | `keel/README.md` and `keel/docs/ARTEFACT-MAP.md` | on disk, tracked | at this stamp `README.md` is 11854 bytes / 176 lines and this map 16115 bytes / 161 lines before the rewrite; neither size is asserted for the revised files |
| A25 | A git remote | `keel/.git/config` | **none configured** | `git remote -v` prints nothing |

## 2. The demonstration's inputs (rentguard) — revision of record

| quantity | file / revision | status | source |
|---|---|---|---|
| The demonstration repository | `rentguard/`, HEAD `eef6bdb…`, 82 commits, clean worktree | on disk | `git -C rentguard log`, `status` |
| rentguard's frozen original, R1–R10, W1–W4 | `rentguard/CHARTER.md`, 5821 bytes, 91 lines | on disk, committed; **byte-identical to keel's snapshot** `tests/_artefacts/rentguard-CHARTER-a72e7c4.md`, both sha256 `046fa7d91a3ac47d…` | both files hashed at this stamp |
| rentguard's anchor block | `rentguard/CHARTER.md` lines 7–15; **no `Ratified at:` line at all** | not auditable — the audit says so and exits non-zero | `keel charter ../rentguard/CHARTER.md` prints 539 bytes, `0e96174d…`, and **exits 1** (findings); `keel audit` output in §3 |
| The numbers rentguard's charter pins | `rentguard/CHARTER.md` line 30: *"Re-measured at `74b9f7a` (clean worktree, 189 passed / 0 failed, 45 subtests…)"*; coverage floor 90.2% at line 44 | the pinned revision exists and is an ancestor of HEAD | **quoted, not re-measured** |
| The revisions R7 names, and the fixes they precede | `keel/CHARTER.md` line 99: `bd63920`, `ce69cea`, `c512125`, `310f449`; D7 pairs them with `590c58e`, `d5fdaea`, `da51005` | all seven exist in `rentguard` and are ancestors of its HEAD | `git cat-file -t`, `git merge-base --is-ancestor` |
| The by-hand catalogue | one catalogue, **all six names, the merge stated** (D11 F6, `PROJECT-STATE.md` lines 235–244): R2; **R4 and W4 as one finding in two stages**; W1 (R9); W2 (R8); W3 | ruled | D11 F6; rentguard's own W4 (lines 67–74) is the authority for the merge |

## 3. What runs today — measured at keel `fa6fb87`

```
python -m keel --help                       # exit 0 — charter, audit, gate run/hash, review, hook install/status
python -m keel charter CHARTER.md           # exit 0
python -m keel charter ../rentguard/CHARTER.md   # exit 1
python -m keel gate hash keel/cli.py        # exit 0 — sha256:d00cdcd7…
python -m keel audit .            --record <tmp>   # exit 1
python -m keel gate run .         --record <tmp>   # exit 1
python -m keel audit ../rentguard --record <tmp>   # exit 1
python -m keel review --help                # exit 0
python -m keel hook --help                  # exit 0 — install / status
```

| input | what the run reports |
|---|---|
| `charter CHARTER.md` | 6/6 sections, 9 requirements, **1 gate declared**, `ratified at: 117ac7c`, `review: reported, not required`, frozen original 553 bytes `376f11a4…` |
| `charter ../rentguard/CHARTER.md` | **exit 1** — 5/6 sections (`problems` missing), 10 requirements, 0 gates, `ratified at: (not named)`, frozen original 539 bytes `0e96174d…` |
| `audit .` | exit 1 — `[vacuity] gates: the ratified table at 117ac7c holds 1 prompt row(s) and no executable gate … R2's gate is an executable script with a content hash, so the hash half of this audit verified nothing`; and `REVIEW (clean context, R4): missing — no review line in k.jsonl` |
| `gate run .` | exit 1 — `no ratified gate: the hash half of this repository verifies nothing, so there is nothing to run` |
| `audit ../rentguard` | exit 1 — `[missing-section] problems`, `[vacuity] gates` (no anchor, no executable gate), `NOT AUDITABLE: the charter names no ratification commit`, `REVIEW … missing` |

The record written by those runs (the audit writes it even when the run fails, D8/A3):

```
{"at": "…Z", "kind": "header", "record": "keel/runs", "version": 1}
{"at": "…Z", "commit": "fa6fb87…", "divergences": 1, "exit": 1,
 "gates": [{"hash": "sha256:1f8b54b07bbe…", "name": "review-prompt",
            "path": "review-prompt.md", "ratified": "sha256:1f8b54b07bbe…",
            "status": "locked"}], "kind": "audit", "ratified": "117ac7c"}
```

The header line **no longer carries the anchor** — D12's withdrawal of the second copy is implemented;
the anchor lives once, in the charter's `Ratified at:` line, and each audit entry carries the anchor it
used.

## 4. Findings, each with the file it lives in

**F1 — the audit did not exist. Closed** at `2006f46`; the gate runner, review half and hook installer
have since landed too (`077`…`fa6fb87`). §3 is first-hand output.

**F2 — the hash half is vacuous, and keel's own audit exits 1 for it. Open, by design.** One ratified
gate is a `kind: prompt` row, which cannot defeat vacuity; the audit says exactly that in one line. The
cure is keel's own coverage gate (R8), whose interface is ruled in D19 and ratified in D20. This is the
quotable state of the project: the tool audits, and what it finds on its own repository is that nothing
executable is enforced yet.

**F3 — the demonstration input moves; ruled by D11 F3.** rentguard went 71 → 82 commits during tonight.
D4 binds the audit, not the dependency, and D11 (lines 246–255) rules that **no input is ever named by a
moving reference**: the demo names the four revisions in R7's cell, and later rentguard commits change
nothing. rentguard's `CHARTER.md` is byte-identical to the snapshot this map measures.

**F4 — collection from the repository root: measured, then unreproduced, then measured again.** Measured
at `b81c374` (this map's first revision): two mode-0700 `pytest-cache-files-*` directories at keel's root
and `python -m pytest -q` → **2 collection errors, exit 2**. D11 F4 recorded it **unreproduced** at
`1b65a53`-time: the directories were gone after a run and 34 tests collected, exit 0. Measured again at
`1b65a53` and again at `fa6fb87`: the two directories are present, and `python -m pytest -q
-p no:cacheprovider` in the worktree → **2 collection errors, exit 2** (`--collect-only` gathers 99 tests
and still reports the 2 errors). It is therefore a condition of a dirty working directory on this host,
not a property of the revision: a `git archive` of the same revision collects and runs green (A21). The
structural half is closed — `.gitignore` carries the pattern so `git status` stays clean. Naming the test
paths avoids it; this map does not patch it.

**F5 — the untracked docs. Closed** at `ec18e0c`.

**F6 — the five by-hand defects were two lists. Ruled by D11 F6** (`PROJECT-STATE.md` lines 235–244):
one catalogue, printed with **all six names**, the merge stated — R2; **R4 and W4 are one finding in two
stages**; W1 (R9); W2 (R8); W3. Both earlier lists had each dropped a name, R4 and W2 respectively, which
is why both read as fine.

**F7 — counting caution. Ruled by D11 F7.** `Measure-Object -Line` drops blank lines; counts a stranger
will check are taken from newline bytes. Used throughout this page.

**F8 — a citation resolving outside its repository. Closed** at `0914eb1`.

**F9 — the anchor covered less than its record said. Ruled by D11 F9 and D12; closed.** The parser anchors
the whole section and prints 553 bytes; the red test that edits the recommendation passes.

**F10 — D12's `[anchor-moved]` and D13's `[unbuilt]` were ruled but not in the code. Closed.** At
`1b65a53` the strings appeared 0 times; at `fa6fb87` `anchor-moved` appears 3 times and `unbuilt` once in
`keel/keel/*.py`, and D12's withdrawal of the record header's anchor is visible in the record above.

**F11 — a charter with no `Ratified at:` line exits 1; D12 (line 302) says exit 2.** Measured on rentguard
at `eef6bdb`: `NOT AUDITABLE`, and exit **1**, because `Audit.compute_exit` ranks findings above
`cannot_run` and rentguard also has a missing section and vacuity. The two clauses collide whenever a
not-auditable charter carries any other finding — which is exactly the demonstration input. Owned by
Mason (code) or Proctor (test); named here, not patched.

**F12 — the review half exists and has never run.** `keel review` and its `.git`-less export are
implemented (A15); no `kind: "review"` line exists in any record, so both audits print `REVIEW … missing`,
and R7's pair of runs at the four revisions is still unexecuted (Proctor's). R3's three classes —
missing / unrequested / shifted — are produced by a reviewer that has not yet been started on either
repository.

**F13 — a gate row that is a prompt cannot satisfy R2's vacuity rule, and the charter says so.** One
ratified gate, `kind: prompt`, and the audit's vacuity line names why it does not count. This is D15's
design working (a locked instruction is not an executable check) and it is the reason F2 stays open until
the coverage gate lands. Recorded so a reader does not read `gates ratified: 1` as "the mechanical half
is satisfied".

## 5. Not covered here

- Whether the review half's export, deny-list and manifest rules survive contact with a real reviewer —
  that is the R7 demonstration's drift half, Proctor's to run.
- Everything in the wider workspace that is not keel (`parked/`, `paper/`, `grok/`, `gpu/`, …).
- Whether a stranger would find it useful — W1 in `keel/CHARTER.md` lines 120–122; neither this map nor
  the README has a mechanism for it.
