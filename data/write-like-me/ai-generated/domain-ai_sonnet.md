# The Model Is Not Your AI Strategy

## Building enterprise AI that understands your domain, operates within your constraints, and produces results you can verify

Every enterprise leader believes AI matters. Fewer can say what happens after the pilot.

Copilots are live. Chat interfaces are shipped. Agents are running in every function that will have them. The technology works — that was never really the question. The question is whether it survives contact with production: real data, real permissions, real consequences for getting it wrong.

McKinsey's 2025 numbers say it plainly. 88% of organizations use AI somewhere, up from 78% a year ago. 62% are experimenting with agents. And still: only 23% are scaling agents anywhere in the business. No function has cracked 10% scaled adoption. Just 39% report any enterprise-level EBIT impact — and for most, it's under five percent.

Adoption is universal. Value is rare.

This is not a model problem.

The frontier models are already highly capable and getting better every quarter. What's missing is the architecture around them — the domain knowledge, interfaces, permissions, validation, evaluation, and user experience that turn probabilistic intelligence into something you can actually run a business on.

That's the shift from generic AI to domain-specific AI.

A generic model knows a staggering amount about the world. It knows nothing about your product architecture, your engineering conventions, your approval processes, your proprietary terminology, your customer-specific rules, your current project state, or the conditions under which a given action is actually valid.

Those are the things that determine whether AI creates business value. Not the model.

The next phase of enterprise AI won't be won by the company with the longest prompt, or even necessarily the strongest model. It will be won by whoever engineers the best system around the model.

At TypeFox we describe that system in three words: **grounding, validating, integrating**. Domain-specific AI connects models to proprietary knowledge, live systems, and expert workflows — and adds the structural boundaries that make the output usable in real operations.

## The model is a component, not the system

A large language model is a reasoning engine. It is not an application. Treating it like one is where most AI initiatives go wrong.

A production system needs to know what's relevant to the task at hand. It needs controlled access to tools and systems. It needs to know what actions are actually possible. It needs a way to tell a plausible answer from a valid one. It needs an interface where experts can inspect, correct, approve, or reject what happens. And it needs a way to measure whether the whole thing is getting better.

OpenAI frames an agent the same way: a model, explicit instructions, a defined tool set, a workflow inside guardrails. Keep the architecture as simple as the task allows. Add autonomy only where it earns its keep. Route anything high-risk to a human.

That changes what a CIO is actually deciding.

It's no longer "which model do we standardize on?"

It's: **what architecture lets us apply models safely to our proprietary work?**

Models will change. Prices will change. Providers will change. What looks exceptional today is table stakes within a year.

Your domain won't change that way.

Your processes, your engineering knowledge, your business rules, your validation logic, your integrations, your data structures, your operational expertise — those are the durable assets. Good architecture makes them usable by whichever model makes sense today, and the one that replaces it next year.

## Context engineering beats prompt engineering

The first wave of LLM applications was mostly prompts — wording, system messages, templates, increasingly elaborate instructions.

Useful. Not sufficient.

As systems get more capable and workflows get longer, the real problem becomes: **what should the model know, right now?**

Anthropic calls this context engineering — curating everything the model sees: instructions, tools, retrieved information, history, external data, intermediate results. Their framing is the one to remember: a model's attention is a finite, depletable resource. Every irrelevant token competes with the ones that matter. The goal isn't more context. It's more relevant context.

Dumping thousands of documents into a retrieval system and hoping the model finds what matters is not an information architecture. It's an abdication of one.

Real context engineering answers specific questions: Which product version is this? Which rules apply to this customer? Which spec is authoritative? Which decisions constrain the next one? What's confidential? What's stale? Which concepts should be structural rather than re-explained in prose every time?

That means domain models, metadata, project information, documentation, and system state have to be treated as architecture — not as a pile of documents to search.

TypeFox's Domain-Specific AI approach puts this layer first: give the model the right information at the right time, instead of hoping generic model knowledge substitutes for what only you know.

For enterprises with decades of accumulated expertise, this is the opportunity. Your advantage is already encoded across your organization. AI gives you a new interface to it — but only if the architecture can expose it precisely.

## Give AI tools, not unrestricted access

Knowledge isn't enough. The real jump — from conversational AI to agentic AI — is the ability to act: query a database, inspect a repository, call an engineering service, validate a configuration, file a ticket, update a document, run a simulation, generate code, kick off a workflow.

That's where AI gets operationally valuable.

It's also where architecture stops being optional.

The Model Context Protocol has become the default mechanism for connecting AI to external tools and data. It's a good integration layer. But exposing an API to a model is not the same as designing an AI-ready tool.

Good AI interfaces work at the level of the domain. A manufacturing agent shouldn't have to reverse-engineer a dozen service calls to validate a machine configuration. A financial assistant shouldn't have to infer which combination of database writes constitutes an approved transaction. An engineering agent shouldn't get shell access just because the task eventually touches a file.

The interface should hand over **explicit capabilities with explicit semantics** — nothing more.

This is why we build custom MCP servers around the concepts, validations, and workflows that actually matter in a client's domain. Not every capability. The right ones.

Security makes this non-negotiable. Researchers call the underlying failure mode the "lethal trifecta": untrusted input, access to sensitive data, and the ability to act, all in the same agent at once. Remove any one leg and a successful prompt injection becomes an annoyance instead of a breach. That's the real argument for narrow tool design — not theory, but the difference between an agent that can be tricked into leaking data and one that structurally can't.

The MCP spec backs this up: mandatory authorization design, token validation, defined security boundaries, explicit user control over data access. It bans token passthrough outright and names the "confused deputy" problem directly — a server with legitimate elevated access, tricked into using it for someone who shouldn't have it.

OWASP ranks prompt injection its top LLM risk and lists excessive agency — too much functionality, permission, or autonomy for the task — right behind it. And it's blunt about a common misconception: neither RAG nor fine-tuning makes prompt injection go away.

The principle is simple:

**The model decides which permitted operation is useful. The software decides what's actually allowed.**

That separation is the entire difference between an enterprise-grade agent and a demo with a longer leash.

## Models reason. Software enforces.

For years the AI-reliability conversation has been about making models less wrong. Useful — but the wrong focus wherever correctness can be verified by software instead.

Don't tell the model to "be careful about power consumption." Calculate the power budget.

Don't ask it to remember the grammar. Parse it.

Don't hope it fills in four mandatory fields. Validate them.

Don't trust it to spot incompatible components. Encode the compatibility rules.

Don't let it guess which state transitions are legal. Enforce the state machine.

**Don't ask a probabilistic system to guarantee what a deterministic one can verify.**

That's a structural guardrail. Prompts influence behavior. Structure defines what behavior is even possible.

OpenAI's production guidance says the same thing from the other direction: layer model checks with deterministic rules, tool safeguards, auth, access control, and human escalation. No single mechanism carries the system.

NIST's Generative AI Profile — the closest thing the U.S. has to an official playbook here — treats trustworthiness as something engineered across the whole lifecycle, not a behavior you hope the model has.

Which changes how you should think about hallucinations. The goal isn't a model that never errs — unrealistic. The goal is an architecture where the errors that matter are detectable, contained, and correctable. That's a much stronger engineering claim to be able to make.

## Domain-specific languages are an unusually powerful AI interface

Natural language is great at expressing intent. Flexible, accessible, dense with meaning.

It's also ambiguous — for the same reasons.

Enterprise systems need both: the freedom of natural language where interpretation earns its keep, and the precision of formal structure where correctness is the point.

DSLs are that bridge. A domain-specific language gives a concept explicit syntax and semantics — an engineering configuration, a business rule, a diagnostic sequence, a deployment spec — in a form that's both machine-processable and readable by the people who actually understand the domain.

With modern LLMs, something new happens: both sides now speak text. An agent generates DSL text directly. Existing language infrastructure parses it, resolves references, type-checks it, validates it, and returns precise diagnostics. The agent repairs its own output from those diagnostics.

**intent → generation → validation → repair → verified result**

The model handles ambiguity. Deterministic tooling handles everything that can be formalized. And it runs in reverse too: a DSL becomes compact, structured context — instead of prose or a sprawling JSON blob, the model gets the same concise representation your experts already use.

We call the mix of formal structure and natural-language elements **semiformal language**. Syntax carries what must be exact; names, comments, and annotations carry intent and rationale. The model reads both at once.

That's one reason we built Langium AI — connecting LLM systems directly to the parsing, validation, and structural services of Langium-based DSLs, so the model doesn't have to guess a language's rules. They're part of the environment.

For business-critical AI, that's not just elegant. It's a hard boundary between **what AI proposes** and **what the organization accepts as valid**.

## Evals turn AI quality into an engineering discipline

Software engineering has one big advantage over most early AI projects: teams know how to test expected behavior. AI needs the same discipline.

A demo is not an evaluation. Running a prompt five times and eyeballing the output is not a strategy. And user complaints after launch are far too late to learn that a new model, a tweaked prompt, or a changed retrieval strategy quietly broke something important.

OpenAI frames the loop as **specify, measure, improve**: define what "good" means for the real workflow — with domain experts, not just engineers, building a "golden set" of reference cases — measure against it, fix what fails. Their point about benchmarks is worth repeating: a frontier leaderboard score tells you almost nothing about how the system performs on your specific workflow, because no public benchmark was built for your conditions.

Agent evals go further, because the text response is often not the outcome that matters. Did the database update? Was the configuration valid? Did it call the right tools? Did it respect the approval boundary? Did it recover when a step failed?

Anthropic draws the line that matters here: the transcript — what the agent said and did — versus the outcome — what actually changed. An agent can report a configuration validated, a record updated, a ticket filed, and be wrong on every count. Grading the transcript alone misses exactly the failures that matter. Anthropic also separates capability evals (what can it do) from regression evals (can it still do what it used to) — and recommends combining deterministic checks, model-based grading, and human judgment depending on the task.

This is where domain tooling turns out to be an evaluation asset in disguise.

A parser is a grader. A compiler is a grader. A type checker is a grader. A business-rule engine is a grader. A test suite is a grader. A simulator is a grader. A domain validator is a grader.

The more of your definition of correctness already exists in executable form, the more rigorously you can evaluate AI-generated work. Langium AI builds on exactly this — repeated runs, historical comparisons, DSL-specific evaluations structured like the software tests your team already trusts.

There's a strategic payoff too: strong evals reduce your dependence on any one model. When a new model ships, you don't debate whether it "feels better" for three weeks. You run the suite. Quality, latency, cost, failure modes, domain correctness — compared, not argued about. That's a model-portability strategy, not just a QA process.

## Agents need a harness

The same principle applies to autonomous agents. Give a capable agent a broad instruction and a toolset and you can get astonishing results — or astonishingly inconsistent ones. The difference is usually the environment around the agent, not the model.

A real harness gives an agent what sustained work requires: project instructions, architectural guidance, tool definitions, skills, validation hooks, tests, checkpoints, retry logic, and clear rules for when a human has to step in.

At TypeFox we build agent-ready project harnesses around existing software: a repeatable **plan → execute → verify** loop that lets agents make real progress without losing the architectural intent of the project.

Anthropic's engineering team has published two rounds of research on this in the past year — "Effective Harnesses for Long-Running Agents" in late 2025, and a harness-design follow-up in early 2026 — and both land on the same point: harness design changes what the same model can accomplish. Just as important, they're explicit that harness complexity should shrink as models improve, not pile up forever.

That's the discipline to hold onto. Constrain models where constraint creates value — don't bury them under permanent machinery built for last year's model's limitations. Every component earns its place.

The parts of the harness that last aren't elaborate orchestration frameworks. They're what you already needed regardless of AI: clear architecture, explicit specs, automated tests, machine-readable diagnostics, strong APIs, reproducible environments, well-defined responsibilities. AI just raises the return on all of it.

## Human control is also a UX problem

Enterprise AI gets discussed as if every interaction should be a chatbot. It won't be.

Chat is excellent for exploration, ambiguity, open-ended intent. It's poor at most of what existing interfaces already do better.

The strongest AI applications mix modes: an expert describes a change conversationally, inspects the result in an editor, sees inline diagnostics, reviews a diff, accepts what's right, and triggers verified execution — one workflow, several interaction styles. Elsewhere AI shows up as a completion, an inline explanation, a command-palette action, a generated form, or a background operation that only surfaces when judgment is actually needed.

That's why AI interaction design is core to our Domain-Specific AI work — not "add chat," but find where AI is the most useful interface between an expert and the system underneath.

Baukasten, our React UI library for domain-specific applications, was built on the same logic: a semantic component API that constrains the visual decision space, sharing logic across VS Code, Eclipse Theia, Electron, and the browser. For coding agents, that same constraint means less room to invent inconsistent styling — more reasoning capacity left for actual application behavior.

The broader point: **AI-ready architecture is usually just good architecture, made explicit.** Clear interfaces, semantic APIs, good diagnostics, consistent abstractions, machine-readable specs — all of it helps humans and agents equally. Organizations that build this way aren't just adopting AI. They're making their entire technology estate more operable, period.

## Governance has to become part of the architecture

The move from assistants to agents changes the governance problem for CIOs. A chatbot that drafts text has a small blast radius. An agent that touches confidential data, engineering artifacts, internal services, or transactions is a different class of system.

Policy documents don't contain that risk. Governance has to be technical: identity, authorization, tool boundaries, data classification, auditability, validation, approval workflows, observability.

Europe just made this concrete. Since August 2, 2026, Article 50 of the EU AI Act requires providers and deployers of interactive and generative AI systems to disclose when a user is talking to AI — regardless of whether the system is "high-risk" under the Act's other provisions. Non-compliance: up to €15 million or 3% of global annual turnover, whichever is higher. That's not a compliance footnote. That's a board-level number.

But regulation shouldn't be why you build this. It's also just what makes AI manageable. A CIO should be able to answer: which systems can this agent reach? Which operations can it run, under whose identity? What entered the model's context? What was proposed, validated, approved — by whom? What happened next? Can we reproduce the failure and prevent it recurring?

If a platform can't answer those questions, it isn't ready for real autonomy. No matter how good the demo looked.

## Use AI to accelerate transformation — keep the result

AI is also changing how these systems get built. A well-equipped agent can analyze a legacy application, translate repetitive structures, generate integration code, build UI components, migrate configurations, write tests, and explore architectural alternatives fast.

That's real leverage for modernization work and proofs of concept. But speed alone proves nothing.

A prototype that shows an LLM can generate something impressive proves very little. A strong prototype proves the **architecture** works: the model gets the context it needs, the integrations hold, the output validates, the security boundaries hold, users can actually review results, and the result has a maintainable path into production.

Same logic for AI-assisted migrations. Baukasten's constrained API and agent skill turn legacy-to-new-component migrations into a bounded, reviewable task — the agent does the repetitive work, engineers supervise at the level of intent, not line by line.

Use AI aggressively where it accelerates engineering. Invest the acceleration into a foundation you can actually keep.

## The CIO priority: own your domain layer

The AI market will keep moving fast. That's a reason to build the architecture now — not a reason to wait.

Models will improve. Frameworks will come and go. Providers will add capabilities. Standards will shift. The cost curve will keep falling in your favor.

Concentrate ownership on what stays valuable through all of it. Five things, made explicit:

1. **Choose workflows, not generic AI features.** Start with expert work where domain knowledge, reasoning, or automation actually changes the economics.
2. **Define the domain and what "correct" means.** Terminology, models, rules, specs, validators, tests, authoritative sources.
3. **Expose capabilities through narrow, intentional interfaces.** Domain-level tools with real permissions — not broad access to raw infrastructure.
4. **Build evaluations before you scale autonomy.** Turn expected behavior, edge cases, security requirements, and real scenarios into repeatable evals and regression suites.
5. **Design human control into the workflow.** Where transparency matters, where review adds value, when escalation is mandatory, what's safe to automate outright.

That produces an architecture that evolves instead of getting rebuilt every time the model landscape shifts.

Open standards like MCP help. Open-source foundations help. Explicit domain models help more.

But the single decision that matters most is conceptual: keep your organization's proprietary intelligence outside the foundation model. Models should be consumers of your domain layer — never the place where it lives.

## Domain-specific AI is the enterprise opportunity

For TypeFox, this is a continuation of more than ten years building languages, IDEs, visual tools, and domain-specific software for complex industries. Language engineering has always meant turning expert knowledge into structures a computer can process, without forcing experts to think like programmers. Custom IDEs have always meant putting the right information and operations in front of the right person at the right moment. Validation has always meant turning domain rules into executable feedback. Tool integration has always meant connecting specialized workflows to the systems around them.

AI doesn't replace any of that. It raises the value of all of it.

A language model gives you an unprecedented interface for intent and reasoning. Domain engineering gives that intelligence the structure it needs to become dependable work. Put them together:

Give the model exactly the context it needs. Give it tools built for the domain. Make critical concepts explicit. Validate everything that can be validated. Measure what matters. Keep permissions narrower than capabilities. Give experts a real way to supervise results. Keep the domain layer independent enough that the next generation of models plugs straight into it.

That's how AI goes from demonstration to infrastructure.

The advantage was never going to come from having access to AI — access is already everywhere. It comes from making AI **fluent in the knowledge, systems, constraints, and workflows that make your organization different from everyone else.**

That's domain-specific AI.
