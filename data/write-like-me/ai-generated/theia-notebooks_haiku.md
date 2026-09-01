# Building Native Notebook Support in Eclipse Theia: How Open Source Powers Custom Development Environments

## Why Notebooks Matter Now

Notebooks have quietly become the primary interface for how millions of developers work. Data scientists run analyses in Jupyter. Researchers document findings alongside code execution. Data engineers prototype pipelines. When Microsoft added native notebook support to VS Code in 2021, it signaled a shift: notebooks weren't experimental anymore—they were table stakes.

For organizations building custom IDEs using Eclipse Theia—the open platform behind development environments at Arduino, ARM, Smartface, and VUEngine—this posed an urgent question: How do we give our users access to modern notebook workflows without building everything from scratch?

The answer required more than copying code. It demanded deep architectural thinking and genuine commitment to the open source ecosystem.

## The Problem: Why Earlier Approaches Fell Short

Before VS Code built notebook support into its core, extensions used a workaround called webviews—essentially embedding a mini-website inside the editor. It worked, but it was fragile.

**The Performance Trap:** Each notebook extension bundled its own copy of the Monaco editor (the text editing engine powering VS Code) to handle individual cells. In a notebook with 50 cells? You got 50 instances of Monaco, each consuming memory and processing power. Users with large notebooks watched their machines slow to a crawl.

**The Consistency Problem:** Without a unified standard, extension developers invented their own notebook experiences. One extension's notebook looked and behaved differently from another's. Users got whiplash switching between tools built on the same platform.

**The Developer Experience Gap:** If you wanted to add Python syntax highlighting to notebook cells, or JavaScript linting, you faced a fragmented nightmare. Language tools had no standardized way to plug into notebooks. Every extension became an island.

## VS Code's Solution: A Blueprint for Extensibility

VS Code solved this by building four interlocking systems:

**Serializers** translate between different notebook file formats and a unified internal model. Whether you're working with Jupyter notebooks, Observable, or custom formats, serializers handle the conversion transparently.

**Kernels** manage execution. They're the engine that runs cell code and maintains computation state, abstracting away the complexity of different languages and runtimes.

**Renderers** turn kernel output into what users see on screen. Instead of hardcoding how to display charts, tables, or custom visualizations, renderers consume output in standard formats (images, HTML, plain text) and render it flexibly. A notebook can support dozens of output types without coupling rendering logic to the kernel.

**Event and Lifecycle APIs** let extensions respond to every meaningful moment: when a cell executes, when a kernel restarts, when users navigate the notebook.

This architecture grew to over 30,000 lines of code in VS Code alone—a signal of genuine complexity. When Theia first emulated VS Code's extension APIs in 2019, notebook support was necessarily stubbed out: extensions would load without breaking, but nothing actually happened.

## Closing the Gap: Bringing Notebooks to Theia

### The Challenge

In summer 2023, TypeFox took on the challenge to build genuine notebook support for Theia. Not as a side feature or a future roadmap item, but as a fully realized, production-ready capability. The initial implementation required over 11,000 lines of carefully architected code—and that was just the beginning.

### How Real Open Source Works

The process revealed how mature open source projects actually operate:

**Rigorous Peer Review:** Theia's governance requires independent review of major contributions. Reviewers from Ericsson and Castle Ridge Software subjected the initial pull request to serious scrutiny, uncovering regressions, edge cases, UX gaps, and architectural questions. Every issue was addressed.

**Pragmatic Acceptance:** Rather than demanding perfection, the Theia leadership team made a principled choice: merge the functional foundation with a clear commitment to iterate. Instead of waiting for a hypothetical "1.0," the project accepted "good and improvable" and proved it by backing up that commitment with action.

**Continuous Improvement Through Community:** Since the initial merge in August 2023, 50 additional pull requests have systematically refined the implementation—adding kernel restart capabilities, improving outline navigation, fixing accessibility issues, and supporting advanced workflows. The feature has evolved because the project invested in ongoing stewardship.

### What Actually Got Built

- **Full notebook file support:** Read, edit, and save notebooks in standard formats without data loss
- **Multi-kernel execution:** Run multiple kernels concurrently with seamless switching
- **Language integration:** Code completion, diagnostics, and linting work inside notebook cells, powered by Theia's existing language servers
- **Advanced features:** Kernel selection, restart workflows, outline navigation, and keyboard support that matches user expectations
- **A sustainable architecture:** Future extensions can build on these foundations without reimplementing core functionality

## Why This Matters Beyond Theia

This work illustrates a principle that applies across open source and technology partnerships: **genuine compatibility beats convenient imitation.**

Theia didn't build a notebook system that *sort of* worked like VS Code notebooks. It built real compatibility—allowing the Jupyter extension ecosystem and dozens of other notebook tools to run on Theia without modification. Organizations building custom IDEs can now offer their users modern notebook workflows without sacrificing the platform customization and performance that make Theia compelling.

For decision makers evaluating IDE platforms or contemplating deep customization of development environments, this signals something important: maturity means more than polished releases. It means active participation in the open source commons. It means technical expertise applied to problems that don't have easy answers. It means believing that the whole ecosystem benefits when platforms work together.

## The Broader Implications

Custom development environments are becoming standard in large organizations—insurance companies, automotive suppliers, aerospace firms, and financial institutions all build specialized IDEs tailored to their workflows. These organizations need platforms they can trust and evolve over years, not platforms that become maintenance liabilities.

TypeFox's investment in Theia's notebook support demonstrates something that's increasingly rare in vendor-driven ecosystems: a creator willing to invest in making their foundational platform a genuine, long-term alternative to proprietary solutions.

The notebook implementation is available today in Theia. Organizations adopting it inherit both the feature itself and the principle behind it: platforms that thrive are ones where real expertise solves real problems—not where hype chases features.
