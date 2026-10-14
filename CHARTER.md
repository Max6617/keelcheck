# Charter — keel (working name)

The one file a human reads. Drafted by an agent from the opening conversation on 2026-10-14, read and
**approved by the user** the same evening, in their words:

> wish 2 you can throw away but the ret is good

That was the only change asked for, and it was made **before** freezing — so the original below has never
been edited. From here it is frozen: later clarifications are appended as new requirements, never merged
into it. An anchor that quietly gets improved is not an anchor.

## The frozen original

The user's words, verbatim:

> okay yes lets go with your recommendation. launch and create bots for that project

And the recommendation those words accept, as written in `ECC-ASSESSMENT.md` before the decision:

> narrow to the join and build it — small, self-contained, git hook first and harness adapter last,
> exactly as the spec already orders it — and keep using rentguard as the demonstration, because we can
> then say the audit found five real defects on a real project rather than that it seems like a good idea.

## Ratification

Ratified at: `ae375c6` — the freeze commit, and the reference side of every comparison (D1, D8).

- **Gates ratified: none yet.** Until the first gate is declared and ratified the mechanical half of the
  audit reports *vacuous*, which is a divergence — an audit that verified nothing is not a clean run.

## What it is for

Two artefacts, one loop.

- **The charter** — one file per project: what it is for, what it is good at, the problems the human and
  the agent agreed on, the requirements, the permissions. Drafted by an agent from the opening
  conversation, approved by a human, then **frozen**.
- **The audit** — run at every milestone: the enforced checks first, then a drift review with **clean
  context**, then a two-minute report of the divergences and the wishes.

The problem it exists for: an instruction does not get forgotten, it gets **moved**. Through sub-agents,
summaries, compactions and rewrites each hop nudges it, and nothing ever compares the current state
against the original. The human notices at the end, if at all. **Prose is not enforcement.**

## What it is good at — and what it is not for

Good at: one small project, one human, any agent, with every requirement either naming the mechanism that
upholds it or being marked a **wish**. Not for: a spec-authoring suite, a memory or learning layer, a
harness of its own. Not a server, not a daemon, not a job runner.

## The problems the human and the agent agreed on

Added 2026-10-14, because R1's format names this section and the first parser run reported it missing from
this file and from `rentguard/CHARTER.md` — both 5/6. The finding was on us, which is the honest version of
the demo. What was agreed, in the opening conversation:

- An instruction is not forgotten, it is **moved** — through sub-agents, summaries, compactions and rewrites
  — and after a few hops nobody has it in the original words.
- Nothing in the loop compares the current state against the **original**; the human notices at the end, if
  at all.
- **Prose is not enforcement.** A rule written in a document that no mechanism upholds is a wish, and the
  difference must be visible in the file rather than in someone's judgement.
- The neighbours solve the opposite problem — ECC accumulates and evolves memory, Spec Kit keeps specs
  living — so the gap is the **join**: freeze once (human-approved), enforce by named mechanism, and audit
  divergence against the frozen original with a clean-context reviewer.

## Why this is the gap (checked against the neighbours, 2026-10-14)

- **ECC** (MIT, 17 harnesses) already ships enforcement — blocking hooks with exit codes, sandbox
  profiles, a fresh-context reviewer, an evidence trail — and its memory *accumulates and evolves*:
  instincts become skills, memories get promoted. Nothing in it freezes an original or audits against
  one.
- **Spec Kit** makes *living* specs first-class, which is the opposite of freezing.

So the claim is the join, and only the join: **one human-approved frozen original; requirements that name
their mechanism or are marked wishes; gates hashed so a model may propose one but never weaken one; an
audit that reports missing / unrequested / shifted.** The word "checkpoint" is taken and means
state-versus-state in ECC, so the audit is our word for our thing.

## Requirements

Every requirement carries how it is honoured. `enforced-by:` = a mechanism makes the violation
impossible, fatal or recoverable. `checked-by:` = a human judges it, or a demo makes the state visible.
**Neither = a wish**, and the wishes list is the audit's most valuable output.

| # | requirement | enforced-by | checked-by | state |
|---|---|---|---|---|
| R1 | The charter format is fixed: purpose, strengths, agreed problems, requirements, permissions, scopes; a requirement with neither `enforced-by` nor `checked-by` is a wish and the parser says so | code: the charter parser | — | draft |
| R2 | Gates are locked code: a gate is a script recorded in the charter with a content hash, and the audit fails when a hash differs from the ratified one | code: hash comparison | — | draft |
| R3 | The audit reports divergence from the frozen original in three classes — **missing / unrequested / shifted** — plus the wishes, readable in two minutes | code: the frozen-original block is diffed against `ae375c6`; the drift review (clean context) classifies the rest | the human reads it | draft |
| R4 | The drift review runs with **clean context**: a fresh agent holding only the frozen original and the current state, never the history that produced it | code: the runner writes the reviewer's inputs to `.keel/review-context.json` and the drift report names that file | — | draft |
| R5 | Integration surfaces in this order: git hook first, CLI second, MCP third, harness hook adapter last | code: the hook installer | — | draft |
| R6 | No daemon and no server: a bounded CLI run, and an MCP call that returns | code: no long-lived process, no listening socket | — | draft |
| R7 | The tool proves itself on **rentguard**: the audit — mechanical half plus clean-context drift review — names the five defects the by-hand audit found, each attributed to the half that finds it, and reports a gate-less input as **vacuous**, never clean | — | the audit run at `bd63920`, `ce69cea`, `c512125` and `310f449`, and the human reads the report | draft |
| R8 | 94% of the code and 100% of the surface exercised; one writer per file; every count names a commit; red tests before fixes | code: keel's coverage gate and the suite — **neither is built, so this is unbacked until they are** | the CI run | draft |
| R9 | Nothing is published without the user's explicit word | — | the user's explicit word before any push | checked, not enforced |

## The wishes

**Decision appended before freezing the states, 2026-10-14 (not part of the frozen original):** R2's
"ratified" hash is read from the **ratification commit**, not from the working-tree charter
(`git show <sha>:CHARTER.md`), and the audit reports a gate with no run record as missing. Ruling recorded
as D1 in `PROJECT-STATE.md`, this repository's record.

**W1 — "a stranger would find this useful" has no mechanism.** Adoption is the user's test of
impressive, and nothing here makes a stranger install it; only the demonstration does, and the
demonstration is one project long.

**W2 — clean context is asserted, not proved.** R4 says a fresh agent reviews the drift, and nothing
outside the runner can verify that the reviewer really had no history. The strongest available check is
that the runner records what it handed the reviewer.

**Struck before freezing, 2026-10-14, at the user's word:** the wish *"nothing is published is a promise,
not a lock"*. Publishing keel is the user's decision and they are content with that; it is a human check,
so it belongs in R9 as `checked-by` rather than as a wish, and the "no remote configured" observation went
with it. A wish removed on purpose leaves that trace rather than disappearing.

## Permissions

- **Money:** none needed yet. A GPU or any spend needs the Main Bot's approval first.
- **Publishing:** the user's decision alone, for the tool and for its name.
- **The name `keel` is a working name** and may change; the user decides.

## Scopes

Everything here is scope `project` except R9, which is `all` — "never publish without asking" belongs to
every project, not this one.
