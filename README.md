# TypeFox Agent Skills

A collection of [agent skills](https://agentskills.io/) for the open source technologies maintained at [TypeFox](https://www.typefox.io/).

## Using Skills

Install skills with the [`skills`](https://www.npmjs.com/package/skills) CLI:

```sh
# Install all skills from this repo
npx skills add TypeFox/agent-skills

# Install a specific skill
npx skills add TypeFox/agent-skills -s <skill-name>
```

Skills are activated automatically when their trigger conditions match your conversation context. See the [agent skills documentation](https://agentskills.io/) for details on how skills work and how to manage them.

## Writing Skills

Each skill lives in its own subfolder under `skills/`. To get started, install the skill-creator skill first:

```sh
npx skills add anthropics/skills -g -s skill-creator
```

Then use `/skill-creator` in Claude Code to scaffold, edit, and test skills interactively.
