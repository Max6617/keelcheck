# What the keelcheck tests pin, and what they refuse to guess

`tests/` is Proctor's lane. This file records the contract the tests are written against, so a test is
never written against a guess (D3 in `../PROJECT-STATE.md`).

## The ruled contract (D3, corrected by D8)

The audit is exercised **only through the CLI**, never through `keelcheck/` internals:

```
python -m keelcheck audit <path-to-repo>
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
  the demonstration, because D4 keeps `rentguard/` read-only). `keelcheck audit` accepts a directory and
  writes `<dir>/runs.jsonl`; `keelcheck gate run` does not yet — that is red in `test_gate_cli.py`.

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
| `test_parser_boundaries.py` | **Red against landed code**: a requirement row silently dropped when its id cell is empty or its id column is labelled something unknown; a `checked-by` cell holding a zero-width character or `&nbsp;`, which renders blank but is read as content. Driven through `python -m keelcheck.charter`, never imports, with a **crash guard** — a traceback's non-zero exit is not an acceptable answer, or a broken parser would turn every hole into a pass. Both holes were open at `ec18e0c` and closed in Mason's uncommitted build; the tests stay as regressions. |
| `test_audit_cli.py` | **Red against `HEAD`**: the adversarial set — a missing section, a gate edited after ratification, a hash rewritten in the working-tree charter, a gate with no run record, a CRLF worktree that must **not** read as a gate content change (D9), the append-only record, vacuity (D8), wishes non-fatal, `--fail-on-wish`, an unparseable charter, **the frozen original moving when the accepted recommendation is edited (D11/F9)**, and the clean-context file. The first test asserts `keelcheck audit --help` exists, so no other test can pass because the command is unknown. |
| `test_gate_cli.py` | **Two reds, four pins** on `keelcheck gate run` / `keelcheck gate hash`: a gate that **ran and failed** (or timed out) is recorded with the ratified hash, the audit accepts the record and reports **exit 0, no divergences**; and `--record <directory>` works for `keelcheck audit` but not for `keelcheck gate run`, which executes the gate and then exits 2 without recording it. Pins: an audit run never counts as a gate run (the skipped-gate property), a gate whose content changed is never executed, `hash`/`ratified` are D10's two sides, and `gate hash` is git-normalized (D9). |
| `test_cli_encoding.py` | `--json` on `rentguard/CHARTER.md` must survive a cp1252 stdout; the host's `PYTHONIOENCODING` is pinned inside the test, never inherited. Asserts `!= 2` and that the arrow round-trips, because D12 moved the exit code and `== 0` was asserting the fixture's cleanliness. |
| `test_hook_cli.py` | **Red at `7371668`, built at `08771ce`.** Installer: a failing ratified gate must **block a commit** and a passing one must let it land (the second is the guard against a git-caused block); the hook must leave the `kind: gate` record the audit reads; an existing hook is never clobbered and `--force` keeps it as `pre-commit.keelcheck-backup`; no anchor → install nothing, exit 2; idempotent; POSIX `#!/bin/sh` with no CRLF; the body carries a marker and absolute paths. **Five git-level tests skip on this host** (git's `sh.exe` cannot start — see below); the hook's command is executed directly by four others, so the *behaviour* of the body is still verified here. |
| `test_review_cli.py` | **Red against `6810818`, closed at `e9ec9a1`/`18023d9`.** The clean-context review with stub reviewers: the state is always reported and is divergence only when required; verdict mapping (clean 0, partial/divergence/unverified 1); evidence checked against the export **and** the charter; malformed/error/timeout recorded with a reason and exit 2; fresh → stale on one byte → fresh again; a failed review never satisfies a required one, a partial one does (presence is mechanical); the prompt is a hashed artefact and a weakened one is refused before a review runs; the reviewer is never run through a shell; the export carries the prompt and no history, no secrets, no committed record directory; the vacuity message names what it tested. |

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

## The D12/D13 round: measured, filed, closed at `e8fb52e`

Suite: **49 passed** at that commit. The three reds Proctor filed at `92cfeec` are closed there:

1. **A charter with no `Ratified at:` line is exit 2.** `compute_exit` now sorts findings into content
   divergences and vacuity, and vacuity alone no longer overrides "not auditable"; a content
   divergence without an anchor still wins, so a missing section in an unratified charter stays 1.
   Test: `test_a_charter_with_no_ratification_pointer_cannot_run_honestly`.
2. **D13's carve-out covers only the two paths *this run* writes**, at the `--record` location. With
   the record elsewhere, `.keel/runs.jsonl` named in a cell is `[unbuilt]` — including keelcheck's own R4
   when audited with `--record` outside the repo, which is a cell fix for Gilbert, not a code fix.
   Test: `test_the_unbuilt_carve_out_covers_only_what_this_run_writes`.
3. **`keelcheck charter` is exit 1 for a parsed charter with findings, 2 when the file is not a charter** —
   no `## Requirements` section is a format failure, exactly like a heading with no table.
   Test: `test_keel_charter_exit_codes_are_the_ones_d12_rules`.

Fixed and pinned in the same round: a gate record counts only when its `result` is `pass`
(fail/timeout/error each named with the recorded result); `keelcheck gate run --record <dir>` and
`keelcheck audit --record <dir>` agree; the record header carries no anchor; `[anchor-moved]` names both
SHAs and fires once; a non-canonical pointer is `[format]` and quotes the line.

**One test changed because D12 moved the exit code, not the subject.** `test_cli_encoding.py` used to
require `returncode == 0` on the rentguard snapshot; that asserted the charter's cleanliness, which is
`test_charter_silent_wish`'s business. It now requires `!= 2`, no `UnicodeEncodeError`, and that the
arrow round-trips through the JSON — the encoding property it exists for.

## The review round, and the R5 environment split

**Suite at 1aa89b7: 88 passed, 5 skipped.** Both numbers are measurements, not estimates.

**Two real findings came out of 	est_review_cli.py, and both were red against landed code** — so the
ordering was red-after-code, named rather than dressed up as red-first:

1. **Evidence was verified by containment only.** _inside_export returned True for *any* relative
   string, because Path.resolve() does not require the target to exist and the only test was that
   the result sat under the export root. 
o-such-file.md and R999 both counted as verified, and
   the requirement-id branch D15 names was not implemented at all. Fixed at e9ec9a1.
2. **The export did not carry the prompt.** REVIEW-PROMPT.md was not written into the tree, so what
   the reviewer was told was not part of what was handed over whenever the prompt was not a tracked
   repo file. Fixed at e9ec9a1.

**One test was split, not made flaky.** The .env/private.pem test also asserted REVIEW-PROMPT.md
was present; that assertion failed once — correctly, because the file was missing — and the fix
followed. The secret-file case itself never failed. The two properties are now separate tests. Mason's
candidate for a real flake — two reviews in the same repo inside one second share

eview-<utc second>/ — is a naming risk, not something this suite can trigger deterministically
from outside; it is on the record instead of being covered by a test that only sometimes runs.

**The R5 split is environmental and auto-detected.** git for Windows runs hooks through its own
sh.exe, and under this host's sandbox sh.exe cannot create its named objects
(NtCreateDirectoryObject(...msys-2.0S5-...): 0xC0000022) — the same limitation that makes git
clone impossible here. So *every* hook fails to start, which means the git-level tests cannot measure
anything: the block test would pass because sh crashed, not because the gate failed. _git_sh_works()
probes it with a **trivial foreign hook**, never one of ours, so a broken installer cannot skip its own
tests. The five git-level tests skip with that reason; four tests execute the installed hook's exec
line directly (passing → exit 0 and a passing kind: gate record the audit accepts, failing → exit 1,
python off PATH → still exit 0), and the body's marker and absolute paths are pinned on the text.
On a host where sh works, the five come back.
## Backlog properties, taken in order

**Covered at 10f6e2 + these tests (45 passed, 5 skipped in the two files):**

- **The cap and the never-omitted rule** (design item 8). A 21 MB tracked file trips the byte cap, the
  line records 	runcated: true, and the gate script a row names is still in the export along with
  the charter. ig.bin sorts before 	ools/gate.py, so a naive cap drops the named path first.
- **--export DIR**: the tree lands under the caller's directory and the record points at it.
- **The 1 MB stdout cap**: over it, 
esult: malformed and the reason names the cap.
- **core.hooksPath**: the installer resolves the hooks directory through git, so the hook lands in
  .githooks/pre-commit and not in the default directory.

**Still open, named rather than claimed:**

- *Symlinks that leave the export.* Needs a real symlink; os.symlink on this host is
  privilege-dependent, so it lands behind a capability probe (skips here) unless it works.
- *The coverage gate* (	ools/coverage.py, R8/D13). Its red needs the script's interface stated
  first — above all **how the floor is forced low enough to test the failing side** without editing
  the script, since the red has to prove the gate fails below the floor, not only passes above it.
## Corrections to this file's own findings

- **The checkout-dependent manifest was my fixture, not the code** (withdrawn 2026-10-14, same night
  it was filed). _support.write used Path.write_text, which translates to CRLF on Windows, so
  every fixture was CRLF in the worktree while git stored whatever was committed — D9's class, and it
  produced a false red against uild_manifest. With the fixture written LF and one state reviewed
  under both core.autocrlf configurations, both reviews produce the same manifest hash. The helper
  now writes LF, so a fixture carries the bytes a checkout of it would have. core.autocrlf is
  repo-wide, so the linked worktree in that test was never a second checkout; the test says so.
- **D21 (Gilbert).** A working-copy prompt edit is disclosed, not refused: the reviewer receives the
  anchored bytes and the line must carry working_copy_differs: true plus the working file's hash.
  A self-inconsistent anchor still refuses. Only the disclosure is missing at ee9fa6a.