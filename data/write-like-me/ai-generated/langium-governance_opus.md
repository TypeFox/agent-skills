# Open governance for Langium

**Today we submitted Langium as a project proposal at the Eclipse Foundation. It is the fifth time we have handed something we built to someone else — and every time, it has been the best decision we made for it.**

## The strange business of giving your work away

The people who founded TypeFox built Xtext. For years it was the center of our professional lives, and for a good while it was the center of our business. It is also not ours. It has lived at the Eclipse Foundation for well over a decade, governed by a process none of us controls, used by companies who have never heard of us.

That should have been a catastrophe for a consulting firm. Instead, Xtext ended up in ECU toolchains, railway signaling systems, telecom configuration platforms, and financial rule engines — places no single vendor's roadmap could have carried it. It became infrastructure. And infrastructure, it turns out, is a far better thing to have built than a product you own outright and defend alone.

We took the lesson. [Theia](https://github.com/eclipse-theia/theia), [Sprotty](https://github.com/eclipse-sprotty/sprotty), [LSP4J](https://github.com/eclipse-lsp4j/lsp4j), [Open VSX](https://github.com/eclipse/openvsx) — all started here, all handed over. Today Langium follows them, as a proposed project under the [Eclipse Cloud Development](https://projects.eclipse.org/projects/ecd) top-level project.

We are not doing this because Langium is finished, or because we lost interest, or because someone asked. We are doing it because we intend Langium to still matter in 2035, and we have learned that the surest way to guarantee that is to make sure it does not depend on us.

## The question nobody puts in the RFP

When a technical executive evaluates a language toolkit, the feature comparison is the easy part. It is also not the part that keeps anyone awake.

The real question sits underneath, usually unspoken: *what happens to us if the company behind this changes its mind?*

It is a fair question, and the industry has spent the last several years teaching everyone to ask it. Licenses get changed. Repositories go quiet. Open-core boundaries move. A dependency that looked like a foundation turns out to have been a favor.

Here is the uncomfortable truth about Langium as of yesterday: the answer to that question was "TypeFox." We hold the copyright. We appoint the committers. We own the name. We could, in principle, relicense the whole thing on a Tuesday.

We have no intention of doing that. But *intention* is not a control. And no serious architecture board should accept intention where a structure belongs.

An open-source license tells you what you may do with the code today. Governance tells you what can happen to the project tomorrow. Langium has had an excellent license since its first commit. Starting now, it gets governance to match.

## What we are actually handing over

Not the work. The power.

| | Yesterday | Under Eclipse governance |
|---|---|---|
| License | MIT | MIT — unchanged |
| Copyright | TypeFox | Contributors, with Foundation stewardship |
| Project decisions | TypeFox | Elected leads and committers, per the [Eclipse Development Process](https://www.eclipse.org/projects/dev_process/) |
| Committer rights | Granted by TypeFox | Earned on merit, granted by committer vote |
| Contribution IP | Project policy | Eclipse Contributor Agreement plus Foundation IP due diligence |
| Trademark | TypeFox | Eclipse Foundation, as neutral steward |
| Vulnerability reporting | TypeFox | [Eclipse Foundation Security Team](https://www.eclipse.org/security/) |

Read that table as a list of things we can no longer do to you. We cannot relicense Langium. We cannot rename it, move it behind a paywall, or quietly let it die. We cannot keep the committer list closed to competitors — and yes, that includes vendors who compete with us directly. If they earn commit rights through sustained contribution, they get them, and their vote counts as much as ours.

That is not generosity. It is the price of being infrastructure, and we are paying it deliberately.

One point deserves emphasis, because it trips up nearly everyone who hears "Eclipse": **the license does not change.** Langium has been MIT-licensed from the beginning and stays MIT-licensed. Joining the Eclipse Foundation does not drag you into the EPL. Embed it, ship it, sell what you build on it. Nothing about your legal position changes.

## Why this particular foundation

Eclipse is not famous for web development, so the choice is worth defending rather than asserting.

The Foundation's origins are in the Java IDE, and for two decades that IDE has quietly served as the platform underneath an enormous amount of industrial engineering tooling. But it did not stop there. Eclipse is now an umbrella over several distinct ecosystems — [IoT](https://iot.eclipse.org), [software-defined vehicles](https://sdv.eclipse.org), [cloud development tools](https://ecdtools.eclipse.org) — and it is where a surprising share of Europe's serious open-source industrial software has ended up.

Three reasons decided it.

**We have run this experiment four times.** Theia, Sprotty, LSP4J, Open VSX. Every one of them grew after the handover, not before. We know exactly what the migration costs and exactly what it buys.

**Our customers do not deploy these projects one at a time.** A typical solution we build is a Langium language server inside a Theia or VS Code shell, with Sprotty diagrams and Open VSX handling extension distribution. Until today, that stack straddled two governance models and two security contacts. Now it is one — one IP process, one disclosure path, one set of rules for the whole toolchain. Anyone who has assembled a software bill of materials for a regulated customer knows precisely how much that is worth, and it is more than it sounds. The Foundation has made [supply chain security a first-class concern](https://newsroom.eclipse.org/eclipse-newsletter/2022/november/making-software-supply-chain-security-new-pillar-eclipse-foundation), and we would rather inherit that than build it.

**It is European.** Since January 2021 the Foundation has been legally established as [Eclipse Foundation AISBL](https://www.eclipse.org/org/), an international non-profit based in Brussels. For European enterprises and public buyers, a strategic dependency governed under EU law is not a footnote — it is increasingly the first slide.

There is a fourth reason, less strategic and more satisfying: Langium arrives at Eclipse as a sibling to Xtext. The toolkit our founders built in Java, and the toolkit our engineers rebuilt for the web, will now sit in the same portfolio under the same rules. Organizations with a decade of Xtext investment get a documented route to a web stack, and a genuine choice between two mature platforms instead of a migration ultimatum.

Xtext went first. Langium follows. That is a nice thing to be able to write.

## What this changes for you: almost nothing

If you build on Langium today, here is your migration plan.

The repository may move to a new GitHub organization, with redirects. That is the whole list.

The website, the docs, the discussions, the chat room all stay. The same engineers keep leading development — Langium is not a project we are setting adrift, it is one we are anchoring. Work on the [v2.0 release](https://github.com/langium/langium/milestone/7) continues on schedule, and the [roadmap](https://github.com/langium/langium/discussions/863) is unaffected: a library for building type systems, a more expressive grammar language, a generic serializer. The surrounding ecosystem keeps growing, including our implementation of the [SQL language](https://github.com/langium/langium-sql). Given the maturity of the code base, we expect to request a graduation review soon after the migration completes.

## Now the part where we ask something of you

The proposal is open for public review at [projects.eclipse.org](https://projects.eclipse.org/proposals/eclipse-langium). TypeFox, EclipseSource, and Ericsson are on record as interested parties. That list is short, and it should not be.

**Put your organization's name on it.** Comment on the proposal. It takes minutes, commits you to nothing, and it is the clearest signal a project's stewards get about whose requirements deserve weight. If Langium is load-bearing for something you ship, say so publicly — quiet dependence buys you no influence at all.

**Send code.** The committer path is merit-based and genuinely open. Sustained contribution earns a vote on where this goes.

**Or fund it.** If Langium matters to your roadmap but your engineers are committed elsewhere, [talk to us](https://www.typefox.io/contact/) about sponsoring features, fixes, or support. Money moves a roadmap faster than an issue report, and we would rather build what you actually need than guess.

We have spent a decade building tools that outlast the companies that commissioned them. Langium is the next one. Come help decide what it becomes — because from today, that decision is no longer ours alone.
