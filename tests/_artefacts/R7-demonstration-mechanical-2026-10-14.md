# R7 — the rentguard demonstration, run mechanically and by drift review

**Tool:** `keel@b81c374` for the parser half (column 1 below); the drift half ran on `keelcheck` at the
revisions named in each row. The parser snapshot is unchanged since `489f47d` and was measured through
a detached worktree, so the answers are the landed parser's, not a working tree's.
**Input:** `rentguard/CHARTER.md` at `rentguard@a72e7c4`; the byte-identical snapshot
`rentguard-CHARTER-a72e7c4.md` beside this file is what was parsed, and the live file still matches it.
**Raw output:** `assay_rentguard_parser_b81c374.txt` / `.json`; the drift documents are
`assay_r7_drift_one_call_2026-10-16.json` (current state `310f449`), `assay_r7_drift_pre_bd63920.json`,
`assay_r7_drift_pre_ce69cea.json`, `assay_r7_drift_pre_c512125.json`.
**Re-recorded 2026-10-16** at the user's word (*"out and rerecord"*), to take the author's machine out of
the evidence: each of the four was run again against a **cleaned copy** of the same revision (local paths
elided to `<workspace>`, the two UTF-16 capture logs removed), and the copies are named in §3. The
recorder is `r7-pre-fix-reviews.py` for the three pre-fix revisions. **Every number in this file below is
the re-recording's**; the 2026-10-14/15 figures are kept in §5 as history rather than deleted, and the
finding they support — 2 of the 5 by-hand defects named at the pre-fix revisions, none at three of them,
R7 not met as written — is **the same on both recordings**.
**Typo repair, stated rather than quietly done (2026-10-15):** the earlier revision of this file had
lost the leading `b` of `bd63920`, the `a` of `assay_…` and similar at several places, in prose that was
never re-read. They are repaired here; no measurement and no claim changed, and the JSON beside this
file is the evidence for every number below.

## 1. What the parser half finds

| finding | value |
|---|---|
| requirements parsed | 10 |
| wishes by the R1 rule (neither cell) | **R2, R4, R8** (3) |
| `enforced-by` cells that name no artefact | **R5, R9** (2) |
| state column says wish, the rule does not | R9 (1) |
| the rule says wish, the state does not | R2, R4 (2) |
| required sections | **5/6 — `problems` missing** |
| gate content hashes declared in the charter | **0** |

Two things this run finds that the by-hand audit did not list: rentguard's charter is **5/6** (no
`problems` section — D4 keeps it as the finding rather than patching the input), and R5's `enforced-by`
is **evidence, not a mechanism** ("3 rentals, $0.0264" is a past event; nothing checks that the
end-to-end proof still holds).

## 2. The mechanical pair, both ends (D7)

The divergence list is **identical** at `bd63920` and at `310f449` — `[missing-section] problems` and
`[vacuity] gates`, with `NOT AUDITABLE` and exit **2**. It names none of the five by-hand defects,
because rentguard's charter declares **zero ratified gates**: a hash-checking audit on that input
verifies nothing, and "a named gate has no run record" never fires because no gate is named. That
vacuity is itself a named divergence (exit 1) — which is why
`test_a_charter_with_zero_ratified_gates_is_a_named_finding_not_a_clean_run` exists: otherwise the
demonstration input is the first place the tool lies.

The reports are **not** byte-identical: the living state differs (asserted enforcement 3 → 2, and R2,
R5, R6, R10 change state and cells). The mechanical half *sees the state move* and names none of it as
divergence.

**The deployment trap, recorded because it costs a demo:** `git archive` then extract gives
`CANNOT RUN HONESTLY: git cannot name HEAD: … not a git repository` and exit 2 — the audit needs a real
repository at the revision. `git worktree add --detach <dir> <rev>` works here; `git clone` does not
(it spawns `sh`).

## 3. The drift half, four runs

One `claude -p` call each, foreground, in its own detached worktree, `--record` outside every read-only
tree, prompt via `--prompt-repo keel`. Every run: `history_reachable: unknown`, `unverified: 0`,
verdict `divergence`, exit 1.

| revision | when | seconds | anchor (UTC) | files seen/total | verified | missing / unrequested / shifted | named of the five |
|---|---|---|---|---|---|---|---|
| `310f449` (current state) | 2026-10-16 | 209.0 | — | 69/69 | 13 | 4 / 3 / 6 | **1 as a different MCP item, 1 partly** |
| `bd63920` (pre-fix) | 2026-10-16 | 127.7 | 09:42:23 | 46/46 | 10 | 2 / 2 / 6 | **2** |
| `ce69cea` (pre-fix) | 2026-10-16 | 142.9 | 09:44:47 | 45/45 | 12 | 3 / 2 / 7 | **2** |
| `c512125` (pre-fix) | 2026-10-16 | 258.8 | 09:49:06 | 54/54 | 10 | 2 / 2 / 6 | **0 (both are fixed by then)** |

**The copies the four runs reviewed, named so a reader can tell them from the revisions themselves:**
`310f449` → copy `abb95cedef`, `bd63920` → `d812cd3e80`, `ce69cea` → `c5d24cfe15`, `c512125` →
`e88777b6a4`. Each is that revision with the two UTF-16 captures removed and three local paths in
`docs/VERIFICATION.md` elided to `<workspace>`; nothing else was touched, and the file counts above are
the cleaned copies' (`48/48` → `46/46` at `bd63920`, `47/47` → `45/45` at `ce69cea`, `56/56` → `54/54` at
`c512125`).

The reviewer declared its own limits with each run — no suite executed, no git metadata,
`history_reachable: unknown` because the export is provably `.git`-less while the reviewer's own loaded
context is not observable. That is the honesty the design asked for, and it is why "no unverified"
means "nothing asserted without evidence it could see", not "the tree has no other problem".

## 4. R7's per-half table — the finding

Requirement as written: the audit reproduces the five by-hand defects, each attributed to the half that
finds it. **Measured: it does not.** The readiest honest sentence is the table.

| # | by-hand defect (human) | parser half | drift, current state (`310f449`) | drift, pre-fix (`bd63920` / `ce69cea` / `c512125`) |
|---|---|---|---|---|
| 1 | no way to arm the guard over MCP | **symptom only** — R2 is a wish whose state says `met` | not named as that defect; a *different* MCP item was named (`[shifted] watch / MCP rentguard_watch: the stopped field`) | **named at `bd63920`**: `[missing] MCP surface: watch and init tools` — "a Bot that rents through MCP cannot start the guard that enforces the cap". **Named at `ce69cea`**: `[missing] MCP tools for watch and init` — "without watch, a Bot can rent through MCP but cannot start the guard". **Not named at `c512125`** — it names the *documentation* as shifted ("mcp_server.py advertises eleven tools including rentguard_watch, docs stale"), which is the fix having landed |
| 2 | the guard could stop a healthy pod | **missed** — R4 reads `NOT MET`, honest about the gap, silent about the behaviour | partly: `[missing] guard.watch stop path (hardening of a money-critical path)` and the frozen original's end-to-end proof, both as gaps rather than as the defect | **named at `bd63920`**: `[shifted] guard idle rule (guard.watch / Snapshot.effective_idle_minutes)` — "watch() passes wall-clock time since the guard started as `idle_since_start_minutes` whatever the GPU utilisation … any watched pod, even a busy one, is stopped as 'idle'". **Named at `ce69cea`**: `[missing] A fix, with a test, for the guard's idle-clamp defect (F-5)` — "a pod 32 seconds old can be stopped as idle, and no test covers it". **Not named at `c512125`** — F-5 appears only as a stale open defect in the docs, because the clamp is in the code by then |
| 3 | the cap exists only while `watch` runs | **found as a state class** — R9's `enforced-by` is prose and its state says wish | not named | **not named at any of the three.** Closest is `bd63920`'s `[missing] End-to-end proof of the guard (watch) on a real rented GPU` — a different claim ("never proven on a real billing machine", not "the cap stops when `watch` exits") |
| 4 | no technical lock on publishing | **found as a state class** — R8 has neither cell → wish | not named as a mechanism; publication itself is `unreviewed` | **not named at any of the three.** `ce69cea` and `c512125` put the act out of reach in `unreviewed` — "no git remote or history to check" — and what they name is the *readiness claim* exceeding the tree (`[shifted] Release-readiness status`, `[shifted] publish readiness claim`). A too-high claim, not the absent lock |
| 5 | the volume path unexercised | **missed** — prose in the wishes section, no requirement row | not named | **not named at any of the three.** `ce69cea`'s `[shifted] Quickstart configuration guidance` names `volume_name` vs `volume_id` (a config-doc divergence) and `c512125`'s `[shifted] docs/KNOWN-FAILURES.md` notes "volumes in doctor" as an implemented remedy — neither is the unexercised path |

**Score, stated the way the numbers read:** the parser half carries three of the five as *state classes*
(R2, R8, R9) and none as divergence; the drift half names **2 of 5** at the pre-fix revisions, where the
defect *is* the state, and 3 of 5 not at all, at any revision. At the current state it names at most one
cleanly (and as a different MCP defect) and one partly.

**R7 is NOT MET as written.** That is the finding, and it is not softened here or anywhere else: the
claim was not met, and the attempt to test it further is what produced the numbers above. The reason is
structural, not a reviewer failure — the five are partly *history* (by the later revisions two had been
fixed, so a reviewer of that state can only see their absence as stale docs), partly **behaviour no
requirement row encodes** (W4: every line of the defect executed and the coverage floor still stood), and
partly **prose with no row** (W3, W2). A gate catches that class only after a human conceives the
scenario; the audit can never generate the scenario.

**The pre-commitments held.** No run was re-cut because it named fewer than five; every finding above is
quoted to the revision it came from; and a failed call is recorded as a failed call, not as a small
number (see §5).

## 5. The pre-fix runs that failed, and why the column read *not measured*

The first attempt ran all three pre-fix revisions in one background job and **all three failed at the
reviewer** (exit 2, "no JSON object in the reviewer's output (exit 1)"). Keel recorded an **error with no
verdict and no fabricated findings**, so the drift column read *not measured* at those revisions — a
failed call is not a small number. Cause, diagnosed rather than guessed: the identical command in the
**foreground** at `bd63920` succeeded (exit 1, 187 s), so it was the background context. Two further
harness faults, both mine and both fixed before the released runs:

- the wrapper discarded claude's stderr, so a failure gave no reason; it now prints the reviewer's
  stderr tail and stdout tail;
- the first released attempt passed a **minimal** environment and `claude.exe` (a Bun binary) died in 5 s
  with `The %SystemRoot% environment variable is not set` — a failure with no reviewer call made is a
  harness fault and must not be recorded as a reviewer fault. One retry with the whole environment: 189 s
  and 198 s, both clean.

**The 2026-10-16 re-record hit the same fault again, which is why it is written down twice.** The fix
above had been applied to the *run*, not to the script: `r7-pre-fix-reviews.py` still passed
`env={"PYTHONIOENCODING": …, "PATH": …}`, so the first re-record attempt produced three artefacts whose
whole content was `exit: 2` and claude's `%SystemRoot%` sentence. Nothing was kept from that attempt —
the files were overwritten by the run that worked — and the script now passes the parent's environment
with the encoding pinned, with the reason in a comment beside it. **A harness fault that is fixed only in
the transcript comes back the next time the transcript is not read.**

**What the re-record changed, and what it did not.** Changed: the numbers in §3 (they are the new runs'),
the file counts (the cleaned copies carry two fewer each), and the quoted subjects in §4, which the
reviewer worded differently — `ce69cea` now names the idle clamp as `[missing]` rather than `[shifted]`,
which is a sharper version of the same finding. Not changed: **2 of 5 at each pre-fix revision, 0 at
`c512125`, and R7 not met as written** — the earlier recording, at `310f449` 241 s / `bd63920` 187 s /
`ce69cea` 189 s / `c512125` 198 s with 14/12/14/12 verified items, supports the same sentence, and the
older artefacts were not kept because they carry the author's machine in the provenance fields they
record.

## 6. What a mechanical half can and cannot carry (unchanged)

Can carry, because it is all declarative: a requirement naming neither a mechanism nor a check; an
`enforced-by` cell that is prose rather than an artefact; a state column disagreeing with the rule in
either direction; a required section missing; a ratified gate whose content hash changed or that has no
run record; zero ratified gates at all (vacuity); the frozen block edited; the ratification pointer
disagreeing with the record. Cannot carry: behaviour no row encodes (W4); prose with no row (W3); and
whether a declared gate is *sufficient* — v1 checks that a gate ran and its hash is intact, so a gate
that runs, passes and measures the wrong thing is green.

## 7. Findings beyond R7's five, routed rather than evaporated

The twelve from the current-state run went to Scribe (documentation contradictions, stale R3/R10 states,
`KNOWN-FAILURES.md` listing fixed defects, missing install evidence at the release pin, the probes in the
release tree) and to Gilbert (the ~$2.14 the reported budget excludes, the third rental with no record in
the tree). The pre-fix runs repeat most of those and add:

- `runpod.py` hard-codes `UserKnownHostsFile=NUL` on **every** OS while `cli.py` only substitutes a
  `{null}` placeholder that is never present, so Linux and macOS get a file named `NUL` — and
  `docs/limitations.md` says NUL is a Windows thing (`bd63920`, `ce69cea`, `c512125` all name it);
- `docs/fake.md`'s "real output" contains lines the printed script cannot produce (`ce69cea`,
  `c512125` stale-quickstart item is the same class);
- `tests/conftest.py` globally monkeypatches `shutil.rmtree`/`tempfile.mkdtemp` and writes scratch
  outside the checkout, tying a release-bound suite to this Bot workspace (`c512125`);
- the R10 coverage figure disagrees between `tools/coverage.py` (`0.89` measured) and `CHARTER.md` R10
  (`74.8%`) (`c512125`).

These are findings about rentguard, not about R7, and none of them is one of the five.
