# Naming risk: is `keel` already used by a developer tool?

**See also:** `research/name-shortlist.md` (2026-10-15) — the candidate shortlist, each name
checked on PyPI, npm and crates.io with dated evidence. This file records why `keel` itself fails.

Deliverable 3 for keel. Written by Sift, 2026-10-14. The user decides the name; this is a risk
report, not a blocker.

**Verification status.** Sections 1–4 were **re-verified against the registries on 2026-10-14
22:30–22:55 (§2b)**, after the first write at 19:25. Every mark below was re-checked where the
endpoint was reachable; the few things still not checked are named in §5. The single most important
change from the first write: a **third** active project in this exact niche, `keel-harness`, now
ships a `keel` binary.

**Confidence marks.** **[A]** = I fetched this primary endpoint myself, and the fetch is dated.
**[B]** = retrieved by one delegated reader (a single subagent, one reader — a second read of the
same page would be a transcription check, not independent evidence) via the URL given, **not
re-checked**. **[C]** = snippet only or unverified. Nothing here is a trademark search, and none of
it is legal advice.

---

## 1. Short answer

**The string `keel` is not available as a package name on any major registry, and a binary named
`keel` already ships on `PATH` from at least three separate, actively-published npm packages.**
One of those collisions is not merely a name: `keel-workflow` is a live Python CLI in *exactly* this
category — an individual developer's git/PR workflow tool that runs gates — with a `keel` command of
its own.

---

## 2. Collisions that matter

| Name | Where | What it is | Notes | Mark |
|---|---|---|---|---|
| `keel-workflow` (provides `keel`) | PyPI | "Keel turns coding agents into work owners" — Python CLI, ≥3.11, Apache-2.0, author **Berkay Turancı** (individual). `keel setup / plan / ship / run-gates / merge`; an append-only run ledger `.keel/state/run-ledger.jsonl`; review verdicts "bound to the commit SHA"; a merge lock; `knobs.implement_mode: tdd`; installs into Claude Code / Codex / Cursor / Antigravity; Homebrew tap `berkayturanci/keel` | `pip install keel-workflow` **provides the `keel` command**. Versions through at least 2026-09-30; page asserts v1.32.0 in its own docs | **[A]** |
| `keel` | npm | teamkeel — "Your production-grade backend from one file", `bin: {"keel": "keel"}`, AGPL-3.0-only, v0.494.1, postinstall fetches a Go binary from `keel-releases.s3…`, homepage `keel.so` | Ships a real `keel` executable onto `PATH` | **[A]** |
| `@christang/keel` | npm | "Keel **OpenSpec** execution discipline CLI for Claude Code, Codex, and OpenCode", `bin: {"keel": "bin/keel.js"}`, MIT, v5.138.0, depends on `@fission-ai/openspec`, provenance-attested | Another spec-driven-development CLI that installs a `keel` command | **[A]** |
| `keel` | PyPI | A 2018 ncurses process-killer by **Anguel Hristozov** (`modelorona`), v0.1, sole release 2018-06-06, "Kill proccesses effectively and easily" | Makes `pip install keel` resolve to something else entirely; re-verified 2026-10-14 | **[A]** |
| `keel-cli` | PyPI | "CLI for the projects workspace", v0.0.4, last release 2026-05-11, MIT, owner `andmatei`; deps include typer, rich, pydantic | Taken; re-verified | **[A]** |
| `keel` | crates.io | 2018 Kubernetes client library by `aaronfriel`, v0.0.1, 1,942 downloads, **no bin** | Dead; re-verified | **[A]** |
| `keel-harness` | crates.io | **"A gated harness for AI-assisted delivery: auditable stopping conditions and durable memory across coding agents"**, Rust, MIT/Apache-2.0, author **Dane Balia**, **`bin_names: ["keel"]`**, v0.11.1, **31 versions since 2026-08-23**, last published **2026-10-02**, 749 downloads, repo `daneb/keel` | **The sharpest collision yet found: it ships a `keel` binary and describes gates plus durable memory for coding agents — keel's own pitch, in Rust, active this month.** Assessed in deliverable 2; this row is the naming half | **[A]** |
| `keel` | RubyGems | Kubernetes deploy tool for Rails, 2017, 16,265 total **[B]** | | **[B]** |
| `io.spinnaker.keel:keel` | Maven Central | Spinnaker's declarative service | | **[B]** |
| `keel` | Docker Hub / GitHub | `keelhq/keel` Kubernetes operator, 2,736 stars (GitHub API, re-verified; updated 2026-10-11) **[A]**, 44.9M pulls **[B]** | Not a CLI ("No CLI/API" **[B]**) | **[A]/[B]** |
| `keel` | Language | The Keel programming language, ~104 stars **[B]** | | **[B]** |
| `keel`, `@keel-dev/cli`, `create-keel-app`, `keel-core`, … (204 npm hits **[B]**), 3,169 GitHub repos, 60 crates **[B]** | npm / GitHub / crates | Scaffolders, SDKs, MCP servers, a 3D framework, Go scaffolding (`slice-soft/keel`, `docs.keel-go.dev`) | The namespace is crowded well beyond the rows above. GitHub's own count re-verified | **[A]/[B]** |

**Clean negatives reported:** no Homebrew-core formula `keel` (404 **[B]**), no `library/keel` Docker
image (404 **[B]**), no `keel` in Debian stable or the AUR **[B]**. I did not re-fetch these; treat
them as one reader's results.

---

## 2b. Re-verification, 2026-10-14 22:30–22:55 (every row fetched by me, HTTP status recorded)

| Name | Endpoint | Result | Mark |
|---|---|---|---|
| `keel-workflow` (PyPI) | `pypi.org/simple/keel-workflow/` | Exists; **latest 1.32.0**; 0.6.0 → 1.32.0 in the index; author Berkay Turancı; Apache-2.0; README explicitly says `pip install keel-workflow` "provides the `keel` command" and documents a Homebrew tap `berkayturanci/keel` | **[A]** |
| `keel` (PyPI) | `pypi.org/pypi/keel/json` | 200; v0.1 (2018-06-06), ncurses process killer | **[A]** |
| `keel-cli` (PyPI) | `pypi.org/pypi/keel-cli/json` | 200; v0.0.4 (2026-05-11) | **[A]** |
| `keelhook`, `keelcheck`, `pykeel`, `keel-git` (PyPI) | `pypi.org/pypi/<name>/json` | **404 — all four free** | **[A]** |
| `keelson` (PyPI) | `pypi.org/pypi/keelson/json` | 200; RISE-Maritime SDK, v0.5.3 — taken | **[A]** |
| `keel` (npm) | `registry.npmjs.org/keel/latest` | 200; `bin: {"keel":"keel"}`, AGPL-3.0-only, **v0.494.1**, teamkeel, postinstall fetches a Go binary from S3 | **[A]** |
| `@christang/keel` (npm) | `registry.npmjs.org/@christang/keel/latest` | 200; **v5.138.0**, `bin: {"keel":"bin/keel.js"}`, MIT, provenance (`slsa.dev/provenance/v1`), "OpenSpec execution discipline CLI for Claude Code, Codex, and OpenCode" | **[A]** |
| `keelhook` (npm) | `registry.npmjs.org/keelhook/latest` | **404 — free** | **[A]** |
| `keel` (crates.io) | `crates.io/api/v1/crates/keel` | 200; v0.0.1 (2018), Kubernetes client library, no bin | **[A]** |
| `keel-harness` (crates.io) | `crates.io/api/v1/crates/keel-harness` | 200; **`bin_names: ["keel"]`**, v0.11.1 (2026-10-02), 31 versions, gated harness for AI-assisted delivery | **[A]** |
| `keel` (GitHub user) | `api.github.com/users/keel` | 200; a **User** account (not an org), created 2010-11-07, 67 public repos — `github.com/keel` is taken | **[A]** |
| `keel` in repo names (GitHub) | GitHub search API, `keel in:name` | `total_count: 3169`; top hit `keel-hq/keel`, 2,736 stars, updated 2026-10-11 | **[A]** |

**Not checked, and named as a gap:** any **trademark** register (USPTO/EUIPO/WIPO). That needs a
proper search with legal review; nothing in this file is a substitute for it. Also **not**
re-checked tonight: RubyGems, Maven Central, Docker Hub, Homebrew-core, Debian/AUR, `keel.dev` /
`usekeel.com`, and the npm/GitHub/crates namespace *counts* other than the GitHub one above. PyPI
JSON reports `downloads` as `-1`, so no download figure here is from PyPI itself.

---

## 3. The part that is not a naming problem

`keel-workflow` deserves its own paragraph because it changes the *project* picture, not just the
label. From its own PyPI metadata **[A]**, it already ships: a fixed multi-step "backbone" with
gates slotted in (`keel run-gates`, and a `build gate` that fails with "no build gate configured" if
unset), an **append-only run ledger** (`.keel/state/run-ledger.jsonl`), a **merge lock** with a
re-checked merge window, **review evidence pinned to the commit SHA**, "test-first" verification
(`knobs.implement_mode: tdd`), and an intake step that returns `needs-input` when the issue has no
deliverable or no acceptance criteria.

That overlaps keel's requirements-machinery and audit areas more than either neighbour already
assessed in `ECC-ASSESSMENT.md` does. What it does **not** appear to have, from the same page: a
human-approved **frozen original** (its intake reads a GitHub issue, not an anchor), a
requirement-to-mechanism binding in keel's `enforced-by:`/`checked-by:` sense, **hashed** gates, or a
divergence audit against an original. So it strengthens the "the join is the claim" argument rather
than contradicting it — but it must be assessed honestly in deliverable 2, and its existence weakens
any "nobody has combined gates with an evidence trail" sentence we might have written.
There is a **second** active one, verified in the same session: npm `@christang/keel` v5.138.0 —
"Keel — OpenSpec execution discipline for AI coding agents — Claude Code, Codex, and OpenCode"
([README](https://raw.githubusercontent.com/TanglmChris/keel/main/README.md)) — which states the drift
thesis nearly word for word and ships a contract fingerprint, requirement-coverage closure and a
clean-context re-derivation. So two independently authored, actively developed projects already ship
under this exact name, **both targeting Claude Code and Codex**, one bilingual with an Anthropic
plugin-directory listing. Full assessment in [`prior-art-join.md`](prior-art-join.md) §4.

---

## 4. Verdict and options

**Collision risk: high.** Not "blocked" — the big uses are in other categories (Kubernetes operator,
backend framework, Go scaffolding, a language) and the incumbents in this exact niche
(`keel-workflow`, `@christang/keel`, `keel-harness`) are single-author packages with small download
counts. But:

- `pip install keel` and `npm i keel` are gone; the package would need a qualified name anyway.
- The **console script** is the sharper problem. A tool whose whole value proposition is "run this at
  your commit/push" wants a short command, and `keel` is contested by at least seven independent
  projects across npm, PyPI, crates and Homebrew taps. Whatever we call the package, installing a
  bare `keel` risks shadowing or being shadowed. `keel-harness` in particular already puts a Rust
  `keel` **binary** on `PATH` for the same audience.
- The metaphor is popular precisely because it reads as "backbone/stability", so the crowding is not
  a coincidence and is unlikely to thin out.

**Options, cheapest first:**

1. **Keep the working name for the project/charter, ship under a qualified package name** and do not
   install a bare `keel` binary (e.g. package `keelhook`, console script `keelhook`, repository
   `keel`). The charter's name and the installable name need not match; the charter already says the
   name is the user's call and may change.
2. **Move off `keel` entirely**, keeping the metaphor. **Verified free on PyPI 2026-10-14**: `keelhook`,
   `keelcheck`, `pykeel`, `keel-git` (all 404); **verified free on npm**: `keelhook` (404). Not checked
   on npm: `keelcheck`, `pykeel`, `keel-git`. `keelson` is taken on PyPI **[A]**. A name free on both
   registries with a distinct console script is the low-friction choice.
3. **Keep `keel` and accept the ambiguity** — defensible for a personal/internal tool that is never
   published. R9/W2 currently say nothing gets published without the user's word, so this is a real
   option today and stops being one the moment publishing is on the table.

**What I would hand the user in one line:** the name is taken on every registry and as a command, and
three active projects in adjacent niches ship a `keel` binary; either the project keeps `keel` as an
internal codename with a different published name, or we pick a free one now. The user decides;
nothing here blocks the build.

---

## 5. Sources

Verified by me, **first pass 19:25 and second pass 2026-10-14 22:30–22:55** **[A]** (the second pass
re-fetched every row of §2b and confirmed 1–4):

- `pypi.org/pypi/keel-workflow/json` · `pypi.org/simple/keel-workflow/` — metadata, README, index
  through 1.32.0.
- `pypi.org/pypi/keel/json` · `pypi.org/pypi/keel-cli/json` · `pypi.org/pypi/keelson/json` — taken.
- `pypi.org/pypi/keelhook/json` · `pypi.org/pypi/keelcheck/json` · `pypi.org/pypi/pykeel/json` ·
  `pypi.org/pypi/keel-git/json` — all 404.
- `registry.npmjs.org/keel/latest` · `registry.npmjs.org/@christang/keel/latest` — taken;
  `registry.npmjs.org/keelhook/latest` — 404.
- `crates.io/api/v1/crates/keel` · `crates.io/api/v1/crates/keel-harness` — taken.
- `api.github.com/users/keel` — the `keel` login is a User; GitHub repository search `keel in:name`
  reports `total_count` 3,169.

Retrieved by one delegated reader; URLs given, **not independently re-fetched** **[B]**:

- <https://rubygems.org/gems/keel> · <https://search.maven.org/solrsearch/select?q=keel>
- <https://hub.docker.com/r/keelhq/keel> · <https://keel.sh>
- <https://www.npmjs.com/package/@wednesday-sol/keel> · <https://keel-lang.com> · <https://keel.so>
- <https://docs.keel-go.dev/en/cli/overview/> · <https://formulae.brew.sh/api/formula/keel.json>

**Not verified / not attempted:** **trademark status (the biggest gap in this file; not searched at
all)**, download counts other than the crates.io figure, whether `keel.dev` / `usekeel.com` resolve to
anything (reported HTTP 200 with no readable content **[C]**), npm availability of `keelcheck` /
`pykeel` / `keel-git`, and whether any of these projects would object. Registry availability is a
snapshot taken **2026-10-14**; it will drift.
