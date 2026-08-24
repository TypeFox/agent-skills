<!--
One file per capability — a stable feature area (auth, routing, viewport) —
never per change (change-shaped state belongs in an exec plan). Create only on
an evidence trigger (see references/docs-structure.md), never for coverage:
N modules → N specs is the failure shape, not diligence.
Content comes from the human (interview answers) and from verified behaviour
(tests, captured output) — a spec inferred from the code restates the code
and starts drifting at the next refactor.
List the file in product-specs/index.md and point AGENTS.md at the index:
an unrouted spec has no readers. Delete these comments before commit.
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

<!-- Lifecycle: this file is the *living* layer — current intended behaviour.
A change to intended behaviour updates this spec in the same change (the
definition-of-done coupling in AGENTS.md). When an exec plan completes, its
durable behavioural deltas merge here; build detail dies with the plan. Why
the behaviour changed goes to an ADR, not here. -->
