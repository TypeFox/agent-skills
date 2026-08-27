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

Interview **relentlessly** until shared understanding — depth is licensed, not rude; sustained interrogation surfaces requirements the user didn't know they had. Map the open markers as a **design tree** — every decision branches into the decisions that hang off it (stack before boundaries; boundaries before quality bars) — and work it in **rounds**:

- **Ask the frontier, wait, recompute.** The frontier is every question whose prerequisites are already settled — what you can ask *now* without guessing at answers you haven't heard yet. Ask the whole frontier in one round, numbered so answers stay attributable; a question whose answer depends on another question still open in this round belongs to a *later* round. Each round's answers reshape the tree: settled decisions push the frontier outward and unblock what depended on them. Where the runtime's question tool caps a batch, a round spans several calls — the round boundary is dependency, never the tool's batch size.
- **Recommended answer with every question.** Transform open questions into confirm/correct decisions: "Based on your CI config, I'd say deploys are the sensitive path — correct?" This is cheaper for the user and shows your repo analysis. Use the native question tool with options where available, the recommended answer listed first.
- **Facts are your job; decisions are the user's.** A frontier question that turns out to need an environment fact goes back to the repo (or a subagent), never to the user — and an in-flight lookup is just an unsettled prerequisite: only its downstream questions wait for it; ask the rest of the frontier now.
- **Escalate depth on signal**: follow up on a brief answer only where a downstream decision depends on it — when a branch is blocked, not for completeness.
- **Termination is an empty frontier, not a count**: the interview is done when every branch has been visited and nothing is left silently assumed — then stop.

## Session mechanics

- **Draft-with-placeholders first** (Phase 3), then interview *only the markers*. The draft is the agenda; update it live after each answer.
- **Group each round by theme** for legibility: commands & environment → boundaries → conventions → quality bars → docs & memory → workflow. The order tracks the dependency structure, so themes usually *are* the rounds — but the round boundary is dependency, and a round mixes themes freely when everything in it is genuinely unblocked.
- **Progress counter**: `[Round 2 — question 4/6]` keeps the user oriented and fatigue visible; with a batching question tool, embed it in the question text.
- **Fatigue management**: order by impact; accept "skip / don't know / decide later" and record it as an explicit open question in the target doc — an honest unknown beats a fabricated certainty. Offer to pause; state lives in the draft, so resuming is free.
- **Write-as-you-go (the critical rule).** Agent statelessness erases anything not captured: every answer lands in its destination file *immediately* — an AGENTS.md line, an ADR, a boundary entry — never in a summary to file later. An interrupted session then resumes exactly where it stopped.

## Unattended sessions

An autonomous harness ("the user cannot answer mid-task questions") or a headless run inverts the pacing, not the protocol: front-load all drafting, settling every prerequisite yourself with labeled defaults, and pre-record every marker as an open question in its destination artifact — the artifacts must be complete even if no answer ever comes. What remains is then a single frontier; ask it as one final round if a question channel exists at all. Where none does — or the knowledge-holder is someone other than whoever launched the run — ship the open questions as a **questionnaire** artifact instead of scattered markers: one document, questions most-important-first (async may get exactly one pass), an answer stub under each, a one-line *why this matters* wherever a question could be misread or invite a throwaway answer. The next attended session (or the knowledge-holder directly) fills it in, and the answers land through the theme→destination map as usual.

## Theme → destination map

| Theme | Destination |
|---|---|
| Commands, environment quirks | AGENTS.md commands section |
| Never-touch paths, secrets, deploy sensitivity | AGENTS.md boundaries |
| Change-coupling rules (what must accompany a bugfix, feature, API change) | AGENTS.md definition of done; sensor-promotion candidates |
| Load-bearing conventions (confirmed from archaeology) | AGENTS.md conventions, or promoted to a lint rule |
| Architecture rationale, rejected alternatives | ADRs |
| Intent and intended behaviour per capability | product-specs/ (evidence-triggered — rubric in `docs-structure.md`) |
| Design history outside the repo, multi-decision rationale | design-docs/ (rescued with provenance) or ADRs |
| Tolerated debt and its reasons | tech-debt-tracker |
| Quality bars, risk appetite per area | sensor thresholds; quality-score.md seeds |
| Org policy (security, data) | security-guidelines.md + derived review prompts |
| Terminology | glossary in design-docs |

Answers that *reject* a recommendation may produce no artifact of their own but are decisions like any other: record them with rationale in the exec plan's decision log — or an ADR when architectural — so the next session doesn't re-propose what the user already declined.

## Spec and design-doc triage *(retrofit, improve)*

Product-specs and design-docs are evidence-triggered (the rubric is in `docs-structure.md`), and half the evidence is human-held — these questions gather it. They are product facts, not AX preferences: the user names what is ambiguous, normative, or critical; whether specs exist then follows from the triggers by convention ("would you like specs?" stays forbidden).

- **Adjudication**: "When a test fails or behaviour surprises someone, what decides bug vs. intended today?" Recommend from the audit ("I found no in-repo source — it's issue threads and your judgment, correct?"). A durable answer that already exists is routed to, not duplicated; "nothing durable" is the trigger.
- **Candidates**: "The audit found intent gaps at (X) and (Y) — evidence: (recurring question / agent mistake / criticality). Which of these behaviours matter enough to pin down as a contract now?" Present a ranked shortlist with the evidence attached; accept "none yet" — the change coupling backfills later, and deferred candidates go on the roadmap.
- **Normativity** *(libraries/frameworks)*: "Is the behaviour documented on (site) a promise downstream users may rely on, or a description that may change? Which modules' behaviour do downstream projects depend on hardest?" The answer separates spec candidates from ARCHITECTURE.md index entries — and fixes how the semver boundary reads.
- **Design-history rescue**: "Where does design rationale live outside the repo — wiki, shared docs, issue threads? Which of those still describe reality?" Every named source becomes a rescue candidate with provenance and an `unverified` trust label until checked.

## Greenfield question bank

With no code to audit, the interview leads (phase order 0 → 4 → 5 → 6). Themes in dependency order; every theme is a product or technical fact — none asks how to design the AX layer, which follows from the answers by convention. Ask with a recommended answer wherever the earlier answers imply one.

**1. Product intent and users** → *product-specs/product-brief.md*
What is being built, for whom, and what does success look like in 6 months? What's explicitly out of scope for v1? (Recommend nothing here — this is pure discovery; everything else depends on it.)

**2. Stack choice, guided by affordances** → *ADR*
Which language/framework — and if genuinely open, recommend by affordances: a strongly typed language (type checking as a free sensor), a constraining framework (conventions abstract away whole error classes), fast build/test tooling (feedback-loop speed), good training-data representation ("boring" beats novel). "You said the team knows TypeScript and this is a web dashboard — I'd recommend TypeScript strict mode + [mainstream framework]; agree?"

**3. Topology commitment** → *ADR*
What shape is this system — CLI, service + API, web app, library, data pipeline? Monorepo or single package? Committing narrows what an agent can produce, which is what makes a comprehensive control set achievable — so push for a commitment, and record it.

**4. Module boundaries** → *ARCHITECTURE.md, structural rules*
What are the 3–6 top-level parts, and which must never depend on which? (Recommend a conventional layering for the chosen topology and let the user correct it.) These lines become import rules on day one, not after the first violation.

**5. Risk profile and quality bars** → *sensor thresholds, security-guidelines.md, AGENTS.md definition of done*
What breaks the business if it breaks — data loss, leaked PII, downtime, wrong numbers? Which parts need the strict bar and which are experimental? Compliance obligations? What must accompany each kind of change — a test with every feature and bugfix, a spec entry, a doc update? This decides gate strictness, the definition-of-done couplings, and where behaviour-dimension work is justified.

**6. Workflow and review model** → *AGENTS.md PR conventions*
Who reviews, what merges without review, PR conventions? Solo-with-agents differs from team-with-agents: recommend gating accordingly.

**7. Org constraints** → *AGENTS.md boundaries, security-guidelines.md*
Mandated tooling/registries/CI? Secrets management? Anything agents must never touch from day one?

Wherever an answer isn't forthcoming, record the open question in the draft artifact and proceed with the recommended default, labeled as such.

Greenfield is also where fabrication is cheapest: with no repo to contradict you, invented product color — location names, a predecessor system, "the user told me X" — reads exactly like fact. The *every fact traces to a source* standard binds hardest here: the user's words, a labeled default, or a marker; nothing in between.

## Sources

- Pocock — the "grill-me" pattern: https://www.aihero.dev/my-grill-me-skill-has-gone-viral — and its living form, the `grilling` (frontier rounds) and `to-questionnaire` (async questionnaire) skills: https://github.com/mattpocock/skills/tree/main/skills/productivity
- agentpatterns — grill-me anti-patterns (why output must feed durable artifacts): https://www.agentpatterns.ai/agent-design/grill-me-technique/
