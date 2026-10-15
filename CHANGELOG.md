# Changelog

Notable changes, newest first. The project follows semantic versioning once it has users; before that,
every release is `0.x` and may change anything.

## 0.0.1 — unreleased

First release. One frozen, human-approved original per project, with every requirement in it naming the
mechanism that upholds it (`enforced-by:`) or the check that judges it (`checked-by:`); a requirement
with neither is reported as a **wish**, and a mechanism that does not resolve in the repository as
`[unbuilt]`.

**What it does**

- `keelcheck charter <path>` parses a charter and reports the requirements that name no mechanism.
- `keelcheck audit <repo>` diffs the frozen original at the ratification anchor and reports divergence in
  three classes — missing / unrequested / shifted — plus the wishes.
- `keelcheck gate run <repo>` runs the ratified gates on a clean tree and records the run;
  `keelcheck gate hash <path>` prints the content hash a gate row records.
- `keelcheck review <repo> --reviewer "<command>"` starts a clean-context reviewer and records what it was
  handed.
- `keelcheck hook install <repo>` / `hook status <repo>` install and report the pre-commit hook that runs
  the ratified gates.

**Not in 0.0.1**

- The MCP surface (R5's third integration surface) — `python -m keelcheck mcp` does not exist yet.
- The harness hook adapter (R5's fourth).

**Known gaps, named rather than implied**

- R7's drift half names 1–2 of the 5 by-hand defects on the demonstration repository, not 5 of 5.
- There is no CI; R8's own cell says the suite and the gate run on a checkout, not in a pipeline.
- Publishing is the user's decision alone (R9). At `0.0.1 — unreleased` nothing has been published.
