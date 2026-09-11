# How to architect software projects for AI agents

Anyone who has delegated real work to a coding agent knows the moment: it confidently runs a build command that doesn't exist, or reinvents a helper your codebase has had for years. The reflex is to blame the model. Here's a more useful lens: the agent did exactly what your repository allowed it to do.

A human developer onboards once, then carries the project in their head. An agent onboards at the start of every single task — no memory of yesterday, no hallway conversations, no colleague two desks away. Whatever your project doesn't tell it, it has to guess. And a guess about a build command is what we politely call a hallucination.

The good news: this is an engineering problem, and it has engineering solutions. This article shows how to architect a software project so that agents can work in it reliably — and why that investment pays off fast.

## Agent experience

The discipline has a name: **Agent Experience (AX)**, coined at Netlify in 2025 by analogy to UX and DX. [agentexperience.ax](https://agentexperience.ax) describes it as the holistic experience AI agents have when interacting with a system — how easily they can access, understand, and operate within it. Applied to a software project, the question becomes: how easily can an agent understand your codebase, verify its own changes, and modify it safely?

You'll meet the same idea under different names. **Context engineering** is the broader discipline of getting the right information to a model at the right time; project-level AX is its versioned, team-shared slice — context that lives in the repository rather than in one person's prompt window. **Harness engineering** is what [OpenAI](https://openai.com/index/harness-engineering/) and [Birgitta Böckeler](https://martinfowler.com/articles/harness-engineering.html) call the practice of building this environment around your codebase — worth knowing, though "harness" also names the agent runtime itself, which is a different topic.

And at the far end of the software lifecycle sits the **software factory**. [Ona](https://ona.com/stories/software-factory-what-we-learned) — which, fun fact, began its life as Gitpod, a project hatched at TypeFox — ran the experiment: in ten days, their automated setup merged 375 pull requests and produced about 67,000 lines of code, without a single human-written line of production code. The humans spent their hours on the layer *around* the product: specs, conventions, quality scorecards, review loops. Ona's conclusion was blunt: the quality of that layer capped what the whole factory could produce. Or in their words: "You do not build the product. You build a factory to build the product."

So what does *agent-ready* actually mean? Most of it follows from one principle: **repo-local or nonexistent.** A human developer patches over missing documentation with implicit knowledge and a quick question in chat. An agent has neither. Anything it cannot reach from inside the repository effectively does not exist — wikis, ticket threads, and the contents of your colleagues' heads are invisible to it. When an agent invents a build command, that is not a model defect to tolerate; it is an AX defect to fix. Agent-ready means the knowledge and the checks an agent needs are in the repo, executable, and current.

There is an honest test for all of this: give an agent a real ticket, with no human help. Does it reliably reach a green verification suite and produce a diff your reviewers accept? Everything that follows serves that test.

## The control system

The most useful mental model for building toward it comes from Böckeler: treat your repository setup as a **control system** that continuously regulates the codebase toward its desired state. Every measure you take answers two questions. Does it steer the agent *before* it acts, or verify the result *after*? And is it deterministic code, or an LLM run?

|  | **Guides** — steer before | **Sensors** — verify after |
|---|---|---|
| **Computational** (fast, cheap, on every change) | one-command setup, task runner, scaffolding, generated reference docs | type checks, linters, tests, structural rules, the build |
| **Inferential** (LLM-run, semantic, gated or scheduled) | AGENTS.md, docs folder, ADRs, specs, skills | AI review passes, security and modularity reviews, doc gardening |

Both directions are mandatory. Sensors without guides, and the agent makes the same mistakes fresh every session — nothing steers it up front. Guides without sensors, and rules pile up with no proof they held. Guides raise first-attempt quality; sensors give the agent a self-correction loop that fixes issues before a human ever sees them.

Two more concepts complete the model.

**The sensor ceiling.** A control system regulates only what some sensor observes. A defect class nothing checks — say, a page that renders broken while unit tests stay green — will ship, and ship again, without ever triggering a correction. The practical rule: before you let more agent work land with *less* human review, widen sensor coverage first. Ona merged roughly 87% of changes without human involvement, at a median of under five minutes from PR to merge — a regime that is only sane because a mesh of automated verifiers covered what human reviewers used to.

**The steering loop.** This is how the system grows. Whenever an agent makes a mistake, don't just prompt harder — change the repository so the mistake cannot recur ([Mitchell Hashimoto's](https://mitchellh.com/writing/my-ai-adoption-journey) founding rule). Escalate until it stops recurring: a line in AGENTS.md → a dedicated doc → a lint rule or structural test → an architectural constraint. Two habits keep the loop healthy: ship the new rule in the same change as the fix it came from, citing the incident — and only add rules for mistakes that actually happened. Speculative rules are dead weight.

The next two sections show how to build each half.

## Architecting the guides

The entry point is [AGENTS.md](https://agents.md) — an open format used by more than 60,000 open-source projects. Think of it as a README for agents: one predictable place for the context a coding agent needs. Two principles decide what goes into it.

**Map, not manual.** Keep it a compact map — around 150 lines — with pointers into deeper documentation. A giant instruction file crowds out the actual task, makes everything look equally important (so nothing is), and rots quietly.

**Every line passes the litmus test:** would removing it cause a mistake the agent wouldn't otherwise make? Ecosystem defaults never earn a line; your deviations from them do. This isn't aesthetics — instructions cost attention and tokens on every single run. One controlled study ([Lulla et al.](https://arxiv.org/abs/2601.20404)) executed real GitHub pull requests with and without a human-written AGENTS.md: median runtime dropped by 28.6% and output tokens by 16.6%. The flip side has been measured too: unedited, LLM-generated overview files *reduced* task success while raising cost. Generation is a fine starting point; it is never the shipped artifact.

Behind the map sits a docs folder with a small set of artifact types, each answering one kind of question. **ARCHITECTURE.md is the map:** where things live, what may depend on what. **Product specs are the promises:** the current intended behaviour of each capability — the document that settles "bug or intended?". **ADRs and design docs are the reasons:** single decisions in ADRs; whole designs, including the alternatives you *rejected*, in design docs — so no future session "helpfully" refactors away a deliberate choice. **Exec plans are the work:** in-flight state for tasks that span sessions. Guidelines cover the conventions no tool enforces yet.

Specs deserve special respect here. Ona's single biggest lesson was that spec quality determined how many bug-fixing rounds a feature needed: most failures were specification failures, not capability failures — the factory built what was described and missed what wasn't. A detailed product spec produced a working app with 54 PRs merged in one day; a five-line spec produced something that needed rounds of cleanup. When agents implement, the spec becomes the control surface.

How do you get all this without a month of writing? You don't write it — you excavate it. Let agents scan your codebase, your git history, and your issue tracker; a surprising share of the knowledge layer can be derived, and verified, from what's already there. For the part that lives only in heads, flip the interaction: let the agent interview your engineers — Matt Pocock's [grill-me](https://github.com/mattpocock/skills/tree/main/skills/productivity) pattern — with every answer landing in its target document immediately. The division of labor is clean: facts are the agent's job to dig up; decisions are yours to make. And one standard governs it all: **every fact traces to a source** — the repo, output captured during the session, or a human's actual words. Everything else is marked "to be confirmed" or left out. A knowledge layer that contains inventions is worse than none.

## Architecting the sensors

Four principles carry the sensor side.

**Verify by execution.** Never trust prose — including your own. Every command cited in agent docs gets actually run, and a doc–reality discrepancy is a first-class finding. This extends to the agents themselves: they demonstrably *read* check scripts and predict the result instead of executing them. So require evidence: run the check, capture the output, read the exit code.

**Verify the relevant output.** A change is proven at the observable output — the rendered page, the emitted data, the API response — never only at the code that produces it. Unit tests happily stay green over a broken layout. Where the agent can't natively perceive the output, supplying perception tooling is part of the architecture: browser automation like Playwright as the agent's eyes on your web UI, a query script over emitted data streams.

**Enforce invariants mechanically where possible.** State the boundary in prose, enforce it with a lint rule or a structural test, and leave the *how* open. Prose is for judgment; machines are for rules.

**Error channels are guidance channels.** A failing check's message lands verbatim in the agent's context at exactly the moment it can act on it — deliberate, benign prompt injection. Write it for self-correction: what's wrong, why the rule exists, what to do instead, how to record a legitimate exception, and where the rule is documented.

Two pieces of sensor discipline keep the whole thing trustworthy. **A sensor reports; it never repairs.** Findings become reviewed work items that travel the normal write path — a sensor that quietly fixes what it measures erases the very signal the steering loop feeds on. And **prove your sensors can fire:** a check that reports success while checking nothing is a false green wearing a sensor's uniform. The cheapest proof is a deliberate failing input.

Getting there follows the same pattern as the guides: let agents audit the repository. They will find inconsistencies — a documented command that no longer exists, a renamed lint rule that silently stopped applying. That's not embarrassing; it's the normal state of any project that has grown over years. Agents fix what's unambiguous and document the repo's instruments — its sensors and actuators — as they go. Two investments multiply everything else: a reproducible development environment with a one-command bootstrap (doubly important for distributed systems, where "works on my machine" compounds across services), and observability tooling that lets agents inspect data from the running system — because runtime signals are sensor input too.

## An agent skill for AX

We have distilled this playbook into an open-source agent skill: **agent-experience**, published in [TypeFox/agent-skills](https://github.com/TypeFox/agent-skills). Point it at your repository and it runs the process described above: it audits what's there — inventorying guides and sensors, checking claims against enforcement, verifying every documented command by execution — interviews your team for the knowledge that lives only in heads, and then generates and maintains the guide-and-sensor layer, held to the standards from this article: repo-local or nonexistent, map not manual, every fact traces to a source.

The skill follows the open Agent Skills format, so it works with compatible coding agents:

```
npx skills add TypeFox/agent-skills -s agent-experience
```

It grew out of the research summarized here and has been hardened by field-testing on real projects, including our own. It's MIT-licensed — take it, use it, and tell us where it falls short.

## Wrapping it up

Remember the honest test: a real ticket in, an accepted diff out, reliably, without a human holding the agent's hand. That's what this architecture buys — and unlike prompting tricks, it compounds. Every mistake becomes a rule or a sensor; every session starts smarter than the last one ended. Your engineers don't disappear from the picture; they move up a level, from typing the code to steering the system that produces it.

At TypeFox, we've spent more than a decade building languages, tools, and development environments for complex domains — and making projects agent-ready is where that experience currently gets its best workout. If you'd like a partner for the journey, or you've read this and think we're wrong about something: we'd genuinely like to hear from you.
