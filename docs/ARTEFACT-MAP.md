# keelcheck — artefact map

Which file holds which quantity, whether it exists, and how each claim was measured. Kept by **Folio**.

**Snapshot — this page is a window, not a revision.** keelcheck went from **`c8778b4` (77 commits)** at
the first measurement to **`574a44f` (88 commits)** at the last, on `main` — **eleven commits inside this
pass**. The demonstration repository rentguard went from **`449a339` (106 commits)** to **`3287a4f`**
(108), clean at the first and carrying two modified files at the last. Measured **2026-10-15,
22:10–22:35 Europe/Vienna**, Python 3.12.6 on this host. File sizes and line counts in §1 were taken at
`c8778b4`; each run in §3 names the commit it read. `.keel/runs.jsonl` gained lines while it was being
read, and one live `gate run` was started and then **stopped** when the revision moved under it, so its
coverage number is deliberately not quoted. Read every row as an observation inside that window, never as
a claim about the tree now; re-measure before quoting.

## How to read this

- **Status** is `on disk`, `in progress` or `missing`; committed vs untracked is part of it. At this
  stamp the worktree carries ` M tests/test_review_cli.py` and the untracked `.assay-tmp/`.
- **Paths are relative to this repository's root** — `CHARTER.md`, `keelcheck/audit.py`,
  `tests/_artefacts/…`, `pyproject.toml`. An earlier revision cited them in the workspace form
  `keel/<path>`, which does not resolve inside the repo: D6's corollary, the class F8 was about, and the
  one thing the rename's blind substitution could not fix. The **survivors of the rename are named as
  survivors** where they appear: the checkout directory `keel/`, the record root `.keel/`, and records
  written before it.
- **`external:`** marks a cited path outside the repository, per D6 (`PROJECT-STATE.md` lines 180–187).
- Counts are bytes and newline lines counted with Python. D11 F7 (lines 328–330) records the caution:
  PowerShell's `Measure-Object -Line` drops blank lines and undercounted an earlier map revision.
- **Versions of this map lie by ageing.** The previous snapshot was `fa6fb87`; since then the product was
  renamed, a second gate was ratified, the anchor moved, the vacuity line closed, the exit-code collision
  in F11 was fixed and the drift half ran. Rows below that changed are marked **was:** so the drift is
  visible rather than silently corrected.

## 1. keelcheck's own artefacts

| # | quantity | file that holds it | status | how it was measured |
|---|---|---|---|---|
| A1 | The charter — the one file a human reads | `CHARTER.md`, 10850 bytes, 150 lines | on disk, committed | `keelcheck charter CHARTER.md`; was 9735 B / 142 L at the previous map stamp |
| A2 | The frozen original — the user's words **and** the recommendation they accepted | `CHARTER.md` lines 12–22 | on disk, committed; **never edited** | prints **553 bytes**, sha256 `376f11a44ebc140f705430a06df8df72f05ab59d2120f4a6e09db1a405e85716`, byte-identical at `ae375c6`, `117ac7c` and `688fce8` (D17, D12) |
| A3 | The approval, in the user's words | `CHARTER.md` line 6 | on disk, committed | quoted there; `PROJECT-STATE.md` lines 36–40 |
| A4 | Requirements R1–R9 with `enforced-by` / `checked-by` / state | `CHARTER.md` lines 91–103 | on disk, committed | `keelcheck charter`: 9 requirements, 0 wishes, **3 human checks**, 0 asserted enforcement |
| A5 | Wishes W1–W2, the struck wish, its trace | `CHARTER.md` lines 118–136 | on disk, committed | strike trace at lines 133–136 |
| A6 | The ratification line — the single anchor | `CHARTER.md` line 26: `Ratified at: \`688fce8\`` | on disk, committed; **moved twice, each at the user's word** | `keelcheck charter` prints `ratified at: 688fce8`; the moves are D17 (lines 486–506) and the 2026-10-15 section (lines 584–589); **was:** `117ac7c` |
| A7 | Decisions D1–D21, the rule set, the lanes, the revision of record | `PROJECT-STATE.md`, 54052 bytes, 609 lines | on disk, committed | D11 F6 lines 274–287, D19/D20 lines 516–555, the 2026-10-15 section lines 578–609; **was** 46453 B / 531 L |
| A8 | `enforced-by` / `checked-by` / neither = wish semantics | `CHARTER.md` lines 87–89 and `external:INTENT-LOOP.md` lines 29–40 | on disk, in the repo and in an external input | D6's `external:` form |
| A9 | Prior-art record (ECC, Spec Kit; why the claim is "the join") | `external:ECC-ASSESSMENT.md`, 65 lines, workspace root | on disk, outside the repository | D6 |
| A10 | The charter parser (R1) | `keelcheck/charter.py`, 31866 bytes, 806 lines | on disk, committed, runs | output in §3 |
| A11 | The audit (R2, R3) | `keelcheck/audit.py`, 34565 bytes, 865 lines | on disk, **one file modified in the worktree**, runs — exit 0/1/2 | `_check_run_record` (lines 381–408) requires a **passing** record, not merely a recorded run; output in §3 |
| A12 | The gate runner and the hash authoring half (R2) | `keelcheck/gate.py`, 10117 bytes, 251 lines | on disk, committed, runs | `gate run` executes `kind: gate` rows only; `gate hash` prints the hash over git-normalized bytes (D9) |
| A13 | The run record and the reviewer's input | `keelcheck/record.py`, 5861 bytes, 155 lines | on disk, committed | the record's real content in §2 |
| A14 | Git-normalized hashing (D9), git plumbing | `keelcheck/normalize.py` 10865 B / 281 L, `gitcmd.py` 4488 B / 127 L | on disk, committed | `gate hash` matches the gate table |
| A15 | The clean-context review half (R3, R4, D15, D21) | `keelcheck/review.py` 29045 B / 682 L, `export.py` 14043 B / 328 L, `review-prompt.md` 2661 B / 58 L | on disk, committed, runs | `keelcheck review --help` exit 0; the prompt is gate row 1; **was:** 19353 B / 9598 B / 2656 B, with a different prompt hash |
| A16 | The git hook installer (R5) | `keelcheck/hook.py`, 11269 bytes, 258 lines | on disk, committed, runs | `hook install` / `hook status`; the installed hook carries the marker **`# keelcheck-hook v1`** (`keelcheck/hook.py` line 40), which is how a second install recognises its own work; the R5 tests still skip on this host (git's `sh`) |
| A17 | The CLI surface (R6) | `keelcheck/cli.py`, 2347 bytes, 68 lines | on disk, committed | `keelcheck --help` exit 0 — **eight** commands as of `35a2758`, including `mcp` |
| A18 | The ratified gate table | `CHARTER.md` lines 112–116 — **three rows at `501a404`**: `review-prompt` → `review-prompt.md` → `sha256:0e4b5764…` (`kind: prompt`); `suite` → `tools/coverage.py` → `sha256:973d639a…` (`kind: gate`); `reviewer` → `tests/_artefacts/claude-reviewer.py` → `sha256:8d5e6a5e…` (`kind: reviewer`) | on disk, committed, **3 ratified (1 executable)** at the anchor `501a404` (charter naming `62dc6be`) | `keelcheck audit`: `gates ratified: 3 (1 executable)`, `DIVERGENCES: none` at `35a2758`; **was:** two rows at `688fce8` (`90df6ebc…`, `c0b4c4ca…`) |
| A19 | Research and design notes | `research/`: `prior-art-join.md` 29336 B, `gates-per-harness.md` 28878 B, `review-attack.md` 19379 B, `drift-review-design.md` 18863 B, `name-keel.md` 13835 B, `name-shortlist.md` 10081 B, `gap-review-half.md` 5496 B | on disk, committed, **inside the repo** | `git ls-files research/`; `gates-per-harness.md` moved in from the workspace root (the D6 corollary) |
| A20 | MCP surface (R5's third, R6's bound) | `keelcheck/mcp.py` — **landed 2026-10-16** (`17e58ba`, then `35a2758`), plus `tests/test_mcp_surface.py` (13 tests, 292 lines) | on disk, committed, runs | `printf '{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n' \| python -m keelcheck mcp`; JSON-RPC 2.0 over stdio, one object per line, only `audit` exposed as a tool; module coverage **95.4%** (104/109) at `35a2758`; tests are Mason's and are queued for Proctor's verification |
| A21 | Tests | `tests/`: **11** `test_*.py` (largest `test_review_cli.py` 42966 B / 831 L, `test_audit_cli.py` 27054 B / 552 L, `test_hook_cli.py` 23275 B / 491 L), plus `_support.py`, `conftest.py`, `_scratch.py`, `CONTRACT.md` 15951 B, `_artefacts/` | on disk, committed; **green verified outside the worktree** | `PROJECT-STATE.md` lines 56–58: at `866912b`, clean worktree, **106 passed, 1 skipped, 0 failed in 4:34**. `test_review_cli.py` is modified at this stamp, so a run now measures a dirty tree |
| A22 | Coverage tool (R8) | `tools/coverage.py`, 17747 bytes, 354 lines, plus `tools/_child_trace.py` 3562 B / 81 L | on disk, committed, ratified as the `suite` gate | **was missing.** Floor **0.83** from the first honest measurement, 2031/2419, rounded down (`PROJECT-STATE.md` lines 584–589); the child tracer is driven by `KEELCHECK_COVERAGE_CHILD`, `KEELCHECK_COVERAGE_DIR` and `KEELCHECK_COVERAGE_PACKAGE`, and a blind measurement is exit 2 rather than a number |
| A23 | Packaging | `pyproject.toml`, 2151 bytes, 46 lines | on disk, committed, **never installed** | entry point `keelcheck = "keelcheck.cli:main"`; **was** 795 B / 28 L |
| A24 | README and this map | `README.md` (13212 B / 199 L before this rewrite) and `docs/ARTEFACT-MAP.md` (17198 B / 169 L before this rewrite) | on disk, tracked | neither revised size is asserted |
| A25 | A git remote | `.git/config` | **none configured** | `git remote -v` prints nothing; R9 keeps publishing a human check |

## 2. The record, and the demonstration's inputs

`.keel/runs.jsonl` (5805 B, **6 lines when I copied it** — it grew to 8 while I read it, another run
is writing to it): header, **three `gate` lines and two `audit` lines**; a later read of the same file
shows **four** audit lines. The gate lines are the stable part:

| line | kind | commit | anchor | result |
|---|---|---|---|---|
| 1 | header | — | — | record root `keelcheck/runs`, version 1 |
| 2–4 | `gate` × 3, all `suite`, all at the ratified hash `sha256:c0b4c4ca…` | `041689b`, `b924d19`, `2ac1aec` | — | **two `fail` (exit 1), one `timeout` (exit null)** — **the suite gate has never passed** |
| 5+ | `audit` | `52ae3da5`, `e1a4f10a`, `16d9bcd2`, `ec879771` | `688fce8` | exit 1, two gates |

**No `kind: "review"` line exists in this record**, so `keelcheck audit .` prints `REVIEW (clean context,
R4): missing` on the project's own repository. The R7 drift reviews that ran were recorded into the held
assays under `tests/_artefacts/`, not here.

| quantity | file / revision | status | source |
|---|---|---|---|
| The demonstration repository | `rentguard/`, HEAD `449a339`, 106 commits, one modified file (`tests/_artefacts/missing_lines_2026-10-14.txt`) | on disk | `git -C rentguard log/status`; **was** `eef6bdb`, 82 commits |
| rentguard's frozen original, R1–R10, W1–W4 | `rentguard/CHARTER.md`, 5821 bytes, 91 lines; frozen original **539 bytes** sha256 `0e96174d…` | on disk, committed; not auditable — **no `Ratified at:` line** | `keelcheck charter ../rentguard/CHARTER.md` → 5/6 sections, 10 requirements, 0 gates, 3 wishes, **exit 1** |
| The numbers rentguard's charter pins | `rentguard/CHARTER.md` line 30 (*"Re-measured at `74b9f7a` (clean worktree, 189 passed / 0 failed, 45 subtests…)"*), coverage floor 90.2% line 44 | pinned revision exists | **quoted, not re-measured** |
| The revisions R7 names, and the fixes they precede | `CHARTER.md` line 101: `bd63920`, `ce69cea`, `c512125`, `310f449`; D7 pairs them with `590c58e`, `d5fdaea`, `da51005` | all seven exist in `rentguard` and are ancestors of its HEAD | `git cat-file -t`, `git merge-base --is-ancestor` |
| The by-hand catalogue | one catalogue, **all six names, the merge stated** (D11 F6, lines 278–287): R2; **R4 and W4 as one finding in two stages**; W1 (R9); W2 (R8); W3 | ruled | rentguard's own W4 (lines 67–74) is the authority for the merge |
| **R7's result, both halves** | mechanical: `tests/_artefacts/R7-demonstration-mechanical-2026-10-14.md`; drift: the four assays `assay_r7_drift_*.json`; summary `PROJECT-STATE.md` lines 593–597 | **run** | **drift names 2 of the 5 at each of the three pre-fix revisions and none at the current state; mechanical gives identical divergence lists at `bd63920` and `310f449` and names the five only as state classes, with W4 and W3 invisible to it** |

## 3. What runs today — measured inside the window above; each run names the commit it read

```
python -m keelcheck --help                        # exit 0 — charter, audit, gate run/hash, review, hook install/status
python -m keelcheck charter CHARTER.md            # exit 0 — 6/6, 9 requirements, 2 gates, anchor 688fce8, 0 wishes
python -m keelcheck charter ../rentguard/CHARTER.md    # exit 1 — 5/6, 10 requirements, 0 gates, 3 wishes
python -m keelcheck audit . --record <copy>       # exit 1 — one divergence, plus REVIEW missing
python -m keelcheck audit ../rentguard --record <tmp>  # exit 2 — not auditable
python -m keelcheck gate hash keelcheck/cli.py    # exit 0
```

| input | what the run reports |
|---|---|
| `charter CHARTER.md` | 6/6 sections, 9 requirements, 2 gates declared, `ratified at: 688fce8`, 0 wishes, 3 human checks, 0 asserted enforcement, frozen original 553 B `376f11a4…` |
| `charter ../rentguard/CHARTER.md` | **exit 1** — 5/6 (`problems` missing), 3 wishes, 2 asserted-enforcement cells (R5, R9), and both disagreements named: R9 declared a wish the rule does not see, R2 and R4 wishes by the rule that are not declared |
| `audit .` against a copy of the repo's own record | **exit 1** — one divergence: `[gate-record] suite: the recorded run of this gate did not pass (result: fail, timeout)`; and `REVIEW (clean context, R4): missing`. **The vacuity line is gone** — 2 gates ratified, 1 executable |
| `audit ../rentguard` | **exit 2** — `[missing-section] problems`, `[vacuity] gates`, `NOT AUDITABLE: the charter names no ratification commit`, `REVIEW … missing`. It was **exit 1** at the previous map stamp (F11) |

The audit writes its record even when the run fails (D8/A3). The record's own content is §2.

## 4. Findings, each with the file it lives in

**F1 — the audit did not exist. Closed** at `2006f46`.

**F2 — the hash half was vacuous. Closed.** Two gates are now ratified, one of them executable
(`suite`), so the `[vacuity]` line has nothing left to report. The single divergence on keelcheck's own
repository is now `[gate-record]`.

**F3 — the demonstration input moves; ruled by D11 F3.** rentguard went 82 → 106 commits during
2026-10-15 and carries one modified file. D11 rules that **no input is ever named by a moving
reference**: the demo names the four revisions in R7's cell, and later rentguard commits change nothing.
Its `CHARTER.md` is still the 5821-byte file the snapshot holds.

**F4 — collection from the repository root: measured, then unreproduced, then closed structurally.**
Measured at `b81c374`: two mode-0700 `pytest-cache-files-*` directories at the root and
`python -m pytest -q` → **2 collection errors, exit 2**. D11 F4 recorded it **unreproduced** — the
directories were gone and **34 tests collected, exit 0** — and an earlier revision of this page wrongly
restated the failure as current. Closed at `33720dc`, which put the rule in the config file
(`testpaths = ["tests"]`, `norecursedirs` including `pytest-cache-files-*`; `af85c71` touched the file
again for the coverage gate), pinned by
`tests/test_suite_config.py::test_a_stray_pytest_cache_directory_cannot_break_collection`. Re-measured at
this stamp with roughly ninety cache directories present: **plain `pytest --collect-only -q` → 122 tests
collected, exit 0**. The litter is not a gate off.

**F5 — the untracked docs. Closed** at `ec18e0c`.

**F6 — the five by-hand defects were two lists. Ruled by D11 F6** (lines 278–287): one catalogue with
**all six names**. Both earlier lists had each dropped a name, R4 and W2 respectively.

**F7 — counting caution. Ruled by D11 F7.** Counts on this page come from newline bytes with Python.

**F8 — a citation resolving outside its repository. Closed** at `0914eb1`; the research lane moved
inside the repo the same way (`c8778b4`), so A19 now resolves.

**F9 — the anchor covered less than its record said. Closed** (`2006f46`): the block is the whole
section, 553 bytes, printed beside its length.

**F10 — `[anchor-moved]` and `[unbuilt]` were ruled but not in the code. Closed** at `fa6fb87`.

**F11 — a charter with no `Ratified at:` line exited 1 where D12 says exit 2. Closed.** Measured at
rentguard `449a339`: `NOT AUDITABLE`, and **exit 2**, even with a missing section and vacuity present.
**Was:** exit 1 at `eef6bdb`; the collision is gone.

**F12 — the review half has run, but not into this repository's record. Half closed.** R7's three
pre-fix reviews ran and are held as assays (D7's pair; §2, R7's result), and the drift half names 2 of
the 5 by-hand defects at each pre-fix revision and none at the current state. But `.keel/runs.jsonl`
carries **no `kind: "review"` line**, so the project's own audit still reports `REVIEW … missing` about
itself. That is honest rather than wrong — the R7 reviews were recorded elsewhere — and it is the reason
`REVIEW: missing` appears on both §3 runs.

**F13 — a prompt row cannot defeat vacuity. Closed** by the `suite` gate.

**F14 — the suite gate has never passed. CLOSED 2026-10-16.** Was: `.keel/runs.jsonl` held three `suite`
runs at the ratified hash — two `fail` and one `timeout` (`2ac1aec`, 19:50Z) — which is why `8f6f8ed`
raised the gate's timeout 600 → 1800 s and titled it *a bound against a hang, not against slowness*.
**Closed by the milestone run at `35a2758`:** `gate suite: pass exit 0`, `TOTAL 2594 2210 85.2%` against
the floor 0.83, recorded under the ratified `suite` hash `sha256:973d639a…` (`.keel/runs.jsonl`
`07:03:17Z`), with two audits at **zero divergences** after it. `_check_run_record`
(`keelcheck/audit.py` lines 381–408) requires a **pass**, and it now has one.

**F15 — a scratch directory is sitting untracked in the repository root.** `?? .assay-tmp/` — **eight
files** at this stamp (`colon_diagnosis.py`, `commit-msg.txt`, `commit-msg2.txt`,
`hookgate-escalated.ps1`, `hookgate.json`, `hookprobe.json`, `preproc_hook_import.py`, `suite.log`) — is
visible in `git status` and is not covered by `.gitignore`, which does carry `pytest-cache-files-*/`.
Named, not patched: `tests/` and the package are not my files.

**F16 — R5's third surface is absent while the record calls it taken. CLOSED 2026-10-16.** Was: the
record named the MCP surface as the next item with reds first while no `mcp` string existed in any
`keelcheck/*.py` and there was no `tests/test_mcp*` — a mid-flight state, named because R5's order
(hook, CLI, MCP, adapter) had its first two and neither of its last two. **Closed by `17e58ba` +
`35a2758`:** `keelcheck/mcp.py` exists, `python -m keelcheck --help` lists `mcp` among eight commands,
and `tests/test_mcp_surface.py` (13 tests) covers it to **95.4%**. R5's fourth item — the harness
adapter — remains **not due and not built**, which is the order's own last position, not a gap.

**F17 — R6's `enforced-by` cell is prose while the mechanism is now checkable.** R6 reads *"No daemon
and no server: a bounded CLI run, and an MCP call that returns"* with `enforced-by: code: no long-lived
process, no listening socket` — a sentence, not an artefact. Mason's `tests/test_mcp_surface.py` now
holds the check itself: one behavioural test that a session ends at EOF (a surface that outlived its
stdin would fail by timeout rather than pass quietly) and one source-level test that asserts no
`socket`, `listen`, `bind`, `socketserver` or `http.server` in `keelcheck/mcp.py`. So the cell could
name `tests/test_mcp_surface.py` — **and that is a charter edit, which is a re-ratification (R2), not a
code change.** Named, not done: the milestone is closed and a re-ratification for a cell's wording is
Max's call to spend, not a lane's.

## 5. Not covered here

- Whether a **stranger** would find it useful — W1 in `CHARTER.md` lines 125–127; neither this map
  nor the README has a mechanism for it.
- The review half's prior-context and deliberate-escape residuals, named rather than closed in
  `PROJECT-STATE.md` lines 607–609.
- Everything in the wider workspace that is not keelcheck (`parked/`, `paper/`, `grok/`, `gpu/`, …).
