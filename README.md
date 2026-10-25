# keelcheck

> **Status: 0.1.0 — early.** The source is public and installs from a checkout; the package is **not on
> PyPI**, and it will not be published without an explicit decision by the maintainer. Interfaces may
> change between 0.x releases.

## What it is

When work is delegated — to sub-agents, to a coding assistant, across summaries and rewrites — the
instruction does not stay put. Each hop nudges it: a requirement becomes a convention, an exception
becomes the rule, a step that was never done becomes "done" in the summary. Nothing in the loop compares
the current state of the work against what was originally asked for, so the person who asked discovers
the drift at the end, if at all. A rule written in prose is not a mechanism; it is a wish.

keelcheck makes the original a file a project can be audited against. The **charter** is one
human-approved document, frozen once approved: what the project is for, the problems it exists to solve,
and a list of requirements. Every requirement must name the mechanism that enforces it — a test, a
script, a gate with a recorded hash — or the check that judges it; a requirement with neither is
reported as a **wish**, and a wish is the honest name for a promise nothing keeps. The **audit** then
compares the repository to that original: it checks each gate's content hash against the table recorded
when the project was ratified, diffs the frozen text byte for byte, and reports what is missing, what was
never asked for, and what has quietly changed meaning. It is for people who delegate real work to coding
agents and need the promises to survive the delegation.

## What a charter contains

- **Six required sections**: purpose, strengths, the problems the human and the agent agreed on,
  requirements, permissions, scopes. A missing section is reported and makes the audit fail.
- **A requirements table**, with how each requirement is honoured:

  ```markdown
  | # | requirement | enforced-by | checked-by | state |
  |---|---|---|---|---|
  | R1 | The CLI accepts a charter | code: the parser | — | draft |
  | R2 | Users can find the quickstart | — | a human reads it | draft |
  ```

  `enforced-by:` means a mechanism makes the violation impossible, fatal or recoverable. `checked-by:`
  means a human judges it (or a demo makes the state visible). **Neither is a wish**, and the audit
  prints every wish it finds. A mechanism cell that names a path which does not resolve in the audited
  repository is reported `[unbuilt]` — a wish wearing a mechanism's name.

- **A gates table**, with a content hash per row:

  ```markdown
  | gate | path | hash | kind |
  |---|---|---|---|
  | suite | tools/coverage.py | sha256:… | gate |
  | review-prompt | review-prompt.md | sha256:… | prompt |
  ```

  A `kind: gate` row is an executable script whose exit code decides pass or fail. `kind: prompt` and
  `kind: reviewer` rows are hashed the same way but are not executed: they pin the instruction a review
  must follow and the command that must have produced it. `kind` is optional and defaults to `gate`.

- **A `Ratified at: <commit>` line.** It names the commit whose charter is the reference side of every
  comparison. The audit reads the gate table from that commit with git, never from the working tree,
  because a working-tree hash can be edited in the same two keystrokes the rule exists to catch.

## Install

Python 3.10 or newer and git are required; there are no runtime dependencies. Not on PyPI — install
from a checkout:

```console
git clone https://github.com/Max6617/keelcheck
cd keelcheck
python -m pip install .
keelcheck --help
```

To try it without installing, run it from the checkout: `python -m keelcheck --help`.

## A first run

Create a `CHARTER.md` with the six sections above and a `git init`. `keelcheck charter` parses it and
reports what it found:

```console
$ keelcheck charter CHARTER.md
charter: CHARTER.md
title:   (untitled)
sections: 6/6 required
requirements: 1
gates: 0 declared
ratified at: (not named)
review: reported, not required
frozen original: 69 bytes, sha256:c3b31931…

REQUIREMENTS (1) -- all four columns
  R1  state: draft
      requirement:  The example exists
      enforced-by:  code: this example
      checked-by:   —
```

`keelcheck audit` then refuses to call it healthy, and says exactly why:

```console
$ keelcheck audit .
ratified: (not named -- this charter is not auditable)
sections: 6/6  requirements: 1  gates ratified: 0 (0 executable)  wishes: 0

DIVERGENCES (1)
  [vacuity] gates: no gate is ratified at (no anchor), and no executable gate is declared …
NOT AUDITABLE: the charter names no ratification commit (`Ratified at: <sha>`), so there is no
  reference side to compare against: not auditable, never clean
REVIEW (clean context): missing
  …
exit: 2
```

That is the intended first run. The next steps are to commit the charter, put that commit's id in
`Ratified at:`, add at least one executable gate row, and run `keelcheck gate run .` so the gate has a
record. From then on `keelcheck audit .` is the command that answers "does the repository still match
what was approved?" — and it exits non-zero when the answer is no.

**On a fresh clone of this repository**, `keelcheck audit .` reports one `[gate-record]` divergence: the
append-only run record lives in `.keel/`, which is not part of the repository. Run
`keelcheck gate run .` once and the record exists; the audit then reads clean.

## Commands and exit codes

| command | what it does | 0 | 1 | 2 |
|---|---|---|---|---|
| `keelcheck charter <path>` | parse a charter and report its requirements, wishes and gates | parses, no missing section | a required section is missing | not a charter / unreadable (or `--fail-on-wish` found wishes) |
| `keelcheck audit <repo>` | check gate hashes against the ratified table, the frozen original, the sections, the run record and the review state | no divergence | divergence of any kind | could not run honestly: no charter, no anchor, no git (or `--fail-on-wish` found wishes) |
| `keelcheck gate run <repo>` | run every ratified `kind: gate` row and record the run | every gate passed | a gate failed, a hash differs, a gate is missing, or no gate is ratified | could not run honestly |
| `keelcheck gate hash <path>` | print the content hash a gate row records, over git-normalized bytes | printed | — | no such file, or outside the repository |
| `keelcheck review <repo> --reviewer "<command>"` | run a clean-context reviewer and record what it was handed | review recorded, verdict `clean` | divergence, partial, unverified or inconsistent verdict, or the ratified prompt no longer matches its hash | could not run honestly: no charter, no anchor, no prompt, unwritable export/record, or the reviewer failed or timed out |
| `keelcheck adapter <harness>` | read one harness lifecycle event on stdin and answer it | allow | — | deny (the harness's decision object is printed) |
| `keelcheck adapter install <harness>` | write the harness settings entry | written | the file already defines hooks; re-run with `--force` | unknown harness, unreadable charter, or no anchor |
| `keelcheck hook install <repo>` | install the pre-commit hook that runs the gate | installed | already installed by something else | could not install |

`audit` also takes `--json`, `--record <path>` (move the run record), `--require-review`, and
`--fail-on-wish`. `gate run` takes `--record <path>` and `--json`. Run any command with `--help` for
its own options.

## The review

The mechanical half is deterministic. The half that needs judgement is the **clean-context review**: a
command you name is run once against a `.git`-less export of the current state, with the frozen original
and the mechanical findings beside it and the review prompt on its stdin. It must answer with exactly
one JSON object:

```json
{
  "verdict": "clean" | "divergence",
  "items": [{"class": "missing" | "unrequested" | "shifted",
             "subject": "…", "evidence": "…", "why": "…", "confidence": "high" | "low"}],
  "unreviewed": ["anything it could not judge"],
  "coverage": {"files_seen": 0, "files_total": 0},
  "reviewer": {"command": "…", "model": "…"}
}
```

Every finding must cite evidence that resolves inside the export; the count the reviewer reports is
checked against the count it was handed; a review that did not happen, a malformed answer, a timeout and
a failed command are all recorded as failures rather than as a pass. That is deliberate: a missing
review is a missing record, not a clean result.

`review-prompt.md` in this repository is the prompt the shipped `review` command uses, and this project
ratifies it in its own charter as a `kind: prompt` gate row. Use your own with `--prompt <path>` or
`--prompt-repo <repo>`; a prompt that is not ratified is accepted but recorded as unratified.

A stub command is a complete test double, so the whole surface can be exercised without a model.

## Integrations

- **Git hook** — `keelcheck hook install <repo>` writes a `pre-commit` hook that runs `gate run`; `hook
  status` reports what is installed. Every local hook can be bypassed (`git commit --no-verify`), which
  is why a bypass shows up in the audit as a **missing** run record rather than as a wrong one.
- **MCP** — `keelcheck mcp` speaks MCP on stdin/stdout, with no socket and no server, and the session
  ends when stdin closes. It exposes one tool: `audit`.
- **Harness adapter** — `keelcheck adapter install claude-code` writes a Claude Code `PreToolUse`
  settings entry; `keelcheck adapter claude-code` reads one event and answers allow (exit 0, no output)
  or deny (exit 2, with the harness's decision object). It refuses a write to the charter, to any path a
  ratified row names, and to the run record; it fails closed. It is a **guardrail, not an enforcement
  boundary**: an indirect rewrite such as `cd tools && rm gate.py` is not caught, and a harness with
  hooks disabled runs nothing.

## What is solid, and what is not

Solid, and covered by the test suite:

- the **anchored audit**: gate hashes are compared with the table at the `Ratified at:` commit, not with
  the working tree; the frozen-original block is diffed byte for byte; a gate that has never passed its
  own record is a divergence; a repository with no ratified executable gate is reported as vacuous,
  never clean;
- the **exit codes** above, including the distinction between a divergence and a run that could not be
  honest;
- the **append-only run record**, which is what turns a bypassed hook or a skipped gate into a visible
  missing record;
- the **review runner's contract**: export, manifest, validation, recording — testable with a stub
  command.

Not done, or not proved:

- **The review is judgement, not proof.** It is run by a command you choose; nothing outside that
  command can show that the reviewer had no prior knowledge of the project. The tool records what it
  handed over and under what conditions; a human has to judge the reviewer.
- **Hooks are reach, not enforcement.** Every local hook can be silenced by the agent it constrains
  (`--no-verify`, or a harness's kill switch). The guarantee is the audit's record, not the hook.
- **The adapter is a guardrail.** A write through an indirect path is not caught; a disabled harness runs
  no adapter.
- **Gates are only as good as what they check.** The audit verifies that a gate ran and that its bytes
  are the ratified bytes; it cannot tell whether the gate measures the right thing. A gate that passes
  can still be measuring nothing.
- **No CI is configured in this repository**, and **no package is published**. Claude Code is the only
  adapter target built so far.

## What it deliberately does not do

- **No daemon and no server.** A bounded CLI run and an MCP call that returns; no long-lived process, no
  listening socket.
- **No harness of its own.** A git hook, a CLI, an MCP session and an optional adapter — not another
  agent runtime.
- **Not a spec-authoring suite.** It freezes an original and audits against it; it does not maintain a
  living spec.
- **Not a memory or learning layer.** It keeps an anchor, not a memory.
- **Not a job runner.** It does not start, schedule or supervise work.

## Conventions

Decision numbers such as **D12** or **D19**, used in this repository's code, tests and charter, refer to
the project's internal decision record, which is not published. The charter's requirement and gate rows are
the normative text: wherever a decision number appears, the sentence beside it states what was decided, and
the number only records that a written decision exists behind it.

## Licence

MIT. See [`LICENSE`](LICENSE).
