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
| 1 | divergence — a ratified gate's file hash differs from the reference at the ratification commit, a named gate has **no run record**, a required charter section is missing, the anchor **moved** since the last record entry (`[anchor-moved]`, D12), an `enforced-by` names a repo path that does not resolve (`[unbuilt]`, D13), or **zero ratified gates were found (vacuity, D8)** |
| 2 | the audit could not run honestly (charter unparseable or unnamed, no `Ratified at:` line, no git), or `--fail-on-wish` was given and wishes exist |

D8 corrected D3 in two places the tests had already been written against, so both were changed in the
same commit as this note: **vacuity is a divergence, not a clean run**, and **the report prints all
four columns** — a requirement guarded only by a `checked-by` sentence is a human check, never silence.
D12 and D13 then added three classes the tests must not treat as clean.

Records: `.keel/runs.jsonl` (append-only, one JSON object per run, written even when the run fails)
and `.keel/review-context.json` (the runner's inputs for the clean-context reviewer, R4).

## The ruled gate shape (D8 ruled A1–A3; A2 superseded by D12)

- **A1** a gate is declared as `| gate | path | hash |` under a `## Gates` heading; the path is
  repo-relative; the hash is `sha256:<64 hex>` over the script's git-normalized bytes.
- **A2 (D12)** the anchor lives in exactly **one** place: the charter's `Ratified at: <sha>` line, in
  the canonical plain spelling (other spellings still parse and are reported `[format]`). A charter
  with no such line is exit 2, never 0. D8's second copy in the record's header was withdrawn: the
  record is append-only, so a legitimate re-ratification would leave that copy stale forever. The
  record keeps the anchor **used on each run**, and when it differs from the previous entry the audit
  prints `[anchor-moved]`, names both SHAs and exits 1.
- **A3** the record paths above, tracked by git; `--record <path>` overrides the location (needed for
  the demonstration, because D4 keeps `rentguard/` read-only). `keel audit` accepts a directory and
  writes `<dir>/runs.jsonl`; `keel gate run` does not yet — that is red in `test_gate_cli.py`.

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
| `test_parser_boundaries.py` | **Red against landed code**: a requirement row silently dropped when its id cell is empty or its id column is labelled something unknown; a `checked-by` cell holding a zero-width character or `&nbsp;`, which renders blank but is read as content. Driven through `python -m keel.charter`, never imports, with a **crash guard** — a traceback's non-zero exit is not an acceptable answer, or a broken parser would turn every hole into a pass. Both holes were open at `ec18e0c` and closed in Mason's uncommitted build; the tests stay as regressions. |
| `test_audit_cli.py` | **Red against `HEAD`**: the adversarial set — a missing section, a gate edited after ratification, a hash rewritten in the working-tree charter, a gate with no run record, a CRLF worktree that must **not** read as a gate content change (D9), the append-only record, vacuity (D8), wishes non-fatal, `--fail-on-wish`, an unparseable charter, **the frozen original moving when the accepted recommendation is edited (D11/F9)**, and the clean-context file. The first test asserts `keel audit --help` exists, so no other test can pass because the command is unknown. |
| `test_gate_cli.py` | **Two reds, four pins** on `keel gate run` / `keel gate hash`: a gate that **ran and failed** (or timed out) is recorded with the ratified hash, the audit accepts the record and reports **exit 0, no divergences**; and `--record <directory>` works for `keel audit` but not for `keel gate run`, which executes the gate and then exits 2 without recording it. Pins: an audit run never counts as a gate run (the skipped-gate property), a gate whose content changed is never executed, `hash`/`ratified` are D10's two sides, and `gate hash` is git-normalized (D9). |
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
  `assay_rentguard_parser_b81c374.{txt,json}`, `assay_parser_boundaries_b81c374.txt` (before the
  parser fix, named to the commit) and `assay_parser_boundaries_worktree-2026-10-14.txt` (after it,
  measured while the fix was still uncommitted), plus `assay_suite_7ed69e3.txt` — the suite at a
  **clean tree**, so the 35-passed count is reproducible from that commit rather than read off a dirty
  worktree. Where a count had to be taken on a dirty tree, the artefact records `git status` and
  `git diff --stat` inside itself, because a working-tree count measures a moving target (rule 2).
- `_artefacts/probe_parser_boundaries.py` is the measurement script, not a test. It reproduces the
  CRLF hazard and the parser boundaries by hand and is safe to re-run.
- A pin is not a red test. D3: Mason landed R1 without a red test in front of it because `tests/` is
  not his file. Those backfilled tests say so; calling them red-first would be the laundering this
  project exists to catch.

## Open reds at `55cd6d7` — three, all measured

Suite: **3 failed / 46 passed** at that commit (Mason's D12/D13 build, tree clean). Each is a
contradiction between a D-numbered ruling and what the command does, not a guess:

1. **A charter with no `Ratified at:` line exits 1, not 2.**
   `test_a_charter_with_no_ratification_pointer_cannot_run_honestly` — D12 says "exit 2, never 0".
   `compute_exit` returns divergence when a finding exists before it consults `cannot_run`, and the
   vacuity finding fires because there is no reference. The number is wrong for the right reason.
2. **D13's carve-out is by name, not by what the run wrote.**
   `test_the_unbuilt_carve_out_covers_only_what_this_run_writes` — with `--record <elsewhere>`, a
   requirement whose `enforced-by` is `.keel/runs.jsonl` counts as built while `.keel/` does not
   exist. The carve-out is for "the two files the audit itself produces"; when the run produces them
   elsewhere, the exception does not apply on its own terms. Deliberate on Mason's side (the defaults
   count too) — the test is the question.
3. **`keel charter` never acts on its own findings.**
   `test_keel_charter_exit_codes_are_the_ones_d12_rules` — a charter missing a required section and a
   file with 0/6 required sections both exit 0, while D12 rules 1 and 2.

Fixed and now pinned at the same commit: a gate record counts only when its `result` is `pass`
(fail/timeout/error each named with the recorded result); `keel gate run --record <dir>` and
`keel audit --record <dir>` agree; the record header carries no anchor; `[anchor-moved]` names both
SHAs and fires once; a non-canonical pointer is `[format]` and quotes the line.
