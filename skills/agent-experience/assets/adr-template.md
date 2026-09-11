---
# One decision and why it was made, frozen when made. What the capability is
# supposed to do *now* — the bug-vs-intended adjudicator — is a product-spec
# (assets/product-spec-template.md).
# Frontmatter semantics and lifecycle: references/docs-structure.md, Decision
# records. Only `status` is load-bearing; drop `date` freely.
status: proposed   # proposed | accepted | superseded — the only field edited after acceptance
date: YYYY-MM-DD   # optional
superseded-by:     # set together with status: superseded; the replacing ADR's filename
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
this one's status to superseded, and point superseded-by at the new file. -->
