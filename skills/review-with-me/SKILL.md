---
name: review-with-me
description: Question the user relentlessly while conducting a code review. Use when the user wants to perform a review of a diff, branch, PR, or uses any 'review with me' or 'help me review' trigger phrases. Do not use when the user wants a finished review report without discussing it, or wants the code changed rather than reviewed.
---

Question me relentlessly about a diff, branch, or PR that needs to be reviewed until we reach a shared consensus on the review points. Walk down each part of the change and resolve issues, concerns and questions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing. Asking multiple questions at once is too much.

If a question can be answered by exploring the codebase, explore the codebase instead.

## Final summary

Once all questions are resolved, report every agreed item as one line in this form:

```
file (line): CHANGE <description>
file (line): NOTE <description>
```

- `CHANGE` is a requested change that must be addressed
- `NOTE` is a question for the author, a nit, or an observation that doesn't block
- use the repo-relative path and the line number in the reviewed revision; use a range (`12-18`) for multi-line spans
- for issues spanning a whole file or directory, use `path (all)`
- list `CHANGE` items first, then `NOTE` items
- list skipped and no-issue items in a short closing line, without file references
