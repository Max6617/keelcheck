# What the keel tests pin, and what they refuse to guess

`tests/` is Proctor's lane. This file records the contract the tests are written against, so a test is
never written against a guess (D3 in `../PROJECT-STATE.md`).

## The ruled contract (D3, corrected by D8)

The audit is exercised **only through the CLI**, never through `keel/` internals:

```
python -m keel audit <path-to-repo>
```

| exit | meaning |
|---|---|
| 0 | the audit ran; no divergence, **and at least one ratified gate was checked**. Wishes may exist and are reported; they do not change the exit code |
| 1 | divergence — a ratified gate's file hash differs from the reference at the ratification commit, a named gate has **no run record**, a required charter section is missing, the ratified/recorded pointers disagree, or **zero ratified gates were found (vacuity, D8)** |
| 2 | the audit could not run honestly (charter unparseable, ratification commit unreadable or unnamed), or `--fail-on-wish` was given and wishes exist |

D8 corrected D3 in two places the tests had already been written against, so both were changed in the
same commit as this note: **vacuity is a divergence, not a clean run**, and **the report prints all
four columns** — a requirement guarded only by a `checked-by` sentence is a human check, never silence.

Records: `.keel/runs.jsonl` (append-only, one JSON object per run, written even when the run fails)
and `.keel/review-context.json` (the runner's inputs for the clean-context reviewer, R4).

## The ruled gate shape (D8 ruled A1–A3; they are no longer assumptions)

- **A1** a gate is declared as `| gate | path | hash |` under a `## Gates` heading; the path is
  repo-relative; the hash is `sha256:<64 hex>` over the script's git-normalized bytes.
- **A2** the ratification commit is named as ``Ratified at: `<sha>` `` in the charter's living state
  **and** as the first line of `.keel/runs.jsonl`; the audit exits 1 when they disagree.
- **A3** the record paths above, tracked by git; `--record <path>` overrides the location (needed for
  the demonstration, because D4 keeps `rentguard/` read-only).

Only A1–A3's *shape* lives in `_support.ASSUMPTIONS`; the values above are ruled. One edit to
`_support.py` still moves every test if a shape changes again.

## Hashing is over normalized content, not worktree bytes (D9)

`_support.hash_bytes` normalizes `\r\n` → `\n` before hashing, because the host sets
`core.autocrlf=true` and a fresh Windows checkout writes CRLF while the blob is LF. A raw-bytes hash
would report a false divergence on every Windows checkout. `_support.hash_file` is that function; no
test hashes raw worktree bytes.

## The files

| file | what it is |
|---|---|
| `test_charter_silent_wish.py` | **Pins** of the parser's answers at `489f47d` (green on landing) plus one red — a `checked-by`-only requirement, hidden by the report. Mason's D8 render fix turned the red green; the pin set is unchanged. |
| `test_parser_boundaries.py` | **Red against landed code**: a requirement row silently dropped when its id cell is empty or its id column is labelled something unknown; a `checked-by` cell holding a zero-width character or `&nbsp;`, which renders blank but is read as content; the two-minute report as a third surface. Driven through `python -m keel.charter`, never imports. |
| `test_audit_cli.py` | **Red against `HEAD`**: the adversarial set — a missing section, a gate edited after ratification, a hash rewritten in the working-tree charter, a gate with no run record, a CRLF worktree that must **not** read as a hash divergence (D9), the append-only record, vacuity (D8), wishes non-fatal, `--fail-on-wish`, an unparseable charter, **the frozen original moving when the accepted recommendation is edited (D11/F9)**, and the clean-context file. The first test asserts `keel audit --help` exists, so no other test can pass because the command is unknown. |
| `test_cli_encoding.py` | `--json` on `rentguard/CHARTER.md` must survive a cp1252 stdout; the host's `PYTHONIOENCODING` is pinned inside the test, never inherited. |

## The anchor test, and a fixture trap it exposed

`test_editing_the_recommendation_moves_the_frozen_original` copies `keel/CHARTER.md`, points it at the
scratch repo's own ratification commit, records the baseline, then edits one word **inside the
accepted recommendation** and requires an `[original]` divergence. It is the red test D11/F9 asked for:
before the fix the parser anchored only the first blockquote (82 bytes), so that edit left the anchor
byte-identical.

Writing it exposed a trap in this suite's own fixture: `charter_text` used to place `Ratified at:`
between the frozen heading and the next heading, which is *inside* the anchored span. Since the pointer
is written after the ratification commit, every fixture would have carried a spurious `[original]`
divergence. The pointer now lives in a `## Ratification` section at the end — the same shape as the real
charter — so the baseline can assert the absence of `[original]` and the moved run its presence.

## Reference hashes and counts name their source

- A pin names the commit it was measured at. `_artefacts/` holds the raw runs:
  `assay_rentguard_parser_b81c374.{txt,json}`, `assay_parser_boundaries_b81c374.txt`, and
  `assay_suite_worktree-2026-10-14.txt` — the last is explicitly a **working-tree** measurement, with
  the dirty `git diff --stat` recorded inside it, because a working-tree count measures a moving
  target (rule 2).
- `_artefacts/probe_parser_boundaries.py` is the measurement script, not a test. It reproduces the
  CRLF hazard and the parser boundaries by hand and is safe to re-run.
- A pin is not a red test. D3: Mason landed R1 without a red test in front of it because `tests/` is
  not his file. Those backfilled tests say so; calling them red-first would be the laundering this
  project exists to catch.
