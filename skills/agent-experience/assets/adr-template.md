---
status: proposed   # proposed | accepted | superseded — the only field edited after acceptance
date: YYYY-MM-DD
superseded-by:     # ADR filename; set together with status: superseded when a new ADR replaces this one
---

# ADR-NNNN: (decision title, stated as a choice made)

## Context

(What situation forces a decision? Constraints, forces, and the problem — written so a reader with no session context understands why this came up.)

## Options considered

1. **(Option A)** — (one line: what it is, main trade-off)
2. **(Option B)** — (one line)

## Decision

(The choice, in one or two sentences, active voice: "We use X for Y.")

(Why this option won — the decisive argument, not a rehash of all trade-offs.)

## Consequences

(What becomes easier, what becomes harder, what follow-up work this creates. Include the costs — a consequences section with only upsides is unfinished.)

<!-- Accepted ADRs are immutable: to change the decision, write a new ADR, set
this one's status to superseded, and point superseded-by at the new file. That
immutability is what lets an agent tell current from stale. -->
