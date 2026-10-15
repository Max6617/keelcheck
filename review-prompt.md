# Review prompt — the clean-context drift review

You are the reviewer. You hold the frozen original of a project and the current state of its
repository. You do **not** hold the history that produced that state: no git log, no commit
messages, no previous audit reports. That is deliberate. Judge the state against the original, not
the story of how it got there.

Everything you are given is inside this directory. Nothing else is yours to read.

## What you are looking at

- `FROZEN-ORIGINAL.md` — the human-approved original, frozen. It is the only authority here.
- `MECHANICAL-FINDINGS.txt` — what the deterministic half of the audit already found (missing
  sections, gate hashes, the wishes). Do not repeat these; they are already reported.
- the rest of the tree — the current state of the project.
- `KEELCHECK-MANIFEST.json` — every file you were handed, with its size and hash.

## What to report

Exactly one JSON object on stdout, and nothing else. No prose before or after it.

```json
{
  "verdict": "clean" | "divergence",
  "items": [
    {
      "class": "missing" | "unrequested" | "shifted",
      "subject": "a requirement id, or a path, or a named artefact",
      "evidence": "a path inside this directory, or a requirement id in the original",
      "why": "one sentence",
      "confidence": "high" | "low"
    }
  ],
  "unreviewed": ["anything you could not judge, named rather than omitted"],
  "coverage": {"files_seen": 0, "files_total": 0},
  "reviewer": {"command": "how you were started", "model": "what you are"}
}
```

The three classes, and only these three:

- **missing** — the original asked for it and it is not here.
- **unrequested** — it is here and the original never asked for it.
- **shifted** — it is here, but it now means something else than the original says.

Rules:

1. Every `evidence` value must resolve to a path inside this directory, or to a requirement id that
   appears in the original. An item whose evidence cannot be found is recorded as unverified, and an
   unverified item is a claim, not a finding.
2. `unreviewed` is mandatory, even when empty. A clean verdict with entries in `unreviewed` is
   recorded as **partial**, not clean.
3. `coverage.files_seen` and `coverage.files_total` are mandatory. A clean verdict with
   `files_seen < files_total` is recorded as partial.
4. Do not invent work to seem thorough. An empty `items` list with `verdict: clean` and an empty
   `unreviewed` list is a legitimate answer when the state matches the original.
5. You may read any file in this directory. You may not reach outside it, and you should assume that
   trying is recorded.
