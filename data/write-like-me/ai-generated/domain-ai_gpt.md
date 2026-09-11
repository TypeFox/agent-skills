# The Model Is Not Your AI Strategy

## Building enterprise AI that understands your domain, operates within your constraints, and produces results you can verify

Enterprise leaders no longer need to be convinced that AI matters. The more difficult question is what comes after experimentation.

Organizations have deployed copilots, built chat interfaces, connected foundation models to internal data, and launched agent pilots. The technology is clearly capable. Yet the distance between an impressive demonstration and a dependable enterprise system remains substantial.

McKinsey’s 2025 global survey captures that gap well. While AI use has become nearly universal among the organizations surveyed and 62% are already experimenting with AI agents, almost two-thirds have not yet started scaling AI across the enterprise. Only 39% report an enterprise-level EBIT impact.

This is not primarily a model problem.

The frontier models are already extraordinarily capable, and they will continue to improve. What enterprises lack is the architecture around them: the domain knowledge, interfaces, permissions, validation mechanisms, evaluation systems, and user experiences required to turn probabilistic intelligence into dependable operational capability.

That is the shift from **generic AI to domain-specific AI**.

The distinction matters. A generic model knows a remarkable amount about the world. It does not inherently know your product architecture, engineering conventions, approval processes, proprietary terminology, customer-specific rules, current project state, internal systems, or the conditions under which an action is actually valid.

Those are precisely the things that determine whether AI creates business value.

The next phase of enterprise AI will therefore not be won by the company with the longest prompt or even necessarily the company with access to the strongest model. It will be won by organizations that engineer the best system around the model.

At TypeFox, we describe that system in three words: **grounding, validating, integrating**. Domain-specific AI connects models to proprietary knowledge, live systems, and expert workflows while adding the structural boundaries required to make their output useful in real operations.

## The model is a component, not the system

A large language model is an extraordinarily powerful reasoning component. Treating it as the complete application is where many AI initiatives go wrong.

A production AI system has several layers. It needs to know what information is relevant to the current task. It needs controlled access to systems and tools. It needs to understand what actions are possible. It needs mechanisms that distinguish a plausible answer from a valid one. It needs a user interface through which experts can inspect, correct, approve, or reject what happens. And it needs a way to measure whether the complete system is actually getting better.

OpenAI describes an agent in similarly architectural terms: a model operates with explicit instructions and a set of tools, executing a workflow within defined guardrails. Its guidance recommends keeping architectures as simple as possible, adding autonomy where it creates value, and retaining human intervention for high-risk operations and failure cases.

That changes the CIO-level decision.

The strategic question is no longer simply, “Which model should we standardize on?”

It becomes: **What architecture will allow us to apply models safely and effectively to our proprietary work?**

Models will change. Prices will change. Providers will change. Capabilities that look exceptional today will become standard tomorrow.

Your domain will not.

Your processes, engineering knowledge, business rules, validation logic, integrations, data structures, and operational expertise are the durable assets. A strong enterprise AI architecture makes those assets usable by whichever models make sense at a given point in time.

## Context engineering is becoming more important than prompt engineering

The first generation of LLM applications focused heavily on prompts. Teams experimented with wording, system messages, templates, and increasingly elaborate instructions.

That remains useful, but it is no longer sufficient.

As AI systems become more capable and operate over longer workflows, the real engineering problem becomes deciding **what the model should know at each moment**.

Anthropic calls this context engineering: curating the complete information state available to a model, including instructions, tools, retrieved information, conversation history, external data, and intermediate results. The goal is not to maximize the amount of information in the context window. It is to maximize the relevance of the information the model receives.

That distinction is critical inside an enterprise.

More context is not automatically better context. Dumping thousands of documents into a retrieval system and hoping the model finds what matters is a weak substitute for understanding the information architecture of the domain.

Effective context engineering answers questions such as:

Which product version is the user working with? Which rules apply to this customer? Which architectural decisions govern this subsystem? Which specification is authoritative? Which identifiers are relevant to the current artifact? Which previous decisions constrain the next one? Which information is confidential? Which context is stale? Which domain concepts should be represented structurally rather than explained repeatedly in natural language?

This is why domain models, metadata, project information, documentation, source artifacts, and system state need to be treated as parts of the AI architecture rather than as an undifferentiated knowledge base.

TypeFox’s Domain-Specific AI approach explicitly puts this layer first: provide the model with the right domain information at the right time instead of expecting generic model knowledge to substitute for proprietary context.

For enterprises with decades of accumulated expertise, this is one of the largest opportunities in AI. Your competitive advantage is already encoded throughout your organization. AI creates a new interface to that knowledge—but only if the architecture can expose it precisely.

## Give AI tools, not unrestricted access

Knowledge alone is not enough.

The major step from conversational AI to agentic AI is the ability to interact with the world: query a database, inspect a repository, call an engineering service, validate a configuration, create a ticket, update a document, run a simulation, generate code, or initiate a business workflow.

This is where AI becomes operationally valuable.

It is also where architecture becomes non-negotiable.

The Model Context Protocol has rapidly established a common mechanism for connecting AI applications with external resources and tools. An MCP server can expose information and operations through machine-readable interfaces that compatible AI clients can discover and use. For enterprises, this makes MCP an attractive integration layer between general-purpose AI systems and proprietary capabilities.

But exposing an API to an AI model is not the same as designing an AI-ready tool.

Good AI interfaces operate at the level of the domain. A manufacturing agent should not need to reverse-engineer a dozen low-level service calls to understand how to validate a machine configuration. A financial assistant should not infer which combination of database updates constitutes an approved operation. An engineering agent should not be given unrestricted shell access simply because the underlying task ultimately modifies files.

The interface should present **explicit capabilities with explicit semantics**.

This is why we build custom MCP servers around the concepts, validations, workflows, and actions that matter in a client’s actual domain. The objective is not to give an agent every possible technical capability. It is to give it the right capabilities.

Security follows the same principle.

The MCP specification explicitly requires careful authorization design, access-token validation, clear security boundaries, and user control over data access and operations. Its authorization specification forbids token passthrough and addresses problems such as confused-deputy attacks.

OWASP identifies both prompt injection and excessive agency as major risks in LLM applications. Excessive agency occurs when an AI system has more functionality, permissions, or autonomy than the task actually requires. Retrieval or fine-tuning does not eliminate prompt-injection risk.

The correct design principle is straightforward:

**The model may decide which permitted operation is useful. The surrounding software decides what is actually allowed.**

That separation is fundamental to enterprise-grade agent systems.

## Models reason. Software enforces.

For years, much of the discussion around AI reliability has centered on making models less likely to produce incorrect answers.

That is useful, but it approaches the problem from the wrong direction when correctness can be determined by software.

If a generated hardware configuration exceeds a power budget, do not merely tell the model to “be careful about power consumption.” Calculate the power budget.

If an AI-generated program must conform to a grammar, parse it.

If a business rule requires four mandatory fields, validate them.

If a proposed system configuration contains incompatible components, encode the compatibility rules.

If only particular state transitions are legal, enforce the state machine.

In other words: **do not ask probabilistic systems to guarantee properties that deterministic systems can verify.**

This is what we mean by structural guardrails.

Prompts can influence behavior. Structural constraints define the space in which behavior is allowed to occur.

OpenAI’s current guidance for agent systems similarly recommends layered guardrails rather than relying on a single model-level mechanism, combining model-based checks with deterministic rules, tool safeguards, authentication, authorization, access control, and human escalation.

NIST’s Generative AI profile likewise treats trustworthiness as something that must be addressed throughout the design, development, use, and evaluation of the complete AI system—not merely through the behavior of the underlying model.

This changes how enterprise architects should think about hallucinations.

The goal is not to build an architecture that assumes the model will never make a mistake. That would be unrealistic.

The goal is to build an architecture in which important mistakes are detectable, containable, and correctable.

That is a much stronger engineering proposition.

## Domain-specific languages are an unusually powerful AI interface

This is also why language engineering has become highly relevant to AI.

Natural language is excellent for expressing intent. It is flexible, accessible, and remarkably information-dense for human communication.

Those same properties make it ambiguous.

Enterprise systems frequently need both worlds: the freedom of natural language where interpretation is valuable and the precision of formal structures where correctness matters.

Domain-specific languages provide exactly that bridge.

A DSL gives important domain concepts explicit syntax and semantics. An engineering configuration, business rule, diagnostic sequence, deployment specification, data transformation, or system model can be expressed in a form that is both machine-processable and readable by the people who understand the domain.

With modern language models, another important property emerges: both sides communicate through text.

An AI agent can generate DSL text directly. Existing language infrastructure can then parse it, resolve references, perform type checks, execute domain-specific validators, and return precise diagnostics. The agent can use those diagnostics to repair its own result.

This produces a fundamentally different AI loop:

**intent → generation → validation → repair → verified result**

The LLM handles the ambiguous part of the problem. Deterministic tooling handles the parts that can be formalized.

The same mechanism works in the opposite direction. A DSL can be supplied to the model as compact, structured context. Instead of describing a complex system repeatedly through prose—or exposing a deeply nested generic JSON representation—you give the model the domain concepts in the same concise form your experts use.

We call the combination of formal structures and natural-language elements **semiformal language**. Formal syntax captures the parts that must be exact; names, comments, strings, and annotations carry additional intent and rationale. The model can understand both simultaneously.

This is one reason we created Langium AI.

Langium AI connects LLM-based systems with the parsing, validation, and structural services of Langium-based DSLs. Instead of asking the model to guess the rules of a specialized language, those rules become part of the AI engineering environment.

For business-critical AI, this is more than an elegant technical pattern. It creates something enterprises badly need: a boundary between **what AI proposes** and **what the organization accepts as valid**.

## Evals turn AI quality into an engineering discipline

Traditional software engineering has a major advantage over many early AI projects: teams know how to define and test expected behavior.

AI systems need the same discipline.

A demo is not an evaluation.

Running the same prompt five times and reading the answers is not an evaluation strategy.

And user feedback after a release is far too late to discover that changing the model, prompt, tool definitions, retrieval strategy, or context selection caused an important capability to regress.

An evaluation suite makes the expectations explicit.

OpenAI describes the basic loop as **specify, measure, improve**: define what good performance means for the actual business workflow, measure the system against those criteria, and use observed failures to improve it. Its enterprise guidance emphasizes contextual evaluations because generic model benchmarks cannot capture the specific conditions under which an organization expects an AI system to operate.

Agent evaluations go further because the final text response is often not the most important outcome.

Did the correct database state result? Was the generated configuration valid? Did the agent call the right tools? Did it respect an approval boundary? Did the test suite still pass? Did it complete the workflow within an acceptable number of steps? Did it recover correctly when one operation failed?

Anthropic’s work on agent evaluations distinguishes between the interaction trace and the actual outcome, and recommends combining deterministic checks, model-based grading, and human expert judgment according to the task. It also distinguishes capability evaluations—what can the system do?—from regression evaluations—can it still reliably do everything it did before?

This is exactly where existing domain tooling becomes particularly valuable.

A parser is a grader.

A compiler is a grader.

A type checker is a grader.

A business-rule engine is a grader.

A test suite is a grader.

A simulator is a grader.

A domain validator is a grader.

The more of your definition of correctness already exists in executable form, the more rigorously you can evaluate AI-generated work.

Langium AI takes this approach directly. Its evaluation tooling supports repeated runs, historical comparisons, heuristic checks, and DSL-specific evaluations structured similarly to familiar software tests.

There is an additional strategic benefit: evals reduce dependence on any particular model version.

When a new model appears, the question does not have to become a multi-week subjective debate about whether it “feels better.” Run it against the evaluation suite. Compare quality, latency, cost, failure modes, and domain-specific correctness.

In that sense, a strong evaluation system becomes part of your model portability strategy.

## Agents need a harness

The same engineering principle applies to autonomous agents.

Giving a capable coding agent or business agent a broad instruction and a set of tools can produce astonishing results. It can also produce astonishingly inconsistent results.

The difference is often the environment around the agent.

An effective agent harness provides the structures needed for sustained work: project instructions, architectural guidance, requirements, tool definitions, skills, validation hooks, progress artifacts, tests, checkpoints, retry behavior, escalation paths, and rules governing when human review is required.

At TypeFox, we build such agent-ready project harnesses around existing software projects. The aim is a repeatable **plan → execute → verify** loop in which agents can make progress autonomously without losing the architectural intent of the project.

This area is developing quickly. Anthropic’s recent work on long-running coding agents shows that harness design can dramatically change what the same underlying models are able to accomplish. Their experiments use structured planning, evaluation, iterative build-and-review cycles, and persistent artifacts to keep agents working coherently on complex software over extended periods. Just as importantly, Anthropic emphasizes removing unnecessary harness complexity as models improve.

That last point deserves attention.

An enterprise AI architecture should constrain models where constraints create value—not bury them under permanent machinery built around the limitations of last year’s model.

Every component should earn its place.

The most durable parts of the harness are therefore usually not elaborate agent orchestration frameworks. They are the assets your organization already needs independently of AI: clear architecture, explicit specifications, automated tests, machine-readable diagnostics, strong APIs, reproducible environments, and well-defined responsibilities.

AI makes the return on those engineering investments substantially higher.

## Human control is also a user-experience problem

Enterprise AI is often discussed as though every interaction should become a chatbot.

That is unlikely to be the final shape of the market.

Chat is excellent when the user needs to explore, ask open-ended questions, explain intent, or negotiate ambiguity. It is poor at many tasks that existing interfaces already handle more effectively.

The strongest AI applications therefore combine interaction modes.

An expert might describe a desired change conversationally, inspect the generated result in an editor, see diagnostics inline, review a graphical diff, accept selected modifications, and trigger a verified execution—all within one workflow.

In other situations, AI may appear as a completion, an explanation beside an error, an action in a command palette, a suggested transformation, a generated form, or an autonomous background operation that surfaces only when human judgment is required.

This is why AI interaction design is a core part of our Domain-Specific AI offering. The objective is not to add chat. It is to determine where AI creates the most useful interface between a domain expert and the underlying technical system.

The same thinking shaped Baukasten, our React UI library for domain-specific applications.

Baukasten deliberately constrains the visual decision space through a semantic component API and reusable design system. Applications can target VS Code, Eclipse Theia, Electron, and the browser while sharing the same application and component logic. For coding agents, that constrained API also reduces opportunities to invent inconsistent styling or nonexistent interfaces and allows more reasoning capacity to remain focused on application behavior.

This illustrates a broader point: **AI-ready architecture is often simply good architecture made more explicit.**

Clear interfaces help humans and agents.

Semantic APIs help humans and agents.

Good diagnostics help humans and agents.

Consistent UI abstractions help humans and agents.

Machine-readable specifications help humans and agents.

The organizations that structure their systems this way are not merely adopting AI. They are making their technology estate increasingly operable by both people and machines.

## Governance must become part of the architecture

For CIOs, the expansion from assistants to agents also changes the governance problem.

A chatbot that drafts text has a limited blast radius. An agent that can retrieve confidential information, change engineering artifacts, call internal services, or initiate transactions is a different class of system.

Policies alone cannot contain that risk.

Governance must be expressed technically through identity, authorization, tool boundaries, data classification, auditability, validation, approval workflows, and observability.

The European regulatory environment makes this increasingly tangible. Since August 2, 2026, transparency obligations under Article 50 of the EU AI Act apply to certain interactive and generative AI systems, including requirements to make users aware when they are directly interacting with AI.

But regulation should not be the primary reason to engineer these properties.

They are also what make AI operationally manageable.

A CIO should be able to answer: Which systems can this agent access? Which operations can it perform? Under whose identity? Which information entered the model context? Which result was proposed? Which validations ran? Who approved the action? What happened afterward? Can we reproduce the failure? Can we prevent it from recurring?

A production AI platform that cannot answer those questions is not ready for serious autonomy.

## Use AI to accelerate transformation—but keep the result

AI itself is also changing how these systems can be built.

A well-equipped agent can analyze a legacy application, translate repetitive structures, generate integration code, build UI components, migrate configurations, create tests, and rapidly explore architectural alternatives.

This creates enormous leverage for modernization projects and proofs of concept.

But speed is not enough.

A prototype that proves only that an LLM can generate something impressive is of limited value. A strong prototype proves that the **architecture** works: the model receives the necessary context, integrations are viable, output can be validated, security boundaries are sound, users can review results effectively, and the resulting software has a maintainable path into production.

The same principle applies to AI-assisted migrations.

Baukasten provides a simple example. Its constrained API and agent skill make transformations from legacy VS Code UI components into a new component system a bounded, reviewable task. The agent can perform repetitive migration work while engineers supervise the transformation at the level of intent.

This is the pattern we apply more broadly to prototypes and migrations: use AI aggressively where it accelerates engineering, but invest that acceleration into a foundation the organization can actually keep.

## The CIO priority: own your domain layer

The AI market will continue to move extraordinarily quickly.

That is a reason to invest in architecture, not a reason to postpone it.

Foundation models will improve. Agent frameworks will appear and disappear. Providers will add capabilities. Standards will evolve. The cost curve will keep moving.

Enterprises should therefore concentrate ownership on the parts that remain strategically valuable across those changes.

A practical starting point is to make five things explicit:

1. **Choose workflows, not generic AI features.** Start with valuable expert work where access to domain knowledge, reasoning, or automation changes the economics or quality of the process.

2. **Define the domain and the definition of correctness.** Identify the terminology, models, rules, specifications, validators, tests, and authoritative information sources the system needs.

3. **Expose capabilities through narrow, intentional interfaces.** Give AI access to domain-level tools with appropriate permissions rather than broad technical access to underlying infrastructure.

4. **Build evaluations before scaling autonomy.** Convert expected behavior, known edge cases, security requirements, and real user scenarios into repeatable evaluations and regression suites.

5. **Design human control into the workflow.** Decide where users need transparency, where review adds value, when escalation is mandatory, and which actions are safe enough to execute automatically.

This creates an AI architecture that can evolve without being rebuilt every time the model landscape changes.

Open standards such as MCP help. Open-source foundations help. Explicit domain models help even more.

But the most important architectural decision is conceptual: keep the proprietary intelligence of your organization outside the foundation model.

Make models consumers of your domain layer—not the place where your domain layer lives.

## Domain-specific AI is the enterprise opportunity

For TypeFox, this direction is a natural continuation of more than ten years of building languages, IDEs, visual tools, and domain-specific software for complex industries.

Language engineering has always been about translating expert knowledge into structures computers can process without forcing experts to think like general-purpose programmers. Custom IDE development has always been about giving users the right information and operations in the right context. Validation has always been about turning domain rules into executable feedback. Tool integration has always been about connecting specialized workflows with the systems around them.

AI makes all of those capabilities more valuable.

A language model provides an unprecedented interface for intent and reasoning. Domain engineering provides the structure that turns that intelligence into dependable work.

Put the two together and the architecture becomes clear:

Give the model precisely the context it needs.

Give it tools designed around the domain.

Represent critical concepts explicitly.

Validate everything that can be validated.

Measure the behavior that matters.

Keep permissions narrower than capabilities.

Give experts meaningful ways to supervise results.

And keep the entire domain layer independent enough that the next generation of models can plug into it.

That is how AI moves from demonstration to infrastructure.

The enterprise advantage will not come from simply having access to artificial intelligence. Access is becoming ubiquitous.

The advantage will come from making AI **fluent in the knowledge, systems, constraints, and workflows that make your organization different from everyone else**.

That is domain-specific AI.
