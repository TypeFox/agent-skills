---
name: ts-code-reviewer
description: Perform a senior-level TypeScript/JavaScript code review and produce an actionable REVIEW.md report using Conventional Comments notation. Use this skill for code reviews, PR reviews, diff reviews, or feedback on TS/JS code (.ts, .tsx, .js, .jsx, .mts, .cts files). Do not use for non-TypeScript languages or for one-line syntax questions.
---

# TypeScript Code Review

Produce a thorough, actionable code review of TypeScript/JavaScript code at the level of a principal engineer. The review should be rigorous on substance (correctness, types, security, performance) while remaining respectful and educational in tone — every reviewer's feedback lands on a person, not a compiler.

## Workflow

Follow these steps in order:

1. **Gather the code.** Identify what is being reviewed — a file, a diff, a PR, pasted snippets. If only a fragment is provided and surrounding context would change the review (e.g. a function whose callers aren't visible), ask the user briefly before proceeding.

2. **Confirm the output location.** Ask the user where to write the review file. Default suggestion: the same directory as the code being reviewed, named `REVIEW.md`. Do not write the file until the location is confirmed. A short question like "I'll write the review to `<path>/REVIEW.md` — does that work, or would you prefer somewhere else?" is enough.

3. **Analyze.** Walk the code against the dimensions in the [Analysis framework](#analysis-framework) below. Do not include this analysis in the output — it is internal scaffolding to form the review.

4. **Write the review** to the confirmed path using the structure in [Output format](#output-format). All feedback items must use Conventional Comments notation (see `conventional-comments.md`).

5. **Surface the file** to the user with a short summary of the verdict and the top 1–3 priorities. Do not restate the whole review in chat — the file is the deliverable.

## Review philosophy

These principles shape how feedback is written. They matter because a review that is technically correct but tonally off will be ignored or resented, and a review that is gentle but vague will not improve the code.

- **Assume good intent.** The author made reasonable choices given context you may not have. Seek to understand before critiquing.
- **Be specific and actionable.** Vague feedback wastes everyone's time. Every issue gets a clear path to resolution — usually a concrete code suggestion.
- **Balance criticism with praise.** Acknowledge what is done well. Good review is mentorship, not gatekeeping. Include at least one `praise:` when the code earns it.
- **Prioritize ruthlessly.** Not everything matters equally. Distinguish blocking issues from polish.
- **Teach, don't just correct.** Explain the *why* so the author learns the principle, not just the fix.
- **Prefer questions over accusations when uncertain.** If you don't know whether something is a bug or intentional, use `question:` rather than `issue:`.

## Analysis framework

Systematically consider the code along these dimensions. Not every dimension produces feedback for every review — use judgment about what is worth raising.

**Correctness** — logic errors, off-by-one mistakes, incorrect conditionals, race conditions, async/await misuse, unhandled promise rejections, null/undefined handling, type assertions hiding bugs.

**Type safety** — appropriate use of strict typing vs `any`/`unknown`, correct generic constraints and inference, discriminated unions and exhaustiveness checks, type guards and narrowing, sensible use of utility types (`Partial`, `Required`, `Pick`, `Omit`, etc.).

**Security** — injection vulnerabilities (SQL, XSS, command injection), improper handling of user input or sensitive data, secrets in code, insecure dependencies, authentication/authorization gaps.

**Performance** — unnecessary re-renders (React), expensive computations in hot paths, memory leaks (event listeners, subscriptions, closures), N+1 queries, inefficient algorithms, bundle size concerns, missed caching opportunities.

**Readability and maintainability** — clear naming, appropriate function/module size, single responsibility, comments where they help (and absence of misleading ones), consistent style.

**Idiomatic TypeScript** — modern ES/TS features used appropriately, sensible module organization, interface vs type alias choices, enum vs `as const`, functional vs class-based patterns.

**Error handling** — comprehensive handling and propagation, meaningful error messages, graceful degradation, edge cases.

**Testing** — testability of the code, missing coverage on critical paths, test design issues if tests are included.

## Conventional Comments

Refer to `references/conventional-comments.md` for the full label and decoration reference. Read it before starting a review.

## Output format

Use this exact structure for `REVIEW.md`:

```markdown
# Code Review: [Brief description or filename]

## Summary

A 2–4 sentence high-level assessment. What does this code do well? What are the primary areas for improvement?

**Verdict:** `APPROVE` | `APPROVE_WITH_SUGGESTIONS` | `REQUEST_CHANGES`

## Statistics

- **Total Comments:** [N]
- **Blocking Issues:** [N]
- **Non-blocking Suggestions:** [N]
- **Praise:** [N]

## Prioritized Recommendations

1. **(Blocking)** [Most critical change]
2. **(Blocking)** [Second most critical]
3. **(Non-blocking)** [Important but not blocking]
...

---

## Detailed Feedback

### Blocking Issues

[One entry per blocking issue, using the per-comment template below]

### Suggestions & Improvements

[One entry per non-blocking suggestion]

### Nitpicks & Polish

[Trivial items]

### Questions

[Items needing author clarification]

### Praise

[Positive observations]

## Additional Notes

[Optional broader observations]
```

### Per-comment template

Each feedback item in the detailed sections follows this template:

```markdown
**<label> (<decorations>): [Concise title]**

**Location:** `filename.ts:L##`

**Original Code:**
\`\`\`typescript
// the code in question
\`\`\`

**Suggested Fix:**
\`\`\`typescript
// the proposed code
\`\`\`

**Rationale:**
Why this matters and why the suggested change is better. Reference principles, patterns, or docs where it helps.
```

For lightweight comments (`nitpick:`, `praise:`, `typo:`), the rationale and code blocks can be condensed or omitted — match weight to substance.

A complete worked example of a finished review is in `references/example-review.md`. Read it before writing your first review for this skill, especially to calibrate the tone and depth of `Rationale` sections.

## Final checks before delivering

Before surfacing the review to the user, verify:

- The verdict matches the severity of the feedback (don't mark `APPROVE` if there are blocking issues).
- Every blocking issue has a concrete suggested fix, not just a complaint.
- At least one `praise:` is included if the code deserves it.
- Statistics counts match the actual content.
- File paths and line numbers in `Location:` fields are accurate.
