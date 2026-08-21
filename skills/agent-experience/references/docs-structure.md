# The docs/ system of record — versioned memory for agents

**The principle: everything relevant for future agent sessions lives in the repo — current state and past decisions — under version control, so every human and agent cloning it shares one consistent memory.** This is a deliberate alternative to external memory services (memory hubs, vector stores): those persist but don't *adjudicate* — when two memories conflict or one goes stale against the code, a hub stores everything and settles nothing. Repo-based memory gets adjudication for free: PR review, diffs, blame, CI checks, branch consistency. Design consequence: **each fact lives in exactly one place, everything merges through review, and staleness is a bug with automated detection.**

One distinction keeps the record clean: the agent's *intra-session scratchpad* (working notes, ephemeral) is never filed; *inter-session institutional memory* (anything a future session needs) always is.

## Reference layout

The full layout, for orientation — **propose the minimal subset the project actually warrants, never this tree by default** (the per-artifact table below says when each part earns its place):

```
AGENTS.md                     # the ~100-line map (see agents-md.md)
ARCHITECTURE.md               # domain map, package layering, invariants
docs/
├── design-docs/
│   ├── index.md              # catalogued, with verification status
│   └── core-beliefs.md       # golden principles (see techniques.md)
├── adr/                      # decision records, one per file
├── exec-plans/
│   ├── active/               # in-flight plans with progress & decision logs
│   ├── completed/            # archived plans — history stays greppable
│   └── tech-debt-tracker.md
├── product-specs/            # functional intent per feature, indexed
├── generated/                # CI-regenerated ground truth (db-schema.md, api-surface.md)
├── references/               # llms.txt files for key dependencies
├── SECURITY.md  RELIABILITY.md  …   # per-concern docs with real project-specific rules
└── QUALITY_SCORE.md          # per-domain quality grades, tracked over time
```

Everything is indexed and cross-linked; AGENTS.md points into it; CI validates the knowledge base is current and structurally correct (`check_docs.py` covers commands and paths); a doc-gardening agent handles semantic staleness.

## Per-artifact guidance

| Artifact | What it holds | When it earns its place | Maintenance rule |
|---|---|---|---|
| **AGENTS.md** | Map + irreducible always-on rules | Always — any repo an agent touches | Every-line litmus; cited commands verified |
| **ARCHITECTURE.md** | Where things live, boundaries, layering, invariants | More than a handful of modules, or any monorepo | Update on structural change; back with structural tests so drift is caught mechanically |
| **design-docs/ + core-beliefs** | Durable design rationale; operating principles | Product-scale repos; teams with real design history | Index with verification status; garden regularly |
| **adr/** | One decision per file: context, options, decision, consequences | The moment ≥2 people or ≥1 agent make architectural choices, or "why" questions recur | Append-only; supersede, never edit |
| **exec-plans/** | Multi-session task state: plan, progress log, decision log | Work spanning multiple sessions or context windows | active → completed lifecycle is mandatory GC; small ephemeral plans stay out |
| **tech-debt-tracker** | Known, tolerated debt with its business rationale | As soon as debt is consciously deferred | Fed by GC agents; pruned on payoff |
| **product-specs/** | Functional intent per feature | Behaviour-dimension work; anything an agent implements or regression-tests against | Spec precedes implementation |
| **generated/** | Derived ground truth (schemas, API surfaces) | Whenever a non-prose source of truth exists | Regenerated in CI; never hand-edited; failing regeneration fails the build |
| **references/ (llms.txt)** | Dependency docs in LLM-ready form | Dependencies the agent misuses or hallucinates | Pinned to the dependency version; refreshed on upgrade |
| **Per-concern docs** | Cross-cutting requirements (security, reliability…) | The concern has real project-specific rules — not generic advice | Pair each with a sensor where possible (AppSec checklist → review skill) |
| **QUALITY_SCORE** | Graded map of where quality is weak | Larger codebases running GC agents | Updated by the scheduled quality-grading pass |

**Small-project variant — the Memory Bank pattern.** When even the minimal subset is oversized, a fixed small file set serves as session-start memory: `projectbrief.md` (what/for whom), `productContext.md` (why), `systemPatterns.md` (architecture), `techContext.md` (stack, setup, constraints), `activeContext.md` (current focus, last decisions, next step), `progress.md`. Operating rules: AGENTS.md instructs the agent to read the bank at session start and update the active files at session end; everything is committed. Known failure mode: **contradictions between the files** — which is why single-source-of-truth and eventual graduation to the structured layout matter. The leanest viable variant is a feature list + progress file + `init.sh`, updated every session.

**Structured task graphs.** Markdown exec-plans suffice for most repos. When plans become graph-shaped — many interdependent work items, multiple agents discovering work — piles of markdown give agents "dementia" (yesterday's decision indistinguishable from a three-week-old brainstorm); consider a git-stored, dependency-aware issue tracker (e.g. Beads). Plain GitHub Issues lack the dependency semantics agents want, so pointer-only task memory is weaker than either option.

## Plans as first-class artifacts

Complex work gets an execution plan in `docs/exec-plans/active/` (use `assets/exec-plan-template.md`): goal, decomposition, progress log, decision log — so any future session resumes without external context. Completion **moves** the file to `completed/`: history stays greppable, the active set stays small — this move *is* the memory GC, not optional tidying. Lightweight plans for small changes deliberately stay out of the record.

## Decision records

The rationale layer of memory. Canonical shape (Nygard; use `assets/adr-template.md`): context → options considered → decision → consequences, one decision per numbered file in `docs/adr/`. **Accepted records are immutable — changing your mind means a new record superseding the old one.** That immutability is precisely what lets an agent distinguish current from stale.

Agent-specific wiring:

- List the key *active* ADRs in AGENTS.md ("do not contradict accepted ADRs: ADR-0012 …").
- Instruct the agent to draft a new ADR before implementing any architectural decision not covered by an existing one.
- **Consent-gated creation**: the agent *suggests* an ADR when it detects a decision being made; only the user's confirmation creates it. Interviews emit ADRs as a natural by-product — an answered "why is it built this way?" is an ADR waiting to be filed (write-as-you-go).

## Hygiene invariants

1. Single source of truth per fact; pointers everywhere else.
2. No duplication of the README or of anything a linter already enforces.
3. Freshness is mechanically checked: link/structure lint in CI, commands-and-paths verification (`check_docs.py`), doc-gardening for semantics.
4. Explicit lifecycle on everything: active/completed for plans, accepted/superseded for ADRs, verification status on design docs.
5. Docs merge through review like code; agents may draft, humans (or reviewer agents) adjudicate.
6. Provenance on anything mirrored from outside.

**The external-pointer rule.** Link out only where the agent has a fetch path (`gh` CLI for issues/PRs, an MCP connector for the tracker); otherwise the target is invisible and the pointer is dead weight. Pattern: pointer + one-line mirrored summary + provenance link. Never vendor full copies — they drift, and drifted copies actively misinform (see the AX standards).

## Sources

- OpenAI — Harness engineering (the docs-as-system-of-record layout and GC practice): https://openai.com/index/harness-engineering/
- Nygard-shape decision records: https://github.com/architecture-decision-record/architecture-decision-record
- Unblocked — why memory hubs don't adjudicate: https://getunblocked.com/blog/team-memory-hubs-ai-agents/
- Beads — structured task graphs in git: https://github.com/steveyegge/beads
