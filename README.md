# keel

> **Draft — nothing is published and nothing is installed anywhere.** Written by Folio on 2026-10-14.
> Measured at keel `b81c374` (9 commits, branch `main`) and at the demonstration repository rentguard
> `ad2e880`. Publication is the user's decision alone (`keel/CHARTER.md` line 121; R9 at line 96), and
> nothing here has been pushed or packaged. Every number below names the file it came from, and the one
> place the demo cannot run yet says so instead of implying that it did.

## What it is

keel keeps one frozen, human-approved original for a project — the charter — and requires every
requirement in it to name the mechanism that upholds it (`enforced-by:`) or the check that judges it
(`checked-by:`); a requirement with neither is reported as a **wish** (`keel/CHARTER.md` lines 82–84).
At each milestone the **audit** runs the enforced checks first, then a drift review with clean context,
and reports divergence from the frozen original in three classes — **missing / unrequested / shifted** —
plus the wishes (lines 38–39; R3 at line 90). It is meant to arrive in the order *git hook, CLI, MCP
call, harness adapter* (R5 at line 92), and the core needs a git repository and nothing else.

## Why a frozen original matters

> An instruction does not get forgotten, it gets **moved**. (`keel/CHARTER.md` line 41)

Through sub-agents, summaries, compactions and rewrites each hop nudges the instruction a little, and
nothing ever compares the current state against the original; the human notices at the end, if at all
(lines 41–43). The sharper version of the story is in the plan that started this:
*"don't delete that folder"* was written down, and the folder was deleted anyway, with no backup
(`external:INTENT-LOOP.md` lines 12–16). **Writing an instruction down does not honour it.**

So the original is drafted by an agent, approved by a human, and then **frozen**: later clarifications
are appended as new requirements, never merged back in — *"an anchor that quietly gets improved is not
an anchor"* (`keel/CHARTER.md` lines 8–10). The freeze is not a formality in either direction:

- The one change the user asked for was made **before** it and kept as a trace. Their words were *"wish 2
  you can throw away but the ret is good"* (line 6): the wish was struck, the rule moved to R9 as a human
  check, and the strike left its trace in the file (lines 113–116).
- And it is checkable. Measured on 2026-10-14: the frozen-original block (lines 12–22) is 530 bytes,
  sha256 `093a271b4c150594dceeaf51ebbcb0a5c2329118ba16239c14481bf2fffc94c2`, and byte-identical at the
  freeze commit `ae375c6`, at HEAD `b81c374`, and in the working tree — while the rest of the file grew
  from 99 to 127 lines. That is ruling D5 (`keel/PROJECT-STATE.md` lines 122–129): the anchor is the
  block, not the file, which is precisely why the living part may change without the original moving.

Gates answer the same rule from the other side. A gate is code recorded in the charter with a content
hash; an agent may propose one, but once a human ratifies it, changing it needs an approval recorded with
a *new* hash and the audit fails on a mismatch (R2 at `keel/CHARTER.md` line 89). Where the ratified hash
is read from — the ratification commit, `git show <sha>:CHARTER.md`, never the working tree — is ruling
D1 (lines 100–103).

## The 60-second demo

**Status: it cannot run yet. The command does not exist.** Measured at keel `b81c374`:

```
python -m keel audit --help
# keel: unknown command: audit        (exit 1)
```

What follows is the shape the demo takes — and then the half that **does** run today, measured, because
that half is the honest part.

### The shape: two revisions, one pair of runs

R7 (`keel/CHARTER.md` line 94) commits the tool to running the audit against `rentguard/CHARTER.md` at
`bd63920`, `ce69cea`, `c512125` and `310f449`. D7 (`keel/PROJECT-STATE.md` lines 140–155) says why a
single run at rentguard's HEAD cannot be the demo: the fixes are ancestors of HEAD, so the charter there
already records the defects as closed. The audit is run with rentguard's worktree at a named revision:

| revision | what the audit must report there | why that revision |
|---|---|---|
| `bd63920` | the MCP-arming defect as divergence | the commit immediately before the fix, `590c58e` (D7) |
| `ce69cea` | the idle-clamp defect — a guard that could stop a healthy pod | immediately before `d5fdaea` |
| `c512125` | the volume-transport defect | immediately before `da51005` |
| `310f449` | only what is still open: the cap that exists only while `watch` runs, and the absent technical lock on publishing — and **not** the three closed defects as open | rentguard's HEAD when D7 was written |

All seven revisions named in that table exist in `rentguard` and are ancestors of its current HEAD
`ad2e880` (measured 2026-10-14). **Open item:** nothing yet specifies *how* a revision is handed to the audit — the ruled
contract is `python -m keel audit <path-to-repo>` (`keel/tests/CONTRACT.md` lines 10–21) with
`--record <path>` and `--fail-on-wish` (D8/A3, `keel/PROJECT-STATE.md` lines 170–174). This page does not
invent a flag for it.

### The half that runs today

```
cd keel
python -m keel charter ../rentguard/CHARTER.md      # exit 0, measured 2026-10-14 at b81c374
```

Against the five defects the by-hand audit found on rentguard:

| by-hand defect (rentguard's row) | in the parser run |
|---|---|
| no way to arm the guard over MCP (R2) | found as a **symptom** — the row's state says `met` and it names no mechanism |
| the guard could stop a healthy pod (W4) | **missed** — it lives in code, in no requirement row |
| the cap exists only while `watch` runs (W1 / R9) | found |
| no technical lock on publishing (W2 / R8) | found |
| the volume path unexercised (W3) | **missed** — prose in the wishes section, not a requirement row |

The score and the wording are the R7 artefact's
(`keel/tests/_artefacts/R7-demonstration-mechanical-2026-10-14.md` lines 23–33), whose numbers are pinned
to `fbd9837`; the parser output is the same at `b81c374` because the package is unchanged since
`489f47d` (`git diff --stat 489f47d..HEAD -- keel/` is empty). On keel's own charter the same command
reports `6/6` sections, `9` requirements, `0` wishes and `0` asserted enforcement.

The miss is the point, and it is why the demo is a *pair* of runs rather than one: a
requirements-table audit reads the charter about itself, and the two defects that cost money or data
resolve in code and in prose. It is also why the audit must report a gate-less charter as **vacuous**
rather than clean — measured today, neither charter declares a single gate (no `## Gates` heading in
`keel/CHARTER.md` or `rentguard/CHARTER.md`), and `keel/CHARTER.md` lines 28–29 already rule that an
audit which verified nothing is a divergence, never a clean run.

## Install and run

**Nothing is installable yet, and I did not install it here.** `keel/pyproject.toml` (795 bytes,
28 lines) declares the entry point `keel = "keel.cli:main"`, `requires-python = ">=3.10"` and no
dependencies — but installing it would mutate the shared interpreter environment other Bots are using,
so this page reports only the zero-install form, which I did run on Python 3.12.6:

```
cd keel
python -m keel --help                             # exit 0 — one command today: charter <path>
python -m keel charter CHARTER.md                 # exit 0 — 6/6 sections, 9 requirements, 0 wishes
python -m keel charter ../rentguard/CHARTER.md    # exit 0 — see the demo above
python -m keel audit ../rentguard                 # exit 1 — keel: unknown command: audit
```

The tests, as they stand at `b81c374` — red by design, because `keel audit` does not exist yet:

```
python -m pytest -q -p no:cacheprovider tests/test_audit_cli.py tests/test_charter_silent_wish.py tests/test_cli_encoding.py
# 13 failed, 16 passed in 9.81s
```

Name the modules: `python -m pytest` from the repository root stops with 2 collection errors (exit 2) on
two unreadable `pytest-cache-files-*` directories that nothing ignores — finding F4 in
`docs/ARTEFACT-MAP.md`.

The surfaces are meant to arrive in the charter's order (R5, `keel/CHARTER.md` line 92): **git hook
first**, then the **CLI**, then an **MCP call**, then a **harness hook adapter** last. One ruling matters
to anyone reading that order: D2 (`keel/PROJECT-STATE.md` lines 75–82) accepted that every local surface
can be silenced by the agent it constrains (`--no-verify`, `disableAllHooks`), so hooks are *reach*, not
enforcement — and the guarantee moves into the audit: ratified hashes anchored to a commit (D1) plus an
append-only run record in which a bypass appears as a **missing** line.

## What it deliberately does not do

- **No daemon and no server.** A bounded CLI run and an MCP call that returns; no long-lived process, no
  listening socket (R6, `keel/CHARTER.md` line 93).
- **No harness of its own.** A git hook, a CLI and an optional adapter — not another agent runtime
  (lines 47–49).
- **Not a spec-authoring suite.** Spec Kit makes *living* specs first-class, which is the opposite of
  freezing an original (`external:ECC-ASSESSMENT.md` line 73).
- **Not a memory or learning layer.** ECC's memory accumulates and evolves — instincts become skills,
  memories get promoted — and nothing in it freezes an original or audits against one (lines 69–72).
  keel is the anchor, not the memory.
- **Not a job runner.** It does not start, schedule or supervise work (line 49).

## Status of every number on this page

| claim | source | reproducible here? |
|---|---|---|
| keel `b81c374`, 9 commits, branch `main`, no remote configured | `git rev-parse`, `git rev-list --count`, `git remote -v`, 2026-10-14 | yes — a commit |
| the frozen-original block is byte-identical at `ae375c6`, `b81c374` and the worktree (530 bytes, sha256 `093a271b4c150594…`) | `git show` + sha256, 2026-10-14 | yes — two commits and a worktree |
| the charter file itself grew from 99 to 127 lines after the freeze | `git show ae375c6:CHARTER.md` vs the worktree | yes |
| parser on `keel/CHARTER.md`: 6/6 sections, 9 requirements, 0 wishes, 0 asserted enforcement | `python -m keel charter CHARTER.md` at `b81c374` | yes, at this commit |
| parser on `rentguard/CHARTER.md`: 5/6 sections (`problems` missing), 10 requirements, 3 wishes (R2, R4, R8), 2 asserted (R5, R9) | same command; the input is byte-identical to the `a72e7c4` snapshot (`046fa7d91a3a…`) | yes, at this commit |
| `keel audit` does not exist: exit 1, unknown command | measured at `b81c374` | yes |
| the suite: 13 failed / 16 passed when the three modules are named; collection from the root fails (2 errors, exit 2) | measured at `b81c374`, `-p no:cacheprovider` | yes, at this commit |
| rentguard `ad2e880`, 75 commits, worktree modified (1 file) | `git -C rentguard log`, `git status`, 2026-10-14 | yes |
| the seven demo revisions exist and are ancestors of rentguard's HEAD | `git cat-file -t`, `git merge-base --is-ancestor` | yes |
| rentguard: 189 passed / 0 failed, 45 subtests, coverage floor 90.2% | `rentguard/CHARTER.md` lines 30 and 44, pinned at `74b9f7a` | **no — quoted, not re-measured** |
| the two files in Folio's lane (`README.md`, `docs/`) are untracked | `git status --porcelain` | yes |

Two caveats a stranger should carry away. The by-hand defects are named **two different ways** in two
files — `keel/PROJECT-STATE.md` line 43 lists R2, R4, W1, W3, W4, while the R7 artefact's table lists
R2, W4, W1, W2, W3 — so "the five" needs a ruling before an audit can claim to reproduce them (finding
F6). And the map behind every row above, with every missing artefact named, is
[`docs/ARTEFACT-MAP.md`](docs/ARTEFACT-MAP.md).
