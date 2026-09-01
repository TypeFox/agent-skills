## 1. Break the IDE Silo: Real-Time Collaboration for Any Development Environment

Most real-time collaboration features are deeply tied to a particular editor or technology stack. But what if the same collaborative session needs to span VS Code, Eclipse Theia, IntelliJ, Eclipse IDE, and custom applications?

We faced exactly this problem with Eclipse Open Collaboration Tools. Our solution was to pull the hard parts of collaboration out of the IDE entirely. A standalone service process handles the collaboration protocol, authentication, encryption, session lifecycle, and Yjs-based document synchronization, while exposing a small JSON-RPC interface that any development environment can consume.

Using our IntelliJ integration as a concrete example, this talk shows how that architecture works—from launching the service and joining a session to synchronizing edits and awareness information between peers. We’ll also look at the design decisions that make the same approach applicable to Eclipse IDE and other desktop tools.

The broader lesson: interoperability becomes much easier when collaboration is infrastructure, not an editor feature.

## 2. Less Choice, Better Code: Designing UI Systems for Humans and AI Agents

The fastest way to make an AI coding agent better at building user interfaces might be to give it fewer choices.

Modern frontend development exposes enormous freedom: colors, spacing, typography, breakpoints, states, component APIs, styling strategies. Humans struggle to keep all those decisions consistent. Coding agents have the same problem—except every incidental decision also consumes context and reasoning capacity that could have gone into the actual feature.

We took the opposite approach with Baukasten, an open source React toolkit for domain-specific applications. Its deliberately constrained semantic API encodes visual decisions into the design system. The same application can then run natively in VS Code, Eclipse Theia, Electron, and the browser, while an accompanying agent skill gives coding agents an authoritative, compact description of how to use it.

This talk explores what happens when we treat constraints not as a limitation, but as an optimization for both human and AI-assisted development: smaller decision spaces, more predictable code, cleaner diffs, portable applications—and more reasoning spent on what the software actually does.

## 3. Delete the Tree: Rethinking Language Tooling for Speed and Scale

Language engineering frameworks have built concrete syntax trees for decades. So we asked a dangerous question: do we actually need one?

When developing Fastbelt, our new high-performance language engineering framework in Go, we found that concrete syntax trees could account for more than 70% of a workspace’s memory footprint in real applications. Yet language servers still need their essential capability: mapping positions in source text to semantic model elements and back.

Fastbelt eliminates the CST and directly connects tokens with AST nodes instead. Combined with zero-copy string slicing, parallel parsing and reference resolution, explicit concurrency primitives, and an API designed without inheritance-based escape hatches, this changes both the performance characteristics and architecture of a language framework.

We’ll explain the trade-offs behind these decisions and share concrete benchmark results, including build throughput growing from roughly 7 MB/s on one core to 45 MB/s on 16 cores, and lexer throughput improving from 30 MB/s to 180 MB/s.

Sometimes performance optimization is not about doing the same work faster. It is about realizing you never needed to do the work at all.

## 4. When the AI Joins the Pairing Session: Collaborative Coding with Agents as Peers

AI-assisted coding is still surprisingly solitary. One developer asks an agent to change the code, watches what happens, and eventually shares the result with everyone else.

What if the agent joined the collaborative session instead?

With the OCT Agent, we are experimenting with coding agents as first-class participants in Eclipse Open Collaboration Tools sessions. Everyone can talk to the agent through the shared chat, everyone sees its responses, and proposed code changes appear as a shared diff that the team can discuss before accepting them.

The interesting part is that we did not build another coding agent. Instead, we created a bridge between two open protocols: OCT for real-time collaboration and the Agent Client Protocol for communication with coding agents. That means ACP-compatible agents can participate without OCT knowing which agent is behind the bridge.

This talk covers the architecture, why our first “AI typing with a live cursor” experiment was the wrong interaction model, how shared review changes the human-agent workflow, and the unresolved challenge of providing workspace context when an agent runs on another participant’s machine.

Pair programming gets more interesting when the third chair is occupied by an AI.

## 5. AI Agents Don’t Know Your DSL: Teach Them, Then Test Them

General-purpose coding agents benefit from enormous amounts of training data about JavaScript, Python, Java, and other popular languages. A domain-specific language may exist only inside one company.

That changes the AI engineering problem completely.

Instead of hoping that a better model will magically understand unfamiliar syntax and semantics, we can explicitly teach agents about a DSL—and then measure whether that teaching actually works. With Langium AI, we combine generated language descriptions, agent skills, and an evaluation framework designed specifically for DSL-aware agents.

This talk shows how existing language and domain documentation can become executable evaluations and agent guidance. We’ll explore DSL-specific skills, system prompts derived from language structures, and an evaluation API that feels like ordinary software testing while accounting for the non-deterministic nature of AI: repeated runs, aggregate scores, heuristic checks, collected metrics, and historical comparisons.

The result is a much more engineering-driven answer to “Can an agent work with our language?” Instead of guessing, demoing, or trusting a single impressive result, we can teach it, test it, improve it, and know where the limits are.

## 6. Stop Waiting for the Next Model: Engineering Reliable AI Systems Today

The next language model will be better. Your software still has to work today.

Much of the AI industry is caught in an upgrade loop: a model fails at something, so we wait for the next release and hope the problem disappears. But reliable AI applications cannot be built on hope. They need architecture.

Whether AI performs one precisely bounded task inside an existing application or operates as an autonomous agent, the underlying engineering problems are remarkably similar: providing the right context, storing and retrieving knowledge, decomposing work, interacting with tools and environments, combining intermediate results, and validating the outcome.

This talk presents a software-engineering view of AI systems that deliberately moves the model out of the spotlight. We’ll look at how abstractions, domain-specific capabilities, workflows, agent loops, and verification mechanisms determine whether an AI feature is useful and trustworthy.

The goal is neither to downplay what language models can do nor to speculate about what they might do next year. It is to build better systems with the capabilities we actually have.
