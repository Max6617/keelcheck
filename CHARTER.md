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
| R3 | The audit reports divergence from the frozen original in three classes — **missing / unrequested / shifted** — plus the wishes, readable in two minutes | code + the drift review | the human reads it | draft |
| R4 | The drift review runs with **clean context**: a fresh agent holding only the frozen original and the current state, never the history that produced it | the runner starts a fresh context and records that it did | — | draft |
| R5 | Integration surfaces in this order: git hook first, CLI second, MCP third, harness hook adapter last | code: the hook installer | — | draft |
| R6 | No daemon and no server: a bounded CLI run, and an MCP call that returns | code: no long-lived process, no listening socket | — | draft |
| R7 | The tool proves itself on **rentguard**: running the audit there must reproduce the defects that were found by hand | the audit run against `rentguard/CHARTER.md` | the human reads the report | draft |
| R8 | 94% of the code and 100% of the surface exercised; one writer per file; every count names a commit; red tests before fixes | `tools/coverage.py` and the suite | the CI run | draft |
| R9 | Nothing is published without the user's explicit word | — | the user's explicit word before any push | checked, not enforced |

## The wishes

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
