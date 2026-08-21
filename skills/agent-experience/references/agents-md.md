# AGENTS.md — content model, evidence, projections

AGENTS.md is the root map: the always-on, project-scoped context every agent session starts from. It is an open format (agents.md, stewarded by the Agentic AI Foundation) read natively by Codex, Cursor, Copilot, Gemini CLI, Devin, Windsurf, Aider, Amazon Q, Factory Droid, and more — plain Markdown, no required schema. Its job is to be a **map, not a manual**: teach the agent where to look next, and carry only the irreducible always-on rules.

## Content model, in leverage order

Order sections by observed leverage. When trimming to the length ceiling, cut from the bottom.

1. **Project snapshot** — 1–3 sentences: what this is, primary stack with exact versions, package manager. Functions like a role prompt.
2. **Commands** — exact, copy-pasteable, verified by execution: install, dev (with ports and prerequisite services), test, **single-test**, lint, typecheck, build, migrate — with timings where they change behavior ("full suite ~4 min; prefer single-test while iterating"). This is the single highest-leverage section: listed commands get used ~160× more than unlisted ones. Name non-obvious tooling choices explicitly (uv not pip, bun not npm, just not make).
3. **The why** — purpose of the project and its key components, so the agent grasps intent, not just structure. Critical in monorepos: name the apps, shared packages, services.
4. **Layout by purpose** — directory-*purpose* lines ("`src/services/` — business logic; keep handlers thin"), key entry files, canonical utilities ("use the typed client in `src/api/client.ts`, not raw fetch"). Purposes are stable; full file trees drift and demonstrably don't speed navigation — skip them.
5. **Conventions not already enforced by tooling.** If the linter catches it, don't restate it. Pair every prohibition with its concrete alternative: "don't instantiate HTTP clients directly — use the shared `apiClient` from `lib/http`". Bare don'ts make agents cautious and over-exploratory; files with 15+ unpaired prohibitions measurably degraded output.
6. **Boundaries and definition of done** — files never to touch, generated dirs, migration rules, secrets policy ("never commit secrets" is the single most common genuinely helpful constraint), destructive-command rules; and what proof is required before claiming completion.
7. **PR/commit conventions** — title format, conventional commits, what to exclude.
8. **Pointers** — into docs/: ARCHITECTURE.md, the key active ADRs ("do not contradict accepted ADRs: ADR-0012 …"), and available skills. This is the map function: one line each, no summaries of what the target says.

## Evidence and limits

The numbers to reason (and argue) from — each traces to a single study, so treat them as direction and rough magnitude, not constants:

- **Instructions are followed — that's the problem.** Unnecessary requirements increase reasoning tokens 14–22%. Every line costs on every task, forever.
- **Listed commands get used ~160× more** than unlisted ones — the command section plus a task-runner surface is the highest-leverage guide pair that exists.
- **Human-written beats generated.** LLM-generated AGENTS.md files slightly *reduced* task success while raising cost ~23%; human-written improved success ~4%. Mechanism: generated files are redundant with existing docs, and context files are ineffective as repo *overviews* — their value is the non-inferable deltas.
- **Length**: aim under 150 lines (30–50 for small repos). Beyond that, lost-in-the-middle effects make late rules ignorable while cost keeps rising. Hard practical ceiling: 32 KiB; effective ceiling far lower.
- **Highest ROI**: information underrepresented in training data — internal tools, unusual build systems, house frameworks, project-specific traps. Agents already know npm, pytest, and cargo.

**Exclusion list** — none of these earn a line, ever:

- generic engineering platitudes ("write clean code", "follow best practices", "be careful")
- README duplication (project pitch, feature list, install boilerplate)
- style rules a linter/formatter already enforces
- full directory listings / file trees
- large code samples
- temporary task state ("currently migrating X" — that's an exec plan)
- stale precision (table names, row counts, version numbers that drift)

The litmus for every surviving line: *would removing it cause a mistake the agent wouldn't otherwise make?*

## Drafting procedure

1. Start from `assets/AGENTS.template.md` — it encodes the section order above with per-section guidance comments.
2. Fill sections **only from verified facts**: Phase 2's executed commands, Phase 1's inventory, confirmed conventions. Mark everything else `(to be confirmed)` for the interview. Markers stand for *project facts* only — never for AX design choices, which the skill's defaults settle.
3. Delete any section that would only restate ecosystem defaults, and delete all guidance comments before commit.
4. Never ship raw generation. `/init`-style scaffolds and this template are drafts to be edited against reality — the evidence above says an unedited generated file is worse than none.

## Projections and the multi-tool ecosystem

One source, projected to many tools — never parallel sources that drift apart.

- **AGENTS.md is the source.** All content lives here.
- **Claude Code reads only `CLAUDE.md`** — it does not read AGENTS.md directly. Create a `CLAUDE.md` containing exactly:

  ```markdown
  @AGENTS.md
  ```

  plus, optionally, genuinely Claude-specific additions (hooks caveats, Claude-only tool notes) below the import. A symlink also works but needs admin rights or developer mode on Windows — the import file is the portable choice. Claude Code additionally supports path-scoped rules in `.claude/rules/` (rules that apply only to files matching a glob) — use them when a rule is real but only applies to part of the tree, instead of growing the root file.
- **Nested files for monorepos**: a smaller, more concrete `AGENTS.md` per package/app; agents merge root → nearest along the path. The root keeps the map and cross-cutting rules; per-package files carry package-specific commands and conventions. Pair each nested AGENTS.md with its own `CLAUDE.md` projection.
- **Other tools' native locations** (`.cursor/rules`, `.github/copilot-instructions.md`, `GEMINI.md`, `.windsurf/`) — when the team uses those tools, project the same source there: a one-line import where the tool supports it; where it doesn't, a file containing just "Read AGENTS.md in the project root." Never generate copies of AGENTS.md — copies drift from the source no matter what their header promises.
- **Migration helpers**: Claude Code's `/init` can ingest existing instruction files from other tools (`.cursor/rules`, `.github/copilot-instructions.md`, AGENTS.md), and `/import` copies configs across — useful when consolidating a repo that grew several competing rule files. Consolidate into AGENTS.md as the single source; retire the rest to projections.

When you find multiple divergent instruction files in an audit, that *is* the finding: pick AGENTS.md as the source, merge the genuinely distinct content, and turn the rest into projections.

## Sources

- Format and ecosystem: https://agents.md
- GitHub's 2,500-repo analysis (content areas, what helps): https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/
- Evidence on generated vs. hand-written files and instruction cost: https://arxiv.org/html/2602.11988v1
- Claude Code memory/import mechanics (CLAUDE.md, `@AGENTS.md`, rules): https://code.claude.com/docs/en/memory
