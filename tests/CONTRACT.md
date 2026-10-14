# What the keel tests pin, and what they refuse to guess

`tests/` is Proctor's lane. This file records the contract the red tests are written against, so a
test is never written against a guess (D3 in `../keel-project-state.md`).

## The ruled contract (D3)

The audit is exercised **only through the CLI**, never through `keel/` internals:

```
python -m keel audit <path-to-repo>
```

| exit | meaning |
|---|---|
| 0 | the audit ran; no divergence. Wishes may exist and are reported; they do not change the exit code |
| 1 | divergence: a ratified gate's file hash differs from `git show <sha>:CHARTER.md`, a named gate has **no run record**, or a required charter section is missing |
| 2 | the audit could not run honestly (charter unparseable, ratification commit unreadable), or `--fail-on-wish` was given and wishes exist |

Records: `.keel/runs.jsonl` (append-only, one JSON object per run) and `.keel/review-context.json`
(the runner's inputs for the clean-context reviewer, R4).

## Open assumptions — isolated in `_support.py`

D1/D3 fix the exit codes and the record paths but not the shape of a gate declaration or of the
ratification commit reference. Those live in `_support.ASSUMPTIONS` and nowhere else, so one edit to
`_support.py` moves every test when Gilbert rules them:

- **A1** a gate is declared as `| gate | path | hash |` under a `## Gates` heading;
- **A2** the ratification commit is named in the charter's living state as ``Ratified at: `<sha>` ``,
  and the reference hash is read with `git show <sha>:CHARTER.md` (D1);
- **A3** `.keel/runs.jsonl` and `.keel/review-context.json` as above.

## The files

| file | what it is |
|---|---|
| `test_charter_silent_wish.py` | **Pins** of the parser's answers at `489f47d` (green on landing) plus one red: a `checked-by` sentence keeps a requirement out of the wishes and the report never prints the column, so a charter can read "0 wishes, 0 asserted" while a sentence is the only guard. |
| `test_cli_encoding.py` | Red: `--json` on `rentguard/CHARTER.md` exits 1 under a cp1252 stdout (`UnicodeEncodeError` on `→`). `PYTHONIOENCODING` is pinned in the test. |
| `test_audit_cli.py` | Red: the adversarial set — a missing section, a gate edited after ratification, a hash rewritten in the working-tree charter, a gate with no run record, the append-only record, wishes non-fatal, `--fail-on-wish`, an unparseable charter, and the clean-context file. First test asserts `keel audit --help` exists, so no other test can pass because the command is unknown. |

## A pin is not a red test

D3: Mason landed R1 without a red test in front of it because `tests/` is not his file. Those
backfilled tests are **pins** — green on landing, labelled as such. Calling them red-first would be
the laundering this project exists to catch.
