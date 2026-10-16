# keelcheck

> ## ⚠️ Work in progress
>
> **Not a dependency yet, and not published anywhere.** The source is public so the work can be read;
> there is **no release**, `pip install keelcheck` does not work, and interfaces may change without
> notice. Publishing a package is the user's decision alone (`CHARTER.md` lines 138–145; R9 at line 103).
> What is solid is written down where it can be checked: three gates ratified at the anchor `501a404`,
> two passing gate runs under the ratified `suite` hash, and an audit that reads **zero divergences** at
> the tip. `.keel/` is gitignored, so the run record itself stays on the machine that produced it —
> re-run `keelcheck audit .` to see the state for yourself.

> **Draft, measured as it was written.** Written by Folio and corrected in place as the tree moved: the
> MCP surface (R5's third) landed on 2026-10-16 with its tests independently verified, and this block's
> earlier sentence *"nothing is published, nothing is installed anywhere, nothing has been pushed"* was
> true when written and is corrected here rather than left standing — the source is now in a public
> repository, while the package remains unpublished. Every number below names the revision it was
> measured at; where the tree has moved since, the page says so instead of rounding over it.

**The name.** The product, the package and every command are `keelcheck`. `keel` survives in exactly
three places, on purpose (`CHARTER.md` lines 142–145): the **checkout directory** `keel/`, the **record
root** `.keel/`, and **records written before the rename**, which the export still recognises
(`keelcheck/export.py`, `RECORD_MARKERS`). Everything a reader types is `keelcheck`.

## What it is

keelcheck keeps one **frozen, human-approved original** for a project — the charter — and requires every
requirement in it to name the mechanism that upholds it (`enforced-by:`) or the check that judges it
(`checked-by:`); a requirement with neither is reported as a **wish**, and a mechanism that does not
resolve in the repository is reported `[unbuilt]`, because that is a wish wearing a mechanism's name
(`CHARTER.md` lines 87–89; D13). The **audit** runs the enforced checks first — each gate's content
hash against the table ratified at the anchor commit, the frozen original byte for byte, the run record —
then a **clean-context review**, in which a reviewer holding only the frozen original and a `.git`-less
export of the current state reports divergence as **missing / unrequested / shifted** (R3 at line 97, R4
at line 98, the gate table at lines 105–116). It runs as a CLI, a git hook, an MCP call and a review
runner (`keelcheck --help`, eight commands), in the charter's order *git hook first, CLI second, MCP
third, adapter last* (R5 at line 99), and the core needs a git repository and nothing else.

## Why a frozen original matters

> An instruction does not get forgotten, it gets **moved**. (`CHARTER.md` line 48)

Through sub-agents, summaries, compactions and rewrites each hop nudges the instruction a little, and
nothing ever compares the current state against the original; the human notices at the end, if at all
(lines 48–50). The sharper version is in the plan that started this: *"don't delete that folder"* was
written down, and the folder was deleted anyway, with no backup (`external:INTENT-LOOP.md` lines 12–16).
**Writing an instruction down does not honour it.**

So the original is drafted by an agent, approved by a human, then **frozen**: later clarifications are
appended, never merged back in — *"an anchor that quietly gets improved is not an anchor"* (lines 8–10).
The freeze is checkable, and two things about it are worth a stranger's attention:

- The frozen-original block (lines 12–22) is **553 bytes**, sha256
  `376f11a44ebc140f705430a06df8df72f05ab59d2120f4a6e09db1a405e85716`, printed by `keelcheck charter`.
  It is byte-identical at all three commits the anchor has named: the freeze commit `ae375c6`, `117ac7c`
  and today's `688fce8`.
- The **anchor moved twice**, each time at the user's word, and each move is a **human event, not a
  re-measurement** — that is where a person's approval sits, and a bot moving it to make its own audit
  green is exactly the laundering path the tool exists to catch (D17, `PROJECT-STATE.md` lines 486–506;
  today's move lines 584–589). It lives in exactly one place, the charter's `Ratified at:` line; the run
  record keeps the anchor *used on that run*, and a change is reported as `[anchor-moved]` with both SHAs
  (D12). The record shows the change rather than letting it pass.
- Gates answer the same rule from the other side. An agent may propose one; once a human ratifies it,
  changing it needs a new approval and the audit fails on a hash mismatch. **Three gates are ratified
  today**, at the anchor `501a404`: the review prompt (`kind: prompt`), `tools/coverage.py`, the coverage
  gate (`kind: gate`), and the reviewer wrapper (`kind: reviewer`, which pins the command a required
  review must have been started by — `CHARTER.md` lines 112–116).

## The 60-second demo

The audit runs today. Measured at `0f14231`, the revision this page was last corrected at:

```
python -m keelcheck audit .            # from the repository root

keelcheck audit -- …\keel
commit:   0f14231…
ratified: 62dc6be
sections: 6/6  requirements: 9  gates ratified: 3 (1 executable)  wishes: 0

DIVERGENCES: none

REVIEW (clean context, R4): missing
  no review line …; run `keelcheck review <repo> --reviewer "<command>"` (D15)
exit: 0
```

**And this is what it printed before the milestone, kept because it is the honest history:** a single
divergence, `[gate-record] suite: the recorded run of this gate did not pass`, with the suite gate never
having passed at the ratified hash — two `fail` (exit 1) and one `timeout` (exit null) — which is why the
gate's timeout was raised 600 → 1800 s and titled *a bound against a hang, not against slowness*
(`PROJECT-STATE.md` lines 590–592). The first passing run is recorded at `35a2758` (85.2% against the
0.83 floor) and the newest at `c5b1092` (85.2%); the earlier failures stay in `.keel/runs.jsonl` as
history rather than being tidied away. Nobody has to trust either summary line: `_check_run_record`
(`keelcheck/audit.py` lines 381–408) requires a **pass**, not merely an execution — so the audit said so
out loud for as long as that was true, and stopped saying it when it stopped being true.

## The 60-second demo — the same command on a repository with no anchor

On a real repository without an anchor, the same command refuses to call anything healthy:

```
python -m keelcheck audit ../rentguard
→ exit 2
  [missing-section] problems: a section R1's fixed format names is missing from the charter
  [vacuity] gates: no gate is ratified at (no anchor), and no executable gate is declared …
  NOT AUDITABLE: the charter names no ratification commit (`Ratified at: <sha>`): not auditable, never clean
  REVIEW (clean context, R4): missing
```

### The two-revision demonstration, and its honest result

R7 commits the tool to proving itself on rentguard — its charter is real, and a by-hand audit of it found
five defects (six names, below). A single run at rentguard's HEAD cannot be that proof: the fixes are
ancestors of HEAD, so the charter there already records the defects as closed. D7 therefore defines the
demo as a **pair** of runs — at the revision immediately before each fix, and at HEAD. Both halves have
now run, and the result is smaller than the claim:

| half | result |
|---|---|
| **mechanical** — gate hashes, frozen block, sections, vacuity | identical divergence lists at `bd63920` and at `310f449`; it names the five by-hand defects only as **state classes** (R2's `met` claim being the one that is a lie, with R9 and R8 stating their gaps) — and **W4 and W3 are invisible to it**, because they live in code and in prose, not in a requirement row |
| **clean-context drift review** | names **2 of the 5** at each of the three pre-fix revisions (`bd63920`, `ce69cea`, `c512125`), every finding quoted to its revision — and **none of them** on the current state |
| **combined** | R7 reads **met in part at the pre-fix revisions** and **not met as written on the current state**. It is not "the audit reproduces the by-hand audit", and this page will not say it is |

Sources: `tests/_artefacts/R7-demonstration-mechanical-2026-10-14.md`, the four `assay_r7_drift_*.json`
assays — **re-recorded 2026-10-16** against cleaned copies, the reason and the copies named in that
file's §3 — and `PROJECT-STATE.md` lines 593–597.

### The five by-hand defects, all six names

rentguard's by-hand audit found five defects, which are **six names**, because R4 and W4 are one finding
in two stages — the guard was unproven and, tested, it was wrong (D11 F6, `PROJECT-STATE.md` lines
278–287):

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

**Nothing is installable from an index yet; the wheel builds and installs, measured at `c5168d0`
(2026-10-15) into a fresh virtual environment, so nothing shared is mutated.** `pyproject.toml` (2151
bytes, 46 lines) declares the entry point `keelcheck = "keelcheck.cli:main"`, `requires-python =
">=3.10"` and no dependencies. The zero-install form was run on Python 3.12.6 from the repository root:

```
python -m keelcheck --help                       # exit 0 — seven commands, no `mcp`
python -m keelcheck charter CHARTER.md           # exit 0 — 6/6, 9 requirements, 2 gates, anchor 688fce8
python -m keelcheck charter ../rentguard/CHARTER.md   # exit 1 — 5/6: a charter that parses with findings
python -m keelcheck audit ../rentguard           # exit 2 — see the demo
python -m keelcheck gate hash keelcheck/cli.py   # exit 0 — the hash a gate row records, over git-normalized bytes
python -m keelcheck review --help                # exit 0 — the clean-context runner
python -m keelcheck hook install <repo>          # installs the pre-commit hook (R5); `hook status` is read-only
```

**The install, measured at `c5168d0`** (Scribe, 2026-10-15): the wheel is built from the checkout,
installed into a clean venv, and the console script is run from that venv — the install concern above is
answered by the venv rather than by not installing.

```
python -m pip wheel . --no-deps --no-build-isolation -w dist
#   Created wheel for keelcheck: filename=keelcheck-0.0.1-py3-none-any.whl size=55005 sha256=c05efef8…
# Successfully built keelcheck       [27 s, exit 0]

<venv>\Scripts\python.exe -m pip install --no-index --no-deps dist/keelcheck-0.0.1-py3-none-any.whl
# Successfully installed keelcheck-0.0.1

keelcheck --version                    # keelcheck 0.0.1        [exit 0]
keelcheck gate hash keelcheck/cli.py   # sha256:79885adac75a12d83afa49f5cea59f65e159f0332a0e929935d30dc4340df2c0
```

Two flags are load-bearing on this host and neither is needed on a machine with network:
`--no-build-isolation`, because an isolated build waits at `Installing build dependencies: started`
fetching the `setuptools>=68` that `pyproject.toml` requires (measured here: still there after 7
minutes, then killed); and `--no-index --no-deps`, because there is nothing to resolve. The digest above
is the one at `c5168d0` and will differ from any recorded earlier, since the file changes.

`keelcheck review <repo> --reviewer "<command>"` runs a command keelcheck never sees a shell for, with a
`.git`-less export as its working directory and the ratified prompt on stdin; it returns one JSON object
classifying what it sees as missing / unrequested / shifted (D15, D21). A stub command is a complete test
double, so none of this needs a model.

The test suite was last verified **from outside the worktree**: at `866912b`, in a clean checkout,
**106 passed, 1 skipped, 0 failed in 4:34** (`PROJECT-STATE.md` lines 56–58; the skip is an R5 hook test,
because git's own `sh` cannot start in this sandbox). I am **not quoting a current count**: the suite has
grown since that commit, and at this stamp the worktree carries ` M tests/test_review_cli.py`, so a run
now would measure a moving, dirty tree. For the same reason I started a live `keelcheck gate run` and
**stopped it** when eleven commits landed under it — its coverage number would have described a revision
that no longer exists.

The surfaces arrive in the charter's order (R5, line 99): **git hook first** (installer landed), **CLI**
(seven commands), **review runner** — then MCP and a harness adapter, neither of which exists at this
stamp. One ruling matters to anyone reading that order: D2 accepted that every local surface can be
silenced by the agent it constrains (`--no-verify`, `disableAllHooks`), so hooks are *reach*, not
enforcement — the guarantee moves into the audit: hashes anchored to a commit, plus an append-only record
in which a bypass appears as a **missing** line.

## What it deliberately does not do

- **No daemon and no server.** A bounded CLI run that returns; no long-lived process, no listening socket
  (R6, `CHARTER.md` line 100).
- **No harness of its own.** A git hook, a CLI and an optional adapter — not another agent runtime
  (lines 52–56).
- **Not a spec-authoring suite.** Spec Kit makes *living* specs first-class, which is the opposite of
  freezing an original (`external:ECC-ASSESSMENT.md`).
- **Not a memory or learning layer.** ECC's memory accumulates and evolves — instincts become skills,
  memories get promoted — and nothing in it freezes an original or audits against one. keelcheck is the
  anchor, not the memory.
- **Not a job runner.** It does not start, schedule or supervise work (line 56).
- **No CI.** R8's own cell says so: the suite and the gate run on this checkout, not in a pipeline
  (`CHARTER.md` line 102).
- **Not published, not packaged, not pushed** — and publishing is the user's word alone (R9).

## Status of every number on this page

| claim | source | reproducible here? |
|---|---|---|
| the frozen-original block is 553 bytes, sha256 `376f11a4…`, byte-identical at `ae375c6`, `117ac7c` and `688fce8` | `keelcheck charter CHARTER.md`; `git show` of all three commits | yes |
| the anchor is `688fce8` and lives once, in the charter's `Ratified at:` line | `CHARTER.md` line 26; D17 and the 2026-10-15 record | yes |
| three gates are ratified at the anchor `501a404`: `review-prompt` `sha256:0e4b5764…`, `suite` (coverage) `sha256:973d639a…`, `reviewer` `sha256:8d5e6a5e…` | `CHARTER.md` lines 112–116; `keelcheck audit` | yes |
| the coverage gate's floor is **0.83**, from the first honest measurement 2031/2419 | `PROJECT-STATE.md` lines 584–589 | **no — quoted; re-measure with `gate run`** |
| the record's newest `suite` run is a **pass** at the ratified hash (`c5b1092`, 85.2%; the first was `35a2758`), with the earlier two `fail` and one `timeout` kept as history | `.keel/runs.jsonl` | yes — code |
| the drift half names **2 of 5** by-hand defects at each of the three pre-fix revisions, and none of them at the current state (a different MCP item and a partial guard gap are named there) | `PROJECT-STATE.md` lines 593–597; `tests/_artefacts/assay_r7_drift_*.json` | yes — the assays are committed, re-recorded 2026-10-16 with each run naming its cleaned copy |
| keelcheck: 77 commits at `c8778b4`, 88 at `574a44f`, 11 landed during this pass; 83 tracked files | `git rev-list --count`, `git ls-files`, measured 2026-10-15 | yes — commits |
| rentguard: 106 commits at `449a339`, 108 at `3287a4f`; its `CHARTER.md` unchanged at 5821 bytes | `git -C rentguard log`; the file itself | yes |
| rentguard: 189 passed / 0 failed, 45 subtests, coverage floor 90.2% | `rentguard/CHARTER.md` lines 30 and 44, pinned at `74b9f7a` | **no — quoted, not re-measured** |
| the suite's last outside-worktree verification: 106 passed, 1 skipped, 0 failed in 4:34 | `PROJECT-STATE.md` lines 56–58 | **no — quoted; the suite has grown since** |
| the seven demo revisions exist and are ancestors of rentguard's HEAD | `git cat-file -t`, `git merge-base --is-ancestor` | yes |
| a `kind: "review"` line is absent from `.keel/runs.jsonl`, so both audits print `REVIEW … missing` | the record, read directly | yes — code |

The full table — every artefact, its size, its revision, and the findings it carries — is
[`docs/ARTEFACT-MAP.md`](docs/ARTEFACT-MAP.md).
