# Publish checklist — keelcheck

What has to be true before `keelcheck` goes to an index, and what Max's own upload action would do.
This page performs no publish and prescribes none: publishing is Max's decision alone (`CHARTER.md`
line 103, R9), and this file is **preparation, not permission**. The credential is his too, and it
arrives through a secure card, never through a chat.

The shape is rentguard's, deliberately: preconditions that each name the command or file which settles
them, the commands in order, the credential and how it is used without being printed, and a verification
that installs from the index rather than from a wheel path.

## The revision this page describes

- **`3d04f31` was the pass revision** — the three-row gate table the anchor move was built on — with
  package version **`0.0.1`**. **The anchor moved on 2026-10-16 to `501a404`** (charter naming
  `62dc6be`), and the audit is now clean there; the content above it since then is Mason's R5 surface
  (`17e58ba`, `35a2758`), which does not touch the three gate files — verified by
  `git diff 501a404 35a2758 -- review-prompt.md tools/coverage.py tests/_artefacts/claude-reviewer.py`,
  which prints nothing.
- **The wheel measurement was re-taken on 2026-10-16 at the tree `ed9b40e`** — 60,473 bytes, sha256
  `9cbaa378…`, install and console-script smoke included in §1 — and the earlier one (55,005 bytes,
  sha256 `c05efef8…`, at `c5168d0`) is kept as history. Both are recorded in the README's install section
  and in rentguard's `docs/VERIFICATION.md`.
- **There is now a public git remote, and still no CI.** `origin` is
  `https://github.com/Max6617/keelcheck` — created **private** at Max's word on 2026-10-16 and made
  **public** the same morning, also at his word. It carries the full history, verified by
  `git ls-remote --heads origin` rather than by the push's own message. **A readable repository is not a
  package publication:** R9 is untouched, no index carries `keelcheck`, and the README opens with a
  work-in-progress banner precisely because a stranger can now find the source. What changed is that
  there is a "push" half where there was none, so the code moves by `git push` rather than by hand.
  `docs/ARTEFACT-MAP.md` A25 records it, and F19 records what publicness exposes (local paths, no
  secrets).
- **What the remote does *not* carry: the audit record.** `.keel/` is gitignored on purpose — *"records
  are the tool's own history, not source"* (`.gitignore` line 11) — so `runs.jsonl`,
  `review-context.json`, and every gate-pass and audit claim on these pages are evidence that lives on
  the machine that produced it. A reader of the repository can re-run `keelcheck audit .` and see the
  state for themselves; they cannot read our runs. Recorded as **F18** in the artefact map and left
  alone, because un-ignoring it is a design decision rather than a typo.

The measurements below that say `3d04f31` were read or run at that revision, before the anchor moved;
where a number has been re-taken since, it says so and names its own revision.

## 1. Preconditions

Each one names what settles it. Nothing here is a judgement call dressed as a check.

- [ ] **R9 — Max's explicit word.** `CHARTER.md` line 103: *"Nothing is published without the user's
  explicit word"*, `checked-by` *"the user's explicit word before any push"*, state *checked, not
  enforced*. Nothing else on this page substitutes for it, and no Bot may take it as given.
- [ ] **The audit is clean.** Settled by `keelcheck audit .` printing **zero divergences** and exiting 0.
  **It does: `DIVERGENCES: none`, `exit: 0`, at `35a2758` (audits recorded `07:16:32Z` and `07:16:42Z`,
  `ratified: 62dc6be`).** `REVIEW (clean context, R4): missing` is also printed, and it is **reported,
  not required** — the charter's own word — so it is not a divergence and does not block. For the
  record, this is what it read **before** the anchor move — six divergences, all of them the pending
  re-ratification rather than defects, kept here because that state is what the move cleared:

  ```text
  [gate] review-prompt: the working charter declares sha256:0e4b5764a... but the ratified table
         at 688fce8 records sha256:90df6ebca...; editing the working-tree hash does not re-ratify a
         gate (D1)
  [gate] review-prompt: review-prompt.md: its content hash changed since ratification
         (sha256:90df6ebca... -> sha256:0e4b5764a...); 58 -> 63 lines
  [gate] suite: the working charter declares sha256:973d639a8... but the ratified table at 688fce8
         records sha256:c0b4c4ca1...; editing the working-tree hash does not re-ratify a gate (D1)
  [gate] suite: tools/coverage.py: its content hash changed since ratification
         (sha256:c0b4c4ca1... -> sha256:973d639a8...); 354 -> 369 lines
  [gate-record] suite: the recorded run of this gate did not pass (result: fail, timeout)
  [gate-unratified] reviewer: declared in the working charter but not ratified at 688fce8
  ```

  `REVIEW (clean context, R4): missing` is also printed, and it is **reported, not required** — the
  charter's own word — so it is not a divergence and does not block.
- [x] **The anchor moved, in the tool's own order — done 2026-10-16.** The anchor is commit **`501a404`**
  (charter naming `62dc6be`), and the sequence ran exactly as this page prescribed: a gate run on a
  clean tree, then two audits at **zero divergences** each. The move itself was reported once as
  `[anchor-moved] 688fce8 -> 62dc6be` with one `[gate-table]` per moved row, which is the shape D12 asks
  for. The three row hashes were re-verified against the files this morning, and a script confirmed the
  frozen-original block is byte-identical at the old and new anchor (**553 bytes, sha256 `376f11a44…`**).
  **Two gate runs have passed on clean trees, both under the ratified `suite` hash:**
  - `35a2758` — `pass exit 0`, **759.1 s**, suite `126 passed`, `TOTAL 2594 2210 85.2%` (the milestone run);
  - `c5b1092` — `pass exit 0`, **510.0 s**, suite **143 passed**, `keelcheck/mcp.py` **116/112/96.6%**,
    `TOTAL 2601 2215 85.2%`. This is the newest row, and it is the one a publish from the current tip
    would cite; the audit reads `DIVERGENCES: none` at both tips.

  Read from the code rather than assumed: a gate run is taken from the charter **at `Ratified at:`**, so
  the runner refuses to run the working tree's unratified gate (`gate suite: locked`) — the word comes
  first by construction, and a passing run recorded at the new hash satisfies `[gate-record]` **with no
  second run** once the anchor names it.
- [x] **R5's third surface — the MCP call — landed 2026-10-16.** `python -m keelcheck mcp` is a bounded
  stdio JSON-RPC call that returns (R6's shape, with tests asserting both the behaviour and the absence
  of a socket or a listening server), and `keelcheck --help` now lists it. Files: `keelcheck/mcp.py`
  (+183), `keelcheck/cli.py` (+4), `tests/test_mcp_surface.py` (+292, 13 tests); commits `17e58ba` and
  `35a2758`; coverage of the new module **95.4%** (104/109), which is what keeps the total above the
  floor. Only `audit` is exposed as a tool — the smallest useful surface; `charter` and the others
  follow if wanted. R5's fourth item (the harness hook adapter) is not due and not built, and the
  README's *"then MCP and a harness adapter, neither of which exists at this stamp"* needs the first
  half of that sentence retired before the ask.
- [ ] **R7's demonstration closes, or the claim narrows.** Settled by the audit's drift column and the
  record: **R7's headline is a correction, not a completion** (`PROJECT-STATE.md` lines 593–604). The
  clean-context half names **1–2 of the 5** by-hand defects, not 5 of 5, and the current state names
  **1**. The run at `310f449` reports the MCP fix, which is D2, the guard proof — not D1. So the
  README's demo section is a demonstration of the *mechanical* half and an honest partial on the drift
  half, and it must not read as "the tool found all five".
- [ ] **The name is free — and it is a one-time claim.** Settled by
  `https://pypi.org/pypi/keelcheck/json` returning **404**, re-checked 2026-10-15. Re-check it on the
  day. The registry shortlist and Max's word put the product here (working tree from `6ff67e8`), and
  `keel` itself is taken three ways (`research/name-keel.md`).
- [x] **Packaging metadata, and the two files a stranger looks for first.** Settled by reading
  `pyproject.toml`: name `keelcheck`, version `0.0.1`, MIT, author Max Reischl, `requires-python >= 3.10`,
  no dependencies, entry point `keelcheck = keelcheck.cli:main`, classifiers present. The two files it
  did **not** carry were added on 2026-10-15: **`LICENSE`**, MIT with
  `Copyright (c) 2026 Max Reischl (github.com/Max6617)` — which materialises the `authors` line rather
  than deciding anything — and **`CHANGELOG.md`**, headed `## 0.0.1 — unreleased`, naming what ships and
  what does not. `license = { text = "MIT" }` is a metadata line, not a licence; the file is what a
  stranger looks for first and the changelog is second.
- [x] **The wheel builds and installs into a clean venv — re-measured 2026-10-16 at the current tree.**
  Built from the tree at `ed9b40e` (whose package is `c5b1092`'s) by the route in §2:
  `keelcheck-0.0.1-py3-none-any.whl`, **60,473 bytes, sha256 `9cbaa378…`**, in 8 s. A fresh venv's
  `pip install --no-index --no-deps` printed `Successfully installed keelcheck-0.0.1`; the installed
  package **carries `mcp.py`** (14 modules); `keelcheck --version` printed `keelcheck 0.0.1`; `--help`
  lists **eight** commands, the eighth being `mcp`; `keelcheck gate hash keelcheck/cli.py` printed
  `sha256:5779df4d…`; and the **installed console script** answered an MCP session —
  `tools/list` came back with the `audit` tool. The previous measurement (55,005 bytes, sha256
  `c05efef8…`, at `c5168d0`) is superseded rather than deleted: the package has since gained `mcp.py`
  and the CLI its eighth command, which is exactly why this page says a wheel measurement names its
  revision.

## 2. The exact commands, in order

Run from the checkout root, on a **clean** tree. This host has no route to PyPI, so the build runs with
the **host interpreter** (which carries `setuptools`) and the isolated path is deliberately not used:

```console
$ git status --porcelain          # must print nothing — and it did, before and after the build
$ python -m pip wheel . --no-deps --no-build-isolation -w dist
#   Created wheel for keelcheck: filename=keelcheck-0.0.1-py3-none-any.whl size=60473 sha256=9cbaa378…
# Successfully built keelcheck            [8 s, exit 0, 2026-10-16, tree ed9b40e]
```

The same command at `c5168d0` produced 55,005 bytes / sha256 `c05efef8…` in 27 s. Both are the same
route on different trees, which is the point of naming the tree beside the number.

An sdist is what the index also wants, built the same way — `python -m build` is **not available on this
host** (`No module named build.__main__`), so the sdist step is named and unproven here:

```bash
python -m build --sdist --wheel           # a machine with network; not run here
python -m twine check dist/*              # twine is not installed here either
```

Uploading is the publication. It is not run by this page, and it is not run at all without R9:

```bash
python -m pip install --upgrade twine
TWINE_USERNAME=__token__ TWINE_PASSWORD="$DSH_SECRET_PYPI_TOKEN" python -m twine upload dist/*
```

Then the verification in §4, which is the step that actually closes this page.

## 3. The credential

- **The token is Max's**, requested through a secure card (`request_secret`), stored as a team secret
  and read only from its environment variable. It is never typed into a chat, never written to a file,
  and never echoed: `twine` reads it from `TWINE_PASSWORD` in the environment of that one command.
- Use `TWINE_USERNAME=__token__`. A project-scoped token is enough for a first upload; an account-wide
  token is not needed and is the wrong default.
- **What "it worked" looks like without printing the secret**: `twine upload` prints the package, the
  version and the index URL, and exits 0. If it exits non-zero, read the message rather than re-running
  with the token inline — a token in a shell history is a leaked token.

## 4. The verification: install from the index, not from a wheel

This is the keel-specific half of the rentguard pattern: there is no *public* remote a stranger can
fetch from and no index entry to read back, so "done" means **a stranger's command, from the index,
answering what this repository says it answers**. It cannot be run here: `keelcheck` returns 404 on PyPI
today, and this host has no route to it. It is written down so it can be run, not reported as run.

```console
$ python -m venv /tmp/kc-verify && /tmp/kc-verify/bin/python -m pip install keelcheck
Successfully installed keelcheck-0.0.1

$ /tmp/kc-verify/bin/keelcheck --version
keelcheck 0.0.1                                    # what the README's install block says

$ cd <a checkout of this repository at the published revision>
$ /tmp/kc-verify/bin/keelcheck gate hash keelcheck/cli.py
sha256:5779df4d4008517ba51d79500e1cebec3bdc428cbd6bb11c48481b39ad4180df   # at ed9b40e (package c5b1092)
```

The second command hashes a file **in the checkout**, not in the installed package, so the digest must
be read at a named revision: it is `sha256:5779df4d…` at `ed9b40e`, whose package is `c5b1092`'s (it was
`sha256:79885ada…` at `3d04f31`; the CLI gained the `mcp` command in between), and it changes whenever
`keelcheck/cli.py` changes. A verification that does not name its revision is not a verification.

**The wheel half of this page is fresh; the index half cannot be run here.** The build, the install into
a clean venv and the console-script smoke were all re-measured today against the wheel above; what stays
unrun is only the part that needs an index — `pip install keelcheck` with network — because `keelcheck`
returns 404 on PyPI and this host has no route to it.

When the wheel is on the index, run exactly the above and paste the real output into the README's install
section in place of "not run here".

## 5. What is not claimed

- **No package is published.** Nothing is on any index, and `pip install keelcheck` does not work. The
  **source** is publicly readable — `github.com/Max6617/keelcheck`, private until 2026-10-16 and public
  since, at Max's word — and its README opens with a work-in-progress banner saying exactly that. Source
  is not a release: the version stays `0.0.1`, unreleased, until Max publishes.
- **No CI, no badge.** R8's own cell says the suite and the gate run on a checkout, not in a pipeline.
  There is no published green badge to point at, and this page must not imply one.
- **The MCP surface exists as of 2026-10-16** (§1: `python -m keelcheck mcp`, R5's third), and the
  drift half of R7 is **partial** (§1). README claims that depended on the MCP surface become true; the
  ones that depend on the drift half stay aspirational and must say so.
- **The README's gate row describes an older anchor.** It says *"two gates are ratified:
  `review-prompt` `sha256:90df6ebc…` and `suite` (coverage) `sha256:c0b4c4ca…`"* — the values at
  `688fce8`. **The ratified table is now three rows at `501a404`** (`0e4b5764…`, `973d639a…`,
  `8d5e6a5e…`), and the working charter and the anchor now declare the same three. Both of the README's
  statements are true of the revision they were written at, and the row is expected to be rewritten
  from the anchor rather than from this page.
- **`tools/coverage.py` is a ratified gate.** It appears in the charter's gate table with a content hash,
  and `keelcheck audit` fails when it differs from the ratified one. **A publish is not a reason to move
  that hash**, and this checklist does not touch it: the file is edited only as a gate change, under a
  re-ratification from Max — which is what §1's anchor move was.
- **The version is `0.0.1` and it is the first thing anyone would install.** There is no released
  version anywhere, so there is no upgrade path to describe and no compatibility promise to make.

## 6. What Max's action would do, and what cannot be undone

- **It would upload `keelcheck 0.0.1` to PyPI**, making `pip install keelcheck` work and printing the
  README on the project page. The **source** is already public, so the index adds the installable
  artefact rather than revealing the code — and the README's work-in-progress banner travels to the
  project page with it.
- **The name stops being free at that moment.** `keelcheck` is one of the few names free on PyPI, npm
  and crates.io (§1); the first upload claims it, and a name is not released by deleting a release.
  A version can be **yanked**, never deleted, and its bytes can never be replaced: a mistake in `0.0.1`
  is permanent history with `0.0.2` beside it.
- **What becomes true that is not true today**: `pip install keelcheck` works; the README's install
  section can carry a real transcript from the index; the "not published" banner comes down. Everything
  else on this page — the clean audit, R5's MCP surface, R7's drift half — is a precondition for the
  claim to be *honest*, not for the upload to succeed.

## 7. The ask

When the preconditions in §1 are settled, one message to Max, and it asks one question:

1. what it is, in two sentences;
2. the exact thing being published — package `keelcheck`, version `0.0.1`, MIT, under which account —
   and that the index would become the only public copy;
3. the evidence: the clean audit at a named commit, the three gate hashes, the wheel that was built and
   installed, and the R5/R7 items that are still open and named as open;
4. what becomes irreversible: the name, the version, the bytes;
5. **publish?**
