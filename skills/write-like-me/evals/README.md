# Running the write-like-me evals

Read this before launching. `evals.json` is the spec — prompts, expectations, assertions.
This file is the part the schema has no field for: what the *orchestrator* must do so the
runs produce gradeable output. Fixtures and the calibration behind every number in the
assertions are in [files/README.md](files/README.md).

Six cases, all in the skill's two modes:

| id | name | mode | produces |
|---|---|---|---|
| 0 | `missing-profile-stops` | process, no profile | **response text only** |
| 2 | `process-keeps-structure` | process, default | `.styled.md` + report |
| 3 | `soft-setting-gates-by-tier` | process, soft | `.styled.md` + report |
| 4 | `extract-with-tiers` | extract | `profile/jo-style.json` + render |
| 5 | `tone-steering-stays-inside-the-profile` | process, tone brief | `.styled.md` + report |
| 6 | `short-input-adds-nothing-and-reports-briefly` | process, pasted text | **response text only** |

Baseline is **no skill at all** — write-like-me has never been evaluated, so there is no
previous version to compare against.

## Before you run: the contamination gate

`AGENTS.md` at the repo root describes these fixtures, which makes it an answer key for a
baseline run, and the harness caches it into every subagent's context at session start.
**A session that started with `AGENTS.md` and `CLAUDE.md` in context cannot run these evals
in-process.** Follow the STOP block in `AGENTS.md`: remove both files, launch every run and
grader as its own fresh headless session, verify no child transcript shows injected content,
and restore with `git checkout -- AGENTS.md CLAUDE.md` only after the last child finishes.
In-process subagents stay contaminated regardless.

## Runner requirements

**1. Capture the run's final response as an output.** Evals 0 and 6 write nothing to disk —
that is the behavior under test — and roughly a third of the assertions across all six cases
read "the response". A runner that collects only files from `outputs/` grades those two as
empty and scores them zero for the wrong reason. Save the final assistant message to
`outputs/response.md` for every run.

**2. Give each run its own copy of the fixtures, with absolute paths.** Copy `evals/files/`
into the run directory and rewrite the prompt's repo-relative paths to absolute ones.
`SKILL.md` is explicit that only `scripts/…` paths are relative to the skill directory: a
relative input gets looked for *inside the skill folder*, and the rewrite lands beside the
wrong file. Per-run copies also matter because evals 2, 3 and 5 each assert `ai-draft.md` is
byte-identical afterward — a shared copy plus one in-place edit (or an auto-retried agent
resuming on a dirty tree) silently fails the next case.

**3. Use a transcript mechanism that captures tool calls.** `version-check-performed`
(eval 2) grades on whether `styledb.py info` ran before the profile was used, and
`no-implicit-extraction` (eval 0) needs to see that no profile was written. Both need the
tool-call trace, not just output files. skill-evals' Gate 2 requires this for isolation
verification anyway — just make sure the mechanism you pick records native `Read`/`Write`
calls and not only shell commands.

**4. Resolve eval 4's corpus root before grading.** Two assertions there run
`styledb.py validate --corpus-dir`, whose argument is the directory the DB's own
`documents[].path` entries are relative to — `<workspace>/evals/files/corpus` for a manifest
that records `fs-mocks.md`, `<workspace>/evals/files` for one that records `corpus/fs-mocks.md`.
Read the manifest, then fill it in. Pointed one level off, validate reports `cannot open` and
exits 1 without having verified a single quote or count, which is a grading artefact and not
the run's failure.

## Grading helpers

Most numeric assertions are mechanically checkable. Run these instead of eyeballing —
grader variance on counting em dashes across a 900-word rewrite is real.

```sh
SKILL=skills/write-like-me

# structure + facts (evals 2, 3, 5) — exit 0 and "0 error(s)" is the bar
python3 $SKILL/scripts/structure_check.py ORIGINAL.md REWRITTEN.md

# every rate assertion at once: em dashes, semicolons, colons, contractions,
# first person singular/plural, parentheses, and each profile row's verdict
python3 $SKILL/scripts/textstats.py measure REWRITTEN.md \
  --db FIXTURES/user-style.json --db $SKILL/data/ai-style-patterns.json --sort-gap

# report honesty (evals 2, 3, 5) — the same command re-run on the delivered file is what
# report-figures-reproduce grades against: every figure in the run's before/after table has
# to come back from it. --report-table prints those sections ready to paste, so a mismatch
# means the run retyped or recalled a number rather than measuring it.
python3 $SKILL/scripts/textstats.py measure ORIGINAL.md REWRITTEN.md \
  --db FIXTURES/user-style.json --db $SKILL/data/ai-style-patterns.json \
  --setting SETTING --report-table

# extraction (eval 4) — exit 0 means schema-clean, every quote verbatim in its source,
# and every counted pattern's per-document counts reproduced by re-running its counter.
# CORPUS_ROOT is whatever the DB's own documents[].path entries are relative to, usually
# FIXTURES/corpus; point it one level off and the run reports 'cannot open' and exits 1.
python3 $SKILL/scripts/styledb.py validate profile/jo-style.json --corpus-dir CORPUS_ROOT
```

Assertions are written as **absolute occurrence counts**, while `textstats.py` prints per-1k
rates. Multiply by the rewrite's own word count from the same output (`words`), not by the
original's and not by `wc -w` — the counter strips code blocks, tables and link URLs.

## Four things a grader should not get wrong

**Evals 2 and 3 make opposite demands on the same fixture.** Eval 2 fails if the em dashes
survive; eval 3 fails if they don't. That is the strictness dial working as designed — soft
applies tier-1 patterns only, and this corpus puts every absence pattern at tier 2. Grade
`soft-setting-stated` first: it establishes which contract the rest of that run is under.

**A better-reading rewrite can be a failing one.** `tier-2-absences-untouched` (eval 3) and
`nothing-manufactured` (eval 6) both fail runs that produce nicer prose by overstepping —
a soft pass that strips every em dash, a 64-word note sprinkled with the author's tics. The
skill's claim is convergence on measured rates, not maximal de-AI-ing, so grade the contract
rather than the prose.

**A shared subject is not a transplant.** `no-corpus-text-transplanted` (eval 2) is about a
carried-over *claim*, not shared vocabulary: `corpus/fs-mocks.md` covers the draft's own
subject, so five-word runs will collide innocently. Before failing one, check whether every
content word in the matched run also appears in `ai-draft.md` — if it does, the run is a
restyled version of the draft's own sentence and passes. Only a run that brings in a content
word the draft never used has imported the corpus document's claim.

**A substitution is not a manufacture, and the rate does not tell you which it is.** In a
64-word note every profile row is `too-short`, so a single occurrence prints at several times
the author's rate whatever put it there. Before failing one, check whether it fills a slot a
removal opened and comes from the DB: the em dash's `instead` names colon-elaboration and
parenthetical-aside, and worth-noting's names stance-adverb, so a colon where the em dash was
and an "actually" where "it's worth noting" was are both the procedure working. A habit
dropped into a sentence that offered no slot is the failure this assertion is for.
