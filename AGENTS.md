# TypeFox Agent Skills

A collection of agent skills in the [agentskills.io](https://agentskills.io/) format for open source technologies maintained at TypeFox. The product is the Markdown skill definitions under `skills/` — there is no application to build. Scripts are Python 3.8+, stdlib-only; pytest is the only test dependency.

## STOP — before running any skill evaluation

If your task is to run a skill evaluation (skill-evals, or any with-skill vs. baseline comparison): **stop immediately — do not start.** The harness injects this file and CLAUDE.md into every subagent's context, cached at session start, so eval runs launched from this session are contaminated — this file even describes the eval fixtures, an answer key for baselines — and removing the files mid-session does not help. Remove AGENTS.md and CLAUDE.md first, run the evaluation in a fresh session started without them, and restore both afterwards with `git checkout -- AGENTS.md CLAUDE.md`.

A session that already started with these files in context can still orchestrate: remove AGENTS.md and CLAUDE.md, then launch every eval run and grader as its own fresh headless session (`claude -p`) — a separate process assembles project memory from disk at its own start, so nothing is injected while the files are absent. In-process subagents (Agent/Workflow) stay contaminated regardless. Verify, don't assume: grep each child session transcript's first turn for injected AGENTS.md content, and restore the files only after the last child (including retries and graders) has finished.

## Commands

```sh
pytest skills/agent-experience/scripts/test_check_docs.py -q         # check_docs unit tests (the only script tests so far), <1s
pytest skills/agent-experience/scripts/test_check_docs.py -k NAME    # single test by keyword
python3 skills/agent-experience/scripts/check_docs.py --exclude 'skills/*/evals/*' .   # doc-freshness check, <1s
```

Installing skills for end use is `npx skills add TypeFox/agent-skills` (see README) — not needed for development.

## Why and where

- `skills/<name>/` — one skill per folder: `SKILL.md` (frontmatter `name` matches the folder; `description` states when to trigger *and* when not to; the body carries the procedure and points to the reference that owns each piece of detail), `references/` for that detail, loaded on demand, `evals/evals.json` for eval definitions, optional `assets/` and `scripts/`.
- `skills/<name>-workspace/` — gitignored eval output, recreated by skill-evals runs.
- To create or modify a skill use the skill-creator skill; to measure whether it helps use skill-evals (both installable per README).

## Conventions

- Every skill ships evals in `evals/evals.json` (missing for ts-code-reviewer; adding them is planned as a standalone task).
- Python scripts stay stdlib-only so `check_docs.py` runs against any target repo with bare Python 3.8+ — it is run from the skill, never copied into target repos (registry distribution, e.g. PyPI, is a possible later step).

Skill changes mostly fold back findings — from an eval report, a run in another project, or a PR review — and fold-backs have produced the same three faults repeatedly. These rules fence them:

- **One owner per rule, term, and number.** Each rule, threshold, step list, and jargon term is defined once, in one file of the skill, plainly at first use; every other mention points to that file instead of restating it or leaving the term bare. A finding that the agent skipped a rule sharpens the owner line once, with one sentence of rationale — never a second copy in the other files the agent also reads, never added caps or "always/never" on the existing line. A copy is a fork, not emphasis: copies in this repo drifted apart — a 100-line map limit in one file against 150 in another, a four-part message format against five — until a dedupe pass reconciled them (commit "Remove redundancy across SKILL.md, references, and templates").
- **New content fits the skill it lands in.** Read the whole SKILL.md before editing. A change uses the skill's existing terms — no synonym for a concept the skill already names — and slots into its existing sections, step order, and reference layout; it opens a new section or file only when no existing owner fits. A change to a rule updates its owner and re-reads every pointer to it.
- **A finding enters as the general rule it instances.** One eval run, one project, or one reviewer's wording is a sample of one. Write the rule the finding is an instance of, with the case as at most a one-line example; if no general rule can be stated yet, hold the finding and list it as held, with the reason, in the commit message so the next fold-back does not re-apply it. Four counters built from one reviewer's phrases, and a rule that classed AI-typical patterns as removals, were reverted as over-fitted to that one draft: on hand-written prose a counter fired more than on the AI corpus, and the rule flagged habits the author's own corpus shows (commit "Mark unvetoed AI rows and re-rate profile rows per register").

## Boundaries and definition of done

- Never edit `skills/*-workspace/` — generated eval output.
- Files under `skills/*/evals/files/` are eval fixtures and may be *intentionally broken* (dead paths, bloated agent docs). Never "fix" them in repo-wide cleanups; check_docs excludes them deliberately.
- Done means: the check_docs command above passes locally with output shown, and any changed `SKILL.md` frontmatter still matches its folder name. Run the pytest suite only when a change touches `skills/*/scripts/` — skill scripts are self-contained, so other changes cannot affect them.
- A new skill ships its `evals/evals.json` in the same PR. A substantive change to an existing skill includes reviewing its `evals/evals.json` in the same change — do the prompts, expected outputs, and assertions still describe the changed behavior? — and updating it where they don't. Only *re-running* evals is a judgment call (they are token-expensive), not a gate; the spec review is cheap and always happens.
- A behavior change to a script in `skills/*/scripts/` includes matching unit-test updates in the same change.
- A change to skill content is checked for redundancy and consistency before it is done: grep a distinctive phrase of each added or changed rule across the skill's files and confirm it is stated once (pointers aside), and re-read every number, count, and step order the change touched in each file that mentions it.
- If reality contradicts this file, fix it in the same change — never silently work around a stale rule.

## PR conventions

- Work on a feature branch and open a PR to `main`; short imperative commit subjects (see git history for the pattern).
