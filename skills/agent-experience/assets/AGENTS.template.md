<!--
Drafting scaffold — not boilerplate. Evidence says raw generated AGENTS.md files
make agents *worse*; this template only helps if every line is filled from
verified facts (executed commands, confirmed conventions) or explicitly marked
`(to be confirmed)` for the interview. Markers stand for project facts only —
commands, boundaries, conventions — never for AX design choices.
Before commit: delete every section that would only restate ecosystem defaults,
delete all <!-- guidance --> comments, and run the litmus on each remaining
line: would removing it cause a mistake the agent wouldn't otherwise make?
Target: under 150 lines; 30–50 for a small repo.
-->

# (project name)

<!-- Snapshot: 1–3 sentences. What this is, primary stack with exact versions,
package manager. Functions like a role prompt. -->
(to be confirmed: one-sentence purpose). (Stack: language + version, framework, package manager.)

## Commands

<!-- The highest-leverage section: listed commands get used ~160× more.
Only commands you have actually run, verbatim, with flags. Include timings
where they change behavior. Always include the single-test form. Name
non-obvious tooling (uv not pip, just not make). -->

```sh
(install command)        # (timing)
(build command)
(typecheck command)
(lint command)
(test command)           # full suite, (timing)
(single-test command)    # e.g. run one test file/case
(dev-server command)     # port, prerequisite services
```

## Why and where

<!-- Purpose of the key components, then directory-*purpose* lines — not a file
tree (trees drift and don't help navigation). Name canonical utilities the
agent should reach for. Critical in monorepos: name apps/packages/services. -->

- `(dir)/` — (purpose; e.g. "business logic; keep handlers thin")
- Use (canonical utility, e.g. "the typed client in `src/api/client.ts`"), not (the hand-rolled alternative).

## Conventions

<!-- Only conventions NOT enforced by a linter/formatter. Pair every
prohibition with its concrete alternative — bare don'ts degrade output.
Inferred-but-unconfirmed patterns stay marked until the interview. -->

- Don't (prohibited thing) — use (concrete alternative) instead. (to be confirmed)

## Boundaries and definition of done

<!-- Never-touch files, generated dirs, migration rules, secrets policy,
destructive-command rules. Then: what proof is required before claiming a task
complete (which sensors must pass, evidence captured). -->

- Never edit `(generated dir)/` by hand — regenerate with `(command)`.
- Never commit secrets; (secrets policy). (to be confirmed)
- Done means: (verification commands) pass locally with output shown.

## PR conventions

- (title format / commit convention / what to exclude) (to be confirmed)

## Pointers

<!-- The map function: one line each into deeper docs. No summaries. -->

- `ARCHITECTURE.md` — module boundaries and layering.
- `docs/adr/` — do not contradict accepted ADRs: (list key active ones).
