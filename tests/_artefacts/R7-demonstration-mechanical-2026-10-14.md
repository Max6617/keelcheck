# R7 — the rentguard demonstration, run mechanically

**Tool:** `keel@b81c374`. The parser is unchanged since `489f47d`, and this was measured through a
detached worktree at `b81c374`, so the answers are the landed parser's — not the working tree's
(Mason's R2 build was uncommitted at the time; `assay_suite_worktree-2026-10-14.txt` says so).
**Input:** `rentguard/CHARTER.md` at `rentguard@a72e7c4`; the byte-identical snapshot
`rentguard-CHARTER-a72e7c4.md` beside this file is what was parsed, and the live file still matches it.
**Command:** `python -m keel.charter <snapshot>` and `--json`. Raw output:
`assay_rentguard_parser_b81c374.txt` / `.json` (superseding the `489f47d` pair; the answers are the
same).

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

## The five defects a human found, against what a mechanical audit can see

Two questions per defect, not one: did the run find it, and **what would a mechanical detector have
needed in order to find it?** The second is the real limit of the first version, and it is the part a
README must not round off.

| # | by-hand defect (found by a human) | found at b81c374? | what a mechanical find would need | mechanisable in v1? |
|---|---|---|---|---|
| 1 | no way to arm the guard over MCP (rentguard R2) | **symptom only** — R2 is a wish whose state says `met`: a met claim with nothing behind it | a declared gate that calls the MCP arming path end to end and asserts the guard is armed; then `met` has a run record behind it | **yes, once such a gate is written** — the cell alone names nothing, so today only the symptom is visible |
| 2 | a guard that could stop a healthy pod (W4) | **missed** — R4 reads `NOT MET`, honest about the gap and silent about the behaviour | a scenario gate: a synthetic pod 32 seconds old, provider idle reported large, assert the guard does **not** stop it. Coverage cannot catch it — every line of the defect executed | **no** — the scenario has to be imagined before it can be gated; no requirement row encodes it. Drift review, not the mechanical half |
| 3 | the cap exists only while `watch` runs (W1) | **found** — R9's `enforced-by` is prose ("only while `watch` runs") and its state says wish | nothing more: the cell is the finding. A gate could only assert a cap that survives `watch`'s exit — which is the design W1 refuses | **yes, as written** (the cell). The missing supervisor is a design call, not a check |
| 4 | no technical lock on publishing (W2) | **found** — R8 has neither cell → wish | a gate that fails while a public remote or a publish path exists (a configuration control) | **yes, once such a gate is written**; today only the wish is visible, not the absence of the lock |
| 5 | the network-volume path unexercised (W3) | **missed** — prose in the wishes section, no requirement row | a gate that exercises `[runpod].volume_id` end to end (or at the transport seam), declared and hashed. After the volume was deleted there was nothing to attach | **no, and not only for lack of a volume** — a requirements-table audit never sees prose that has no row |

Score at b81c374: **2 clear (W2/R8, W1/R9), 1 symptomatic (R2), 2 not mechanically findable (W4, W3).**
The user's "five real defects" is not withdrawn: the audit is two halves by R3's own wording, and W4
and W3 belong to the drift-review half.

**Dated note, 2026-10-14 (D11/F6).** The table above carries five rows; the catalogue of record carries
**six names**, because rentguard's own W4 says in terms that it "is what R4's wish looked like once it
was tested". Row 2 is therefore one finding in two stages, and the six names are: **R2**; **R4 + W4**
(the guard unproven, then tested and wrong); **W1** (R9); **W2** (R8); **W3**. This note adds **R4**,
which this file's list had dropped; the record's list had dropped **W2** instead. Same count, different
membership — which is why both read as fine. No listing in this file may print five names again.

## The honest boundary of the first version

What the mechanical half can find — all of it **declarative**, i.e. written in the charter or in git:

- a requirement that names neither a mechanism nor a check (R1's wish);
- an `enforced-by` cell that is prose rather than an artefact (asserted enforcement);
- a state column that disagrees with the rule, in either direction;
- a required section missing;
- a ratified gate whose content hash changed, or a named gate with no run record;
- zero ratified gates at all (vacuity): an audit that verified nothing;
- the frozen-original block edited, or the ratification pointer disagreeing with the record.

What it **cannot** find, and why:

1. **Behaviour that no requirement row encodes.** W4 is the type specimen: the guard was wrong, every
   line of the defect executed, and the coverage floor still stood at 74.8%. A gate catches this only
   after a human conceives the scenario; the audit can never generate the scenario.
2. **Prose that is not a requirement row.** W3 lives in the wishes section. The parser reports the
   *requirements table*; a paragraph with no row in it is invisible to it.
3. **Whether a declared gate is sufficient.** v1 checks that a gate ran and that its hash is intact.
   A gate that runs, passes, and measures the wrong thing is green. rentguard's own R10 note is the
   proof: the money defects all sat in lines the coverage gate already counted.

The consequence for R7's claim: the mechanical half reproduces **three of five** — two clearly (R8,
R9) and one as a symptom (R2) — and the drift review is what the other two need. That is a narrower
sentence than "the audit found five defects", and it is the one the README has to earn.

## The miss is the finding

The audit sees the charter about itself, and the two defects that cost money or data resolve in
**code**, not in the charter. D7 already answers this properly — two revisions, one pair of runs:
the revision immediately before each fix must report the defect as divergence, and rentguard HEAD
must report only what is still open. That half cannot run yet: there is no audit, and **rentguard's
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
no run record" (D8, exit 1) never fires because no gate is named. An audit that exits 0 there would
be reporting health it never measured. D8 now makes that vacuity itself a named divergence and an
exit 1, which is why `test_a_charter_with_zero_ratified_gates_is_a_named_finding_not_a_clean_run`
exists in the adversarial set: otherwise the demonstration input is the first place the tool lies.

## One drift found while measuring

D7 pins the demonstration at rentguard HEAD `310f449`. The rentguard **code** repository has since
moved to `ad2e880`; `rentguard/CHARTER.md` itself is unchanged (the snapshot test in
`test_charter_silent_wish.py` still passes), so the demonstration input is intact. The D7 wording
"at rentguard HEAD `310f449`" is now stale and is flagged to Gilbert rather than edited here.

## R7's per-half table, measured by Proctor 2026-10-14 (ssay_r7_mechanical_two_revisions.txt)

Gilbert dry-ran the pair; I reproduced it before this write-up depends on it, and one of his two facts
needs stating more narrowly. **The divergence list is identical at d63920 and 310f449** —
[missing-section] problems and [vacuity] gates, with NOT AUDITABLE and exit 2 — and it names
none of the five by-hand defects. **The reports are not byte-identical**: the living-state section
differs, because the fixes landed between the revisions (asserted enforcement 3 → 2, and R2, R5, R6,
R10 change state and cells). So the mechanical half *sees the state move* and names none of it as
divergence.

| # | by-hand defect (human) | mechanical divergence | mechanical state class | drift review |
|---|---|---|---|---|
| 1 | no way to arm the guard over MCP (rentguard R2) | none | R2 is a wish at both revisions; at 310f449 its state says met with nothing behind it — the symptomatic reading, and it is not present at d63920, where R2 reads NOT MET honestly | to run |
| 2 | a guard that could stop a healthy pod (W4) | none | none: R4's row reads NOT MET at both, honest about the gap and silent about the behaviour | to run |
| 3 | the cap exists only while watch runs (W1) | none | R9 is sserted_enforcement **and** declared_wish_not_wish at both revisions: a condition wearing a mechanism's name | to run |
| 4 | no technical lock on publishing (W2) | none | R8 has neither cell at both revisions → wish | to run |
| 5 | the volume path unexercised (W3) | none | none: prose in the wishes section, no requirement row, so the requirements-table half never sees it | to run |

**What the mechanical half carries at those revisions**: problems (a missing section) and vacuity
(zero ratified gates) as divergences, and three of the five as *state classes* — R2, R8, R9 — of which
only R2's met claim is a lie rather than a stated gap. The problems finding and the vacuity finding
are not among the five; they are findings about rentguard's charter that the by-hand audit did not
list, which is what this note already recorded.

**What that means for the claim.** The two-revision pair does not discriminate by divergence class: the
demonstration cannot say "the audit reproduces the by-hand audit". It can say what the table says —
the mechanical half names the charter's own gaps (a missing section, no ratified gate, three wishes)
and the drift review is what must name the five, or the shortfall is the finding. No sentence here may
print five defects as mechanically found.
## R7 as written is NOT MET (recorded 2026-10-14, Gilbert's ruling 2)

The requirement claims the audit reproduces the by-hand defects with each attributed to the half that
finds it. Measured: **neither half reproduces the five.** The mechanical half carries rentguard's
charter gaps (problems, zero ratified gates, three wishes) and none of the five as divergence; the
drift review, run once on a faithful copy of 310f449, named at most one cleanly (R2's row, as a
*different* MCP defect — un's command.split() mangling) and one partly (W4 as an unproven gap
rather than a wrong guard), with two reachable but unnamed (publishing under unreviewed, the volume
deletion as *unrequested*) and three unnamed. **Not met as written.** The twelve extra findings the
review produced are routed to Scribe and to Gilbert, not softened here.

Also unrun at the time of writing: D7's **pre-fix** revisions (d63920, ce69cea, c512125) — the
five were still present there, which is where a clean-context reviewer can see the defect as the
state. One call each, queued.