# The clean-context drift review — design proposal

By **Mason**, 2026-10-14. **Status: proposal, no code.** Written so the claim can be attacked
before it exists (Gilbert's instruction, this turn). Not a decision; D-numbered rulings are Gilbert's.

The mechanical half landed at `2006f46`: hash-locked gates, the anchor, vacuity, the wishes. This is
the other half — the one R3/R4 hinge on and nothing yet implements.

## What the claim has to be

R4: the drift review runs with **clean context** — a fresh agent holding only the frozen original and
the current state, never the history that produced it. R3: the output is a classified list —
**missing / unrequested / shifted** — plus the wishes. W2 already admits the hole: *clean context is
asserted, not proved; the strongest available check is that the runner records what it handed the
reviewer.*

So the design has to do two things at once: make the reviewer as clean as a local mechanism can make
it, and make the runner's claim about what it handed over **auditable** rather than trusted. The
second is the part that can be built honestly; the first has a residual that no local mechanism closes
(section 5).

## 1. How the runner obtains a reviewer with no history

Three levels, in increasing strength. The runner takes the strongest available, and **records which
one it got** — because "the reviewer was clean" is not a boolean the tool can observe, but "the history
was not reachable from where the reviewer ran" is.

**T1 — prompt only (weakest, always available).** `keel review <repo> --reviewer "<command>"` builds
the prompt from `.keel/review-context.json`, writes it to the command's stdin, and reads one JSON
object from its stdout. The reviewer is a *process the user names* and the runner starts: no session
id, no transcript, none of the tool state that produced the work. Any harness is one command string
(`claude -p`, `codex exec`, a local model, a script). The tool requires none of them — R5 puts the
harness adapter last and optional, and this keeps it there.

**T2 — history out of reach (recommended default).** The runner exports the current state to
`.keel/review/<run>/tree/`: the audited worktree **with `.git` removed**, built by allow-list (tracked
files plus the working tree, minus `.git` and minus the record directory), plus `FROZEN-ORIGINAL.md`
(the anchor block, with its byte length and hash) and `MECHANICAL-FINDINGS.txt`. The reviewer is
started with that directory as its cwd. Clean context then stops being a promise about the model's
*input* and becomes a property of its *reach*: there is no git log, no commit message, no reflog, no
stash and no previous audit report in the directory it is pointed at, even if it tries to look. A
reviewer that runs shell commands cannot escape the export accidentally; it can only leave it
deliberately, which is visible in what it returns.

**T3 — another machine or credential (strongest, optional).** Nothing is required of the tool: the T2
export is a directory, so it can be shipped to a clean container, a different vendor, or another
person. The interface stays at T2 so that T3 is a deployment choice, not a second code path.

**This environment.** A DSH subagent the runner starts has its own context and never sees the parent's
transcript — that is T1 with a guaranteed-fresh conversation, which is the strongest freshness
available to us. It is *not* T2 by itself: a subagent can run shell commands, so unless it is pointed
at the export it can `git log` in the audited repository. T1 + T2 together is what we can actually run
here: fresh conversation, history-free directory. What the runner records either way is
`history_reachable: none | git | unknown` — `none` when it built the export and `.git` was absent,
`git` when it fell back to running in the repository, `unknown` when the user pointed it somewhere the
tool did not build.

## 2. What the runner hands over

Two artefacts, both hashed and both recorded.

**`.keel/review-context.json` — the framing.** Already implemented at `2006f46` and written by every
audit: the frozen original (text, byte length, `sha256`), the living state (every requirement with all
four columns, the wishes, the human checks, the asserted enforcement), the gate table (ratified vs
measured), the mechanical findings, and an inventory (path, bytes, tracked flag). Deliberately absent:
the git log, commit messages, previous audit reports, and any file *content* other than the charter.
The reviewer's value comes from not having the narrative of how the repository got here.

**`.keel/review/<run>/tree/` — the current state as content.** The export from T2 plus the two
generated files. The reviewer reads *this*, not the repository: path citations in its output are
resolved against the export, so an item that cites a file it invented is visible.

**`REVIEW-PROMPT.md` — the whole instruction.** The anchor block, the three class definitions with one
example each, the output schema, and the rule that anything it cannot judge goes in `unreviewed`. It
is the same text for every project, and it is *in the export*, so what the reviewer was told is part of
what was handed over.

**Size is bounded and the bound is stated.** Default cap (say 2000 files / 20 MB). Over the cap the
runner exports the inventory plus the files that requirements and gates name, and marks the review
`partial` with the omitted count — a bounded review that says what it did not see, never a silent
truncation.

## 3. What the reviewer must return

Exactly one JSON object on stdout, validated before anything is recorded:

```json
{
  "verdict": "clean" | "divergence",
  "items": [
    {"class": "missing" | "unrequested" | "shifted",
     "subject": "R4 or keel/gate.py or the hook installer",
     "evidence": "a path in the export, or a requirement id in the charter",
     "why": "one sentence",
     "confidence": "high" | "low"}
  ],
  "unreviewed": ["what it could not judge, named, not omitted"],
  "reviewer": {"command": "...", "model": "..."}
}
```

The rules the runner enforces **mechanically** — which is what makes this half testable with no model
at all (a stub command that prints JSON is a complete test double, so Proctor can attack this surface
deterministically):

- a `class` outside the three, an item with no `evidence`, or output that is not one JSON object is
  **rejected and named**: recorded as `malformed`, the audit exits 2, never a silent pass;
- every `evidence` string must resolve to a path in the export or a requirement id in the charter;
  when it does not, the item is kept and marked `evidence-missing` — a model's citation is checked,
  never trusted;
- `unreviewed` must be present even when empty: a reviewer that reports clean and names what it could
  not see is honest, and one that reports clean and names nothing is claiming total coverage;
- `verdict: clean` with items, or `divergence` with none, is a contradiction and is reported as one;
- the runner never rewrites the reviewer's words. It validates, counts, and prints them with
  provenance.

## 4. How the tool records what it handed over

This is where W2 gets a real answer, by the same move that made D1 and D2 work.

- The context file's own `sha256`, the export **manifest** (path, bytes, sha256 per file, plus
  `git_absent: true`) and the prompt's hash are recorded in the append-only record as a
  `kind: "review"` line: the command and argv, the two hashes, the exit status, the item count per
  class, and the `unreviewed` list.
- **A required review that did not happen is a missing record, not a wrong one.** `keel audit
  --require-review` reports "no clean-context review recorded for commit X" as a first-class
  divergence. R4 then stops being a promise the runner makes and becomes a fact the audit can see
  *missing* — exactly how a bypassed hook became visible in D1/D2.
- The two-minute report prints the verdict with its provenance: reviewer command, the model if the
  reviewer names one, the context hash, `history_reachable`, and what it listed as unseen. A drift
  item with no provenance is not printed as a finding.
- **The reviewer's output is a claim, and the audit treats it as one.** It is reported separately from
  the mechanical findings; the mechanical half never consults it; `--fail-on-drift` is opt-in. A model
  may inform a human verdict and may never be the only enforcement (INTENT-LOOP), and that is also why
  the review cannot be what decides exit 0.

## 5. The failure mode I cannot rule out

**The reviewer already knows the history, and the tool cannot tell.** T2 removes history from the
reviewer's *reach*; it says nothing about the reviewer's *prior*. Three ways it happens anyway: the
harness reuses a session, or hands a subagent a context inherited from the parent; the harness
auto-loads memory or rules files that narrate the project (ECC does exactly this, and it is the
harness most likely to host us); the model carries the project in its weights, in a vendor-side cache,
or from an earlier session — and this project's own Bots are the clearest case, since a Bot asked to
review keel has been in the loop. What the tool can do is record the input and the command; a human
has to judge the reviewer. Stated rather than smoothed over, in D1's residual class.

**Second, and it limits the method even with a truly fresh reviewer:** a fresh reviewer can rationalise
too. Its bias is not "we meant this" but "this must be meant" — handed an anchor and a pile of code, it
will invent intent for what it sees, and it cannot know what was *possible but absent*. The unexercised
volume path in rentguard's W3 is the example: it is visible in the current state only as prose in the
charter, and a reviewer reading code will not miss a folder that is not there. `unreviewed` plus
per-requirement coverage is the mitigation; it is not a cure, and this is a ceiling on what "drift
review" can promise.

**Third, smaller: it is not deterministic.** Two runs disagree and the record then holds both. The
audit reports the newest with its provenance and never averages — but a reviewer that flips between
runs is useless as a gate, which is a further reason the drift half stays a human input rather than an
exit code.

## 6. Build order, and what it costs

1. `keel review <repo> --reviewer "<command>"`: build the export, run the command, validate the JSON,
   append the `review` line. **No model needed for a test** — a stub command covers all of it.
2. `keel audit --require-review`: read the record for a review of the current commit and report a
   missing one as divergence.
3. Harness adapters last, from primary sources (Sift's `research/gates-per-harness.md` is the input),
   documented as examples of a command string, never as a dependency.

## 7. Attacks folded in (Proctor, 2026-10-14)

Eight holes Proctor found in this document, and what each one changes. They are also the
acceptance list for `keel review`, testable with a stub command.

1. **Evidence could leave the export.** "Resolve to a path in the export" as written accepted
   `../PROJECT-STATE.md`, an absolute path, or a symlink pointing out. Fixed: evidence is
   canonicalized against the export root (`realpath`, then a check that it is under the root),
   an absolute path or any `..` that escapes is `evidence-missing`, and the export itself never
   follows a symlink whose target leaves it.
2. **`verdict: clean` with a non-empty `unreviewed` read as clean.** Fixed: a clean verdict with
   any unreviewed entry is recorded and printed as **`partial`**, and a partial review does not
   satisfy `--require-review` for a requirement whose mechanism is a gate-class check.
3. **A divergence whose every item is `evidence-missing` is a claim backed by nothing.** Fixed:
   items are counted as `verified` and `unverified` separately in the record, and a divergence
   with no verified item is recorded as `unverified` — a claim, never a confirmed finding. The
   record therefore distinguishes a claim from a verified claim.
4. **`--require-review` must make presence mechanical, never the verdict.** Written into the
   design: no exit code ever depends on `verdict` or on item counts. The only exit effect of the
   review is a **missing**, **stale** or **malformed** review line. Anything else would make a
   model the sole enforcement, which INTENT-LOOP forbids.
5. **"No review for commit X" needed a definition of X.** Keyed to HEAD it goes red on every
   commit, including during the R7 demonstration. Fixed: the review line records the export
   **manifest hash**, and `--require-review` demands a review whose manifest matches the manifest
   of the current state. A review of a different state is reported as **stale** (naming both
   manifest hashes), distinct from missing.
6. **Nothing bounded the reviewer's output or runtime.** Fixed, mirroring the gate runner: a
   `--timeout` (default 600 s); a stdout cap (1 MB) over which the output is `malformed`; a
   non-zero exit, a command that cannot start, or a timeout is recorded as `error` with the
   OS error or the stderr tail as the reason — written to the record even when the run fails.
7. **The export is a leak surface.** Fixed by never shipping more than the judgement needs: only
   files in the audited revision plus the working tree's changes to them; a deny-list for
   `.env*`, `*.pem`, `*.key`, `id_*`, `.ssh/` and anything the charter's permissions name;
   `.gitignore`d files are not exported. Symlinks are never followed — one whose target leaves
   the export is listed in the manifest as `symlink-outside` and skipped. Every skipped path and
   the reason goes in the manifest, so a leak is visible in the record rather than silent. And
   the plain fact stays in the document: the export is handed to *whatever command the user
   names*, so a third-party model means third-party data.
8. **The cap is a place to hide.** Fixed: the omitted set may never contain a file that a
   requirement, a gate or a finding names; the omitted count and the full omitted-path list go in
   the manifest and are printed in the two-minute report. `unreviewed` gets a denominator: the
   prompt requires `coverage: {files_seen, files_total}`, and a `clean` verdict with
   `files_seen < files_total` is recorded as `partial`, like (2).

Two of these (1 and 7) are the same property from both ends — the reviewer's citations and the
runner's export must both be confined to one directory — and they are the reason the export root,
not the repository root, is the reference point for everything the reviewer says.

## Open questions for Gilbert (rulings, not guesses)

1. **Is the review prompt a hashed artefact like a gate?** If its hash is in the charter's living state
   and compared at the ratified revision, a model cannot weaken the reviewer's instructions — R2's rule
   applied to one more artefact. A1's gate table is for executable scripts, so this needs a shape
   rather than a reuse.
2. **Is `--require-review` the default for the R7 demonstration, or opt-in?** Default makes R4 a
   mechanism; opt-in keeps the mechanical half usable alone, which the tool should be.
3. **One record file or two?** I propose the `review` line in the same `runs.jsonl`, so a bypass and a
   missing review are the same shape of absence. A separate file is easier to read and easier to drop.
