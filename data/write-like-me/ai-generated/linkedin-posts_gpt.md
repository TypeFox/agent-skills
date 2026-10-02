## 1. Open collaboration for IntelliJ and other desktop applications

Real-time collaboration should not depend on which IDE your team happens to use.

With the new OCT Service Process, Eclipse Open Collaboration Tools can now be integrated into non-TypeScript desktop applications through a standalone JSON-RPC bridge. The service encapsulates the hard parts — session lifecycle, communication, encryption, and Yjs-based synchronization — behind a simple stdin/stdout API.

The first result is already here: an OCT extension for IntelliJ. An Eclipse IDE integration is next, using the same approach.

This moves OCT another step toward what we set out to build from the beginning: an open collaboration layer that works across development environments instead of creating another isolated ecosystem. VS Code, Eclipse Theia, custom web apps, IntelliJ — and increasingly anything that can speak the protocol.

Jonah’s article walks through the architecture and implementation in detail, from authentication and session setup to synchronized documents and cursor positions.

If cross-IDE collaboration matters to your tooling strategy, this is the piece that makes the architecture much more portable.

## 2. Baukasten: a UI toolkit for building modern domain-specific applications

What if building a UI for VS Code, Eclipse Theia, Electron, and the web did not mean maintaining four different front ends?

That is the idea behind Baukasten, our new open source React component library for domain-specific applications.

Baukasten is designed for the dense, tool-heavy interfaces we regularly build: trees, virtualized tables, tabs, split panes, context menus, forms, dialogs, and other IDE-grade components. The same application code can target VS Code webviews, Theia, Electron, or a standalone browser application while inheriting the host environment’s theme and accessibility settings.

There is another reason we deliberately keep the API constrained: coding agents.

When visual decisions are encoded in a design system instead of scattered across utility classes and one-off styles, an agent can spend more of its context and reasoning budget on the actual application logic. Baukasten even ships with an Agent Skill that teaches compatible coding agents how to use the library correctly.

So the constraint is intentional: fewer arbitrary choices, more consistency, and a UI foundation that works equally well for humans and agents.

## 3. An architecture for efficient language engineering

Performance in language tooling is not something you can bolt on at the end. It has to shape the architecture from the beginning.

That is exactly what we are doing with Fastbelt, our new language engineering framework written in Go.

The latest article explains several architectural choices behind its performance characteristics. Fastbelt avoids building a conventional concrete syntax tree and instead links tokens directly to AST nodes, removing a major source of memory overhead. In our application projects, CSTs have accounted for more than 70% of a workspace’s memory footprint.

Fastbelt is also designed around parallelism. Parsing, symbol-table construction, reference resolution, validation, and read-only language-server operations can make use of multiple cores. In one benchmark, workspace build throughput increased from roughly 7 MB/s on one core to about 45 MB/s on 16 cores.

And we treat performance like any other feature: benchmarks run in CI, so regressions become visible with every change. That discipline already helped us push tokenizer throughput from about 30 MB/s to 180 MB/s.

Fastbelt v0.1 is available now. This article explains why it is fast — not just that it is.

## 4. AI agents in collaborative coding sessions: The OCT Agent

A coding agent does not have to be a private assistant sitting behind one developer’s screen.

What happens when it joins the collaboration session as another participant?

That is the idea behind the OCT Agent. It connects ACP-compatible coding agents to an Eclipse Open Collaboration Tools session, where everyone can interact with the agent, see its responses, review proposed changes, and decide together whether to accept them.

The important part is the collaboration model. If an agent runs locally for one developer, the rest of the team only sees the result after that developer has reviewed it. In an OCT session, the interaction itself becomes shared: prompts, explanations, and diffs are visible to everyone.

We deliberately built the OCT Agent as a bridge rather than yet another agent framework. It uses the open Agent Client Protocol, so it can connect to compatible tools such as Claude Code, Codex CLI, Goose, or OpenCode. Proposed changes appear as diffs instead of being written directly into the shared workspace.

It is still an evolving proof of concept, but it points toward a collaboration model we find much more interesting: humans and agents working in the same transparent session, without locking either side into one editor or one AI vendor.

## 5. Agent skills and better evals with Langium AI

General-purpose coding agents are impressive — right up until they meet a language they have barely seen before.

That is a common problem with domain-specific languages. Their syntax and semantics usually have little or no representation in an LLM’s training data, so even strong agents start guessing.

The latest Langium AI update is aimed directly at that gap.

We added a CLI that can set up Langium AI tooling and evaluations in minutes, a set of Agent Skills that teach compatible agents how to work with Langium and Langium AI, and a redesigned evaluation API that feels much closer to writing normal tests in TypeScript.

The evaluation part matters especially. Instead of judging an agent by a handful of convincing demos, you can define repeatable cases, run them multiple times, collect metrics, retain history, and compare results as prompts, skills, models, or tooling evolve.

We even provide a skill for creating DSL-specific skills — giving a general-purpose agent explicit knowledge about the language it is supposed to work with, and then evaluating how much that knowledge improves the result.

For us, this is the interesting direction for AI in language engineering: less guessing, more structure, and measurable progress.

## 6. Building with AI

AI is now an integral part of our work at TypeFox — but our starting point is still software engineering, not magic.

In the first article of our “Building with AI” series, Daniel Dietrich lays out how we think about domain-specific AI and why it fits naturally with what we have been doing for years: understanding complex domains, finding useful abstractions, and building tools that help experts work with them.

We see two broad directions. AI can enrich existing systems with capabilities that were previously hard to formalize. Or it can become more autonomous, acting through agent loops and interacting with its environment. Technically, both directions share many of the same engineering problems: context, knowledge retrieval, task decomposition, tool integration, checks, and validation.

That is why we are much more interested in reliable systems than in waiting for the next model release to solve everything. The useful question is not simply “which model should we use?” but “which tasks should AI handle, what context does it need, and how do we verify the result?”

This article opens the series with that foundation. The next steps go deeper into how these systems are actually built.
