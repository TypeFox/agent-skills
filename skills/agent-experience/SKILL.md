---
name: agent-experience
description: Make a code repository agent-ready with state-of-the-art AX (Agent Experience): audit and set up AGENTS.md / CLAUDE.md and agent docs, wire verification sensors with self-correction messages, and build docs-as-memory (architecture docs, ADRs, exec plans). Use when the user wants to make a repo agent-ready or AI-friendly, onboard coding agents, create/review/improve AGENTS.md, CLAUDE.md, or other agent instruction files, set up a project for agent-first development, asks why an agent keeps repeating a mistake, asks any AX question (general or project-specific), or mentions "harness engineering", "agent readiness", "context engineering" (its repo-side slice), or "AX". Not for building agent runtimes or orchestration code, nor for authoring a single agent skill — use skill-creator for that.
---

# Agent Experience (AX)

AX is the experience AI agents have when working in a repository — how easily they can access, understand, verify, and safely change it. Two reframings drive everything in this skill. First, **onboarding happens at the start of every task**: a human onboards once, an agent re-onboards every session, so everything a new hire needs in week one, the agent needs in minute one, on every run. Second, **hallucination is what inference looks like when context is missing**: when an agent invents a build command or misuses an internal API, that is not a model defect to tolerate — it is an AX defect to fix.

**The honest test** — the single success criterion behind every artifact this skill produces: *an agent given a real ticket, with no human help, reliably reaches a green verification suite and produces a diff a reviewer accepts.* Optimize for that. Readiness checklists and scores are diagnostics for spotting neglect, never targets to maximize.

Vocabulary: write "AX" and "agent-ready" in everything you produce. When reading sources or searching the web, also recognize the synonyms: *context engineering* (the superset term — this skill is its repo-side slice), *harness engineering* (in its repo-side sense), *agent readiness*, *agent legibility*, *ambient affordances*. Generated artifacts never say "harness" — that word collides with the agent-runtime meaning.

## The control system in brief

Treat the repo-side AX setup as a control system that regulates the codebase toward its desired state. Two control directions × two execution modes give a 2×2 that classifies everything you find or create:

| | **Guides** (feedforward — steer before the agent acts) | **Sensors** (feedback — verify after it acts) |
|---|---|---|
| **Computational** (deterministic, fast, cheap — run on every change) | one-command bootstrap, task-runner command surface, scaffolding, codemods, generated reference docs, deterministic dev env | type checks, linters, tests + coverage, structural/dependency rules, mutation testing, secret scanners, the build |
| **Inferential** (LLM-run, semantic, costly — run at gates or on a schedule) | AGENTS.md, skills, docs/, ADRs (architecture decision records — short, versioned docs capturing one decision, its context, and its consequences), specs, code-level discoverability | review skills, modularity reviews, security/data reviews, doc-gardening, janitor/GC agents |

Both directions are mandatory. Feedback-only, the agent repeats the same mistakes every session — nothing steers it up front. Feedforward-only, rules accumulate but nothing ever verifies they held. Guides raise first-attempt quality; sensors give the agent a self-correction loop that fixes issues before they reach human eyes.

**The steering loop** is the practice that builds and maintains the system: whenever an agent makes a mistake, engineer the repository so that mistake cannot recur — never settle for "prompt harder". Escalate any recurring failure up this ladder until it stops recurring:

1. a line in AGENTS.md →
2. a dedicated doc or skill →
3. a lint rule or structural test →
4. an architectural constraint.

Keep quality left: fast computational sensors run alongside the coding session; expensive and inferential ones run post-integration or on a schedule.

## Non-negotiables — the AX standards

Hold every artifact you audit or generate to these. In improve mode they are the audit checklist; in every mode they are the generation rules. Cite them by tagline when explaining findings (e.g. "this violates *map, not manual*"), as this document does itself.

1. **Repo-local or nonexistent.** Anything the agent can't reach from inside the repo effectively doesn't exist — wikis, chat threads, and people's heads are invisible. Push knowledge into versioned repo artifacts. An external system counts as reachable only where a fetch path exists (e.g. `gh` for GitHub issues); otherwise mirror a one-line summary with the link as provenance.
2. **Map, not manual.** The root instruction file is a ≲150-line map that teaches the agent where to look next, with progressive disclosure into docs/. A giant file crowds out the task, makes everything "important" (so nothing is), rots into stale rules, and can't be mechanically verified.
3. **Every line passes the litmus test:** *would removing it cause a mistake the agent wouldn't otherwise make?* Instructions are not free — single-study numbers, but the best we have: unnecessary rules cost 14–22% extra reasoning tokens, commands listed in AGENTS.md get used ~160× more than unlisted ones, and unedited LLM-generated overview files *reduce* task success while raising cost ~23%. Deviations from ecosystem defaults earn lines; defaults never do.
4. **Never trust prose — verify by execution.** Every command cited in agent docs is verified by actually running it, with the exact invocation and timing recorded. A doc–reality discrepancy is a first-class finding, not noise.
5. **Enforce invariants mechanically where possible; prose only where judgment is required.** State the boundary ("parse data shapes at the boundary"), enforce it with a lint or structural test, and leave the how open.
6. **Error channels are guidance channels.** Every custom check emits messages written for agent self-correction: what's wrong, why the rule exists, what to do instead — and, where judgment is legitimate, how to record a justified exception.
7. **Single source of truth.** Each fact lives in exactly one place; everything else points at it. Never vendor copies of external docs — audited vendored files have drifted 183 lines from upstream, still instructing agents to run tools removed months earlier.
8. **Run it, don't read it.** Agents demonstrably *read* check scripts and predict their results instead of executing them. Require evidence-backed verification: execute the check, capture the output.
9. **Write-as-you-go.** Agent statelessness erases anything not captured: every interview answer and decision lands in its durable artifact immediately — never in a summary to be filed later.
10. **Docs are verified like code.** Freshness is mechanically checked (`scripts/check_docs.py` verifies cited commands, paths, intra-doc pointers, and frontmatter graph edges, and flags unverified generalizations), and every artifact has an explicit lifecycle: active/completed for plans, accepted/superseded for decision records.
11. **Convention over configuration.** This skill carries opinionated defaults for the AX layer itself — which artifacts to create, doc layout, sensor wiring, message patterns — and applies them whenever the user hasn't stated otherwise. Interviews and template placeholders gather *project facts* (intent, scope, technical architecture); they never poll the user on how to design the AX layer ("would you like ADRs?" is a forbidden question). An unprompted user preference or a hard project constraint overrides a default and gets recorded as an ADR. When in doubt, convention wins.
12. **Every fact traces to a source.** Any statement in a generated doc traces to the repo, to output captured this session, or to the user's own words — anything else is marked `(to be confirmed)` or omitted. Product color counts: an invented name, count, or backstory is as much a fabrication as an invented database choice, and the user is never quoted or paraphrased saying something they did not say.

## Pick your mode

Find the user's situation and jump in — state your chosen mode and scope before starting (that statement is Phase 0; consult alone skips it):

| Mode | Entry signals | Phases |
|---|---|---|
| **Retrofit** | Existing codebase; no or thin agent setup ("make this repo agent-ready", "onboard Claude/Codex here") | All phases 0–6, the full playbook |
| **Improve** | Agent instruction files already exist ("review our AGENTS.md", "make our agent docs follow AX standards", "why does the agent keep getting X wrong?") | All phases 0–6, scoped to the existing docs: audit against the standards, shrink, verify, restructure. Touch sensors only where docs state rules nothing enforces |
| **Greenfield** | No code yet ("set up a new project for agent-first development") | 0, then 4–6 — phases 1–3 are skipped (no code to audit); interview-first (see Greenfield specifics) |
| **Consult** | A question about AX, general or project-specific ("what belongs in AGENTS.md?", "is our CLAUDE.md too long?"), or one small, specific change ("add the release commands to AGENTS.md") | None — no phase spine; answer or apply directly (see Consulting specifics) |

## The workflow

One shared phase spine; the mode selects which phases run and at what depth.

### Phase 0 — Scope and mode

State the mode you picked, why, and what you will deliver, before doing anything else. If the request is narrower than the mode's full output ("just write an AGENTS.md"), keep the audit phases — generation without audit produces exactly the bloated files this skill exists to prevent — but scale the deliverable to what was asked.

**Done when** the user knows the mode and the planned deliverables.

### Phase 1 — Inventory and classify *(retrofit, improve)*

Scan the repo per the inventory checklist (agent files, human docs, command surface, verification configs, CI, hooks, environment, governance, generated artifacts, external-memory traces) — this is native Glob/Grep work. Place every finding in the control-model grid: guide or sensor × computational or inferential × lifecycle stage. Empty cells become the gap list. Cross-check *claims vs. enforcement*: every documented rule either has a sensor or is a promotion candidate; every sensor is either effective or advisory/ignored.

Load `references/audit-playbook.md` for the checklist, classification procedure, and matrix format.

**Done when** you have the classified inventory (matrix or equivalent — empty cells explicit), the gap list, and the claims-vs-enforcement findings.

### Phase 2 — Verify by execution *(any mode with existing code)*

Never trust documented commands — run them, in fresh-checkout order: install → build → typecheck → lint → test (full, then a single test) → dev-server boot. Record the exact working invocations, flags, prerequisite services, and timings, each labeled warm or fresh — a maintainer's warm checkout understates fresh-clone cost (feedback-loop speed is an AX property that shapes the whole design). Run `scripts/check_docs.py` over the existing agent docs. Discrepancies between docs and reality are first-class findings. While here, probe affordances: typed language? boundaries expressible as import rules? constraining framework conventions? Note sandbox friction — network needs, credentials, OS assumptions.

Load `references/audit-playbook.md` (verification protocol section).

**Done when** a verified command block exists, backed by captured output, with every discrepancy listed.

### Phase 3 — Assess and draft with placeholders

Distill the non-inferable deltas: deviations from ecosystem defaults, the verified command block, rules-without-sensors triage, boundaries (from CODEOWNERS, .gitignore, CI deploy steps), conventions mined from the code marked *observed, unconfirmed*. Draft the target artifacts — AGENTS.md from `assets/AGENTS.template.md`, plus the minimal docs/ subset this project actually warrants — with explicit `(to be confirmed)` markers wherever the repo couldn't answer. Never silently assume: a marker is a question for Phase 4; an unmarked guess is a fabrication (*every fact traces to a source*).

Load `references/agents-md.md` (content model, exclusion list) and `references/docs-structure.md` (which docs artifacts this project warrants).

**Done when** drafts exist and every unknown is a marker, not a guess.

### Phase 4 — Interview the placeholders

Interview the user to resolve exactly the markers — codebase-first is absolute: never ask what Phases 1–3 answered. Follow the grill protocol: one question at a time, themed batches in dependency order, a recommended answer with every question ("based on your CI config, I'd say X — correct?"), a visible progress counter, "skip / decide later" recorded as an explicit open question. Write each answer into its durable artifact immediately (*write-as-you-go*). Questions target intent, scope, and technical architecture — the AX layer's own shape follows the defaults and is not up for interview (*convention over configuration*).

Load `references/interview.md` for the protocol, theme→destination map, and question bank.

**Done when** no markers remain — each is resolved or recorded as an explicit open question.

### Phase 5 — Generate and wire

Produce the final artifacts:

- **AGENTS.md** per the content model, plus the **CLAUDE.md projection** (`@AGENTS.md` import — Claude Code does not read AGENTS.md directly) and nested per-package files for monorepos. Every other agent tool the user names or the repo shows traces of (Copilot, Cursor, Gemini, …) gets its projection too: a one-line import or pointer at that tool's native location, never a copied body. Every command in it comes from Phase 2's verified block.
- **Docs nucleus**: the minimal subset from Phase 3's triage (typically `docs/ARCHITECTURE.md` + `docs/adr/` + `docs/exec-plans/`), using `assets/adr-template.md` and `assets/exec-plan-template.md`. Product-specs and design-docs only on their evidence triggers from the triage (`references/docs-structure.md`) — specs from `assets/product-spec-template.md`, never as a per-module dump.
- **Sensors** per the escalation ladder for the promotion candidates from Phase 1, each with self-correction messages (*error channels are guidance channels*). Offer to install `scripts/check_docs.py` into the repo with a CI job that runs it with `--require-docs` — a gate whose docs vanish must fail, not report "nothing to check" forever (*docs are verified like code*). Every sensor and command added this session gets cited in AGENTS.md — in the commands section or the definition of done — because an unlisted sensor is one no future session will run.

Load `references/techniques.md` (sensor/guide catalog, self-correction message patterns) and `references/agents-md.md` (projections, drafting rules).

**Done when** artifacts are written and sensors are wired into the dev loop or CI.

### Phase 6 — Prove it and hand off

Run every new or changed sensor and `scripts/check_docs.py` against the final state; fix what fails — evidence-backed, output captured (*run it, don't read it*). Judge each sensor by its output, not its exit code: prove it can fire (a deliberate failing input is the cheapest proof), and prove it at every scope the docs claim for it — a gate advertised as covering README.md is proven by a deliberate failure in README.md, not by firing somewhere else. A check that reports success while checking nothing is a false green shipped as a sensor. Verification litters: remove the caches and build artifacts your runs created (`__pycache__/`, `.ruff_cache/`, …) from the delivered copy — and if no `.gitignore` covers them, that gap is itself an AX finding to fix or surface.

Then run the **claim check** over every doc this session wrote or changed — and every comment or message written into code or config along the way: a rationale invented for a config line is a fabrication exactly like an invented command. Re-read each as a skeptical reviewer and trace every factual claim to this session's evidence — captured output, a file actually read, or the user's words. Generalizations ("every module has a test file") are verified exhaustively or weakened; commands appear exactly as proven in the delivered copy; anything untraceable is fixed, marked `(to be confirmed)`, or cut (*every fact traces to a source*). Three claim families reliably slip past self-review because you just wrote what they describe, so they get mechanical treatment: pointers to other content ("see the open questions below") and claims quantified over a directory ("one test file per `src/` module") are both flagged by `check_docs.py` — every flagged quantifier is enumerated against that directory in-session or rewritten without it — and claims about tooling this session installed are exactly what the sensor-scope proof above tests. Then deliver:

1. The **remediation roadmap** for everything deferred, in foundational→sophisticated order (see the remediation ordering in `references/audit-playbook.md`), each step small and individually shippable.
2. The **steering loop as standing practice**: tell the team that from now on, every recurring agent mistake gets engineered away up the escalation ladder — the setup you built is the seed, not the finished system.

**Done when** everything green is proven with captured output, the claim check comes back clean, and the roadmap is delivered.

## Greenfield specifics

With no code to audit, Phases 1–3 are skipped — after Phase 0 you go straight to the interview (Phase 4), which leads: use the greenfield question bank in `references/interview.md` (product intent, users, stack, topology, module boundaries, risk profile, workflow, org constraints — every theme a product or technical fact, none an AX design preference).

Guide stack and topology decisions by **affordances** — the structural properties that make a repo governable: a strongly typed language (type checking is a free sensor), a constraining framework (conventions abstract away whole error classes), fast build/test tooling (feedback-loop speed), clearly definable module boundaries (expressible as import rules). Committing to a topology reduces variety: it narrows what an agent can produce, which is what makes a comprehensive control set achievable. Rigid layered architecture — usually postponed until hundreds of engineers — becomes an *early* prerequisite with agents, because constraints are what allow speed without decay.

Day-one build order: root map (AGENTS.md + CLAUDE.md projection) → one-command bootstrap and task-runner command surface → in-session sensors (typecheck, lint with agent-failure-mode rules, fast tests, secrets pre-commit) → docs nucleus (`docs/ARCHITECTURE.md`, `docs/adr/` seeded with the stack/topology decisions from the interview, `docs/exec-plans/`, and `docs/product-specs/product-brief.md` holding the interview's intent answers — the one spec greenfield warrants; per-capability specs come later, spec-first per feature).

Boundary: this skill sets up the AX layer around the user's chosen project scaffolding — it does not generate the application itself. The pull to cross this line is strongest at the end, when a working feature feels like the honest proof that the loop works. It is not: the sensors firing on deliberate failures prove the loop, and a feature silently answers product questions the interview left open. The ceiling is scaffold-level — a smoke-tested placeholder route and an empty, clearly labeled schema stub; no domain logic, no seeded domain data, no working screens. The user supplies product and technical decisions; the AX setup derived from them is applied by convention, not negotiated.

## Consulting specifics

Consult is for the light requests: the user wants to understand something about AX, or wants one specific change, and the phase spine would be ceremony. Skip the phases and the Phase 0 announcement — a question deserves an answer, not a preamble.

- **Ground answers in this skill's model.** Explain through the control system and the standards, citing taglines as everywhere else. Load only the reference file that covers the topic (e.g. `references/agents-md.md` for a question about AGENTS.md content) — not the whole set. When the answer is a *document*, route it before you write it: ARCHITECTURE.md is the **map**, product-specs are the **promises**, ADRs and design docs are the **reasons**, exec plans are the **work**. Anything about what a capability is *supposed to do* — bug-vs-intended, a disputed behaviour, a promise that keeps being broken — is a product-spec, not an ADR; `references/docs-structure.md` is the reference that covers that choice. For questions about *this* project, check the actual repo state with targeted searches before answering; never speculate about files you could read.
- **Targeted changes obey the standards at the scale of the edit.** Every added line passes the litmus test; any command you write down is verified by execution first; each fact lands in its single source of truth, and the CLAUDE.md projection stays a pure `@AGENTS.md` import. What consult never does: inventory, interview, roadmap, readiness score.
- **Escalate by offer, not by action.** If the question or edit exposes a deeper problem — the file violates *map, not manual*, documented commands don't run, rules have no sensors — name it in a sentence or two and offer improve mode. Don't launch the full workflow uninvited.
- **Know when you've left consult.** "Write our AGENTS.md" or "restructure our agent docs" is artifact-scale work: that's improve or retrofit, audit included. Say you're switching modes, then switch.

## Reference files

Load these when their phase comes up — don't read them all upfront.

- `references/audit-playbook.md` — inventory checklist with globs, classification procedure, verification protocol, distillation heuristics, readiness checks, remediation ordering. Load in Phases 1–3 and when writing the Phase 6 roadmap.
- `references/techniques.md` — the full guide/sensor catalog with selection criteria (regulation dimensions, lifecycle placement, affordances), self-correction message patterns, and operating the control system over time. Load in Phase 5 and when writing the roadmap.
- `references/agents-md.md` — AGENTS.md content model in leverage order, evidence and limits, drafting procedure, CLAUDE.md and multi-tool projections. Load in Phases 3 and 5; the primary reference for improve mode.
- `references/docs-structure.md` — the docs/ system of record: layout, fact routing, per-artifact when-and-how, plans, decision records, product specs and design docs (evidence-triggered), the library/framework case, hygiene invariants. Load in Phase 3 (docs triage) and Phase 5 (generation).
- `references/interview.md` — grill protocol, session mechanics, theme→destination map, greenfield question bank. Load in Phase 4; in greenfield mode load it first.

## Before you're done

Check the mode's definition of done: **retrofit** — verified commands, AGENTS.md + CLAUDE.md projection, docs nucleus, wired sensors, roadmap, all proven by execution; **improve** — the docs are shorter, every line passes the litmus test, every command verified, claims-vs-enforcement resolved or on the roadmap; **greenfield** — interview answers captured in durable artifacts, day-one AX layer in place around the user's scaffolding, nothing past the scaffold ceiling; **consult** — the question answered (or the change applied and verified) grounded in the standards, with any deeper gap you spotted offered, not silently pursued or dropped.

In every mode: the CLAUDE.md projection exists wherever an AGENTS.md was written; no vendored copies; no unresolved silent assumptions — open questions are recorded as open questions; every doc — and every code or config comment — you wrote or changed has passed the claim check. Readiness scores you produced are labeled as diagnostics. And in the phase-spine modes, the closing message hands over the steering loop: the honest test — ticket in, green suite and accepted diff out, reliably — is the target; this session's setup is only the seed.
