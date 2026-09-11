<!--
One file per *system or capability* — the implementation strategy *as built*:
the structure, the invariants the design relies on, and the alternatives
rejected on the way. When one earns its place (the triggers), how it is routed
(design-docs/index.md with a trust label, AGENTS.md pointing at the index) and
its lifecycle: references/docs-structure.md, Design docs. Content comes from
the design conversation, the interview, and rescued sources with provenance —
never from summarizing the code. Target: 1–3 pages, a few at most. Delete
these comments before commit.
-->

# Design: (system or capability name)

## Context and scope

<!-- 2–4 sentences: the problem this design solves and where the system sits.
Link the spec and the ARCHITECTURE.md entry instead of restating them —
promises live in the spec, placement and layering in ARCHITECTURE.md. Cite
ADRs by number: a design doc cites its decisions, never restates them. -->

(what this system does and for which promises; links: `docs/product-specs/(capability).md`, the ARCHITECTURE.md entry, ADR-NNNN)

**Provenance** *(rescued designs only)* — (origin: wiki page, shared doc, or thread, with URL or path; its date; rescued YYYY-MM-DD)

## Goals and non-goals

<!-- Non-goals are the higher-value half: what this design deliberately does
not solve, so a future session doesn't "complete" it. A non-goal is a
conscious choice with a reason, not a negated goal. -->

- Goal: (a property the design must deliver — not a feature list)
- Non-goal: (what it deliberately leaves out, and where that concern lives instead)

## Design

<!-- The mechanism, not a walkthrough of the code: components and their
responsibilities, the data flow between them, key interfaces by *name*
(public symbols, config keys — searchable and rename-tolerant, unlike deep
file links). A diagram earns its place only where prose alone would be
misread. -->

- **Components** — (component: its responsibility; one line each)
- **Data flow** — (how a request, event, or value travels through the components)
- **Key interfaces** — `(symbol or config key)` — (one-line role)

### Invariants

<!-- What must stay true after any change, stated as an absolute ("an external
call never runs inside a transaction"). Each cites the sensor that enforces it
— a test, lint rule, or structural rule, by a path check_docs.py can verify —
or is marked as a promotion candidate: an invariant with no sensor is a claim. -->

- (invariant) — enforced by `(test / lint rule / structural rule)`
- (invariant) — (promotion candidate: no sensor yet)

## Alternatives considered

<!-- Every option a competent engineer — or an agent recognizing a familiar
pattern — would propose, with the trade-off that decided against it. This
section is what stops the next session from re-proposing a rejected option as
a fresh idea. Where one decision has its own ADR, cite it instead of
restating the options. -->

- **(alternative)** — rejected because (the decisive trade-off); (ADR-NNNN where recorded)

## Cross-cutting concerns

<!-- Security, privacy, data migration, performance, operability — the
concerns that get forgotten. Only what this design decides about them. When
none applies, say so in one line rather than deleting the heading — a missing
heading cannot be told apart from a concern nobody considered. -->

- (concern): (what the design does about it)

## Amendments

<!-- Append-only, dated. The change that alters the design adds a line here
in the same change — never a silent rewrite — so a reader can tell the
original design from what changed. A design replaced wholesale gets a new
doc; mark this one historical in the index. -->

- YYYY-MM-DD: (what changed and why; the ADR or exec plan that drove it)

<!-- Lifecycle (references/docs-structure.md, Design docs): amended in the same
change that alters the design; the trust label lives in design-docs/index.md.
check_docs.py verifies that the paths this doc cites exist, not that the
design is still true — a stale design doc is worse than none, because an agent
believes it. -->
