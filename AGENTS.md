# TypeFox Agent Skills

A collection of agent skills in the [agentskills.io](https://agentskills.io/) format for open source technologies maintained at TypeFox. The product is the Markdown skill definitions under `skills/` — there is no application to build. Scripts are Python 3.8+, stdlib-only; pytest is the only test dependency.

## Commands

```sh
pytest skills/agent-experience/scripts/test_check_docs.py -q         # full script test suite, <1s
pytest skills/agent-experience/scripts/test_check_docs.py -k NAME    # single test by keyword
python3 skills/agent-experience/scripts/check_docs.py --exclude 'skills/*/evals/*' .   # doc-freshness check, <1s
```

Installing skills for end use is `npx skills add TypeFox/agent-skills` (see README) — not needed for development.

## Why and where

- `skills/<name>/` — one skill per folder: `SKILL.md` (frontmatter `name` matches the folder; `description` states when to trigger *and* when not to), `references/` for detail docs loaded on demand, `evals/evals.json` for eval definitions, optional `assets/` and `scripts/`.
- `skills/<name>-workspace/` — gitignored eval output, recreated by skill-evals runs.
- To create or modify a skill use the skill-creator skill; to measure whether it helps use skill-evals (both installable per README).

## Conventions

- Every skill ships evals in `evals/evals.json` (known gap: ts-code-reviewer has none yet).
- Python scripts stay stdlib-only so `check_docs.py` remains copy-installable into target repos.

## Boundaries and definition of done

- Never edit `skills/*-workspace/` — generated eval output.
- Files under `skills/*/evals/files/` are eval fixtures and may be *intentionally broken* (dead paths, bloated agent docs). Never "fix" them in repo-wide cleanups; check_docs excludes them deliberately.
- Done means: the pytest suite and the check_docs command above pass locally with output shown, and any changed `SKILL.md` frontmatter still matches its folder name.

## PR conventions

- Work on a feature branch and open a PR to `main`; short imperative commit subjects (see git history for the pattern).
