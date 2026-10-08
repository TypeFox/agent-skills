---
layout: home
hero:
  name: TypeFox Agent Skills
  tagline: General-purpose instructions that coding agents load when a task calls for them. Install once, and the matching skill activates from your conversation context.
  actions:
    - theme: brand
      text: Browse the skills
      link: /agent-experience
    - theme: alt
      text: View on GitHub
      link: https://github.com/TypeFox/agent-skills
features:
  - title: Agent readiness
    details: Make a repository agent-ready, and measure whether a skill actually improves agent output.
    link: /agent-experience
  - title: Go
    details: Community idioms for API design, errors, concurrency and naming, plus doc comments that render on pkg.go.dev.
    link: /idiomatic-go
  - title: VS Code
    details: Publishing extensions to the Marketplace and Open VSX.
    link: /publish-vscode-extension
  - title: Your own voice
    details: Rewrite agent-written drafts so they read as you, from a style profile built from your own writing.
    link: /write-like-me
---

## Scope

The skills here are general-purpose. Each covers a practice or workflow that applies across projects, such as making a repository agent-ready, writing idiomatic Go, or publishing a VS Code extension.

Skills that are specific to one project, such as a framework's API or a repository's build and release setup, are not collected here. They ship in that project's own repository, next to the code they describe.

## Install

Install all skills with the [skills](https://www.npmjs.com/package/skills) CLI, or pick a single one:

```sh
npx skills add TypeFox/agent-skills
npx skills add TypeFox/agent-skills -s <skill-name>
```

Or install the repository as a Claude Code plugin:

```sh
/plugin marketplace add TypeFox/agent-skills
/plugin install typefox-agent-skills@typefox
```

Skills are activated automatically when their trigger conditions match your conversation context. See the [agent skills documentation](https://agentskills.io/) for how skills work and how to manage them.

## Eclipse Foundation AI Registry

These skills are also listed in the [Eclipse Foundation AI Registry](https://ai.open-vsx.org/), a catalog of skills, MCP servers, plugins and agents for AI-assisted development, curated by the organizations that publish them. The [TypeFox organization page](https://ai.open-vsx.org/orgs/typefox) shows every skill from this repository. The registry follows the `main` branch of this repository and refreshes daily, so a change merged here is listed there within a day.
