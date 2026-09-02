# TypeFox Agent Skills

A collection of agent skills in the [agentskills.io](https://agentskills.io/) format for open source technologies maintained at TypeFox. The product is the Markdown skill definitions under `skills/` — there is no application to build. Scripts are Python 3.8+, stdlib-only; pytest is the only test dependency.

## STOP — before running any skill evaluation

If your task is to run a skill evaluation (skill-evals, or any with-skill vs. baseline comparison): **stop immediately — do not start.** The harness injects this file and CLAUDE.md into every subagent's context, cached at session start, so eval runs launched from this session are contaminated — this file even describes the eval fixtures, an answer key for baselines — and removing the files mid-session does not help. Remove AGENTS.md and CLAUDE.md first, run the evaluation in a fresh session started without them, and restore both afterwards with `git checkout -- AGENTS.md CLAUDE.md`.

A session that already started with these files in context can still orchestrate: remove AGENTS.md and CLAUDE.md, then launch every eval run and grader as its own fresh headless session (`claude -p`) — a separate process assembles project memory from disk at its own start, so nothing is injected while the files are absent. In-process subagents (Agent/Workflow) stay contaminated regardless. Verify, don't assume: grep each child session transcript's first turn for injected AGENTS.md content, and restore the files only after the last child (including retries and graders) has finished.

## Commands

```sh
pytest skills/agent-experience/scripts skills/write-like-me/scripts -q   # all script unit tests, <1s
pytest skills/write-like-me/scripts -k NAME                              # single test by keyword
python3 skills/agent-experience/scripts/check_docs.py --exclude 'skills/*/evals/*' .   # doc-freshness check, <1s
```

Script tests live next to their scripts as `skills/<name>/scripts/test_*.py`; `pytest skills` would also collect eval fixtures' own tests, so name the script directories explicitly.

Installing skills for end use is `npx skills add TypeFox/agent-skills` (see README) — not needed for development.

## Why and where

- `skills/<name>/` — one skill per folder: `SKILL.md` (frontmatter `name` matches the folder; `description` states when to trigger *and* when not to), `references/` for detail docs loaded on demand, `evals/evals.json` for eval definitions, optional `assets/`, `scripts/`, and `data/` (bundled data files the skill reads, e.g. write-like-me's AI style-pattern DB).
- `skills/<name>-workspace/` — gitignored eval output, recreated by skill-evals runs.
- To create or modify a skill use the skill-creator skill; to measure whether it helps use skill-evals (both installable per README).

## Conventions

- Every skill ships evals in `evals/evals.json` (missing for ts-code-reviewer; adding them is planned as a standalone task).
- Skill content defines each jargon term or metaphor once, plainly, at first use — or points to the file that defines it — and every other mention references that definition instead of restating it or leaving the term bare.
- Python scripts stay stdlib-only so they run anywhere with bare Python 3.8+ — they are run from the skill, never copied into target repos (registry distribution, e.g. PyPI, is a possible later step).
- Skills that persist per-user state (write-like-me's style profile) keep it under `$HOME/.agents/<skill-name>/`, never in the target repo or the skill folder; the skill's schema reference (`skills/write-like-me/references/db-schema.md` for write-like-me) documents the format and carries a version number.

## Boundaries and definition of done

- Never edit `skills/*-workspace/` — generated eval output.
- Files under `skills/*/evals/files/` are eval fixtures and may be *intentionally broken* (dead paths, bloated agent docs). Never "fix" them in repo-wide cleanups; check_docs excludes them deliberately.
- Done means: the check_docs command above passes locally with output shown, and any changed `SKILL.md` frontmatter still matches its folder name. Run the pytest suite only when a change touches `skills/*/scripts/` — skill scripts are self-contained, so other changes cannot affect them.
- A new skill ships its `evals/evals.json` in the same PR. A substantive change to an existing skill includes reviewing its `evals/evals.json` in the same change — do the prompts, expected outputs, and assertions still describe the changed behavior? — and updating it where they don't. Only *re-running* evals is a judgment call (they are token-expensive), not a gate; the spec review is cheap and always happens.
- A behavior change to a script in `skills/*/scripts/` includes matching unit-test updates in the same change.
- If reality contradicts this file, fix it in the same change — never silently work around a stale rule.

## PR conventions

- Work on a feature branch and open a PR to `main`; short imperative commit subjects (see git history for the pattern).
