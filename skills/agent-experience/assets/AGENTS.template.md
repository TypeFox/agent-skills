<!--
Drafting scaffold — not boilerplate. Generated AGENTS.md files backfire when
shipped unedited: study data ties files that only restate what the model
already infers to *lower* task success at higher cost. This template only
helps if every line is filled from verified facts (executed commands,
confirmed conventions) or explicitly marked `(to be confirmed)` for the
interview. Markers stand for project facts only — commands, boundaries,
conventions — never for AX design choices.
Before commit: delete every section that would only restate ecosystem defaults,
delete all <!-- guidance --> comments, and run the litmus test on each
remaining line: would removing it cause a mistake the agent wouldn't otherwise
make?
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
complete (which sensors must pass, evidence captured), and the change-coupling
rules — which artifact must accompany each kind of change (e.g. bugfix →
regression test, new feature → test + spec entry, API change → doc update).
Phrase couplings as checkable completion requirements, never hedged advice
("might need updating"); keep only couplings that actually hold in this repo. -->

- Never edit `(generated dir)/` by hand — regenerate with `(command)`.
- Never commit secrets; (secrets policy). (to be confirmed)
- Done means: (verification commands) pass locally with output shown.
- When (kind of change: bugfix / new feature / API change), the change includes (accompanying artifact: regression test / spec entry / doc update). (to be confirmed)
- If reality contradicts this file or docs/, fix the doc as part of the change — never silently work around it.

## PR conventions

- (title format / commit convention / what to exclude) (to be confirmed)

## Pointers

<!-- The map function: one line each into deeper docs. No summaries. Keep the
product-specs line only where the repo keeps behaviour specs. -->

- `docs/ARCHITECTURE.md` — module boundaries and layering.
- `docs/adr/` — do not contradict accepted ADRs: (list key active ones).
- `docs/exec-plans/` — multi-session work gets a plan in `active/`; move it to `completed/` when done.
- `docs/product-specs/index.md` — behaviour contracts; a change to intended behaviour updates its spec in the same change.
