# Publish checklist — keelcheck

What has to be true before `keelcheck` goes to an index, and what Max's own upload action would do.
This page performs no publish and prescribes none: publishing is Max's decision alone (`CHARTER.md`
line 103, R9), and this file is **preparation, not permission**. The credential is his too, and it
arrives through a secure card, never through a chat.

The shape is rentguard's, deliberately: preconditions that each name the command or file which settles
them, the commands in order, the credential and how it is used without being printed, and a verification
that installs from the index rather than from a wheel path.

## The revision this page describes

- **`3d04f31` is the pass revision** — the content an anchor move would name — with package version
  **`0.0.1`**. HEAD is one commit above it (`8e177fc`, `PROJECT-STATE.md` only), and the audit prints the
  same six divergences at both.
- **The wheel measurement was taken at `c5168d0`** — `keelcheck-0.0.1-py3-none-any.whl`, 55,005 bytes,
  sha256 `c05efef8…` — and is recorded in the README's install section and in rentguard's
  `docs/VERIFICATION.md`. A rebuild at the current HEAD produces a different file.
- **There is no git remote and no CI in this repository.** `git remote -v` prints nothing and
  `docs/ARTEFACT-MAP.md` A25 records it. So there is no "push" half to this page at all: **the upload
  is the publication**, and the only thing to verify afterwards is the index.

Everything below was read or run at `3d04f31` unless it says otherwise.

## 1. Preconditions

Each one names what settles it. Nothing here is a judgement call dressed as a check.

- [ ] **R9 — Max's explicit word.** `CHARTER.md` line 103: *"Nothing is published without the user's
  explicit word"*, `checked-by` *"the user's explicit word before any push"*, state *checked, not
  enforced*. Nothing else on this page substitutes for it, and no Bot may take it as given.
- [ ] **The audit is clean.** Settled by `keelcheck audit .` printing **zero divergences** and exiting 0.
  **At `3d04f31` it prints six and exits 1**, and all six are the pending re-ratification rather than
  defects:

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
- [ ] **The anchor moves to the content commit, in the tool's own order.** The three ratified hashes
  above are already verified against the files: `keelcheck gate hash review-prompt.md` →
  `sha256:0e4b5764…`, `keelcheck gate hash tools/coverage.py` → `sha256:973d639a…`,
  `keelcheck gate hash tests/_artefacts/claude-reviewer.py` → `sha256:8d5e6a5e…`, all three matching
  `CHARTER.md` lines 109–111. What is missing is Max's word on the anchor line: one commit carrying the
  new row values (`488c0e1`'s shape), then `Ratified at: 688fce8` → that commit, then the order the
  state file records:

  1. `keelcheck gate run .` on a **clean** tree — measured at **1274.59 s**, bound 3600 s, written into
     `.keel/runs.jsonl`;
  2. one audit, which names the move once as `[anchor-moved]` plus one `[gate-table]` per moved row;
  3. a second audit, which should read zero divergences.

  Read from the code rather than assumed: a gate run is taken from the charter **at `Ratified at:`**, so
  the runner refuses to run the working tree's unratified gate (`gate suite: locked`) — the word comes
  first by construction, and a passing run recorded at the new hash satisfies `[gate-record]` **with no
  second run** once the anchor names it.
- [ ] **R5's third surface — the MCP call — lands.** Settled by the file and the command list:
  `keelcheck/mcp.py` **does not exist** at `3d04f31`, and `keelcheck --help` advertises seven commands
  (`charter`, `audit`, `gate run`, `gate hash`, `review`, `hook install`, `hook status`) with **no
  `mcp`**. Mason is building `python -m keelcheck mcp` now, red first. R5's order is *git hook first,
  CLI second, MCP third, harness adapter last*, so until it lands the order is incomplete and the
  README's own sentence — "then MCP and a harness adapter, neither of which exists at this
  stamp" — stays true.
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
- [ ] **Packaging metadata says what a stranger needs.** Settled by reading `pyproject.toml`: name
  `keelcheck`, version `0.0.1`, MIT, author Max Reischl, `requires-python >= 3.10`, no dependencies,
  entry point `keelcheck = keelcheck.cli:main`, classifiers present. **Two things rentguard has and this
  repository does not: a `LICENSE` file and a `CHANGELOG.md`.** `license = { text = "MIT" }` is a
  metadata line, not a licence file, and it is the first thing a stranger looks for on a project page.
- [x] **The wheel builds and installs into a clean venv.** Measured, at `c5168d0`, by the route in §2:
  `python -m pip wheel . --no-deps --no-build-isolation -w dist` produced
  `keelcheck-0.0.1-py3-none-any.whl` (55,005 bytes, sha256 `c05efef8…`) in 27 s, the venv's
  `pip install --no-index --no-deps` printed `Successfully installed keelcheck-0.0.1`, `keelcheck
  --version` printed `keelcheck 0.0.1`, and `keelcheck gate hash keelcheck/cli.py` printed
  `sha256:79885ada…`, exit 0.

## 2. The exact commands, in order

Run from the checkout root, on a **clean** tree. This host has no route to PyPI, so the build runs with
the **host interpreter** (which carries `setuptools`) and the isolated path is deliberately not used:

```console
$ git status --porcelain          # must print nothing
$ python -m pip wheel . --no-deps --no-build-isolation -w dist
#   Created wheel for keelcheck: filename=keelcheck-0.0.1-py3-none-any.whl size=55005 sha256=c05efef8…
# Successfully built keelcheck            [27 s, exit 0]
```

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

This is the keel-specific half of the rentguard pattern: there is no remote to push and no ref to fetch
back, so "done" means **a stranger's command, from the index, answering what this repository says it
answers**. It cannot be run here: `keelcheck` returns 404 on PyPI today, and this host has no route to
it. It is written down so it can be run, not reported as run.

```console
$ python -m venv /tmp/kc-verify && /tmp/kc-verify/bin/python -m pip install keelcheck
Successfully installed keelcheck-0.0.1

$ /tmp/kc-verify/bin/keelcheck --version
keelcheck 0.0.1                                    # what the README's install block says

$ cd <a checkout of this repository at the published revision>
$ /tmp/kc-verify/bin/keelcheck gate hash keelcheck/cli.py
sha256:79885adac75a12d83afa49f5cea59f65e159f0332a0e929935d30dc4340df2c0   # at 3d04f31
```

The second command hashes a file **in the checkout**, not in the installed package, so the digest must
be read at a named revision: it is `sha256:79885ada…` at `3d04f31`, and it changes whenever
`keelcheck/cli.py` changes. A verification that does not name its revision is not a verification.

When the wheel is on the index, run exactly the above and paste the real output into the README's install
section in place of "not run here".

## 5. What is not claimed

- **Nothing is published.** The package is not on any index, nothing is installed anywhere, and there is
  no remote. That banner in the README stays until the upload succeeds.
- **No CI, no badge.** R8's own cell says the suite and the gate run on a checkout, not in a pipeline.
  There is no published green badge to point at, and this page must not imply one.
- **The MCP surface does not exist** (§1) and the drift half of R7 is partial (§1). Claims in the README
  that depend on either become true only when each lands; until then they are aspirational and said so.
- **The README's gate row reads the anchor's table, not the working charter.** It says *"two gates are
  ratified: `review-prompt` `sha256:90df6ebc…` and `suite` (coverage) `sha256:c0b4c4ca…`"* — those are
  the values at `688fce8`. The working charter now declares **three** rows with different hashes
  (`0e4b5764…`, `973d639a…`, `8d5e6a5e…`), none ratified at the anchor yet. Both statements are true of
  different revisions, and the checklist is where that is said out loud.
- **`tools/coverage.py` is a ratified gate.** It appears in the charter's gate table with a content hash,
  and `keelcheck audit` fails when it differs from the ratified one. **A publish is not a reason to move
  that hash**, and this checklist does not touch it: the file is edited only as a gate change, under a
  re-ratification from Max, exactly like the pending one in §1.
- **The version is `0.0.1` and it is the first thing anyone would install.** There is no released
  version anywhere, so there is no upgrade path to describe and no compatibility promise to make.

## 6. What Max's action would do, and what cannot be undone

- **It would upload `keelcheck 0.0.1` to PyPI**, making `pip install keelcheck` work and printing the
  README on the project page. Because this repository has no remote, the index would be **the only
  public copy** of the package unless a repository is published as well — which is a separate decision,
  and none of it is required for the index to work.
- **The name stops being free at that moment.** `keelcheck` is one of the few names free on PyPI, npm
  and crates.io (§1); the first upload claims it, and a name is not released by deleting a release.
  A version can be **yanked**, never deleted, and its bytes can never be replaced: a mistake in `0.0.1`
  is permanent history with `0.0.2` beside it.
- **What becomes true that is not true today**: `pip install keelcheck` works; the README's install
  section can carry a real transcript from the index; the "not published" banner comes down. Everything
  else on this page — the clean audit, R5's MCP surface, R7's drift half, the licence file — is a
  precondition for the claim to be *honest*, not for the upload to succeed.

## 7. The ask

When the preconditions in §1 are settled, one message to Max, and it asks one question:

1. what it is, in two sentences;
2. the exact thing being published — package `keelcheck`, version `0.0.1`, MIT, under which account —
   and that the index would become the only public copy;
3. the evidence: the clean audit at a named commit, the three gate hashes, the wheel that was built and
   installed, and the R5/R7 items that are still open and named as open;
4. what becomes irreversible: the name, the version, the bytes;
5. **publish?**
