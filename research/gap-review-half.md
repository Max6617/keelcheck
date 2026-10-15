# The largest claim-vs-proof gap: the review half — Sift, 2026-10-15

Question from Gilbert: after tonight's work, where is the single largest gap between what keelcheck
*claims* and what it *proves* — the audit half, the review half, or the export? Answer, evidence, and
the smallest deliverable that would close it. Nothing here is built.

**Revision.** Measured on `keel@2ac1aec`, working tree as it stood at 2026-10-15 ~22:20.

## The gap: the review half

**R3** names the mechanism for classifying divergence as "the drift review (clean context)" and **R4**
claims "a fresh agent holding only the frozen original and the current state". What the tool proves is
that **a caller-named command ran with the export as its cwd and printed one well-formed JSON object** —
and nothing more, because the one number that could anchor that claim to the state the tool itself
handed over is taken from the reviewer instead of from the manifest. `validate_output(stdout, tree,
requirement_ids)` (`keelcheck/review.py:371`) reads `coverage.files_seen` / `coverage.files_total` from
the reviewer's JSON and only ever asks whether `seen < total` (`:423-424`); the runner has the
authoritative count in hand (`manifest["count"]`, `:539`) and does not pass it. The design's §7 item 8
introduced that denominator exactly to stop the cap being "a place to hide" — but the denominator is a
self-report, so a reviewer that saw nothing can declare itself complete and be recorded `clean`.

**Measured, not argued.** On keelcheck's own tree, with the record and export outside the repository, a
four-line stub — `print(json.dumps({"verdict": "clean", "items": [], "unreviewed": [],
"coverage": {"files_seen": 999999, "files_total": 999999}}))` — produced:

```
review: clean  (pass)          review exit: 0
prompt:   review-prompt.md (ratified in keel@688fce8)
export:   ...\exp\tree  (76 files, 794447 bytes)
recorded: verdict=clean  result=pass  prompt_ratified=True  files=76  coverage=999999/999999
```

and `keelcheck audit . --require-review` prints **`REVIEW (clean context, R4): fresh`**. The audit's
one divergence was unrelated (`[gate-record] suite: no run record`). So a command that never read the
export, never called a model, and claimed to have seen 999,999 files in a 76-file export **satisfied
R4's presence check** and is recorded indistinguishably from a real clean-context review.

**Why this is the largest of the three.** The audit half's claims are locally checkable and are
checked: the frozen block is diffed against the anchor, gate hashes are compared, vacuity and
`[unbuilt]` are reported, and a gate with no run record is divergence — a forged record is the same
*shape* of weakness, but the claim there ("the audit fails when a hash differs", R2) is exactly what is
proved. The export's reach is proved by the manifest and was measured (findings 2–4 in
`review-attack.md`). The review half is where the claim is largest and the proof thinnest: the design
already admits the *prior* residual (§5: a reviewer that knows the history) and deliberate escape (§1
correction); it does **not** admit that **no reviewer need exist at all**, and the property that makes
the surface testable — "a stub command is a complete test double" (§3, §6) — is the same property that
makes the record forgeable.

Two supporting facts, recorded and not part of the gap: the charter's R4 row still says *"the runner
that starts the reviewer is not built"* while `keelcheck review` is built, wired into the CLI and tested
— the state column understates what exists; and `--require-review`'s presence check is, by ruling
(§7.4, §8), never allowed to depend on the verdict, so the gap cannot be closed by making the model's
word load-bearing.

## The smallest deliverable that would close it

Two changes, both the same shape as mechanisms the project already trusts (D15/D21's ratified prompt,
D8's run-record presence), and both testable with stubs and **no model and no spend**:

1. **Bind the denominator to the manifest.** Pass `manifest["count"]` into `validate_output` and treat a
   review whose `files_total` differs from it — or whose `files_seen > files_total` — as
   `inconsistent`: recorded, printed, and not satisfying `Review: required`. This makes the coverage
   claim a checked claim against a hash the tool already owns.
2. **Ratify the reviewer, as the prompt was ratified.** A gate-table row with `kind: reviewer` naming
   the accepted command (the prompt's move, one row kind over). A review line whose command does not
   match the ratified row is reported `[reviewer-unratified]` and does not satisfy `Review: required`
   for the demonstration. Substitution then becomes loud rather than silent, which is the tier the
   whole project runs at (D2, D10, D12).

**Size:** one validation change, one new gate-row kind, one comparison, one report line, two red tests
whose negative fixture is the stub above — the same stub that passes today. It touches
`keelcheck/review.py`, `keelcheck/charter.py` and `tests/`, so it is Mason's and Proctor's lanes, not
mine. **What it does not close**, and should not pretend to: a ratified reviewer can still *know* the
history, and a deliberate escape is still undetected locally. Those remain the design's named
residuals — the point of this deliverable is only to make "a clean-context review happened" mean
"a ratified command ran against this manifest's contents", instead of "some command printed JSON".
