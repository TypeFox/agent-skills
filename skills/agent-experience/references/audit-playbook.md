# Audit playbook — inventory, verify, distill, assess

The core discipline: **audit before generate**. The repository is the primary interview subject; the human is the secondary one. Everything below feeds Phase 3's drafts and Phase 6's roadmap.

**Scaling with subagents.** On a large repo, parallel read-only research agents compress Phases 1–3: give each a slice shaped like a phase input (inventory checklist, architecture, external documentation, conventions + git archaeology) so the reports feed the phases directly. The one hard rule: a subagent report is prose, not evidence — it states findings with equal confidence whether or not they were checked. Re-verify any subagent claim in-session before it triggers a mutating action (always) or ships as a fact in a doc (spot-check a sample).

## Phase 1a — Inventory checklist

Enumerate what exists, by category. Globs are indicative starting points, not an exhaustive contract — follow what you find.

| Category | Look for |
|---|---|
| **Agent instruction files** | `AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md`, `.claude/**` (skills, agents, commands, rules, settings, hooks), `.cursor/rules`, `.cursorrules`, `.github/copilot-instructions.md`, `.github/instructions/**`, `GEMINI.md`, `.windsurf/**`, `.codex/**`, nested variants in subdirectories |
| **Human docs** | `README*`, `CONTRIBUTING*`, `docs/**`, `ARCHITECTURE*`, `adr`/`decisions` directories, wiki links referenced from the repo |
| **Command surface** | `Makefile`, `justfile`, `package.json` scripts, `pyproject.toml`/`tox`/`nox`, `Taskfile`, gradle/maven tasks, shell scripts in `scripts/` and `bin/` |
| **Verification configs** | test frameworks and configs, coverage config, lint/format configs (eslint, ruff, checkstyle, prettier…), type-checker configs, structural tools (dependency-cruiser, ArchUnit, import-linter), mutation testing (stryker), SAST (semgrep), secret scanners — and, inside each config, keys that no longer bind in the tool's current version (a renamed or removed rule id silently no-ops, so the intended disable or enable never happens): stale config keys are dead references too |
| **CI/CD** | `.github/workflows/**`, GitLab/Jenkins/other pipelines — every job is a declared sensor; note stages, gating vs. advisory, runtimes |
| **Hooks** | `.pre-commit-config.yaml`, husky, lefthook; agent-runtime hooks in `.claude/settings*` |
| **Environment** | `.devcontainer/**`, Dockerfiles, compose files, `flake.nix`, `.tool-versions`/asdf/mise, lockfiles |
| **Governance** | `CODEOWNERS`, PR/issue templates, branch-protection hints, `SECURITY.md`, license |
| **Generated/derived artifacts** | generated dirs and their generators; observability config (otel, logging setup); migration directories |
| **External-memory traces** | links to issue trackers, wiki URLs, `.beads/`, memory-bank file sets |
| **External documentation site** | a published docs site and its content source — often a sibling repo; find it via README links, package metadata, publish workflows |

An external documentation site is a first-class input, not a trace: locate its content source, derive the content-path → published-URL mapping, and inventory which knowledge exists *only* there — that topic → URL map becomes the AGENTS.md/ARCHITECTURE.md pointers. Verify links between repo and site in both directions; dead cross-repo links are discrepancies of the same rank as Phase 2's dead commands.

## Phase 1b — Classify into the control model

Place every finding into the grid: **guide or sensor** × **computational or inferential** × **lifecycle stage** (in-session, post-integration, scheduled, runtime) — and note which regulation dimension it serves (maintainability, architecture fitness, behaviour; see `techniques.md`). Concretely:

- each CI job, hook, and lint config → computational sensor at some lifecycle stage;
- each doc or rules file → inferential guide;
- scaffolding scripts and generators → computational guides;
- review bots or prompt files → inferential sensors.

Capture the classification as a compact **inventory matrix** (the 2×2 with lifecycle annotations) — or leave it inside the audit report, as long as every *empty* cell is called out explicitly. The form is disposable; the empty cells are the point: they are the **gap list**, the roadmap's raw material. A typical legacy repo has a full computational-sensor cell (tests, lint, CI) and empty guide cells; a typical "we added an AGENTS.md" repo has the reverse.

Then run the two cross-checks that find the real work:

- **Claims vs. enforcement.** For every rule stated in docs or agent files: does a sensor enforce it? Prose-only rules are **promotion candidates** — mechanical ones go to lint/structural tests (escalation ladder), judgment-laden ones stay prose but must earn their line.
- **Enforcement vs. claims.** For every sensor: is it gating or advisory? An ignored advisory sensor is a gap wearing a green badge.

**Done when** the classified inventory (empty cells explicit), gap list, and both cross-check lists exist.

## Phase 2 — Verification protocol

Ground truth over prose: run everything, in fresh-checkout order, and capture the output as evidence (an agent that merely *reads* the scripts and predicts results has verified nothing — that applies to you, now).

1. **install** (dependency setup, exactly as a fresh clone would)
2. **build**
3. **typecheck**
4. **lint** (and format check)
5. **test** — the full suite, then **a single test** (the single-test invocation is disproportionately valuable and disproportionately often undocumented)
6. **dev-server / app boot** where applicable

For each: record the exact working invocation, required flags, prerequisite services, and the **timing**. Timings matter twice — they go into AGENTS.md so agents pick the right verification granularity, and they shape the design (a 40-second lint belongs in a different lifecycle slot than a 2-second one; feedback-loop speed is an AX property).

Timings measured in a warm working copy — dependencies installed, caches hot, builds incremental — understate what a fresh clone or agent sandbox pays. Label every timing **warm** or **fresh**; force freshness where it's cheap (a `clean` before the build, which also verifies the clean command); and never extrapolate a number you didn't measure — an invented timing is a fabrication like any other. Where install cost matters, a fresh-clone probe in a temp directory is the honest measurement.

Exit codes are evidence too — capture them unpiped, per *run it, don't read it* (the trap fires on the very first command you run, so hold the standard from the start, not from this section on).

Record along the way:

- **Discrepancies** between documented and actual commands — first-class findings. They seed the fix list, the doc-gardening backlog, and the `check_docs.py` CI check. Repair immediately only when the fix is answer-independent — unambiguous breakage with exactly one correct repair. Anything whose *why* is still open gets a `(to be confirmed)` marker instead: the interview routinely invalidates early repairs, and a repair that needs a rationale you don't have invites inventing one.
- **Sandbox friction**: network access needed mid-build, credentials, OS assumptions, services that must already be running. Sandboxability gaps are AX gaps — anything the agent needs should stand up inside a coding-agent sandbox without ceremony.
- **Affordance probes** (they set what the roadmap can reach): Is the language typed — is type checking a free sensor, or is adding types a prerequisite investment? Are module boundaries clean enough to express as import rules? Does a constraining framework provide conventions the agent can lean on? Are build/test tools fast enough for in-session feedback?

Run `scripts/check_docs.py <repo-root>` over existing agent docs to mechanically catch cited-but-missing commands and paths. Discovery skips gitignored files; pass `--exclude <glob>` for tracked docs that are intentionally broken (test fixtures, example corpora). It exits non-zero if gitignore filtering discarded every doc it found — a gate that silently discovers nothing would otherwise report success forever. (During the audit itself, a repo with no agent docs yet is a normal state, not a failure; on a re-audit of a repo known to have agent docs, add `--require-docs` so docs deleted or renamed outright fail too.) The script runs from the skill against the target repo — never copy it into the repo: a copy stops evolving with the skill.

**Done when** a verified command block exists (exact invocations + timings), backed by captured output, with discrepancies and friction listed.

## Phase 3 — Distillation heuristics

From the verified inventory, extract exactly the **non-inferable deltas** — what an agent could not work out from the code and its training. Six extraction passes:

1. **Deviation detection.** Everything that departs from ecosystem defaults: uncommon package managers (uv not pip, bun not npm, just not make), non-standard layouts, house frameworks, internal registries, version pins that matter. *Deviations, not defaults, earn lines* — agents already know npm/pytest/cargo conventions.
2. **Verified command block.** From Phase 2, verbatim, with timings. Never a command you didn't run.
3. **Rules-without-sensors triage.** For each prose-only rule from Phase 1b, decide: promote to lint/structural test (mechanical), keep in AGENTS.md or a skill (judgment-laden), or drop (fails the litmus test). Every kept rule pairs the prohibition with the concrete alternative.
4. **Boundaries.** Files never to touch, generated dirs, migration rules, secret paths, config the team hand-tunes, deploy-sensitive files. Source them from CODEOWNERS, `.gitignore` patterns, CI deploy steps — and the interview.
5. **Convention archaeology.** Mine dominant patterns from code and git history: naming schemes, error-handling idioms, test structure, commit-message style — and change-coupling conventions (do bugfix commits carry a regression test? do feature PRs touch specs or docs?), which seed the definition-of-done couplings in AGENTS.md. Mark each one **observed, unconfirmed** — the interview confirms load-bearing vs. habit. Never promote an inferred pattern straight to a rule; teams routinely carry accidental conventions nobody wants enforced.
6. **Docs triage.** Map existing documents onto the `docs-structure.md` layout: what moves, what gets indexed, what is stale (Phase 2 evidence), where single-source-of-truth is violated. Propose the *minimal subset* of artifacts this project actually warrants — never the full layout by default. Product-specs and design-docs are evidence-triggered on top of that (rubric in `docs-structure.md`): collect the triggers here — where behavioural truth lives today and what adjudicates bug vs. intended, capabilities with recurring intent questions or agent mistakes, external design history worth rescuing, systems whose deliberate mechanisms agents keep breaking or refactoring away — so Phase 4 can ask the triage questions in `interview.md` with recommendations attached. Spec candidates carry their evidence; a candidate without evidence is not proposed.

Everything uncertain becomes a `(to be confirmed)` marker in the drafts; nothing uncertain ships as fact.

## Readiness checks (diagnostic, never a target)

A quick yes/no pass to spot obvious neglect — useful in Phase 1 to orient and in Phase 6 to show movement:

1. Root agent file exists, hand-written/hand-verified, under 150 lines, naming exact stack and versions?
2. Every command in it runs, verbatim, from a fresh checkout?
3. A single test can be run with a documented one-liner?
4. Scope boundaries stated (never-touch files, generated dirs, secrets policy)?
5. Definition of done stated (what proof before claiming completion; which artifacts must accompany each kind of change)?
6. Fast in-session sensors exist (typecheck, lint, fast tests) and CI mirrors them?
7. Docs freshness is mechanically checked (cited commands and paths verified — a recurring `check_docs.py` run, or the repo's own tooling)?
8. Monorepo/large repo: nested per-package agent files where the root map can't carry the detail?

**Scores are proxies.** A repo can pass every mechanical check and remain miserable to work in — an accurate-but-unhelpful AGENTS.md, a fast suite that tests nothing, documented-but-violated boundaries. Use readiness checks like coverage numbers: excellent for revealing neglect, useless to maximize. The honest test stays: ticket in, green suite and accepted diff out, reliably.

## Remediation ordering (the Phase 6 roadmap)

Default order, foundational → sophisticated. Each step is small and individually shippable; cut the list where the project's risk profile stops justifying the investment.

1. **Verified command surface + hand-written root AGENTS.md + CLAUDE.md projection.** The map and the verbs. Highest leverage, lowest cost.
2. **Fast in-session sensors**: typecheck, lint with agent-failure-mode rules, fast tests, secrets scan in pre-commit — each with self-correction messages.
3. **Boundaries and definition-of-done** in AGENTS.md; CI mirrors the in-session sensors.
4. **Minimal docs/ nucleus** per the Phase 3 triage (usually `docs/ARCHITECTURE.md` + `docs/adr/` + `docs/exec-plans/`) + a recurring doc-freshness routine (re-run the skill's `check_docs.py` in re-audit sessions; a CI-installable check waits on the checker shipping through a package registry — never copy the script into the repo).
5. **Structural rules** encoding the layer diagram (dependency-cruiser / ArchUnit / import-linter), plus the new-file-must-live-in-known-structure rule.
6. **Skills** for the recurring procedures discovered in the audit (how-to-test, review, release, bootstrap).
7. **Scheduled inferential sensors** (modularity review, security/data review, doc-gardening) and a GC cadence.
8. **Behaviour-dimension work** (per-worktree bootability, browser automation, agent-legible observability) — only where the risk profile justifies it.

**Gate strictness is a function of throughput and risk, not dogma.** With high agent throughput, corrections are cheap and waiting is expensive — minimal blocking gates and fast follow-ups work. In a low-throughput or high-stakes environment the same policy would be irresponsible; gate harder. Say which regime the project is in when you hand over the roadmap.
