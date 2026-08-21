# Interviewing the user — grill protocol and question bank

The codebase can't answer everything. What only the human holds: intent and roadmap; which conventions are load-bearing vs. habit; consciously tolerated debt and its business reasons; risk appetite and quality bars per area; review and merge workflow; deployment realities; org context (compliance, security policy, data rules); what agents must never touch; what "good" looks like here. The whole AX setup is an attempt to externalize what human experience and org alignment implicitly provide — the interview is where that externalization happens deliberately.

## When to interview vs. explore

**Codebase-first is absolute: never ask what Phases 1–3 answered or could answer.** Every question spent on the discoverable burns trust. Skip or truncate the interview when:

- the repo answers it (always explore first);
- external constraints fully determine the answer (an API contract, a regulation — you'd get confirmation, not discovery);
- the work is cheaply reversible (a failing test reveals the gap faster than a question);
- no durable artifact will capture the answer (then the answer will be lost — fix that first or don't ask).

## Fact-finding, not preference-polling

Questions investigate **intent, scope, technical architecture, workflow, risk appetite, and org constraints** — never the user's preferences about the AX layer's own design. "Do you want ADRs?", "how long should AGENTS.md be?", "which doc layout do you prefer?", "would you like an ARCHITECTURE.md?" are all forbidden questions: the skill's defaults settle them (the *convention over configuration* standard). If the user volunteers an unprompted preference or a hard constraint, honor it and record it with its rationale (as an ADR) — the skill honors flexibility; it just never solicits it.

## Core protocol

Interview **relentlessly** until shared understanding — depth is licensed, not rude; sustained interrogation surfaces requirements the user didn't know they had. The rules that make it work:

- **Termination is a goal, not a count**: continue until you're confident you understand the underlying intent — then stop.
- **Walk the decision tree in dependency order.** Decisions have prerequisites; resolve each branch before the branches that depend on it (stack before boundaries; boundaries before quality bars). Don't fire questions randomly.
- **One question at a time** — protects the user's working memory and yields clean, attributable answers.
- **Recommended answer with every question.** Transform open questions into confirm/correct decisions: "Based on your CI config, I'd say deploys are the sensitive path — correct?" This is cheaper for the user and shows your repo analysis. Use the native question tool with options where available.
- **Escalate depth on signal**: follow up on a brief answer only where a downstream decision depends on it — when a branch is blocked, not for completeness.

## Session mechanics

- **Draft-with-placeholders first** (Phase 3), then interview *only the markers*. The draft is the agenda; update it live after each answer.
- **Batch by theme**, resolving each theme's branch before moving on: commands & environment → boundaries → conventions → quality bars → docs & memory → workflow.
- **Progress counter**: `[Question 4/9]` keeps the user oriented and fatigue visible.
- **Fatigue management**: order by impact; accept "skip / don't know / decide later" and record it as an explicit open question in the target doc — an honest unknown beats a fabricated certainty. Offer to pause; state lives in the draft, so resuming is free.
- **Write-as-you-go (the critical rule).** Agent statelessness erases anything not captured: every answer lands in its destination file *immediately* — an AGENTS.md line, an ADR, a boundary entry — never in a summary to file later. An interrupted session then resumes exactly where it stopped.

## Theme → destination map

| Theme | Destination |
|---|---|
| Commands, environment quirks | AGENTS.md commands section |
| Never-touch paths, secrets, deploy sensitivity | AGENTS.md boundaries |
| Load-bearing conventions (confirmed from archaeology) | AGENTS.md conventions, or promoted to a lint rule |
| Architecture rationale, rejected alternatives | ADRs |
| Intent, roadmap, product judgment | product-specs, design-docs |
| Tolerated debt and its reasons | tech-debt-tracker |
| Quality bars, risk appetite per area | sensor thresholds; quality-score.md seeds |
| Org policy (security, data) | security-guidelines.md + derived review prompts |
| Terminology | glossary in design-docs |

## Greenfield question bank

With no code to audit, the interview leads (phase order 0 → 4 → 5 → 6). Themes in dependency order; every theme is a product or technical fact — none asks how to design the AX layer, which follows from the answers by convention. Ask with a recommended answer wherever the earlier answers imply one.

**1. Product intent and users** → *product-specs, project brief*
What is being built, for whom, and what does success look like in 6 months? What's explicitly out of scope for v1? (Recommend nothing here — this is pure discovery; everything else depends on it.)

**2. Stack choice, guided by affordances** → *ADR*
Which language/framework — and if genuinely open, recommend by affordances: a strongly typed language (type checking as a free sensor), a constraining framework (conventions abstract away whole error classes), fast build/test tooling (feedback-loop speed), good training-data representation ("boring" beats novel). "You said the team knows TypeScript and this is a web dashboard — I'd recommend TypeScript strict mode + [mainstream framework]; agree?"

**3. Topology commitment** → *ADR*
What shape is this system — CLI, service + API, web app, library, data pipeline? Monorepo or single package? Committing narrows what an agent can produce, which is what makes a comprehensive control set achievable — so push for a commitment, and record it.

**4. Module boundaries** → *ARCHITECTURE.md, structural rules*
What are the 3–6 top-level parts, and which must never depend on which? (Recommend a conventional layering for the chosen topology and let the user correct it.) These lines become import rules on day one, not after the first violation.

**5. Risk profile and quality bars** → *sensor thresholds, security-guidelines.md*
What breaks the business if it breaks — data loss, leaked PII, downtime, wrong numbers? Which parts need the strict bar and which are experimental? Compliance obligations? This decides gate strictness and where behaviour-dimension work is justified.

**6. Workflow and review model** → *AGENTS.md PR conventions*
Who reviews, what merges without review, PR conventions? Solo-with-agents differs from team-with-agents: recommend gating accordingly.

**7. Org constraints** → *AGENTS.md boundaries, security-guidelines.md*
Mandated tooling/registries/CI? Secrets management? Anything agents must never touch from day one?

Wherever an answer isn't forthcoming, record the open question in the draft artifact and proceed with the recommended default, labeled as such.

## Sources

- Pocock — the "grill-me" pattern: https://www.aihero.dev/my-grill-me-skill-has-gone-viral
- agentpatterns — grill-me anti-patterns (why output must feed durable artifacts): https://www.agentpatterns.ai/agent-design/grill-me-technique/
