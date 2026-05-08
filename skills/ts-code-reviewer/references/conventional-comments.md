# Conventional Comments Reference

All feedback items in a code review use this format:

```
<label> [decorations]: <subject>

[discussion]
```

The label classifies *what kind* of feedback it is. Decorations add metadata about urgency, domain, or scope. The subject is a one-line summary, and the discussion (which appears in the `Rationale` section of the review template) explains the reasoning.

## Labels

Pick the label that most accurately describes the comment. When in doubt between `issue:` and `question:`, prefer `question:` — it is more respectful when you aren't certain something is wrong.

| Label         | Usage                                                                                |
| ------------- | ------------------------------------------------------------------------------------ |
| `praise:`     | Highlight something positive. Include at least one per review when the code earns it. |
| `nitpick:`    | Trivial, preference-based suggestion. Always non-blocking.                           |
| `suggestion:` | Propose a concrete improvement. Be explicit about *what* and *why*.                  |
| `issue:`      | Highlight a specific problem. Pair with a suggested fix when possible.               |
| `question:`   | Seek clarification when uncertain whether something is actually a problem.           |
| `thought:`    | Share an idea sparked by the review. Non-blocking but potentially valuable.          |
| `todo:`       | Small, trivial, necessary change.                                                    |
| `chore:`      | Process-related task (docs, CI, formatting).                                         |
| `note:`       | Non-blocking context the author should be aware of.                                  |
| `typo:`       | Spelling or grammar mistake.                                                         |
| `polish:`     | Nothing wrong, but could be immediately improved.                                    |

## Decorations

Decorations are optional and appear in parentheses after the label. Multiple decorations can be combined, comma-separated.

| Decoration       | Meaning                              |
| ---------------- | ------------------------------------ |
| `(blocking)`     | Must be resolved before approval.    |
| `(non-blocking)` | Should not prevent approval.         |
| `(if-minor)`     | Resolve only if the fix is trivial.  |
| `(security)`     | Security-related concern.            |
| `(performance)`  | Performance-related concern.         |
| `(testing)`      | Testing-related concern.             |
| `(types)`        | TypeScript type-system concern.      |
| `(ux)`           | User experience concern.             |

## Combining labels and decorations

A few real examples of well-formed comment headers:

- `**issue (blocking, security): Password comparison vulnerable to timing attacks**`
- `**suggestion (non-blocking, types): Replace `any` with proper interface**`
- `**nitpick (if-minor): Variable name could be more descriptive**`
- `**question: Is the retry behavior here intentional?**`
- `**praise: Excellent separation of concerns**`

## Choosing severity

A common mistake is over-blocking — marking too many things `(blocking)` dilutes the signal. Reserve blocking for:

- Correctness bugs that will produce wrong behavior
- Security vulnerabilities
- Crashes, unhandled rejections, data loss risks
- Major architectural problems that will be hard to fix later

Style preferences, type-system improvements, refactor opportunities, and "I would have done it differently" feedback are virtually always non-blocking.
