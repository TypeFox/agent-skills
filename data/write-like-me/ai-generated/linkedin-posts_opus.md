## 1. Open collaboration for IntelliJ and other desktop applications

Real-time collaboration shouldn't stop at the edge of the TypeScript ecosystem.

Until now, bringing Open Collaboration Tools into a non-web IDE meant reimplementing the whole stack yourself: session lifecycle, communication logic, encryption, plus a bridge to Yjs. That's a lot of work before the first shared cursor ever blinks.

The new OCT Service Process removes that barrier. It packs all of it into a standalone executable (or an npm package) that speaks JSON-RPC over stdin/stdout — completely independent of whatever your IDE is written in. Java, Kotlin, anything that can start a process and talk over a stream.

The first proof: an OCT plugin for IntelliJ, available now on the JetBrains Marketplace. An Eclipse IDE plugin is already in the works.

Jonah's article walks through the full integration, using IntelliJ as the example: launching and connecting to the process, authentication and room handling, the session lifecycle, and how document sync works when Yjs handles the merges for you.

Open protocols, no vendor silos. Developers stay in the IDE they love, and still work in the same live session.

---

## 2. Baukasten: a UI toolkit for building modern domain-specific applications

When Microsoft deprecated the Webview UI Toolkit for VS Code, extension authors lost their go-to, theme-aware component set. We built a successor — and then discovered it solves a second problem nobody was expecting.

Baukasten (German for "construction kit") is an open source React library for IDE-grade, data-dense applications. Over three dozen component families: buttons, inputs and modals in the core set; virtualized data tables, hierarchical trees, split panes and context menus in the extras.

Write your UI once, ship it to VS Code, Eclipse Theia, Electron and the browser. The application code doesn't change between targets — only one stylesheet import does. Components read semantic `--bk-*` tokens that resolve to the host's own theme variables, so your panel inherits the user's colors, dark mode and high-contrast settings automatically. That's a portability win and an accessibility win in the same move.

Here's the unexpected part: the same deliberate constraint that keeps humans consistent also keeps coding agents on the rails. Every visual decision is pre-decided, so an agent spends its context budget on domain logic instead of picking border radii. Baukasten ships an agent skill, `write-baukasten`, built to the open Agent Skills standard — so it works with Claude Code, Cursor, Copilot, Gemini CLI and Codex alike.

Free, open source, on GitHub.

---

## 3. An architecture for efficient language engineering

We measured where the memory in a language workspace actually goes. In our own projects, the concrete syntax tree accounted for more than 70% of it.

So in Fastbelt, our new language engineering framework, we removed it.

Instead of building a second tree, each token gets linked to the AST node that consumed it, and that node keeps a pointer back. You still get the bidirectional lookup a language server needs — text offset to AST node and back — without paying for a whole parallel structure. Written in Go, where slicing a string shares memory instead of copying it, so tokenizing is nearly free.

The result is a framework built for high throughput, low latency and a small footprint. Parallelized from the ground up: files are tokenized, parsed and reference-resolved concurrently, taking build throughput from ~7 MB/s on one core to ~45 MB/s across 16.

And because performance is a feature, we treat it like one. Benchmarks run in every CI build, and contributors get told in their PR when something regresses. That discipline is how our lexer went from 30 MB/s using Go's regexp package to 180 MB/s today.

Mark's article lays out the full architecture, including why an API without escape hatches makes for a better framework contract.

Fastbelt 0.1 is out. Feedback very welcome.

---

## 4. AI agents in collaborative coding sessions: The OCT Agent

What happens when a coding agent joins your pair programming session as an actual participant?

That's the question behind the OCT Agent. It logs into an Open Collaboration Tools session like anyone else: it gets a name, requests to join, and shows up in the user list. Everyone in the room can prompt it via chat, everyone sees its response, and everyone reviews the proposed changes together before a single line lands.

That last part is the whole point. Run an agent locally and only one person sees what's happening — the rest of the team is excluded until the result appears in the codebase. In a shared session, the agent's work becomes a team decision.

Technically, it's a bridge, not an agent. We didn't reinvent the wheel: it speaks the Agent Client Protocol (ACP, from Zed), which does for coding agents roughly what LSP did for language servers. Any ACP-compatible agent plugs in — Claude Code, Codex CLI, Goose, OpenCode.

Two things we learned the hard way: live agent cursors sound delightful and are miserable in practice, so we went with a shared diff view. And giving an agent full workspace context when it runs on a remote peer's machine is still an open problem — one we'd genuinely like to solve with the community.

Early-stage proof of concept, fully open. Come break it.

---

## 5. Agent skills and better evals with Langium AI

Coding agents are remarkable — right up until they meet your DSL. Novel syntax and semantics simply aren't in the training data, and it shows. Microsoft has flagged the same problem.

Langium AI exists to close that gap, and it just got a substantial update in three parts:

🔹 **A CLI.** `lai init`, `lai gen descriptor`, `lai gen sysprompt`, `lai eval` — from a plain Langium project to running evaluations in minutes. Notably, none of that uses AI. It's entirely programmatic. Setup friction was our biggest complaint, so we removed it.

🔹 **Agent skills.** Installable with a single `npx skills add`, covering everything from general Langium AI knowledge to guided refinement of descriptors, prompts and evals. There's even a skill for building a DSL-specific skill, so a general-purpose agent can get a head start on your language.

🔹 **A rebuilt evaluation suite.** Evals now read like tests — `describe`, a scoring function, run it — but behave like assessments: averaged across runs, with collected metadata and retained history so you can compare over time.

In practice this lets us run a quick litmus test on how hard a DSL-specific agent will be *before* committing serious effort. Ben's article shows exactly how.

All open source, all on GitHub.

---

## 6. Building with AI

"Building AI systems is an act of software engineering." — and with that, we're launching our domain-specific AI services and the *Building with AI* article series.

In the opening post, our CEO Daniel Dietrich sets out how AI fits into what TypeFox has always done: understanding a client's domain deeply, and finding the abstractions that make expert work simpler.

He sees two ways to apply it. The conservative one: enrich existing systems with AI for tasks that were hard to formalize a few years ago — precisely scoped, with verification routines that separate valid results from slop. The radical one: autonomous systems that act proactively, with humans filling the gaps AI can't yet close.

Technically, both land in the same problem class — enriching context with facts, storing and retrieving them, splitting work and recombining it, checking and validating results. Solve it well in one domain and the approach travels.

The post is also refreshingly unsentimental about the present. No working mind, no self-awareness on the horizon. Just useful systems, built carefully, on top of what actually exists today. Which is exactly why anxiety and hype both need to be swept aside.

There is no plug-and-play AI solution. There is engineering. More posts in the series to come.
