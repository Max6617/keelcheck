# keelcheck

> **Draft — nothing is published and nothing is installed anywhere.** Written by Folio on 2026-10-14.
> Measured at keelcheck `fa6fb87` (40 commits, branch `main`) and at the demonstration repository rentguard
> `eef6bdb` (82 commits). Publication is the user's decision alone (`keel/CHARTER.md` lines 134–136; R9
> at line 101), and nothing here has been pushed or packaged. Every number below names the file it came
> from; the two places that cannot be reproduced say so.

## What it is

keelcheck keeps one frozen, human-approved original for a project — the charter — and requires every
requirement in it to name the mechanism that upholds it (`enforced-by:`) or the check that judges it
(`checked-by:`); a requirement with neither is reported as a **wish**, and a mechanism that does not
resolve in the repository is reported as `[unbuilt]`, because that is a wish wearing a mechanism's name
(`keel/CHARTER.md` lines 87–89; `PROJECT-STATE.md` D13). The **audit** runs the enforced checks first —
every gate's content hash against the ratified table, the frozen original byte for byte, the run record —
then a **clean-context review** in which a fresh reviewer, holding only the frozen original and a
`.git`-less export of the current state, reports divergence as **missing / unrequested / shifted** (R3 at
line 95, R4 at line 96, the gate table at lines 103–111). It arrives as a CLI, a git hook and a review
runner (`keelcheck --help`), in the order *git hook first, CLI second, MCP third, adapter last* (R5 at line 97),
and the core needs a git repository and nothing else.

## Why a frozen original matters

> An instruction does not get forgotten, it gets **moved**. (`keel/CHARTER.md` line 46)

Through sub-agents, summaries, compactions and rewrites each hop nudges the instruction a little, and
nothing ever compares the current state against the original; the human notices at the end, if at all
(lines 46–48). The sharper version of the story is in the plan that started this: *"don't delete that
folder"* was written down, and the folder was deleted anyway, with no backup
(`external:INTENT-LOOP.md` lines 12–16). **Writing an instruction down does not honour it.**

So the original is drafted by an agent, approved by a human, and then **frozen**: later clarifications are
appended, never merged back in — *"an anchor that quietly gets improved is not an anchor"* (lines 8–10).
The freeze is checkable, and tonight it was tested the hard way:

- The frozen-original block (lines 12–22) is **553 bytes**, sha256
  `376f11a44ebc140f705430a06df8df72f05ab59d2120f4a6e09db1a405e85716`, printed by `keelcheck charter`.
- The **anchor moved once**, at the user's word, from the freeze commit `ae375c6` to `117ac7c`, the commit
  that carries keelcheck's first gate (line 26). Everything that makes an anchor worth having was checked
  first: the block is byte-identical at both commits, so the move changes only which *gate table* is the
  reference — and moving the anchor is a **human** event, not a re-measurement, because that is where a
  person's approval sits (D17, `PROJECT-STATE.md` lines 453–473). A bot moving it to make its own audit
  green is exactly the laundering path the tool exists to catch, and the tool reported the change rather
  than letting it pass.
- The anchor lives in **exactly one place**, the charter's `Ratified at:` line; the run record keeps the
  anchor *used on that run*, and a change is reported as `[anchor-moved]` with both SHAs (D12).
- Gates answer the same rule from the other side: a gate is a row in the `## Gates` table with a content
  hash. An agent may propose one; once a human ratifies it, changing it needs a new approval, and the
  audit fails on a mismatch. The table's one row is currently a **prompt**, and the audit says plainly
  that a prompt is not an executable check (below).

## The 60-second demo

**Status: the audit runs today. The two-revision demonstration has still not been run.** Measured at keelcheck
`fa6fb87`, on rentguard, the real repository:

```
cd keelcheck
python -m keelcheck audit ../rentguard --record /tmp/keelcheck-runs.jsonl
```

```
keelcheck audit -- …/rentguard
commit:   eef6bdb…
ratified: (not named -- this charter is not auditable)
sections: 5/6  requirements: 10  gates ratified: 0  wishes: 3
DIVERGENCES (2)
  [missing-section] problems: a section R1's fixed format names is missing from the charter
  [vacuity] gates: no gate is ratified at (no anchor), and no executable gate is declared …; R2's gate is
    an executable script with a content hash, so the hash half of this audit verified nothing
NOT AUDITABLE: the charter names no ratification commit (`Ratified at: <sha>`), so there is no reference
  side to compare against (A2): not auditable, never clean
REVIEW (clean context, R4): missing
  no review line …; run `keelcheck review <repo> --reviewer "<command>"` (D15)
exit: 1
```

That is the honest 60 seconds: on a real repository the audit reports three named things and refuses to
call anything healthy — the missing `problems` section, a gate-less charter, and a charter with no anchor
at all. On keelcheck itself the same command reports `6/6 sections, 9 requirements, gates ratified: 1`, and
still exits 1, because the one ratified gate is a **prompt row** and the vacuity line names why it does
not count:

```
[vacuity] gates: the ratified table at 117ac7c holds 1 prompt row(s) and no executable gate … the hash
  half of this audit verified nothing -- and an audit that verifies nothing is not a clean run (D8)
```

### The two-revision shape, still to run

R7 (`keel/CHARTER.md` line 99) commits the tool to running the audit against `rentguard/CHARTER.md` at
four revisions, and D7 (`PROJECT-STATE.md` lines 140–155) says why a single run at rentguard's HEAD
cannot be the demo: the fixes are ancestors of HEAD, so the charter there already records the defects as
closed. The audit exists now, so the pair can be run; it has not been, and that run is Proctor's.

| revision | what the audit must report there | why that revision |
|---|---|---|
| `bd63920` | the MCP-arming defect as divergence | immediately before its fix, `590c58e` (D7) |
| `ce69cea` | the idle-clamp defect — a guard that could stop a healthy pod | immediately before `d5fdaea` |
| `c512125` | the volume-transport defect | immediately before `da51005` |
| `310f449` | only what is still open — the cap that exists only while `watch` runs, and the absent publishing lock — and **not** the three closed defects as open | rentguard's HEAD when D7 was written |

All seven revisions named in the table exist in `rentguard` and are ancestors of its current HEAD
`eef6bdb` (measured 2026-10-14). The demonstration's second half — the clean-context review — is built
(`keelcheck review`, `review-prompt.md` ratified as a hashed gate row, D15) and **has never been started on
either repository**: no `kind: "review"` line exists in any record yet.

### The five by-hand defects, all six names

rentguard's by-hand audit found five defects, which are **six names** because R4 and W4 are one finding in
two stages — the guard was unproven, and tested, it was wrong (`PROJECT-STATE.md` D11 F6, lines 235–244):

| # | the finding | names |
|---|---|---|
| 1 | the MCP surface could not arm the guard | R2 |
| 2 | the guard was unproven and, tested, wrong | **R4 and W4** |
| 3 | the cap exists only while `watch` runs | W1 (R9) |
| 4 | publishing has no lock | W2 (R8) |
| 5 | the volume path is unexercised | W3 |

Both earlier listings of "the five" had each dropped one name — one lost W2, the other lost R4 — which is
why both read as fine. The catalogue now prints all six.

## Install and run

**Nothing is installable yet, and I did not install it here.** `keelcheck/pyproject.toml` (795 bytes,
28 lines) declares the entry point `keelcheck = "keelcheck.cli:main"`, `requires-python = ">=3.10"` and no
dependencies — but installing it would mutate the shared interpreter environment other bots are using, so
this page reports only the zero-install form, which I did run on Python 3.12.6:

```
cd keelcheck
python -m keelcheck --help                          # exit 0
python -m keelcheck charter CHARTER.md               # exit 0 — 6/6 sections, 9 requirements, 1 gate, anchor 117ac7c
python -m keelcheck charter ../rentguard/CHARTER.md  # exit 1 — 5/6 sections: a charter that parses with findings
python -m keelcheck audit ../rentguard --record /tmp/runs.jsonl   # exit 1 — see the demo
python -m keelcheck gate hash keelcheck/cli.py            # exit 0 — sha256:d00cdcd7… over git-normalized bytes (D9)
python -m keelcheck review --help                    # exit 0 — the clean-context runner
python -m keelcheck hook install <repo>              # installs the pre-commit hook (R5); `hook status` is read-only
```

`keelcheck review <repo> --reviewer "<command>"` starts a reviewer that keelcheck never sees a shell for: it is run
with the export as its working directory and the ratified prompt on stdin, and it returns exactly one JSON
object classifying what it sees as missing / unrequested / shifted (D15, `PROJECT-STATE.md` lines
396–451). A stub command is a complete test double, so none of this needs a model.

The tests, at this revision, from a `git archive` (no `.git`, so nothing of the working directory leaks
in):

```
python -m pytest -q
# 93 passed, 6 skipped in 270.59s — the 6 skips are the R5 hook tests:
# git's own `sh` cannot start under this sandbox (D19, PROJECT-STATE.md lines 498–499)
```

Name the test paths if you run in a dirty worktree: `python -m pytest` from the repository root stops
with 2 collection errors on two unreadable `pytest-cache-files-*` directories — finding F4 in
`docs/ARTEFACT-MAP.md`, where it is recorded as measured, then unreproduced, then measured again.

The surfaces arrive in the charter's order (R5, line 97): **git hook first** (installer landed),
**CLI** (five commands), **review runner**, then MCP and a harness adapter. One ruling matters to anyone
reading that order: D2 accepted that every local surface can be silenced by the agent it constrains
(`--no-verify`, `disableAllHooks`), so hooks are *reach*, not enforcement — the guarantee moves into the
audit: hashes anchored to a commit, plus an append-only record in which a bypass appears as a **missing**
line.

## What it deliberately does not do

- **No daemon and no server.** A bounded CLI run that returns; no long-lived process, no listening socket
  (R6, `keel/CHARTER.md` line 98).
- **No harness of its own.** A git hook, a CLI and an optional adapter — not another agent runtime
  (lines 52–54).
- **Not a spec-authoring suite.** Spec Kit makes *living* specs first-class, which is the opposite of
  freezing an original (`external:ECC-ASSESSMENT.md` line 73).
- **Not a memory or learning layer.** ECC's memory accumulates and evolves — instincts become skills,
  memories get promoted — and nothing in it freezes an original or audits against one (lines 69–72).
  keelcheck is the anchor, not the memory.
- **Not a job runner.** It does not start, schedule or supervise work (line 54).

## Status of every number on this page

| claim | source | reproducible here? |
|---|---|---|
| keelcheck `fa6fb87`, 40 commits, `main`, no remote configured | `git rev-parse`, `git rev-list --count`, `git remote -v`, 2026-10-14 | yes — a commit |
| the frozen-original block is 553 bytes, sha256 `376f11a4…`, and byte-identical at `ae375c6` and `117ac7c` | `keelcheck charter CHARTER.md`; `git show` of both commits | yes |
| the anchor moved once, at the user's word, to `117ac7c` | `keel/CHARTER.md` line 26; D17, `PROJECT-STATE.md` lines 453–473 | yes |
| `keelcheck audit .` → exit 1: one `[vacuity]` finding naming the single prompt row, and `REVIEW … missing` | measured at `fa6fb87` | yes, at this commit |
| `keelcheck audit ../rentguard` → exit 1: missing section, vacuity, not auditable, review missing | measured at `fa6fb87` | yes |
| `keelcheck charter ../rentguard/CHARTER.md` → exit 1 (5/6 sections) | measured at `fa6fb87` | yes |
| `keelcheck gate hash keelcheck/cli.py` = `sha256:d00cdcd7…` | measured at `fa6fb87` | yes |
| the suite: 93 passed, 6 skipped from a `git archive` of `fa6fb87` | measured 2026-10-14 | yes, at this commit |
| a dirty worktree cannot collect from its root (2 errors, exit 2); the same revision is green in a clean extraction | measured at `b81c374`, `1b65a53`, `fa6fb87` | yes — and see F4 |
| rentguard `eef6bdb`, 82 commits, clean; its `CHARTER.md` byte-identical to keelcheck's `a72e7c4` snapshot (`046fa7d91a3a…`) | `git -C rentguard log`, `status`; both files hashed | yes |
| rentguard: 189 passed / 0 failed, 45 subtests, coverage floor 90.2% | `rentguard/CHARTER.md` lines 30 and 44, pinned at `74b9f7a` | **no — quoted, not re-measured** |
| the seven demo revisions exist and are ancestors of rentguard's HEAD | `git cat-file -t`, `git merge-base --is-ancestor` | yes |

The map behind every row, with every missing artefact named and every finding dated, is
[`docs/ARTEFACT-MAP.md`](docs/ARTEFACT-MAP.md).
