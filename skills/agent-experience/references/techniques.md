# Techniques — the guide and sensor catalog

Load this when building (Phase 5) or planning (the roadmap). Every technique is classified guide/sensor × computational/inferential; pick by gap, not by novelty.

**Contents**

- [Choosing what to build](#choosing-what-to-build)
- [Computational guides](#computational-guides)
- [Inferential guides](#inferential-guides)
- [Computational sensors](#computational-sensors)
  - [Self-correction messages](#self-correction-messages-the-highest-leverage-idea)
- [Inferential sensors](#inferential-sensors)
- [Drift and runtime sensors](#drift-and-runtime-sensors)
- [Operating the control system over time](#operating-the-control-system-over-time)

## Choosing what to build

Three selection lenses, applied in order:

**1. Regulation dimension — what quality is being regulated?**

- **Maintainability** (easy, low-risk change over time) — the mature dimension with abundant existing tooling; start here. Empirically: computational sensors reliably catch structural issues (duplication, complexity, missing coverage, architectural drift); inferential sensors partially and expensively catch semantic issues (semantic duplication, redundant tests, brute-force fixes, over-engineering); **neither catches** misdiagnosis, unnecessary features, or misunderstood instructions — those stay human. A controlled study found cleaner code didn't change task success but cut the agent's working footprint (~1/3 fewer re-opens of already-edited files) — maintainability practice calibrated for humans transfers to agents.
- **Architecture fitness** — fitness functions: performance requirements as guides + performance tests as sensors; observability conventions as guides + log-quality checks as sensors; layer rules as structural tests.
- **Behaviour** (does it do the right thing?) — **the open problem; be honest about it.** Current best practice: functional spec as feedforward + AI-generated test suite (coverage-checked, ideally mutation-tested) + manual testing as feedback. This over-trusts AI-generated tests; *approved fixtures* (human-approved concrete scenario outputs) help selectively. Route behaviour work toward specs, approved scenarios, mutation testing, and human review — never claim a sensor covers it.

**2. Lifecycle placement — when does it run?** Keep quality left; distribute by cost, speed, criticality:

- *In-session (continuous)*: typecheck, lint, fast tests + coverage, SAST, dependency rules, secrets scan in pre-commit, incremental mutation testing.
- *Post-integration*: re-run all in-session sensors on clean infrastructure, plus the expensive ones — full mutation testing, deep review skills.
- *Scheduled drift detection*: dead-code detection, coverage-quality analysis, dependency freshness, modularity/security/data reviews, doc-gardening.
- *Runtime*: SLO degradation feeding improvement suggestions; LLM judges sampling output quality; log-anomaly flagging.

**3. Affordances — what does this codebase make cheap?** A typed language makes type checking a free sensor; clean module boundaries make structural rules expressible; a constraining framework abstracts away whole error classes; fast tooling makes in-session sensing viable. Start with what the codebase affords (in legacy code, usually maintainability sensors) and improve affordances incrementally. **Variety reduction**: committing to a topology ("CRUD service on JVM", "data dashboard in Node") narrows what an agent can produce, which is what makes a comprehensive control set achievable. Favor dependencies that can be fully internalized and reasoned about in-repo — "boring" technology models better; sometimes a small, well-tested in-repo reimplementation beats an opaque library.

## Computational guides

- **Deterministic dev environment** — lockfiles, devcontainers, Nix, pinned toolchains. The agent must get the same environment every run, ideally inside a sandbox: anything it needs should be installable and runnable in a coding-agent sandbox without ceremony.
- **One-command bootstrap** — `make setup` / `init.sh` that stands the project up per checkout. The gold standard: the application is **bootable per git worktree**, so an agent can launch and drive one isolated instance per change — the prerequisite for behaviour sensors (browser automation, observability).
- **Task-runner command surface** — Makefile/justfile/package scripts as the single discoverable verb set: install, dev, test, test-single, lint, typecheck, build, migrate. Paired with its AGENTS.md listing, this is the highest-leverage guide pair that exists (the ~160× effect).
- **Scaffolding and generators** — templates encoding structure so the agent never invents layout. Pairs naturally with a skill ("bootstrap a new X") wrapping instructions + script.
- **Codemods** — mechanical migrations (OpenRewrite, jscodeshift) exposed as commands, so transformations are executed deterministically rather than re-derived by inference each session.
- **LSP / code intelligence** — language servers wired into the agent runtime for precise navigation and types. For DSL-heavy projects, the language server, validators, and generators *are* the computational half of the AX setup — custom languages need custom AX tooling by definition.
- **Generated reference docs** — derived ground truth (DB schema, API surface, dependency graph) regenerated by CI into `docs/generated/`, so the agent reads reality instead of prose approximations.
- **Typed boundaries** — parse-don't-validate at every ingress; shared typed schemas/SDKs as machine-checkable guides for what data looks like.

## Inferential guides

- **AGENTS.md** — the root map; full treatment in `agents-md.md`.
- **Skills** — reusable on-demand procedures (how-to-test, review, release, bootstrap, migration recipes, debugging-with-observability). Division of labor: *AGENTS.md = always-on project context; skills = on-demand procedures.* The Agent Skills format (agentskills.io) is read by ~40 tools: a folder with `SKILL.md` (YAML frontmatter, `name` + `description`) plus optional `scripts/`, `references/`, `assets/`; ~100 tokens until triggered. Stick to the core spec — vendor extensions are ignored by other tools. Security: the spec has no signing; registries have hosted malicious skills at scale. Treat third-party skills like dependencies — pin, review, prefer single-source references over vendored copies.
- **llms.txt dependency references** — vendor-provided LLM-optimized docs for key dependencies, checked into `docs/references/`, pinned to the dependency version — so the agent doesn't hallucinate library APIs it half-remembers.
- **Code-level discoverability ("SEO for agents")** — roughly half of what agents act on arrives through grep/find hits, not instruction files. Make code findable: domain-driven names over technical ones (`OrderProcessor`, not `OrderServiceFactory`), domain-term synonyms in comments, no duplicate generic filenames (`index.ts` everywhere forces opening them all), no abbreviations, comment the *why* (business rules, decisions), keep verbosity down to conserve the reader's context.
- **Golden principles** — a short, stable, opinionated statement of agent-first operating principles (e.g. "prefer shared utilities over hand-rolled helpers", "never probe data shapes — validate at the boundary or use the typed SDK"), kept in `docs/design-docs/core-beliefs.md`. This is the seed from which lint rules get promoted, and the standard GC agents scan against.

## Computational sensors

- **Type checker** — free, continuous, high-signal. If the stack is untyped, adding types is an affordance investment that comes before sensor work.
- **Linting tuned to agent failure modes.** The lowest-hanging fruit for AI-generated code: max function arguments, max file length, max function length, cyclomatic complexity — none active in common linter defaults; configure them explicitly. Agent-targeted rule packs are emerging (required test files, structured logging).
- **Structural/dependency rules** — dependency-cruiser (JS/TS), ArchUnit (JVM), import-linter (Python): the layer diagram as executable rules ("clients must not import services"), with messages that recap the whole layering concept. Add a rule that every new file must live inside the predefined folder structure — otherwise agents quietly invent new top-level folders. Cheap to author with an agent's help; a genuine replacement for prose structure docs — but limited to what imports and paths can express. Small "taste invariants" belong here too: enforced structured logging, naming conventions, file-size limits.
- **Test suite + coverage** — the regression sensor. A failing pre-existing test poses exactly the right question: accidental breakage (fix the code) or intended change (update the spec and tests)?
- **Mutation testing** — crucial once test-writing is delegated to agents. Coverage says a line executed, not that its effect was asserted: 100% statement coverage via one broad acceptance test can coexist with a dozen surviving mutants and zero unit tests, and end-to-end-heavy AI-generated suites make that gap systematic. Resource-intensive → run incrementally or on demand. Companion pattern: a **query script over the results JSON** (summary / worst files / changed-files-only) so the agent analyzes results without flooding its context.
- **Property-based and fuzz testing** — where the domain suits them (logical edge cases; input resilience).
- **SAST and secrets** — semgrep (or the org's SAST) in-session and in CI; a secrets scanner in the pre-commit hook — a sensor that fires exactly when the agent tries to commit, which also protects against the agent itself.
- **Browser automation as a behaviour sensor** — Playwright/CDP wired into the runtime with procedures for snapshots, screenshots, navigation: the agent reproduces the bug, validates the fix, records before/after evidence, loops until clean. Requires per-worktree bootability.
- **Agent-legible observability** — an ephemeral per-worktree local stack (logs/metrics/traces) queryable via LogQL/PromQL-style tools, torn down after the task. Makes "ensure startup under 800ms" or "no span in these journeys exceeds 2s" tractable — architecture-fitness sensing.
- **The sensor-runner pattern** — a config-driven CLI running all computational sensors continuously (watch-mode), persisting snapshots to report *trends* ("worse than snapshot"), emitting a human status table and a token-efficient agent summary with per-sensor "what good looks like" thresholds. Each sensor is a small adapter script normalizing tool output to a common shape. Log sensor-state history — it feeds the effectiveness heuristics below.
- **Getting the agent to actually check sensors** — the honest options, in increasing reliability: an AGENTS.md instruction or skill (easiest, empirically unreliable — agents skip it and run tools directly); agent hooks (e.g. after file edits); git pre-commit hooks (a reliable forcing point for small-commit workflows); a custom runtime extension. This is a known weak point — set expectations accordingly rather than promising compliance.
- **Run it, don't read it — mitigations.** Agents *read* check scripts and predict their results, trading visible failures for invisible ones. Mitigate with instructions that mandate execution with captured output ("evidence-backed verification"), and — where it really matters — compiled or opaque check binaries the agent can only run. Scope the mandate to *each relevant check, once*: blanket "always verify before claiming done" phrasing adds no evidence and invites redundant re-runs of already-green work.

### Self-correction messages (the highest-leverage idea)

Every error channel is a guidance channel: a check's failure output lands verbatim in the agent's context at exactly the moment it can act — deliberate, benign prompt injection. Override default lint/check output so each message carries four parts: **what's wrong → why the rule exists → what to do instead → how to record a legitimate exception.** Three patterns, with the message text that made them work:

**Judgment-call suppression** — explain intent, permit a reasoned inline suppression with a mandatory reason:

```
✖ no-direct-http: OrderSync.ts:41 constructs its own HTTP client.
  Shared behavior (auth, retries, tracing) lives in the shared client;
  hand-rolled clients silently lose it.
  → Use `apiClient` from src/lib/http.
  → If this call genuinely cannot go through apiClient (e.g. a health
    probe that must bypass auth), suppress with a reason:
      // ax-allow no-direct-http -- (reason)
    Suppressions without a reason fail CI and all are listed in review.
```

Suppressions become visible, reviewable, and a natural code-review starting point.

**Threshold-bump instead of suppression** — for numeric rules (max-lines, complexity), invite the agent to *slightly raise the configured threshold* when refactoring is genuinely unwarranted, rather than suppressing: the rule stays armed and fires again if things worsen, avoiding the binary comply-or-silence choice. Field evidence: the one rule *without* such guidance was exactly the one the agent abused — the custom messages materially change behavior.

**Context-dependent remediation** — the same rule needs different fixes per layer, and the message can carry that:

```
✖ no-console: apps/server/src/jobs/retry.ts:88
  Backend code must use the structured logger (src/lib/log.ts) so output
  carries request IDs and reaches the aggregator.
✖ no-console: apps/web/src/checkout/Form.tsx:12
  Frontend code must not log at all — console output leaks user data to
  the browser. Remove it, or surface the condition in the UI state.
```

Write these messages when you wire each sensor in Phase 5 — a sensor with a stock message is half-installed. `scripts/check_docs.py` practices this pattern on itself; read its output format for a template.

## Inferential sensors

- **Review skills at graded depth** — fast `/code-review` in-session; `/architecture-review`, `/detailed-review` post-integration. The reviewer loop can be agent-to-agent, with the PR driven until all reviewer agents are satisfied and humans optional.
- **Modularity / design review** — the standout empirical result: raw coupling metrics (fan-in/out, DSMs) were noisy and misjudged legitimate hubs, while a prompt-engineered review reading the actual code found real, consequential issues (near-identical files awaiting a refactor agents never volunteer; a page reimplementing an existing hook; a parameter threaded through every level so one change touched 40+ files) — and correctly *excused* the legitimate hubs. Two operational lessons: **run such analyses more than once** (a second cold run surfaces new findings), and ground in the code itself — deterministic coupling data added little. Cross-file design quality is where computational sensing runs out and inference is required.
- **Security and data-handling reviews** — scheduled prompts derived from the org's AppSec checklist and data rules ("no user names reach the web frontend"): org policy turned into recurring sensors.
- **Dependency freshness** — a script gathers age/activity per dependency (computational); an LLM writes the upgrade/deprecation report (inferential).
- **Doc-gardening** — a recurring agent scanning for docs that no longer reflect code behavior, opening fix-up PRs. The semantic complement to the mechanical `check_docs.py` freshness check.
- **GC / janitor agents** — scheduled scans against the golden principles: update quality grades, open small, targeted, under-a-minute-to-review, auto-mergeable refactoring PRs. Agents replicate existing patterns, including bad ones — drift is inevitable, and continuous small debt payments beat painful bursts (teams have burned 20% of every week on manual cleanup before automating it).
- **LLM-as-judge on runtime signals** — sampling response quality, flagging log anomalies, proposing SLO-driven improvements.
- **Caveats** — cost and non-determinism (not every commit); noise management (legitimate patterns flagged as issues need a suppression mechanism or noise compounds); feedback overload can send an agent into over-engineering spirals; green dashboards breed false confidence.

## Drift and runtime sensors

Placement summary for the sensors that run on a cadence, not per-change: dead-code detection, coverage-quality analysis, dependency scanning and freshness, scheduled modularity/security/data reviews, doc-gardening, quality-grade updates — against the codebase; SLO trends and sampled-quality judges feeding suggestions back as issues/PRs — against the running system.

## Operating the control system over time

The setup you ship is a seed. These are the maintenance practices to hand over with it:

- **Sensor-history heuristics.** Log sensor states over time. A never-failing sensor is suspicious — unnecessary, or blind. A frequently-failing one signals weak guides (fix the feedforward side) or over-sensitivity. A declining failure trend signals improving guides or models. An always-green pipeline catches nothing; an always-red one indicts either the code or the pipeline.
- **Instruction cost accounting.** Instructions are not free (the 14–22% effect). Periodically re-run the litmus test over AGENTS.md and prune.
- **Guide/sensor balance review.** Once a sensor set is trusted, which guides can be deleted (context reclaimed)? Where do guides and sensors contradict each other? Are sensors pushing complexity sideways (a max-lines rule squeezing complexity into prop-drilling chains)?
- **Model evolution invalidates controls.** Controls encode assumptions about what models can't do, and those go stale — workarounds built for one model become dead weight on the next. Schedule "is this control still earning its cost?" reviews alongside the sensor-history analysis. Early candidate: evidence-capture mandates — there are first reports of newer models over-verifying, re-checking work that is already green.
- **Instruction rot is the default.** Doc-gardening + mechanical freshness checks + the active/completed and accepted/superseded lifecycles are not optional at scale.
- **Security posture.** Skills and agent-readable docs are an attack surface: unsigned skill registries have carried malware; docs are a prompt-injection channel; pre-commit secret scanning protects against the agent itself. Pin and review third-party skills; single-source instead of vendoring.
- **Don't optimize the score.** Track the honest test; use readiness scores only to find neglect.
- **The human role stays load-bearing.** A good AX setup doesn't eliminate human input — it directs it where it matters: intent specification, judgment calls sensors can't make, and steering the control system itself.

## Sources

- Böckeler — Harness engineering for coding agent users: https://martinfowler.com/articles/harness-engineering.html
- Böckeler — Maintainability sensors for coding agents (sensor catalog, message patterns, sensor-runner): https://martinfowler.com/articles/sensors-for-coding-agents.html
- OpenAI — Harness engineering: leveraging Codex in an agent-first world (legibility, GC agents, observability): https://openai.com/index/harness-engineering/
- Hashimoto — My AI Adoption Journey (the steering-loop founding rule): https://mitchellh.com/writing/my-ai-adoption-journey
- marmelab — Agent Experience best practices (code-level discoverability): https://marmelab.com/blog/2026/01/21/agent-experience.html
