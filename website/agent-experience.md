# Agent Experience

Make a code repository agent-ready: audit and set up AGENTS.md and CLAUDE.md, wire verification sensors with self-correction messages, and build docs that serve as the agent's memory.

Source: [skills/agent-experience](https://github.com/TypeFox/agent-skills/tree/main/skills/agent-experience)

## Install

```sh
npx skills add TypeFox/agent-skills -s agent-experience
```

The skill ships a script that checks agent docs for dead commands and paths. It needs Python 3.8 or newer and nothing beyond the standard library.

## Background

Agent Experience (AX) is how easily coding agents can understand your repository, verify their own changes, and modify it safely. The article [How to architect software projects for AI agents](https://www.typefox.io/blog/software-projects-for-ai-agents/) introduces the topic and the approach this skill implements. In short:

- An agent starts every task from scratch. Whatever the repository does not tell it, it has to find out again or guess. Anything it cannot reach from inside the repository does not exist for it.
- A well-prepared repository works like a control system. Guides (AGENTS.md, the docs folder, a task runner, scaffolding) steer the agent before it acts. Sensors (type checks, linters, tests, structural rules, review passes) check the result afterwards. Without guides the agent repeats its mistakes, and without sensors nothing shows whether the rules were followed.
- When an agent makes a mistake, change the repository so the mistake cannot happen again, in the same change as the fix: add a line to AGENTS.md, write a dedicated doc, add a lint rule or a test, or change the architecture.

The goal: an agent gets a real ticket, works without human help, passes all checks, and produces a change your reviewers accept.

## Usage

The skill activates when you ask to make a repository agent-ready, to create, review or improve AGENTS.md or CLAUDE.md, to set up a new project for agent-first development, or when you ask a question about AX. It picks one of four modes from your request and says which mode it chose and what it will deliver before it starts. Mention which coding agents your team uses (Claude Code, Codex, Copilot, Cursor, ...) so that the instructions are made available to each of them.

### Retrofit: an existing codebase without agent setup

> Make this repo agent-ready. We use Claude Code, and a few teammates use Copilot.

The skill works through six steps:

1. **Inventory.** Finds the instruction files, docs, checks and tools the repository already has, and sorts them into guides and sensors. The gaps show what is missing. Rules that nothing enforces, and checks that no doc mentions, show what needs work.
2. **Run the commands.** Runs every documented command in the order a fresh checkout needs and records which ones work, with their timings. Where the docs and reality disagree, that is a finding.
3. **Draft.** Writes a first AGENTS.md and the docs the project needs from what the repository shows. Everything the repository cannot answer is marked as an open question instead of guessed.
4. **Interview.** Asks you the open questions, suggests an answer for each, and writes your answers into the docs right away. It also offers to go through the git history and the issue tracker for decisions worth writing down.
5. **Generate and wire.** Writes the final AGENTS.md and CLAUDE.md, the docs folder, and checks for the rules that a tool should enforce, each with an error message that tells the agent what to do instead.
6. **Prove and hand off.** Runs every new check and the skill's doc check on the final state, confirms every statement in the new docs against evidence, and gives you a list of the work that remains, in order.

If nobody is there to answer, for example in a headless run, the interview is reduced to a single round or the open questions are written to a file.

### Improve: agent docs exist but do not help

> A teammate generated our AGENTS.md with an AI tool months ago. It is huge, agents ignore half of it, and parts are wrong. Review it against AX best practices.

> Why does the agent keep inventing a test command?

The same steps, limited to the existing docs. The skill reviews them, removes every line that does not prevent a mistake, runs every command they mention, and restructures them into a short map with pointers to the details. It changes checks only where the docs state a rule that no tool enforces, or where an existing check is broken, ignored, or passes without checking anything. Several instruction files that have drifted apart are a finding in themselves: one becomes the source, and the others point to it.

### Greenfield: a new project, no code yet

> I'm starting a new project where coding agents will write most of the code and we mostly review. Set up the foundations for agent-first development.

With no code to look at, the skill starts with the interview: what the product is for, who uses it, the stack, and how the code will be structured. From the answers it sets up AGENTS.md and CLAUDE.md, a one-command setup and a task runner, fast checks that run while the agent works (type check, lint, tests, secrets scan), and a docs folder with the stack decisions and the product intent written down. The skill prepares the repository around the project scaffolding you chose. It does not build the application: at most a placeholder that the checks can run against.

### Consult: a question or one small change

> What belongs in AGENTS.md, and what does not?

> Add the release commands to AGENTS.md.

No steps and no interview. Questions are answered from the ideas in the article, and questions about your own project are answered after looking at the repository. Small edits follow the same rules as the full setup: a command is run before it is written down, and CLAUDE.md stays a one-line import of AGENTS.md. If the request reveals a bigger problem, such as documented commands that do not run, the skill says so and offers improve mode instead of starting the full workflow on its own.

## The repository layout

The skill writes a standardized structure, which the article explains in detail. This is the full layout; a project gets only the parts it needs. A typical retrofit ends up with AGENTS.md, CLAUDE.md, `ARCHITECTURE.md`, `adr/` and `exec-plans/`.

```
AGENTS.md                     # the root map
CLAUDE.md                     # one line, @AGENTS.md, for Claude Code
docs/
├── ARCHITECTURE.md           # structure: where things live, boundaries, invariants
├── adr/                      # reasons: one decision per file
├── exec-plans/
│   ├── active/               # work: ongoing plans that span several sessions
│   ├── completed/            # finished plans, kept so the history stays searchable
│   └── tech-debt-tracker.md  # known, tolerated debt with its rationale
├── product-specs/            # promises: intended behavior per capability
│   └── index.md              # lists every spec; AGENTS.md points here
├── design-docs/              # strategy: how a system delivers its promises
│   └── index.md              # lists every design doc and whether it was verified
├── generated/                # derived from code, regenerated in CI
├── references/               # llms.txt files for dependencies agents misuse
└── security-guidelines.md    # per-concern rules no tool enforces, one file per concern
```

- **AGENTS.md** is an overview of about 150 lines: what the project is, the commands (all verified by running them), what the main directories are for, the conventions no tool enforces, what counts as done, and pointers into `docs/`. Every line must prevent a mistake the agent would otherwise make; everything else is left out.
- **CLAUDE.md** contains only the line `@AGENTS.md`, because Claude Code reads CLAUDE.md and not AGENTS.md. Other tools get a similar one-line pointer at their own location. There is one source and no copies.
- **docs/** holds the details that AGENTS.md points to and the knowledge that future sessions need. Each kind of file answers one question: `ARCHITECTURE.md` the structure, product specs the intended behavior, design docs the implementation strategy, architecture decision records (ADRs) the reasons, exec plans the state of ongoing work.
- Each fact is written down in exactly one place, and other places link to it. Specs and design docs are only written when there is a reason, such as a feature about to be built or a behavior that is disputed, not for every module.
- Every file has a defined lifecycle: finished plans move to `completed/`, accepted ADRs are replaced by new ones instead of edited, and a spec is updated in the same change as the behavior it describes.
- The commands, paths and links mentioned in the docs are checked by the skill's `check_docs.py` script, so stale references are found mechanically. Docs are changed through pull requests and reviewed like code.

The complete rules are in the skill's references: [agents-md.md](https://github.com/TypeFox/agent-skills/blob/main/skills/agent-experience/references/agents-md.md) for AGENTS.md and [docs-structure.md](https://github.com/TypeFox/agent-skills/blob/main/skills/agent-experience/references/docs-structure.md) for the docs folder.
