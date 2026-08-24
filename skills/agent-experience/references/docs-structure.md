# The docs/ system of record — versioned memory for agents

**The principle: everything relevant for future agent sessions lives in the repo — current state and past decisions — under version control, so every human and agent cloning it shares one consistent memory.** This is a deliberate alternative to external memory services (memory hubs, vector stores): those persist but don't *adjudicate* — when two memories conflict or one goes stale against the code, a hub stores everything and settles nothing. Repo-based memory gets adjudication for free: PR review, diffs, blame, CI checks, branch consistency. Design consequence: **each fact lives in exactly one place, everything merges through review, and staleness is a bug with automated detection.**

One distinction keeps the record clean: the agent's *intra-session scratchpad* (working notes, ephemeral) is never filed; *inter-session institutional memory* (anything a future session needs) always is.

## Reference layout

The full layout, for orientation — **propose the minimal subset the project actually warrants, never this tree by default** (the per-artifact table below says when each part earns its place):

```
AGENTS.md                     # the ~100-line map (see agents-md.md)
docs/
├── ARCHITECTURE.md           # domain map, package layering, invariants
├── design-docs/
│   ├── index.md              # catalogued, with verification status
│   └── core-beliefs.md       # golden principles (see techniques.md)
├── adr/                      # decision records, one per file
├── exec-plans/
│   ├── active/               # in-flight plans with progress & decision logs
│   ├── completed/            # archived plans — history stays greppable
│   └── tech-debt-tracker.md
├── product-specs/            # current intended behaviour per capability, indexed
├── generated/                # CI-regenerated ground truth (db-schema.md, api-surface.md)
├── references/               # llms.txt files for key dependencies
├── security-guidelines.md    # per-concern rules for agents (see the naming note below)
├── reliability-guidelines.md # …one file per cross-cutting concern, as warranted
└── quality-score.md          # per-domain quality grades, tracked over time
```

Everything is indexed and cross-linked; AGENTS.md points into it; CI validates the knowledge base is current and structurally correct (`check_docs.py` covers commands and paths); a doc-gardening agent handles semantic staleness.

## Routing a fact to its artifact

The recurring boundary question — product-specs, design-docs, an ADR, or ARCHITECTURE.md? — resolves by the *kind* of fact, not its topic:

| The fact is… | It lives in |
|---|---|
| how to build, test, and change things here | AGENTS.md (or the nearest nested one) |
| where things live, what may depend on what, structural invariants | ARCHITECTURE.md |
| what a capability is *supposed to do* — current intended behaviour | `product-specs/` — living, updated with the behaviour |
| why it is built this way: one decision, its options and consequences | `adr/` — immutable, superseded never edited |
| why it is built this way: a whole design — strategy, trade-offs, rejected alternatives | `design-docs/` — point-in-time, dated, indexed with a trust label |
| in-flight multi-session task state | `exec-plans/active/` |
| how users consume the product | the external docs site / user docs — the repo keeps the topic→URL map, never a copy |
| anything derivable from code (API surface, schema) | `generated/` — regenerated in CI, never hand-edited |

The mnemonic: ARCHITECTURE.md is the **map**, product-specs are the **promises**, ADRs and design docs are the **reasons** (one decision vs. a whole design), exec plans are the **work**. A document that tries to be two of these inherits both lifecycles and satisfies neither.

## Per-artifact guidance

| Artifact | What it holds | When it earns its place | Maintenance rule |
|---|---|---|---|
| **AGENTS.md** | Map + irreducible always-on rules | Always — any repo an agent touches | Every-line litmus; cited commands verified |
| **ARCHITECTURE.md** | Where things live, boundaries, layering, invariants | More than a handful of modules, or any monorepo | Update on structural change; back with structural tests so drift is caught mechanically |
| **design-docs/ + core-beliefs** | Point-in-time design rationale — strategy, trade-offs, rejected alternatives; operating principles | A design an ADR can't hold; design history worth rescuing (see the design-docs section) | Dated, never silently rewritten; index with trust labels; garden regularly |
| **adr/** | One decision per file: context, options, decision, consequences | The moment ≥2 people or ≥1 agent make architectural choices, or "why" questions recur | Append-only; supersede, never edit |
| **exec-plans/** | Multi-session task state: plan, progress log, decision log | Work spanning multiple sessions or context windows | active → completed lifecycle is mandatory GC; small ephemeral plans stay out |
| **tech-debt-tracker** | Known, tolerated debt with its business rationale | As soon as debt is consciously deferred | Fed by GC agents; pruned on payoff |
| **product-specs/** | Current intended behaviour per capability — the bug-vs-intended adjudicator | Evidence triggers only (see the product-specs section) — never coverage | Spec-first for new behaviour; backfill when touched; updated in the same change as the behaviour |
| **generated/** | Derived ground truth (schemas, API surfaces) | Whenever a non-prose source of truth exists | Regenerated in CI; never hand-edited; failing regeneration fails the build |
| **references/ (llms.txt)** | Dependency docs in LLM-ready form | Dependencies the agent misuses or hallucinates | Pinned to the dependency version; refreshed on upgrade |
| **Per-concern docs** (`security-guidelines.md`, `reliability-guidelines.md`, …) | Cross-cutting requirements (security, reliability…) | The concern has real project-specific rules — not generic advice | Pair each with a sensor where possible (AppSec checklist → review skill) |
| **quality-score.md** | Graded map of where quality is weak | Larger codebases running GC agents | Updated by the scheduled quality-grading pass |

**Naming note.** Files this skill introduces under docs/ are kebab-case (`security-guidelines.md`, `quality-score.md`); only names with an ecosystem-standard casing keep it (`AGENTS.md`, `ARCHITECTURE.md`). In particular, never name a per-concern doc `SECURITY.md`: that name is the community vulnerability-reporting policy, and GitHub detects it in `docs/` as well as the root and `.github/` — a per-concern doc under that name would be surfaced as the project's official security policy. Source material uses uppercase variants (`SECURITY.md`, `RELIABILITY.md`, `QUALITY_SCORE.md`); recognize those when auditing an existing repo, but generate kebab-case.

**Small-project variant — the Memory Bank pattern.** When even the minimal subset is oversized, a fixed small file set serves as session-start memory: `project-brief.md` (what/for whom), `product-context.md` (why), `system-patterns.md` (architecture), `tech-context.md` (stack, setup, constraints), `active-context.md` (current focus, last decisions, next step), `progress.md`. Operating rules: AGENTS.md instructs the agent to read the bank at session start and update the active files at session end; everything is committed. Known failure mode: **contradictions between the files** — which is why single-source-of-truth and eventual graduation to the structured layout matter. The leanest viable variant is a feature list + progress file + `init.sh`, updated every session.

**Structured task graphs.** Markdown exec-plans suffice for most repos. When work becomes graph-shaped — many interdependent items, multiple agents discovering work — piles of prose give agents "dementia" (yesterday's decision indistinguishable from a three-week-old brainstorm). The fix stays inside the standard structure: give each exec plan (or other graph-shaped artifact) a YAML frontmatter carrying the dependency metadata, and nothing else:

```yaml
---
depends-on: [other-plan, …]       # filenames of plans that must be completed first
discovered-from: originating-plan  # provenance when this work surfaced mid-task
---
```

The plan's filename is its id and its folder is its status — no `id:` or `status:` keys to drift (single source of truth). "Ready work" then becomes computable instead of judged: any plan in `active/` whose `depends-on` entries all sit in `completed/`; a `check_docs.py` rule verifies every referenced plan exists. Keep the vocabulary this small until it hurts — a soft `relates-to:` is the only extension that usually earns itself. Plain GitHub Issues lack these dependency semantics, so pointer-only task memory is weaker than frontmatter in the repo.

## Plans as first-class artifacts

Complex work gets an execution plan in `docs/exec-plans/active/` (use `assets/exec-plan-template.md`): goal, decomposition, progress log, decision log — so any future session resumes without external context. Completion **moves** the file to `completed/`: history stays greppable, the active set stays small — this move *is* the memory GC, not optional tidying. Lightweight plans for small changes deliberately stay out of the record.

## Decision records

The rationale layer of memory. Canonical shape (Nygard; use `assets/adr-template.md`): context → options considered → decision → consequences, one decision per numbered file in `docs/adr/`. **Accepted records are immutable — changing your mind means a new record superseding the old one.** That immutability is precisely what lets an agent distinguish current from stale.

Metadata lives in YAML frontmatter, as in exec plans (the MADR community template standardized the same choice): `status:` (proposed | accepted | superseded), `date:`, and the graph edge `superseded-by:`. ADRs sit flat in `docs/adr/`, so unlike exec plans the status must be a frontmatter field, not a folder — it is the one field edited after acceptance. The lifecycle then becomes checkable: `check_docs.py` verifies every `superseded-by` target exists, that `status: superseded` and `superseded-by:` appear together, and that AGENTS.md points only at accepted ADRs.

Agent-specific wiring:

- List the key *active* ADRs in AGENTS.md ("do not contradict accepted ADRs: ADR-0012 …").
- Instruct the agent to draft a new ADR before implementing any architectural decision not covered by an existing one.
- **Consent-gated creation**: the agent *suggests* an ADR when it detects a decision being made; only the user's confirmation creates it. Interviews emit ADRs as a natural by-product — an answered "why is it built this way?" is an ADR waiting to be filed (write-as-you-go).

## Product specs — the living behaviour layer

`docs/product-specs/` holds **current intended behaviour, one file per capability** — a stable feature area (auth, routing, checkout), never a change (change-shaped state is an exec plan). Its job is **adjudication**: when a test fails or behaviour surprises, the spec answers the one question code cannot answer about itself — *bug or intended?* That role is also why staleness is disqualifying here: agents that have just read a doc are measurably *less* likely to verify by running things, so a stale spec doesn't merely mislead — it displaces the check that would have caught it.

A spec must earn three things, and the triage below exists to enforce that:

- **Existence** — it states human-held intent the code can't reveal: purpose, behaviour promises, deliberate non-promises, tolerated limitations. A spec inferred from the code restates the code — redundant on day one, contradicting it after the next refactor. The AGENTS.md generation evidence (see `agents-md.md`) applies with full force to docs/.
- **Routing** — it is listed in `product-specs/index.md`, which AGENTS.md's pointers reach. Measured doc traffic concentrates overwhelmingly on instruction files; an unrouted spec has no readers.
- **Survival** — something breaks when spec and code drift: the change coupling ("a change to intended behaviour updates its spec in the same change" in the AGENTS.md definition of done), contract lines citing their enforcing test by path (`check_docs.py` then verifies the path exists), doc-gardening for semantics.

**Creation is evidence-triggered, never coverage-driven — abstention is the default.** Never create a spec because a capability exists; create one when a trigger fires:

1. behaviour-dimension work is planned on the capability (the spec is its feedforward half — see `techniques.md`);
2. bug-vs-intended questions or agent mistakes recur there;
3. the interview surfaced intent that has no durable home;
4. the capability is high-criticality — regressions expensive, correctness contested;
5. new feature work — spec-first: the spec precedes implementation, and the diff is reviewed against it.

A retrofit therefore ships **zero to three specs** — each with its audit evidence attached, indexed once any exist — never a per-module dump. *N modules → N specs* is the shape of the failure, not of diligence: it is the BDD-rot trajectory (spec suites died when volume outran their readers) restarted with generation costs near zero and review capacity unchanged. Everything else backfills when its capability is next touched — the change coupling makes that automatic — and deferred candidates go on the roadmap, not into files. The interview questions that gather the human-held half of the evidence are in `interview.md` (spec and design-doc triage).

Per spec (use `assets/product-spec-template.md`): intent (2–4 sentences) → behaviour contract (short testable promises, each citing its enforcing test or marked unverified; a concrete scenario only where behaviour is complex enough to be misread) → deliberately not promised → surface (public symbols by *name* — searchable and rename-tolerant, unlike deep links) → pointers (external doc page, related ADRs). Never: overviews, restated code behaviour, technical design, task lists.

**The two-specs problem sets the lifecycle.** Once code and tests exist, a detailed parallel description competes with them for authority — so keep in the spec only what code is bad at expressing (intent, promises, non-goals, constraints, the invariants you don't want rediscovered by trial and error) and delete prose that restates what the code already says. When an exec plan completes, its durable behavioural deltas merge into the capability's spec; the build detail dies with the plan. Why the behaviour changed is an ADR, not a spec paragraph.

Greenfield seeds the directory with a single `product-brief.md` — intent, users, success criteria, explicit out-of-scope, from interview theme 1 — and per-capability specs then appear spec-first as features are built.

## Design docs — dated rationale with a trust label

`docs/design-docs/` holds **point-in-time design rationale**: for one system or initiative, the strategy chosen, the trade-offs weighed, and the alternatives *rejected* — the content that stops a future session from "helpfully" refactoring away a deliberate choice. The ADR boundary is unity of decision: one decision with its options is an ADR; a design spawning several decisions, needing real alternatives analysis, is a design doc (an "ADR" past a page is a design doc wearing the wrong name). Design docs are honest snapshots: **valid as of their date, never silently rewritten after ship** — amend or supersede, like ADRs. Rationale ages far slower than operational detail, so a design doc keeps the why and links to code and specs for the how.

The agent-era addition is the **index with a trust label**: `design-docs/index.md` lists every doc with its verification status — `verified <date>` (checked against actual code behaviour on that date), `unverified` (rescued or aged; not yet checked), `historical` (superseded by reality; kept as design history). Humans infer staleness from style and hallway context; agents can't — the label is what tells a session whether to rely or re-check. Doc-gardening maintains the labels; `check_docs.py` keeps the index's links alive.

**When it earns its place:** a design an ADR can't hold — or **design history worth rescuing**, which is the main retrofit move: rationale living in wikis, Google Docs, and issue threads is invisible to agents (*repo-local or nonexistent*), so Phase 1's external-memory traces become rescue candidates, each pulled in with provenance and `unverified` until checked. Writing *new* rationale at retrofit time is rare; new design docs are written at design time, before implementation. Small repos: ADRs suffice — don't open the directory for symmetry. `core-beliefs.md` (see `techniques.md`) lives here whenever golden principles exist, at any scale.

## The library/framework case

A library or framework repo serves **two agent audiences over disjoint channels**, and the per-feature documentation question splits along that line. *Consumer agents* — downstream developers' assistants — read the published docs site, the package README, the shipped typings, `llms.txt`; they never clone this repo. *Contributor agents* clone the repo and read AGENTS.md and docs/. So:

- **Usage narrative stays on the site** (tutorials, recipes, reference); the repo keeps the topic→URL map (the external-pointer rule), never copies.
- **The default home for per-module knowledge is a module index in ARCHITECTURE.md**: one short entry per feature module — purpose, key public symbols by name, invariants, extension points, dependencies on other modules. That is the answer to "where do our 21 feature modules get documented?": in the codemap index, not in 21 spec files. Mature agent-forward frameworks (Svelte, pydantic-ai, Airflow) converge on exactly this — minimal instruction files, boundaries, conventions; none maintains a per-feature spec tree.
- **A standalone product-spec exists only where a behaviour contract is load-bearing** — downstream code relies on the promised behaviour and semver hangs on it. For a library, documented behaviour *defines* the compatibility contract (Rust's API-evolution RFC: behaviour outside the documented contract "is permitted to change in minor revisions") — which is also why *deliberately not promised* is the section that earns hardest here. A wire protocol, a routing algorithm's guarantees, an undo/redo lifecycle: spec candidates. A hover effect: an index entry.
- **Mechanize the API surface**: a committed, PR-diffed API report (api-extractor or the ecosystem equivalent) under `docs/generated/` turns signature compatibility into a computational sensor; prose contracts then carry only what signatures can't — ordering, lifecycle, semantics.
- **The repo↔site topology is an interview question, not an assumption.** If the site's content source can move into the code repo with the site syncing from it (the Svelte model), docs and code change in one reviewed PR — the strongest freshness mechanism available. Where the site stays separate, keep the pointer model honest: bidirectional link checks, no vendored copies. Migration is an org-level decision — a roadmap proposal, never a default action.

## Hygiene invariants

1. Single source of truth per fact; pointers everywhere else.
2. No duplication of the README or of anything a linter already enforces.
3. Freshness is mechanically checked: link/structure lint in CI, commands, paths, and frontmatter-graph verification (`check_docs.py`), doc-gardening for semantics.
4. Explicit lifecycle on everything: active/completed for plans, accepted/superseded for ADRs, trust labels on design docs, same-change behaviour coupling for product specs.
5. Docs merge through review like code; agents may draft, humans (or reviewer agents) adjudicate.
6. Provenance on anything mirrored from outside.

**The external-pointer rule.** Link out only where the agent has a fetch path (`gh` CLI for issues/PRs, an MCP connector for the tracker); otherwise the target is invisible and the pointer is dead weight. Pattern: pointer + one-line mirrored summary + provenance link. Never vendor full copies — they drift, and drifted copies actively misinform (see the AX standards).

## Sources

- OpenAI — Harness engineering (the docs-as-system-of-record layout and GC practice): https://openai.com/index/harness-engineering/
- Nygard-shape decision records: https://github.com/architecture-decision-record/architecture-decision-record
- MADR's decision to keep ADR metadata in YAML frontmatter: https://adr.github.io/madr/decisions/0013-use-yaml-front-matter-for-meta-data.html
- Unblocked — why memory hubs don't adjudicate: https://getunblocked.com/blog/team-memory-hubs-ai-agents/
- Beads — the dependency-metadata model the exec-plan frontmatter distills: https://github.com/steveyegge/beads
- Böckeler — spec-first / spec-anchored / spec-as-source, and why unmaintained specs fail: https://www.martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html
- OpenSpec — capability-shaped living specs, per-change deltas merged on archive: https://github.com/Fission-AI/OpenSpec
- Eisele — the two-specs problem; what a spec keeps after implementation: https://stackoverflow.blog/2026/08/21/dispatches-from-o-reilly-the-right-amount-of-spec-for-agentic-development
- Pebblous — measured agent doc traffic; docs displacing verification: https://blog.pebblous.ai/report/agent-facing-documentation-behaviour-2026-08/en/
- Adzic — Specification by Example ten years on (how spec suites rot): https://gojko.net/2020/03/17/sbe-10-years.html
- Ubl — Design Docs at Google (shape and real lifecycle): https://www.industrialempathy.com/posts/design-docs-at-google/
- matklad — ARCHITECTURE.md, the codemap and module index: https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html
- Rust RFC 1105 — documented behaviour as the semver contract: https://rust-lang.github.io/rfcs/1105-api-evolution.html
