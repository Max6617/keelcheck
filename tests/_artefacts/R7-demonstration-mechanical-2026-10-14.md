# R7 — the rentguard demonstration, run mechanically and by drift review

**Tool:** `keel@b81c374` for the parser half (column 1 below); the drift half ran on `keelcheck` at the
revisions named in each row. The parser snapshot is unchanged since `489f47d` and was measured through
a detached worktree, so the answers are the landed parser's, not a working tree's.
**Input:** `rentguard/CHARTER.md` at `rentguard@a72e7c4`; the byte-identical snapshot
`rentguard-CHARTER-a72e7c4.md` beside this file is what was parsed, and the live file still matches it.
**Raw output:** `assay_rentguard_parser_b81c374.txt` / `.json`; the drift documents are
`assay_r7_drift_one_call_2026-10-14.json` (current state `310f449`), `assay_r7_drift_pre_bd63920.json`,
`assay_r7_drift_pre_ce69cea.json`, `assay_r7_drift_pre_c512125.json`.
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
| `310f449` (current state) | 2026-10-14 | 241 | — | 71/71 | 14 | 3 / 3 / 8 | **1 cleanly, 1 partly** |
| `bd63920` (pre-fix) | 2026-10-14 | 187 | 21:32:52 | 48/48 | 12 | 2 / 2 / 8 | **2** |
| `ce69cea` (pre-fix) | 2026-10-15 | 189 | 19:57:55 | 47/47 | 14 | 1 / 3 / 10 | **2** |
| `c512125` (pre-fix) | 2026-10-15 | 198 | 20:01:37 | 56/56 | 12 | 1 / 3 / 8 | **0 (both are fixed by then)** |

The reviewer declared its own limits with each run — no suite executed, no git metadata,
`history_reachable: unknown` because the export is provably `.git`-less while the reviewer's own loaded
context is not observable. That is the honesty the design asked for, and it is why "no unverified"
means "nothing asserted without evidence it could see", not "the tree has no other problem".

## 4. R7's per-half table — the finding

Requirement as written: the audit reproduces the five by-hand defects, each attributed to the half that
finds it. **Measured: it does not.** The readiest honest sentence is the table.

| # | by-hand defect (human) | parser half | drift, current state (`310f449`) | drift, pre-fix (`bd63920` / `ce69cea` / `c512125`) |
|---|---|---|---|---|
| 1 | no way to arm the guard over MCP | **symptom only** — R2 is a wish whose state says `met` | not named; a *different* MCP defect was named (`run`'s `command.split()`) | **named at `bd63920`**: `[missing] MCP surface: watch and init tools` — "a Bot can rent through MCP but cannot start the guard that enforces the cap". **Named at `ce69cea`** as a claim: `[shifted] CHANGELOG MCP claim` — "mcp_server.py exposes no watch tool and docs/mcp.md states watch is not exposed". **Not named at `c512125`** — it reports the opposite state ("mcp_server.py now advertises eleven tools including rentguard_watch", docs stale), which is the fix having landed |
| 2 | the guard could stop a healthy pod | **missed** — R4 reads `NOT MET`, honest about the gap, silent about the behaviour | partly: the R4 gap as unproven | **named at `bd63920`**: `[shifted] guard idle rule (idle_since_start_minutes)` — "with the default 10-minute window a busy machine gets stopped as 'idle' after about 10 minutes of watching". **Named at `ce69cea`**: `[missing] Money-critical guard path: idle-stop clamp (F-5)` — "a 32-second-old paid pod can be stopped". **Not named at `c512125`** — it lists F-5 only as a stale open defect in the docs, because the clamp is in the code by then |
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
