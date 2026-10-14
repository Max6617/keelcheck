# R7 — the rentguard demonstration, run mechanically

**Tool:** `keel@fbd9837` (working tree; the audit does not exist yet, so this is the parser stage only).
**Input:** `rentguard/CHARTER.md`, source `rentguard@a72e7c4`; unchanged at `rentguard@310f449`
(clean tree) — the snapshot `rentguard-CHARTER-a72e7c4.md` beside this file is byte-identical
(SHA-256 `046FA7D9…7C4C`).
**Command:** `python -m keel.charter rentguard/CHARTER.md` (and `--json`). Raw output:
`assay_rentguard_parser_489f47d.txt`, `.json` — the parser is unchanged between `489f47d` and
`fbd9837`, but the counts are named against **fbd9837** because that is the tree they were run in.

## What the run finds

| finding | value |
|---|---|
| requirements parsed | 10 |
| wishes by the R1 rule (neither cell) | **R2, R4, R8** (3) |
| `enforced-by` cells that name no artefact | **R5, R9** (2) |
| state column says wish, the rule does not | R9 (1) |
| the rule says wish, the state does not | R2, R4 (2) |
| required sections | **5/6 — `problems` missing** |
| gate content hashes declared in the charter | **0** |

## Against the five defects the by-hand audit found

| # | by-hand defect | mechanical run at fbd9837 | honest read |
|---|---|---|---|
| 1 | no way to arm the guard over MCP | **found, as a symptom** — R2 is a wish *whose state says `met`*: a met claim with nothing behind it. The run cannot see *why* the MCP surface was incomplete. | a human still has to check the surface |
| 2 | a guard that could stop a healthy pod (W4) | **missed** | it lives in code; no row states it. R4 says `NOT MET`, which is honest about the gap and silent about the guard being wrong |
| 3 | the cap exists only while `watch` runs (W1) | **found** — R9 is both `asserted_enforcement` ("only while \`watch\` runs") and `declared_wish_not_wish` | the closest mechanical match to the human reading |
| 4 | no technical lock on publishing (W2) | **found** — R8 has neither cell → wish | |
| 5 | the volume path was unexercised (W3) | **missed** | prose in the wishes section, no requirement row; a requirements-table audit never sees it |

Score at fbd9837: **2 clear (R8, R9), 1 symptomatic (R2), 2 missed (W4, W3).**

## The miss is the finding

The audit sees the charter about itself, and the two defects that cost money or data resolve in
**code**, not in the charter. D7 already answers this properly — two revisions, one pair of runs:
the revision immediately before each fix must report the defect as divergence, and `310f449` must
report only what is still open. That half cannot run at fbd9837: there is no audit and **rentguard's
charter declares zero gates**, so there is nothing executable for it to run at `bd63920`, `ce69cea`
or `c512125`.

That is the sharp edge: R7's reachable half is exactly the gate layer (R2) that is not built. Until
a gate exists that can execute code and be hashed, "reproduce the defects that were found by hand"
reduces to reading back the charter's prose — the failure the project exists to catch.

## Two things this run finds that the by-hand audit did not list

- rentguard is **5/6**: no `problems` section. D4 keeps it as the finding rather than patching the
  input (`keel/CHARTER.md` now has the section; rentguard's charter stays as it was measured).
- R5's `enforced-by` is **evidence, not a mechanism**: "3 rentals, $0.0264" is a past event. The
  parser classes it as asserted enforcement; nothing checks that the end-to-end proof still holds.

## The vacuous pass waiting on this input

With **0** gates declared, a hash-checking audit on rentguard verifies nothing, and "a named gate has
no run record" (D3, exit 1) never fires because no gate is named. An audit that exits 0 there would
be reporting health it never measured. This is the third adversarial property — success when a gate
was skipped, absent, or never ran — standing on the project's own demonstration input.
