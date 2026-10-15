# Name shortlist — Sift, 2026-10-15

**Decided:** the user chose **`keelcheck`** on 2026-10-15; the rename landed atomically at `6ff67e8`
and the anchor moved at `041689b`. This file is the evidence behind that decision and is otherwise
unchanged — the recommendation below is what it was before the decision.

Companion to `name-keel.md`, which records why `keel` itself fails (that file is in the workspace at
`research/name-keel.md`, one level above this repository; the two are not yet in the same directory).
The user decides. Nothing here renames anything.

**What the name has to do.** keel is a Python CLI: `pip install <name>`, a console script, `import
<name>`. It is a charter-and-audit tool — one frozen human-approved original, requirements that name
the mechanism that upholds them, a mechanical audit, a gate runner, and a review half. The good
names are short, pronounceable, unclaimed, and point at *holding to a fixed reference* rather than at
any one integration surface.

**Method, and the limits of it.** Every registry claim below is a direct fetch on **2026-10-15**, with
the HTTP status recorded: PyPI `pypi.org/pypi/<name>/json`, npm `registry.npmjs.org/<name>/latest`,
crates.io `crates.io/api/v1/crates/<name>`. Niche collisions come from GitHub's repository-name search
(`<name> in:name`) and one web search per candidate. **Not checked, and named rather than implied
clear: any trademark register** (USPTO, EUIPO, WIPO) — that needs a proper search and legal review, and
nothing here is a substitute; GitHub organisation/user name availability (only repository names were
searched); Homebrew-core, Debian, the AUR, Docker Hub; `.dev`/`.com` domains; and whether any holder
would object. **Registry availability is a snapshot and drifts.**

## The shortlist

| # | name | PyPI | npm | crates.io | niche collision | CLI / import |
|---|---|---|---|---|---|---|
| 1 | `keelhook` | free (404) | free (404) | free (404) | none found — 0 repos named `keelhook` | `keelhook audit`; `import keelhook` |
| 2 | `keelcheck` | free (404) | free (404) | free (404) | none found — 0 repos named `keelcheck` | `keelcheck audit`; `import keelcheck` |
| 3 | `breasthook` | free (404) | free (404) | free (404) | none found — 0 repos named `breasthook` | `breasthook audit`; `import breasthook` |
| 4 | `leadline` | free (404) | free (404) | **taken** (SeaORM mock DB, created 2026-10-05) | **yes** — [`Nazim22/leadline`](https://github.com/Nazim22/leadline), evidence router / policy engine for coding agents over Claude Code hooks | `leadline audit`; `import leadline` |
| 5 | `ratline` | free (404) | free (404) | **taken, all versions yanked** ("This crate is discontinued"; the name stays reserved) | none in the niche — 11 repos, all unrelated toys, 0 stars | `ratline audit`; `import ratline` |

### 1. `keelhook` — the continuity pick
- **(a)** Free on all three registries (PyPI 404, npm 404, crates 404), all fetched 2026-10-15. The earlier
  `name-keel.md` check gave the same two answers; this is a re-measurement, not a new source.
- **(b)** No package on any of the three registries and **no GitHub repository named `keelhook`**
  (`in:name` → 0). A web search surfaces only the fishing term "keel hook" (a fly-tying shank), not a
  developer tool.
- **(c)** *Practical risk:* it keeps the keel prefix, so it stays inside the crowded family that sank
  `keel` (`keel-workflow`, `keel-harness`, `@christang/keel`, `keel-cli` — assessed in `name-keel.md`
  §2); and "hook" narrows the tool to R5's first surface when the audit is the point. Short,
  unambiguous to say, no typo traps, clean as a command and as an import.

### 2. `keelcheck` — the descriptive pick
- **(a)** Free on all three (PyPI 404, npm 404, crates 404), 2026-10-15.
- **(b)** No registry entry and **0 GitHub repos** named `keelcheck`.
- **(c)** *Practical risk:* same crowded-prefix problem as `keelhook`, and "check" is bland — but it
  names the *audit*, which is what the tool is, rather than one surface. Nine characters, stress-free
  pronunciation (KEEL-check), no homophone or autocorrect trap.

### 3. `breasthook` — the fresh-name pick
- **(a)** Free on all three (PyPI 404, npm 404, crates 404), 2026-10-15.
- **(b)** No registry entry and **0 GitHub repos** named `breasthook`. Nothing in the niche.
- **(c)** *Practical risk, and it is real:* it reads as "breast hook" to a tired eye and to search
  engines — an unfortunate first impression for a tool, and a genuine typo-magnet. It is also long (10
  characters) and obscure: a boatbuilding term for the timber that ties the two sides of the hull
  together at the stem, which is apt but unexplained. It escapes the keel prefix entirely, which is its
  whole advantage.

### 4. `leadline` — free where the CLI ships, blocked where it does not
- **(a)** PyPI free (404), npm free (404), **crates.io taken** — `leadline` 0.2.0, "Scripted mock
  database for testing SeaORM", created 2026-10-05, 24 downloads. A Python CLI is not published to
  crates, so this is the least damaging of the three collisions; it still means the name is not ours
  everywhere.
- **(b)** **A direct niche collision**: [`Nazim22/leadline`](https://github.com/Nazim22/leadline) —
  "Evidence router & policy engine for coding agents … through Claude Code hooks … Local-first; no LLM
  in the hook loop", topics `agent-guardrails`, `agentic-ai`, `claude-code`, `coding-agents`,
  `evidence-router`, `policy-engine`. That is this project's neighbourhood, in the same harness, under
  the same name. Two more unrelated `Leadline` repos exist (Cloudflare's banner app, a WhatsApp lead
  capture).
- **(c)** *Practical risk:* the pronunciation ambiguity is genuine — a lead line (the sounding line,
  "lead" as the metal, /lɛd/) versus "lead" as in to lead (/liːd/); people will say it both ways and
  spell it "leadline" or "ledline". The niche collision makes it the weakest of the five.

### 5. `ratline` — free on the two that matter, unusable on the third
- **(a)** PyPI free (404), npm free (404), **crates.io: `ratline` exists but is discontinued with every
  version yanked** (max version 0.0.0, `max_stable_version: null`, description "This crate is
  discontinued"). Crates names are never released, so this name cannot be published there.
- **(b)** No niche collision: 11 GitHub repos named `ratline`, all unrelated (CSS/HTML/Python, 0 stars).
- **(c)** *Practical risk:* the "rat" syllable is an odd first impression, and the crates ceiling is
  permanent. Short (7 characters), distinct, and it means the rope rungs of a ship's ladder — a
  working part of the structure, which is closer to the tool than it first sounds.

## Checked and rejected (11 names; the evidence is the point)

| name | first blocking hit | what it is |
|---|---|---|
| `keel` | PyPI, npm, crates.io all taken | see `name-keel.md` |
| `holdfast` | **PyPI taken, and in this niche** | ["Governed evolution for LLM and agentic systems"](https://pypi.org/project/holdfast/) — frozen vs evolvable contracts, invariants, drift detection, audit trails, a Claude Code plugin. The closest competitor found in the whole sweep |
| `belay` | PyPI taken | [MicroPython/CircuitPython hardware library and CLI](https://pypi.org/project/belay/), v0.30.1, active |
| `lintel` | PyPI taken | [a Python docstring linter](https://github.com/Mr-Pepe/lintel) — a linter collision, and `lint`-prefix search noise |
| `touchstone` | npm taken | `touchstone` 0.0.3, a browser test-result collector with a CLI |
| `lodestar` | npm taken | `lodestar` 1.0.0-pre-release; and Lodestar is the well-known Ethereum consensus client by ChainSafe |
| `datum` | npm taken | `datum` 0.1.0, deprecated metrics-in-leveldb module |
| `plumbline` | npm taken | `plumbline` 10.0.9, an Angular component-testing utility |
| `lodestone` | npm taken | `lodestone` 0.1.2, a Final Fantasy XIV scraper |
| `seamark` | **PyPI taken, and in this niche** | ["The Seamark CLI: run Harbor evals in the Seamark cloud"](https://pypi.org/project/seamark/) — trial queueing and QA verdicts for coding agents, v0.1.0 (2026-09-30); also taken on crates.io by a Rust JSON:API framework (2026-09-28) |
| `keelblock` | npm taken | `keelblock` 0.0.1, a self-described *"Name placeholder"* (someone parked it) |
| `markline` | npm taken | `markline` 0.7.0, "Timeline via Markdown", with a CLI |

## Recommendation

**If the decision were mine: `keelcheck`.**

One line: it is free on PyPI, npm and crates.io with no repository and nothing in this niche carrying
the name, it says what the tool actually is — the check, not one integration surface — and it keeps the
maritime "keel" continuity of the working name the user already approved, at the cost of living inside
that crowded prefix.

If the user wants out of the `keel` prefix entirely, `breasthook` is the alternative with the same
clean-registry result, and its two costs are named above: it reads as "breast hook", and it is long and
obscure. `leadline` should not be chosen while `Nazim22/leadline` is active.

## Sources (all fetched 2026-10-15; status in parentheses)

- **Free (404)**: `pypi.org/pypi/{keelhook,keelcheck,breasthook,leadline,ratline}/json`;
  `registry.npmjs.org/{keelhook,keelcheck,breasthook,leadline,ratline}/latest`;
  `crates.io/api/v1/crates/{keelhook,keelcheck,breasthook}`.
- **Taken (200)**: `crates.io/api/v1/crates/leadline` · `crates.io/api/v1/crates/ratline` (yanked) ·
  `pypi.org/pypi/{holdfast,belay,lintel,seamark}/json` · `registry.npmjs.org/{touchstone,lodestar,datum,plumbline,lodestone,keelblock,markline}/latest` ·
  `crates.io/api/v1/crates/{keel,keel-harness,seamark}` (earlier passes, `name-keel.md`).
- **Niche searches**: GitHub `search_repositories` with `<name> in:name` for `keelhook` (0),
  `keelcheck` (0), `breasthook` (0), `leadline` (48, incl. `Nazim22/leadline`), `ratline` (11,
  unrelated), `seamark` (66).
