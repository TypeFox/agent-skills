# Skill Evals

Measure whether a skill actually improves an agent's output: run prompts with and without it, grade both against the same checks, and iterate.

Source: [skills/skill-evals](https://github.com/TypeFox/agent-skills/tree/main/skills/skill-evals)

## Install

```sh
npx skills add TypeFox/agent-skills -s skill-evals
```

The skill builds on [skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) from Anthropic and stops right away when that skill is missing. Install it as well:

```sh
npx skills add anthropics/skills -s skill-creator
```

## Background

Writing a skill is a bet: you expect the agent to do better with its instructions than without them. Reading the instructions cannot settle the bet. Only a comparison can: the same tasks with the skill and without, held to the same standard. skill-evals runs that comparison as a loop:

1. Write a few realistic test tasks for the skill.
2. Run each task in separate, clean agent sessions: once with the skill, once without it or with the previous version.
3. Write down what a good result must contain, as checks that can be verified against the output.
4. Grade every output against those checks and add up the results for each side.
5. Read the report, decide what to change in the skill, and run the next round.

skill-creator provides the mechanics: file formats, the helper agents that grade and analyze, and the script that adds up results. skill-evals provides the procedure around them: the order of steps, the decisions it puts to you, and the safeguards that keep the comparison fair. Where skill-creator opens an HTML viewer, skill-evals writes one report file per round.

## Usage

The skill activates when you ask whether a skill helps, want to test or evaluate a skill, compare a new version with the old one, grade outputs that already exist, or improve a skill from evaluation results.

> I wrote a skill that teaches the agent our .statemachine language. It is at skills/statemachine-dsl. Does it actually make the agent better at writing correct .statemachine files? There is a sample at samples/trafficlight.statemachine.

> I reworked the domain-model skill. The old version is on main, the new one is in my working copy. Is the new version an improvement? Sample models are in examples/.

> Just grade the outputs in skills/my-skill-workspace/iteration-2 against the checks in evals.json.

### Keeping the runs clean

A run without the skill that still reads the skill file, or a run that reads a different version than the one assigned, inflates its score and hides the difference you want to measure. The skill therefore confirms what each run read, in the strongest way your agent tool supports: restricting the run to a list of allowed files, auditing its recorded transcript afterwards, or, as a last resort, having the run log every file it opens. A run that read anything else is discarded and run again.

One leak that no log shows: coding agents such as Claude Code feed the repository's AGENTS.md and CLAUDE.md into every agent session they start, from a copy taken when your own session began. If the repository has these files, the skill asks you to remove them, start a fresh session, and restore them with `git checkout -- AGENTS.md CLAUDE.md` afterwards. In a session that has already started, the skill can instead run each test as a separate command-line process, which reads these files fresh from disk and so sees nothing while they are removed.

### Test cases

A test case is a realistic prompt, a description of what a good result looks like, and optional input files. The skill drafts two or three from the skill's own text and examples, your repository, and the conversation, and shows you the draft to confirm or change. Only when it finds nothing to draft from does it ask you what a real user would type. Each case exercises a different part of the skill, at least one is awkward, such as a malformed input or an ambiguous request, and every prompt names real context such as file paths. More cases are added in later rounds only where the results show a gap.

### The comparison runs

Before launching anything, the skill names the two sides of the comparison and asks you to confirm, with a recommendation where your request leaves the choice open. The report calls the side without the new skill the baseline.

- **A new skill** is compared with no skill at all.
- **A changed skill** is compared with its previous version, copied from git so that the run with the old version cannot see the new one.
- **Both** at once, when you want to know whether the new version beats the old one and whether having the skill is worth it at all.

Every test case then runs once per side, all on the same model, so that the result measures the skill and not the model. Where your agent tool reports them, the tokens and running time of each run are recorded as well; a run is never allowed to estimate its own cost. A run that crashes or produces nothing is retried once and then left out of the round with a note.

If your agent tool cannot start separate sessions, the skill hands you one prompt per run to paste into fresh sessions yourself, rather than running the tasks in the current session, which already contains the skill.

### Checks and grading

What a good result looks like becomes clear only after the first outputs exist, so the checks are written then. Each check is a statement that can be verified against the output: the file is valid JSON, both chart axes are labeled, at least three recommendations are given. The skill calls these assertions. There are two kinds:

- **Checks that show what the skill adds.** Something the run without the skill would plausibly get wrong. A check that passes on both sides says nothing about the skill and is rewritten.
- **Checks that guard what must not break.** These may pass on both sides today. They catch a later version of the skill that breaks something that used to work.

Matters of taste, such as writing style or visual polish, do not get a check and are left for you to judge in the report.

Grading marks every check as passed or failed, with evidence quoted from the output. Mechanical checks run as scripts.

### The report

Each round ends with one file, `REPORT.md`, in the round's folder. It has four parts:

1. **Summary.** The difference in pass rate between the two sides, the difference in time and tokens where those were measured, what changed since the last round, and the patterns found in the results.
2. **Verdict.** Recommendations for the skill, the test cases, and the checks, each tied to its evidence.
3. **User review.** The questions only you can answer: whether the approach fits, whether the cost is worth the gain, which findings to address.
4. **Detailed results.** One section per test case with the prompt, links to each run's output, every check with its evidence, and each run's cost.

The skill then stops until you have read the report and replied in the chat. The next round focuses on the cases you comment on; a case you do not mention counts as fine.

### Improving the skill

Your feedback, the failed checks, and the transcripts of the runs feed into changes to the skill's `SKILL.md` and its test cases. The skill fixes causes rather than single examples, prefers a few sharp instructions with their reasons over long lists of rules, and moves work that every run repeated into a script. Then it runs all test cases again as a new round. It stops when you say you are satisfied, when two rounds in a row produce no feedback, or when the difference has not moved for two rounds.

When the skill is in good shape, it offers an optional extra pass from skill-creator that tunes the skill's description so that it activates when it should and stays quiet otherwise.

### Starting in the middle

You do not have to run the whole loop. Say where you are, and the skill starts there: with the runs when test cases already exist, with checks or grading when run outputs exist, with the analysis or the report when grades exist. If you name a single step, such as "just grade these", it does that step and stops. Runs it did not launch itself are audited the same way, and a run it cannot verify is flagged before grading.

### Where files go

- **Committed with the skill:** `evals/evals.json` holds the prompts, expected results and checks, and `evals/files/` the input files. This is the lasting specification of how the skill is tested, and it records nothing about past rounds.
- **Local workspace:** `<skill>-workspace/iteration-N/` next to the skill folder holds each round's outputs, grades, summary numbers, and `REPORT.md`. Rounds are disposable experiments. The skill adds `*-workspace/` to `.gitignore` if it is not there yet.

### Cost and models

A round runs every test case once per side and then grades every output, so a handful of cases turns into dozens of agent sessions. To keep the bill down, run the test cases on a cheaper model than the one that grades them; grading is where rigor matters most. In Claude Code the skill can launch the runs through the Workflow tool or as separate `claude -p --model ...` processes while grading stays on the model of your main session.

The report names the model that produced the runs, because a pass rate means nothing without it. To test a skill on several models, run the loop once per model and compare the reports.
