---
layout: home
hero:
  name: TypeFox Agent Skills
  tagline: Reusable instructions that coding agents load when a task calls for them. Install once, and the matching skill activates from your conversation context.
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
  - title: TypeScript and VS Code
    details: Senior-level code review for TypeScript projects, and publishing extensions to the Marketplace and Open VSX.
    link: /ts-code-reviewer
  - title: Your own voice
    details: Rewrite agent-written drafts so they read as you, from a style profile built from your own writing.
    link: /write-like-me
---

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
