<!--
One file per capability — a stable feature area (auth, routing, viewport),
never per change — holding *current intended behaviour*, updated in the same
change as the behaviour. When a spec earns its place (evidence triggers, never
coverage), its routing (product-specs/index.md, pointed at from AGENTS.md) and
its lifecycle: references/docs-structure.md, Product specs. Content comes from
the human (interview answers) and from verified behaviour (tests, captured
output) — never inferred from the code. *Why* a behaviour was chosen is an ADR
(assets/adr-template.md), frozen when made. Delete these comments before
commit.
-->

# (capability name)

**Intent** — (2–4 sentences: why this capability exists, for whom, and what
"working" means for its users. Human-held knowledge — from the interview, not
inferred from code.)

## Behaviour contract

<!-- Short, testable promises. Each cites the test or check that enforces it —
a path check_docs.py can verify — or is marked (unverified), which makes it a
candidate for the next test written here. Add a concrete scenario
(given/when/then) only for behaviour complex enough to be misread. -->

- (promise) — enforced by `(test file path)`
- (promise) — (unverified)

## Deliberately not promised

<!-- What may change without notice: out-of-scope cases, internals downstream
code must not rely on, limitations that are accepted rather than bugs. This is
what lets an agent tell "regression" from "allowed change" — and for libraries
it marks the semver boundary. Often the highest-value lines in the file. -->

- (non-promise / accepted limitation)

## Surface

<!-- Entry points by *name* (public symbols, config keys — searchable and
rename-tolerant), not deep file links. Point to docs/generated/ where a
generated reference exists. -->

- (public symbol / config key) — (one-line role)

## Pointers

- (external docs page URL — the user-facing narrative for this capability)
- (related ADRs, design docs, or specs)
