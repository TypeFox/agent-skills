---
# Task-graph metadata — keep only when plans depend on each other; delete otherwise.
depends-on: []        # filenames of plans that must be completed first
discovered-from:      # plan that spawned this one, when work surfaced mid-task
---

# Exec plan: (task name)

- **Status**: active (in `docs/exec-plans/active/`; move the file to `completed/` when done — that move is the memory GC, keep the active set small)
- **Goal**: (the outcome in one sentence, with the definition of done)

## Acceptance criteria

<!-- Checkable outcomes, filled in before any work starts — know what "done"
looks like first. Re-verify every item before moving the plan to completed/. -->

- [ ] (criterion — an observable outcome, not an implementation step)

## Decomposition

- [ ] (step 1 — small, independently verifiable)
- [ ] (step 2)
- [ ] (step 3)

## Progress log

<!-- Append-only. One dated line per session or milestone, so any future
session resumes without external context. -->

- YYYY-MM-DD: (what happened, what's next)

## Decision log

<!-- Decisions made *during* this work, with one-line rationale. Promote any
architectural decision to a real ADR in docs/adr/ — this log is for the
task-scoped ones. -->

- YYYY-MM-DD: (decision — rationale)

## Open questions

- (anything unresolved that blocks or shapes remaining steps)
