# LionWeb + Langium: Building Language Tooling That Doesn't Lock You In

Picture the tooling you'd actually want for a serious systems or software engineering project: engineers write specifications in a textual editor, stakeholders review the same system as a diagram they can rearrange, a simulation tool runs against that model, and the results land back in the text as inline guidance — all in the browser, all working from the same underlying model.

That's not a wishlist. It's what teams building complex systems increasingly expect. The problem is that no single tool does all of this, and building custom integrations between every pair of tools you need gets expensive fast. LionWeb is an open, community-driven attempt to fix that at the protocol level. Langium — which we initiated and continue to build — is one of the first serious language workbenches to plug into it. Here's what that combination is good for, where it's still maturing, and what both should tell you about evaluating open source language tooling.

## The problem: no single tool does it all

Web-based tools for modeling and language engineering have matured a lot over the past few years. What hasn't matured is the connective tissue between them. A textual DSL editor, a graphical diagramming tool, a simulator, a validator — each is typically its own island, with its own data format and no agreed way to talk to the others.

For a single project, you can bridge that with point-to-point integrations. For a program with many projects, many tools, and a multi-year horizon, that approach doesn't scale: every new tool pairing means new custom glue code, and every change to one tool risks breaking the glue. This is the gap LionWeb set out to close.

## LionWeb: an open interoperability layer, not another single tool

[LionWeb](https://lionweb.io/) is a community-driven initiative — with participants from both academia and industry — to establish shared data interoperability across the modeling and language engineering ecosystem, so that existing tools can be combined instead of rebuilt.

The concepts are worth knowing because they're what make the interoperability possible, not just academic flavor:

- **Models and metamodels.** Any body of information — including an AST produced by Langium at runtime — is a *model*. The structure of a model is described by a *metamodel*. LionWeb's supported metamodel concepts are themselves described by a stable *meta-metamodel*, comparable to [Ecore](https://eclipse.dev/modeling/emf/) for anyone with an Eclipse Modeling Framework background.
- **Original vs. derived models.** *Original* models hold information a user actively provides — an AST parsed from a Langium-based DSL, for example — and live in LionWeb's central *repository*. *Derived* models are calculated from other models, like validation or simulation results.
- **Editors and processors around the repository.** Editors (a Langium-based DSL editor, a graphical diagram) and processors (generators, validators, type checkers) sit around the repository and exchange models with it according to the LionWeb protocol.

That the community has already produced integrations with tools including [MPS](https://www.jetbrains.com/mps/), [Starlasu](https://starlasu.strumenta.com/), [Freon](https://www.freon4dsl.dev/), and Ecore is a useful signal on its own: this is a live, adopted protocol effort, not a paper spec.

## Langium: the textual layer — and TypeFox's role in it

[Langium](https://langium.org/) is the language workbench for building textual DSLs in the browser. It's MIT-licensed, so it's free to use in commercial and closed-source projects with no strings attached. We initiated Langium in 2021 and have led its development since; since 2023 it's been hosted by the [Eclipse Foundation](https://projects.eclipse.org/projects/ecd.langium), so it isn't tied to any single company's fate — but we're still the team building it day to day and the team you'd work with to tailor it to your project. That's the combination worth noting: we're the inventors, and we're also the people you can bring in to make it fit your specific architecture.

Technically, Langium is parser-based, uses an EBNF-inspired grammar with an [LL(*) lookahead algorithm](https://www.typefox.io/blog/allstar-lookahead/), and is written in TypeScript with the Language Server Protocol built in — the practical successor to [Xtext](https://eclipse.dev/Xtext/) for the web, without the EMF and Eclipse UI dependencies that tied Xtext to the desktop era. You can try it in the [playground](https://langium.org/playground/), scaffold a VS Code extension with Yeoman in minutes, or look through the [showcases](https://langium.org/showcase/) — evidence that this is a workbench people are actually shipping languages with, not a research prototype.

## Putting them together: what the architecture actually does

In practice: Langium is the editor for your textual DSL. Through the LionWeb protocol, the AST Langium produces is transformed into a LionWeb model and stored in the central repository. From there, any other integrated tool — a graphical diagram, a simulator, a validator — can read that same model, and changes made in those tools flow back into the repository and, from there, back into the Langium editor. The underlying model is edited iteratively, from whichever tool fits the task and the stakeholder at that moment, instead of being locked into one editor's view of the world.

## The strategic case: integrate once, not per tool

This is where the combination earns its place in a toolchain decision, not just a technical one.

For LionWeb, Langium is another compatible component — and a distinct one. Most of LionWeb's current tooling leans toward projectional editing; Langium contributes a lightweight, parser-based editor for textual DSLs that runs entirely in the browser with no additional server required, which is a genuinely easy thing to integrate into an existing web application.

For Langium, LionWeb is more than an extra place to save an AST. Because the same model is available to every tool integrated with LionWeb, a Langium-based editor gets a path into diagrams, simulators, and validators without you writing a custom integration for each one. It also loosens an assumption that's often baked into DSL tooling by default: the written text doesn't have to be the single source of truth. You can load and save partial models, work with pieces too large to comfortably fit in one text file, or handle models that don't have a defined grammar at all.

The cost math is the part worth taking to a technology-strategy conversation: integrating Langium with the LionWeb protocol is a one-time effort — build it against the protocol once (call it *O(1)*), rather than once per external tool you eventually want to connect (*O(n)*). And because LionWeb is a community effort, the maintenance of that integration doesn't sit entirely on your project's shoulders either — it's a shared concern across everyone using Langium with LionWeb, not a line item unique to your budget.

## An honest maturity check: what's solid, and what's still open

Vague promises are the fastest way to lose a technical evaluator's trust, so here's where this combination genuinely stands.

**Model transformations — ready to build on.** Moving an AST into a LionWeb model (`ast2model`) and back (`model2ast`) is straightforward to implement in TypeScript today, since both Langium and LionWeb provide TypeScript APIs to work with.

**The serializer gap — the real blocker.** Turning a LionWeb model back into valid Langium-conformant text requires a *serializer*, and Langium doesn't have a generic one yet. Three things get lost without it: characters matched by unassigned data-type or terminal rules aren't stored in the AST and can't be reconstructed; grammar rules with overlapping alternatives — like `MyRule: 'student' Person | 'teacher' Person;` — don't record which alternative applied; and hidden terminals such as comments and whitespace aren't part of the AST at all. The workaround today is a hand-written, per-language code generator: it works, but it's bespoke, and every language building one starts from scratch. We're looking for a funding partner to build a generic serializer instead — a one-time investment that removes this workaround for every Langium-based language, not just this integration, since it also enables in-place AST-to-text transformations for Langium projects generally.

**Incrementality — an open question, and we're saying so.** The LionWeb protocol is designed to support incremental, delta-based transformations alongside full batch ones. Langium's parser isn't currently incremental, so a Langium–LionWeb integration would likely run in batch mode today rather than incremental mode. A workaround exists — diff two AST versions to compute a delta — but whether the cost of computing that diff is smaller than what incrementality would save depends entirely on your model size and how your data actually changes. This is a case-by-case evaluation, not a solved problem, and we'd rather tell you that up front than paper over it.

**Generating a grammar from a bare metamodel — partially automatable, and that's by design.** A LionWeb metamodel describes what data to store, not how a human should write it as text — so a good textual notation can't be fully auto-generated from a metamodel alone; a person still designs that. What can be automated is a serviceable default grammar, JSON-like in structure, as a starting point a language engineer refines (`metamodel2grammar`). The reverse direction — generating a LionWeb metamodel from an existing Langium grammar — is straightforward, since the grammar already implies the AST's node types.

**Reconciling different metamodels for the same concept — an ecosystem-wide problem, not a Langium one.** Even within LionWeb, two integrated tools can model the same real-world concept differently — a flow-chart edge represented as a `from`/`to` link on a node in one metamodel, versus its own `DataFlow` object in another, with different naming conventions on top. Bridging that takes additional model-to-model transformations, and it's a known open challenge in the broader "single underlying model" research space — worth flagging as something LionWeb as a community will need dedicated tooling for, not something specific to combining it with Langium.

## What this means if you're evaluating language tooling

The mid- and long-term case for this combination holds up: Langium-based editors gain an easier path to external modeling and language engineering tools, and LionWeb gains a lightweight, genuinely browser-native textual workbench — extending both ecosystems rather than duplicating either. The open items are real, and the serializer is the one worth weighing most carefully: it's significant, one-time effort, but low ongoing maintenance, since both LionWeb's meta-metamodel and Langium's grammar language are quite stable.

We'd like to contribute this integration to LionWeb as another open-source engagement, and we're looking for a partner to help fund the generic serializer that unlocks it. As an outlook, we may also contribute Typir — our open source library for type checking in the web, currently under development — as a further LionWeb component down the line.

## Talk to us about your architecture

If you're weighing whether to build point-to-point integrations between your modeling and language tools or invest in a shared protocol like LionWeb instead, that's precisely the kind of architecture decision worth thinking through with the people who built the pieces — before any code gets written. And if funding the Langium serializer or the Typir/LionWeb integration is something your project could get behind, we'd like to hear from you specifically. [Get in touch](https://www.typefox.io/contact/), drop into the [Langium community discussions](https://github.com/eclipse-langium/langium/discussions), or join the [LionWeb community](https://lionweb.io/#participation) directly.

---

### Further reading
- Bézivin, J. (2005). *On the unification power of models.* Software & Systems Modeling, 4(2), 171–188. [doi.org/10.1007/s10270-005-0079-0](https://doi.org/10.1007/s10270-005-0079-0)
- LionWeb initiative (2023). [Reference Architecture](https://lionweb.io/specification/reference-architecture/reference-architecture.html)
- Meier, J. et al. (2020). *Classifying Approaches for Constructing Single Underlying Models.* MODELSWARD 2019. [doi.org/10.1007/978-3-030-37873-8_15](https://doi.org/10.1007/978-3-030-37873-8_15)
