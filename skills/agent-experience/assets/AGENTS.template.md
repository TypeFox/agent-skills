<!--
Drafting scaffold, not boilerplate: unedited generated files make agents worse
(evidence and drafting procedure in references/agents-md.md). Fill every line
from verified facts or mark it `(to be confirmed)` for the interview; before
commit, delete every section that would only restate ecosystem defaults,
delete all <!-- guidance --> comments, and run the litmus test on each
remaining line. Target: under 150 lines; 30–50 for a small repo.
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
("might need updating"); keep only couplings that actually hold in this repo.
Couplings into docs/ route by kind of fact and say what the target does not
take (references/agents-md.md, content model: definition of done); keep each
docs/ line only where the repo keeps that doc. -->

- Never edit `(generated dir)/` by hand — regenerate with `(command)`.
- Never commit secrets; (secrets policy). (to be confirmed)
- Done means: (verification commands) pass locally with output shown.
- When (kind of change: bugfix / new feature / API change), the change includes (accompanying artifact: regression test / spec entry / doc update). (to be confirmed)
- A structural change (a module added or moved, a new dependency between modules) updates its `docs/ARCHITECTURE.md` entry.
- A change to intended behaviour updates its spec under `docs/product-specs/` in the same change.
- A change that alters a design adds a dated amendment to its design doc: the delta and the decision, a line or two.
- An architectural decision no accepted ADR covers is proposed to the user as an ADR before the implementation; only their confirmation creates it.
- Work that spans sessions runs from a plan in `docs/exec-plans/active/`; its progress, measurements, verification output and review decisions go there and nowhere else.
- A fact lives in one doc; everywhere else, point to it — a second copy drifts.
- If reality contradicts this file or docs/, fix the doc as part of the change — never silently work around it.

## PR conventions

- (title format / commit convention / what to exclude) (to be confirmed)

## Pointers

<!-- The map function: one line per doc kind, carrying its contract — what it
holds, what stays out, its size where one is set — never a summary of its
content. With the guidance comments gone, these lines and the couplings above
are the docs' rules later sessions go by, with or without this skill; never
point at anything outside the repo (references/agents-md.md, content model:
pointers). Keep the product-specs and design-docs lines only where the repo
keeps those docs. -->

- `docs/ARCHITECTURE.md` — where things live, what may depend on what, structural invariants; names and points, never explains a mechanism or a reason.
- `docs/adr/` — one decision per file, never past a page, immutable once accepted; do not contradict accepted ADRs: (list key active ones).
- `docs/exec-plans/` — work that spans sessions gets a plan in `active/`, with its progress and decision logs, and moves to `completed/` when done; single-session work gets none.
- `docs/product-specs/index.md` — one spec per capability: intent, promises, non-promises; never restated code or task state.
- `docs/design-docs/index.md` — one doc per system, a few pages: mechanism, invariants, rejected alternatives, kept true to the design as built; the index entry is the link and the trust label, nothing else.
