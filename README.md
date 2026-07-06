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

Then use `/skill-creator` in your agent to scaffold, edit, and test skills interactively.

## Evaluating Skills

To measure whether a skill actually improves agent output, use the `skill-evals` skill. It runs prompts with and without the skill, grades both against the same assertions, and writes a comprehensive report.

Install it (and `skill-creator`, which skill-evals depends on):

```sh
npx skills add TypeFox/agent-skills -g -s skill-evals
```

Then use `/skill-evals` in your agent to run the evaluation end-to-end. Use a relatively cheap model for this work; evals spawn many subagent runs and can consume a lot of tokens.

Results are written to a local workspace (gitignored) at `skills/{skill-name}-workspace/iteration-{n}/REPORT.md`. Review that report for the benchmark summary, per-test outcomes, and recommendations before iterating on `SKILL.md` or `evals/evals.json`.
