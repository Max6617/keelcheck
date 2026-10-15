# Prior art on the join

Deliverable 2 for keel. Written by Sift, 2026-10-14. Scope, fixed by the brief: **not** the
neighbours already assessed in `ECC-ASSESSMENT.md` (ECC's enforcement + evolving memory, Spec Kit's
living specs — one sentence each at the end, no more). This file is about anything closer to the
*combination*: a frozen human-approved original, requirement-to-mechanism traceability, gates that
cannot be quietly weakened, and a clean-context audit of divergence.

**Evidence grades.** **[V]** = I fetched the primary source myself in this session. **[R]** =
fetched by one delegated reader (a single reader — a second read of the same page would be a
transcription check, not independent evidence); the URL is given. **[B]** = snippet or
aggregator-API metadata only, content unread. **[C]** = training knowledge or inference, unverified.
Where a claim matters to keel and is only **[R]**, say so when we use it.

**Verification status (added 2026-10-14 22:35).** The grades above record what was fetched, by whom,
when this file was written (19:25). **Nothing in it has been re-verified since 19:25.** Every `[R]`
URL below is one reader's report, not a second reading; every `[B]` item is still a lead. Do not
treat a line here as re-checked until it says so.

**Method note worth keeping.** The reader's search backend returned at least one plausible-looking
but unverifiable hit (an npm package named `dsh-requirements-alignment`); it flagged that and
re-verified every arXiv/DOI claim against the primary endpoint. That is the standard this project
should hold itself to: a search snippet is a lead, not evidence.

---

## 1. Intent drift

**The name-match, and why it is only a partial match.**

- Zhang, Cao, Chen, Sun, *When Users Change Their Minds: Measuring and Repairing Intent Drift in LLM
  Agents*, arXiv:2609.32520, submitted 26 Sep 2026. **[V]** I fetched the abstract. They define
  intent drift as "the failure mode in which superseded parts of the user's intent continue to
  influence the final answer or tool action", introduce IntentFlux (an executable benchmark of
  dialogues with controlled intent changes), and StateForge, which "explicitly maintains the active
  requirements before generation" [V]. Numbers from the abstract: a 627-case calibration where mean
  task score falls 0.476 → 0.384 as superseded and withdrawn information accumulates; on General-Test
  StateForge moves 0.367 → 0.467; supplying the ground-truth final state improves further "but still
  does not recover single-turn performance" [V].
- **The distinction keel needs to register:** this literature is about a *live* intent that the user
  supersedes inside one conversation. keel's case is the inverse — intent that the user already
  approved and *froze*, drifting under an agent's own summarisation and sub-agents. Same words,
  different failure. Nothing in the abstract is about a frozen baseline, so do not cite it as
  validation of the freeze; cite it as validation that "superseded/altered intent keeps influencing
  output" is real and measurable.

**The clean-context premise, empirically.**

- Laban, Hayashi, Zhou, Neville, *LLMs Get Lost In Multi-Turn Conversation*, arXiv:2505.06120, 9 May
  2025. **[V]** I fetched the abstract: an **average drop of 39%** across six generation tasks
  multi-turn versus single-turn, over 200,000+ simulated conversations; degradation decomposes into
  "a minor loss in aptitude and a significant increase in unreliability"; and the headline — "when
  LLMs take a wrong turn in a conversation, they get lost and do not recover" [V]. This is the
  strongest published support for R4's clean-context reviewer: a reviewer that inherits the history
  in which the drift happened is a reviewer inside the failure mode.

**Drift detection as an engineering problem.**

- Maddila, Rashik, Khan, Jha, Saindon, Nagappan, Rigby, *From Code Review to Code Critique: Intent,
  Drift, and Spotlight for AI-Generated Diffs at Scale* (ARCTIC), arXiv:2607.29516 v2, 14 Aug 2026.
  **[R]** Drift = divergence between developer intent and agent output, detected by backtranslation;
  reported QWK 0.907 against human annotators. Industrial and per-diff, not charter-based [R].
- Bhardwaj, *Agent Behavioral Contracts: Formal Specification and Runtime Enforcement for Reliable
  Autonomous AI Agents*, arXiv:2602.22302, 25 Feb 2026. **[V]** I fetched the abstract. Contract
  `C = (P, I, G, R)` = Preconditions, Invariants, Governance, Recovery, runtime-enforced; a
  probabilistic `(p, delta, k)`-satisfaction notion; a **Drift Bounds Theorem** giving expected drift
  `D* = alpha/gamma` for recovery rate `gamma > alpha`; implemented in AgentAssert and evaluated on
  AgentContract-Bench (200 scenarios, 7 models, 1,980 sessions) [V]. This is the nearest thing to a
  *formal* theory of "a contract the agent may not quietly cross", and its Governance/Recovery split
  is the same shape as `enforced-by:`/`checked-by:` plus a remediation path. Note the abstract also
  says "Patent pending" [V] — relevant if we ever write about it publicly.
- Architecture erosion, the older substrate **[R-metadata]**: *Controlling software architecture
  erosion: A survey*, JSS 2011, DOI 10.1016/j.jss.2011.07.036; *Software Architecture Degradation in
  Open Source Software: A SLR*, IEEE Access 2020, DOI 10.1109/ACCESS.2020.3024671.

**Unread leads** (do not cite without reading): VerificAgent arXiv:2506.02539 and *Policy Drift in
Learning AI Agents* DOI 10.18535/ijsrm/v13i07.ec08 **[B]**; *Constraint Drift in Long-Horizon LLM
Agents: How Language Models Forget What They Were Told to Do*, Zenodo 20834503 **[B]** — title
exactly on thesis, **not verified**; Drift-Bench arXiv:2602.02455 and Drift-Bench++ arXiv:2609.38604
**[B]**; RECAP arXiv:2509.04472 **[B]**.

---

## 2. Requirement traceability

The classical literature exists, is large, and — importantly — **binds requirement to requirement
and requirement to code/test, never requirement to the mechanism that upholds it**. That is the
opening keel claims.

- Gotel & Finkelstein, *An analysis of the requirements traceability problem*, ICRE 1994, DOI
  10.1109/ICRE.1994.292398 **[R-metadata]**. Caution recorded by the reader: OpenAlex shows
  `publication_year` 2002 for this DOI; 1994 is the conference, 2002 an IEEE reprint artifact [R].
- **Ramesh & Jarke, *Toward reference models for requirements traceability*, IEEE TSE 2001, DOI
  10.1109/32.895989 [R-metadata].** This is the traceability *information model* work — the closest
  antecedent to a charter format whose entries must declare how they are honoured.
- Also **[R-metadata]**: Ramesh & Edwards 1993, DOI 10.1109/ISRE.1993.324849; Ramesh 1998 CACM, DOI
  10.1145/290133.290147; Spanoudakis & Zisman 2003, DOI 10.1016/S0164-1212(03)00242-5; Egyed &
  Grünbacher ASE 2002, DOI 10.1109/ASE.2002.1115010; Cleland-Huang RE'05, DOI 10.1109/RE.2005.78;
  *Just Enough Requirements Traceability* COMPSAC'06, DOI 10.1109/COMPSAC.2006.57; *Rule-Based
  Maintenance of Post-Requirements Traceability Relations* RE 2008, DOI 10.1109/RE.2008.24; *A
  systematic literature review of pre-requirements specification traceability*, RE 2024, DOI
  10.1007/s00766-023-00412-z.
- The post-/pre-requirements split attributed to Pohl appears to the reader only in a search snippet
  of the IREB CPRE Advanced RM handbook **[B]**. Treat the attribution as unverified.

**Requirements smells — the nearest existing *diagnostic* on requirements text.**

- Femmer et al., *Rapid quality assurance with Requirements Smells*, JSS 2016, DOI
  10.1016/j.jss.2016.02.047 **[R-metadata]** (175 cites); two case studies DOI
  10.1145/2593812.2593817; an SLR DOI 10.2478/cait-2024-0037 **[R-metadata]**.
- Directly on keel's territory: *On the Impact of Requirements Smells in Prompts: The Case of
  Automated Traceability*, ICSE-NIER 2025, DOI 10.1109/ICSE-NIER66352.2025.00016, preprint
  arXiv:2501.04810 **[R-metadata]**. A "wish" is a smell with teeth, and this is the prior art for
  treating sloppy requirement text as a measurable defect rather than a style issue.
- LLM-era **[R-metadata]**: *TraceLLM…*, RE 2026, DOI 10.1007/s00766-026-00460-1; *Toward
  Cost-Efficient Automated Requirements Traceability with LLMs*, RE Workshops 2026, DOI
  10.1109/REW72749.2026.00019.

---

## 3. Frozen baselines and tamper-evident checks

This is where the "join" gets its parts. Four separate traditions each supply one.

**Governance — a frozen record plus a named human who may change it.**

- NASA NPR 7150.2D, effective 2022-03-08 **[R]**. The reader fetched the directive and Chapter 5.
  §5.1.5 requires procedures to "(b) Identify the persons or groups with authority to authorize
  changes" — a change-control authority in regulation [R]. **§5.1.7 SWE-084: "perform software
  configuration audits to determine the correct version of the software configuration items and
  verify that they conform to the records that define them" [R] — that is keel's audit sentence,
  already mandated.** §5.4.6 SWE-200 requires collecting and reporting "software requirements
  volatility metrics" — drift as a measured quantity [R]. Chapter 3.12 is "Software Bi-Directional
  Traceability", with Table 1 traceability by software classification [R]. IEEE 828-2012 (config
  management) is cited **only via NASA's own note**: the reader's direct IEEE URL redirected to an
  unrelated standard [R].
- ISO/IEC/IEEE 29148:2018, Ed. 2, 92 pp **[R]**. Status: confirmed 2024-05-10, then "to be revised"
  2026-02-16, with DIS 29148 in development [R]. **Deliberate gap:** the reader could **not** verify
  from the abstract that 29148 defines "baseline"/"approved baseline" — so we must not claim it does.
- CISA *Secure Software Development Attestation Form* (rev. 2024-05-14), grounded in NIST SP 800-218
  (Feb 2022, DOI 10.6028/NIST.SP.800-218) **[R]**: the deliverable is a human-signed claim, with no
  hashing of the thing claimed. That is keel's P1 primitive, minus the tamper-evidence — a useful
  reminder that a signature on a document does not bind the document to the artefacts.

**Hash-the-check — the closest shipped primitives.**

- **OPA signed bundles [V] — I fetched this myself, and it is the single closest existing primitive
  to R2.** `opa build --signing-key … --verification-key …` produces `.signatures.json`, a JWT whose
  payload lists each file's `name`, `hash` (SHA-256) and `algorithm` [V]. The docs' own words: "OPA
  activates the new bundle only if all the verification steps succeed; otherwise, it continues using
  its existing bundle and reports an activation failure via the status API and error logging" [V].
  Two design lessons for keel: (i) it **fails closed** — a bad signature means the old, ratified
  policy stays in force and the failure is *reported*, not silently run; (ii) the hashes cover the
  enforcement code itself. The missing half is exactly keel's: OPA has no notion of a
  **human-ratified predecessor hash** and a change that becomes legitimate by approval.
  Caveat from the same page: `opa eval` / `opa test` "do not verify bundle signatures at this point
  in time" [V] — the verification is a load-time property, not a universal one.
- in-toto v1.0.0 spec (2 Jun 2023) **[R]**. A signed "supply chain layout" with per-step `threshold`
  (n-of-m signatures), `pubkeys`, and artifact rules MATCH / CREATE / DISALLOW / REQUIRE. Its stated
  defender goal: "no step was changed, removed, or added into the software development process that
  the project owner intended" [R] — which is *missing* + *unrequested*, exactly. But it is
  **bit-for-bit only** ("does not record or verify any accompanying artifact metadata" [R]), so there
  is no *shifted*; and it explicitly will not judge a layout that encodes a bad policy ("it is
  possible to configure the supply chain layout so that no code review is performed… in-toto's role
  is not to judge or block" [R]). It also admits it "does not protect against attackers replaying
  older, as-yet unexpired layouts" and points to TUF as the bootstrap that closes that hole (TUF
  itself was not fetched — treat TUF as **[B]**) [R]. **For keel that is the replay problem in
  miniature:** a ratified gate hash with no freshness anchor can be satisfied by an older, still-valid
  state, which is one more reason the anchor should be "the latest ratification commit" rather than
  "any state whose hashes match" (see [`gates-per-harness.md`](gates-per-harness.md) §7).
- SLSA v1.2 Build Provenance **[R]**: `predicateType https://slsa.dev/provenance/v1`;
  `externalParameters` are untrusted and "MUST be verified downstream"; `resolvedDependencies`
  carry sha256/gitCommit digests; parser MUST ignore unknown fields.
- Sigstore Rekor **[R]**: "immutable, tamper-resistant ledger"; "log remains append-only and entries
  are never mutated or removed"; independent auditing via rekor-monitor / omniwitness. This is the
  primitive for keel's run record where a bypass shows up as a *missing* entry.
- OpenSSF Scorecard **[R]** — and read its own README as a warning: "Scorecard is not intended to be
  a one-size-fits-all solution… The checks themselves are heuristics", and "These scores change as we
  add new heuristics or refine the existing ones" [R]. The measuring instrument is mutable — the
  precise thing keel's hash ratchet forbids. Good to quote at anyone who says "just use Scorecard".

**Change discipline.** ADR tooling (`adr-tools`) does append-and-supersede: `adr new -s 9` creates a
record "flagged as superceding ADR 9" and flips ADR 9's status — **never amend** [R]. That is a weak,
convention-only P1, and it is the shape keel's frozen original should copy: append a new requirement,
never edit the anchor.

---

## 4. Tools against the four pieces

Pieces: **P1** frozen human-signed original · **P2** requirement→mechanism/check binding ·
**P3** tamper-evident gates with ratification · **P4** divergence audit (missing/unrequested/shifted).

| Tool | Shares | Lacks | Grade |
|---|---|---|---|
| **in-toto** | P2 fully; P3 partly (signed layout, thresholds; no predecessor-hash ratchet); P1 partly (owner-signed, `expires`, but no "propose vs ratify"); P4 partly (REQUIRE=missing, DISALLOW=unrequested, bit-for-bit) | *shifted*; any notion of a model proposing and a human ratifying | [R] |
| **gittuf** (OpenSSF; NDSS 2025 paper) | P1+P3 governance nearly exactly: root of trust, versioned in-repo policy, changes only by Policy Administrators, min-approval rules, verification independent of the forge | P2 (protects refs/files, knows nothing of requirements); P4 (no divergence audit) | [R] |
| **contextgit** | P2 strongly: typed graph BR-/SR-/AR-/C-/T-/ADR- with upstream/downstream in Markdown frontmatter, docstrings, JSDoc; staleness detection by checksum; MCP; pre-commit/post-merge hooks; the closest developer-tool analogue of P4's signal | **P1** (items are `status: active`, freely editable; `confirm` just marks synchronized); **P3 entirely** — nothing signed, the index and every requirement are writable by the agent, so a model can "confirm" its own drift; its audit detects upstream *change*, not implementation *shift* | [R] |
| **OpenFastTrace** | P2; a CI-runnable slice of P4 — README: "keeps track of whether you actually implemented everything you planned to… also identifies obsolete parts" | P1, P3, *shifted* | [R] |
| **jamb** | P2 tightly: `@pytest.mark.requirement("SRS001")` binds a test to a requirement ID; trace matrix for IEC 62304 submissions; "suspect links" | P1, P3 | [R] |
| **StrictDoc** | P2 + a coverage-shaped slice of P4: req↔source traceability, ReqIF, JUnit/robot test reports, custom validations, diff screen | P1 (UID/VERSION, no signing), P3 (no hashes, no ratification) | [R] |
| **Doorstop** | P2 + link-integrity checks over YAML items in version control | P3; P1 beyond ordinary git history | [R] |
| **OpenSpec** | requirement artefacts (`SHALL` + WHEN/THEN scenarios, per-change proposals) | **P1 by design** — self-described "fluid not rigid … update any artifact anytime, no rigid phase gates"; no hashing | [R] |
| **Amazon Kiro** | P2 genuinely: EARS acceptance criteria and correctness properties extracted into property-based tests; Agent Hooks under `.kiro/` | P1 and P3 — its own guiding line, per a secondary AWS source, is "Specs are living documents, not frozen contracts" | [R], secondary |
| **Tessl** | unknown | cannot verify spec-freezing, hashing or audit semantics; site and docs did not render | **[B] — unverified for our purposes** |
| **keel-workflow** (PyPI; installs the `keel` command) — the "gates + evidence + ledger" keel | a fixed backbone `s0`–`s12` with gates slotted in; `keel run-gates`; an append-only ledger `.keel/state/run-ledger.jsonl`; `keel merge` "takes the merge lock, re-checks the merge window, reads the live CI rollup and verifies the head-pinned review evidence first"; review verdicts bound to the commit SHA ("If the head commit changes by even one byte, previous review evidence is automatically invalidated"); `knobs.implement_mode: tdd` with a blocking `tdd-order` gate; intake returns `needs-input` when an issue lacks a deliverable or acceptance criteria. **P2 partial** at step/check level (gates bound to backbone steps, declared in `gates:`; checks can carry evidence clauses). **P3 partial**: a recorded `config_hash` that rotates when the contract changes, and head-SHA pinning — but the gate definitions live in plain editable `.keel/project.yaml` under `knobs:`, `keel setup --force` overwrites it, and bypasses are *audited rather than prevented* (`--hotfix` is "the one audited bypass", plus a `keel:evidence-waived` label and a `--deferral`) | **P1** — the anchor is a mutable GitHub issue: "The unit is the issue. keel has no channel for steering a run in flight: to change direction, change the issue." **P4** — the trail audits the run, not divergence from a frozen original. And per its own docs: "The gate review is adapter-enforced… nothing in `keel merge` or `keel evidence-verify` blocks a merge whose gate review never ran." | **[V] — I fetched the package metadata and `docs/keel/configuration.md`** |
| **@christang/keel** (npm; installs the `keel` command) — the "contract fingerprint" keel | *Not a distant neighbour* (this corrects an earlier draft). Its own README states the thesis in nearly our words: "Left alone, an agent tends to drift: it edits files the task never mentioned, loses the thread after a context reset, or checks work off without proof." It has: a **contract fingerprint** with pre-registered expected failures — "The clause lives inside the check text, so it is inside the contract fingerprint… a signature cannot be added or rewritten after the red was observed without the anchor moving, which is what separates a prediction from a transcription" — and "Changing a task's contract after work has started moves its fingerprint, and Keel reports that the evidence produced under the old one is stale"; **requirement→owner binding** via `## Expectation Coverage`, where every expectation must close with a `Durable owner:` (a path that exists or an `https://…` reference), a `Discard reason:`, or a `Covered by:` that `keel gate change-close` cross-checks against the named task's `Covers:`; **clean-context re-derivation** — "`keel context` recomputes the current task and next step from OpenSpec and Git every session, so work survives `/clear`, compaction, and cold starts without depending on chat memory"; **three-state deterministic gates** `pass`/`fail`/`needs-review` with exit codes `0`/`3`/`4`/`1`; a `PreToolUse` write guard bounded by the task's declared `Touch`; and a **human-promotion ratchet** on decisions — a precedent "becomes `authorized` when you accept a promotion that was proposed to you — never by a usage count". "Keel never lets the agent merge." **P2 partial** — `Durable owner:` binds an expectation to an owning *path or reference*, not to a mechanism. **P3 partial** — mutation of a contract moves a fingerprint and is *reported stale*, and re-recording is possible via `--record --keep-evidence`, with the honest admission "**Keel does not verify the claim**"; no content hash over gate definitions that must be re-ratified | **P1** — its original is the OpenSpec change, which OpenSpec's own README says is updated on archive ("Specs updated"; "update any artifact anytime"), and its dependency is `@fission-ai/openspec`, so there is no frozen human-signed anchor. **P4** — coverage closure gives missing/discarded only, and the semantic review is a review step, not a classified divergence report | **[V] — I fetched `TanglmChris/keel`'s README and the npm metadata** |
| **ADR tooling** | a weak P1 convention: append-and-supersede, never amend | P2, P3, P4 entirely | [R] |

**Taxonomy precedent.** Architecture-conformance checking splits violations conventionally into
"absence" and "divergence" **[R-metadata: IEEE Software 2009, DOI 10.1109/MS.2009.117; WICSA 2015,
DOI 10.1109/WICSA.2015.11]**, a two-class ancestor of missing/shifted. The reader marks the
"absence/divergence" claim **[C]** — it did not read those papers. Treat as a lead, not a citation.

---

## 5. The join: what I could not find

**Two of the four pieces are demonstrably shipped, and one of them twice.** This is the sharpened
conclusion, and it replaces the looser "nobody has the join" sentence in an earlier draft of this
file and in `ECC-ASSESSMENT.md`:

- **P2 and a large slice of P3/P4 exist in the wild, independently, in two projects both named
  Keel** (the table above; both verified by me). `berkayturanci/keel` ships gates, SHA-pinned
  evidence, an append-only ledger, a merge lock and tdd ordering. `TanglmChris/keel` ships a contract
  fingerprint, requirement-coverage closure with an explicit discard channel, stateless re-derivation
  across compaction, and a human-promotion ratchet. Both arrived at the drift problem independently,
  from the agent side, and both stopped at **detect-and-report**.
- **The unoccupied ground is three things, not four.** What I found nowhere in the sweep:
  1. a **frozen, human-signed original** that is not the mutable issue or the mutable OpenSpec change;
  2. a **per-requirement `enforced-by:` / `checked-by:` binding** — both tools bind at
     step/check/owner granularity, neither binds a named requirement to the specific mechanism or
     check that upholds it;
  3. a **content hash over the gate definitions whose change requires human ratification** — both
     detect or record config change; neither makes the changed gate *refuse to run*;
  4. and, the semantic half, a **three-class audit** (missing / unrequested / shifted) against the
     original, where *shifted* is a judgement rather than a diff.
- **The sharpest version of the gap survives all of this.** P3-as-shipped (OPA, in-toto, gittuf, and
  both Keels) protects against silent alteration by an *outsider* or reports a change after the fact.
  keel's threat is the **assistant weakening its own gate, with the change looking like an ordinary
  diff**, and none of these assumes the writer of the policy is also the thing being policed. That is
  the defensible claim, and it is narrower and stranger than "gates".

**The two Keels are also a positioning risk, not only evidence.** Both are active, both target
Claude Code and Codex, one is English-and-Chinese with an Anthropic plugin-directory listing, and both
install a `keel` binary — see [`name-keel.md`](name-keel.md) §2. The upside worth recording: two
independent projects converging on "the agent drifts, gate it and evidence it" is evidence the
problem is real, which is a better argument for the charter than novelty ever was.

For completeness, the two already-assessed neighbours, one sentence each as instructed: **ECC**
(affaan-m/ECC) ships blocking hooks, sandbox profiles and a fresh-context reviewer over an *evolving*
memory, so it has the enforcement half but no frozen charter to audit against; **GitHub Spec Kit**
makes living specs first-class, so it has requirement artefacts and deliberately no immutable
original.

---

## 6. What this means for keel

1. **The strongest framing is that this is a re-instantiation, not an invention.** NASA NPR 7150.2D
   §5.1.7 mandates a configuration audit that verifies the delivered item "conform[s] to the records
   that define [it]", and §5.4.6 mandates measuring requirements volatility [R]. keel applies both to
   an LLM agent instead of a flight-software team. That is a much better sentence for the README than
   "we invented an audit", and it comes with a caution from the same source: §5.1.5 requires the
   *persons or groups with authority to authorize changes* to be named [R]. keel's ratification should
   therefore name a human, not just record a hash. (Ties directly to the R2 question in
   [`gates-per-harness.md`](gates-per-harness.md) §7: the ratification commit should carry the
   human's identity and the decision, not only the new hash.)
2. **The strongest warning is in-toto's own honesty.** It will not judge a layout that encodes a
   weak policy: "it is possible to configure the supply chain layout so that no code review is
   performed… in-toto's role is not to judge or block" [R]. **A charter format alone creates no
   enforcement.** The wishes list is not a report; it must be load-bearing — the audit should fail or
   escalate on wishes, or keel is a nicer-looking version of the thing that already failed.
3. **Copy OPA's failure behaviour, not just its mechanism.** On a hash mismatch OPA keeps the old,
   ratified policy in force, refuses to activate the new one, and reports an activation failure [V].
   keel's gate check should do the same: run the ratified gate, refuse the changed one, and name the
   change — never "run the new gate and warn".
4. **The `shifted` class has no prior art in tools.** The nearest are ARCTIC's backtranslation-based
   drift detection [R] and requirements smells [R-metadata]. That is the one place where keel's audit
   should be expected to be weak, expensive or model-judged, and where the charter's own rule applies:
   a model may inform that judgement and may never be its only enforcement.
5. **The freeze is the least-covered piece in this space, and the most contested.** Kiro's docs say
   specs are living documents; OpenSpec markets fluidity; contextgit lets the agent `confirm` its own
   requirements [R]. The competitors are not failing to freeze — they are choosing not to. That is
   the claim to make honestly, and it means keel should be able to answer "why freeze?" with the
   intent-drift and lost-in-conversation evidence in §1, not with an assertion.

---

## 7. Sources

**Fetched by me in this session [V]:**
<https://arxiv.org/abs/2609.32520> · <https://arxiv.org/abs/2505.06120> · <https://arxiv.org/abs/2602.22302> ·
<https://www.openpolicyagent.org/docs/management-bundles> · <https://pypi.org/pypi/keel-workflow/json> ·
<https://registry.npmjs.org/@christang/keel/latest> ·
<https://raw.githubusercontent.com/berkayturanci/keel/main/docs/keel/configuration.md> ·
<https://raw.githubusercontent.com/TanglmChris/keel/main/README.md>

**Fetched by one delegated reader [R]** (all reported successful; URLs as given by the reader):
arxiv.org/abs/2607.29516 · api.openalex.org work searches (requirements traceability; architecture
erosion; requirements smells; architecture conformance checking; requirements volatility; post-req
traceability; LLM traceability) · slsa.dev/spec/v1.2/build-provenance ·
raw.githubusercontent.com/in-toto/docs/master/in-toto-spec.md · in-toto.io ·
docs.sigstore.dev/logging/overview · raw.githubusercontent.com/ossf/scorecard/main/README.md ·
gittuf.dev + gittuf.dev/documentation/maintainers/policy · iso.org/standard/72089.html ·
nodis3.gsfc.nasa.gov NPR 7150.2D main and Chapter 5 · csrc.nist.gov/pubs/sp/800/218/final ·
cisa.gov secure-software-development-attestation-form ·
raw.githubusercontent.com/Mohamedsaleh14/ContextGit/main/README.md ·
raw.githubusercontent.com/itsallcode/openfasttrace/main/README.md ·
raw.githubusercontent.com/vanandrew/jamb/main/README.md ·
raw.githubusercontent.com/strictdoc-project/strictdoc/main/README.md · strictdoc.readthedocs.io user
guide · doorstop.readthedocs.io · raw.githubusercontent.com/Fission-AI/OpenSpec/main/README.md ·
raw.githubusercontent.com/npryce/adr-tools/master/README.md · builder.aws.com Kiro guide ·
kiro.dev/docs/specs (no content) · tessl.io · docs.tessl.io (no content) · registry.npmjs.org/@tessl/cli

**Not verified — do not cite:**
ISO 29148's definition of "baseline" (reader could not confirm) · IEEE 828 (only via NASA's note) ·
the "absence/divergence" taxonomy papers (unread) · the Pohl post-/pre-requirements attribution
(snippet only) · every item in the §1 "unread leads" list · Tessl's semantics · TUF's own docs ·
**"fitness functions" (Ford/Parsons/Kua): the reader looked and found no citable primary source, so we
make no claim about it** · all download counts and star counts quoted in
[`name-keel.md`](name-keel.md) that are not marked [V].
