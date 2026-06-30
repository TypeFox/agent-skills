---
name: skill-evals
description: Run the eval loop that measures whether a skill actually improves an agent's output — design test cases, run them with the skill and against a baseline, grade against assertions, aggregate a benchmark, analyze patterns, and iterate. Use when the user wants to evaluate or test a skill, check whether a skill helps, run skill evals, benchmark a skill against a baseline, grade skill outputs, or iterate on a skill from eval results. Builds on the skill-creator skill for the mechanics; stop if skill-creator is unavailable.
---

# Evaluating a skill with the eval loop

A skill is a bet that some instructions make an agent's output better. **The loop** is how you collect on the bet: run real prompts **with the skill** and against a **baseline** without it (or against the previous version), grade both against the same bar, and read the **delta** — what the skill costs in time and tokens versus what it buys in pass rate. Repeat until the delta stops moving.

This skill is the *spine* of that loop — the order of operations, the two gates that guard it, and the two points where only the user can supply what you need. The *mechanics* — exact file schemas, the grader and analyzer subagents, the aggregation script, the eval viewer — live in **skill-creator**, which this skill drives rather than restates. When you need a schema or a command, follow the pointer into skill-creator.

## Preflight — clear both gates before any activity

### Gate 1: skill-creator must be available

Locate the installed **skill-creator** skill and read its `SKILL.md`. Note its directory as `SKILL_CREATOR`; every mechanic below is addressed relative to it — `SKILL_CREATOR/references/schemas.md`, `SKILL_CREATOR/scripts/`, `SKILL_CREATOR/agents/`, `SKILL_CREATOR/eval-viewer/`.

If skill-creator is not installed, **stop here**. skill-evals is an orchestration layer and cannot run without it. Tell the user to install it (it lives in the `anthropics/skills` repository) and re-run. **Done when** `SKILL_CREATOR` resolves to a readable directory, or you have stopped with that instruction.

### Gate 2: runs must be isolated — and provably so

Every eval run must start from **clean context**. The clean way to get isolation is a **subagent**: a child task with fresh context and one dedicated prompt.

But "I told the subagent not to read the skill" is not isolation you can trust. A baseline that loads the **skill under test**, the with-skill version, the live copy instead of the snapshot, or anything outside its allowlist inflates its score and silently shrinks the delta — sibling skill files and parent-thread instructions are often one `Read` away. You must be able to *verify* what each run loaded, not assume it — and since runs read files through native tools like `Read` and `Glob`, the mechanism has to capture those tool calls, not just commands. Pick the strongest your harness supports:

1. **Allowlist enforcement (preferred).** If you can sandbox or read-scope a subagent to an allowlist of paths, do it: each run gets only what its configuration permits — for the baseline, that configuration's skill set (none, the snapshotted old version, or named helper skills if any) plus eval inputs and its output dir; for with-skill, exactly one version of the skill under test plus inputs and output dir. This makes leaking *impossible* rather than merely discouraged, so nothing needs auditing afterward — the sandbox itself is the proof.
2. **Deterministic tracing (second).** If you can't restrict paths but the harness records a machine-readable trace of every tool call a run made — file-access tools included — audit that trace against the allowlist once the run lands. The harness captures it, so it costs the run nothing and the agent can't edit it away. Where it lives:
   - **Claude Code** persists each subagent's transcript at `<session-dir>/subagents/agent-<id>.jsonl` (you hold the agent id from the spawn). Scan it for `Read` / `Edit` / `Write` / `Glob` / `Grep` `tool_use` entries and confirm every path is on the allowlist.
   - **Codex** emits the equivalent when launched as `codex exec --json` — read the JSONL event stream and check its file-access events against the allowlist.
   - **Cursor** exposes this only if the installed version provides agent hooks (log tool calls through them); absent that, its history lives in undocumented `state.vscdb` SQLite blobs too version-fragile to trust, so drop to self-report instead.
3. **Self-report (fallback).** If neither holds, require every run to **log the resources it loaded**: instruct the subagent to append each skill / spec / input file to `<run-dir>/access-log.md` **as it reads the file** — not only at the end, because a file read right before a Write can slip past a summary log — and to leave its `metrics.json` tool-call counts as corroboration. After the runs you audit each log against that run's allowlist. It is last because it adds work to the run and trusts the agent to report honestly against itself.

**Write the per-run allowlist down before launching** — which skill version (or none), which input files, which output dir. That allowlist is what the isolation verification (Activity 2) and the isolation assertions (Activity 3) check against.

- **Subagents available** (a Task / subagent tool that spawns fresh-context children): each run is one subagent, scoped or logged as above. Normal path; proceed.
- **No subagents**: do **not** quietly run the prompts inline — your context already holds the skill, so an inline "baseline" is fiction. Instead, stop the automated loop and hand the user a fallback: generate the full set of run prompts (one block per run, contents in Activity 2) for them to paste into separate fresh sessions, then collect the outputs into the run directories and resume at grading.

**Done when** you have chosen an isolation mechanism (allowlist, trace, or self-report), written the per-run allowlists, and confirmed subagents work — or switched to the copy-paste fallback and told the user.

Record gate clearance in the workspace before Activity 2 runs — a short `methodology-and-isolation.md` (or note in the first `summary.md`) under the eval output root, naming the resolved `SKILL_CREATOR` path (Gate 1) and the isolation mechanism + per-run allowlists (Gate 2). Without this paper trail, later grading cannot tell whether preflight actually happened or whether a run was contaminated.

## Pick an entry point

The loop runs end-to-end or à la carte — support whichever the user asked for. Find their state and jump in:

- **"Evaluate / test my skill", "does this skill actually help?"** → run the whole loop from Activity 1.
- **Test cases already exist** (an `evals/evals.json`) → start at Activity 2.
- **Runs already produced outputs** → start at Activity 3 (assertions) or 4 (grading).
- **A benchmark already exists** → Activity 6 (analyze) or 7 (human review).
- **"Make it better from these results"** → Activity 8.
- **A single activity named outright** ("just grade these", "aggregate the results") → do that one and stop.

Both gates apply no matter where you enter. Always clear Gate 1 (resolve `SKILL_CREATOR`). When you enter at Activity 3 or later against **pre-existing** run outputs, you can't re-run an isolation that already happened — so audit it instead: check each run directory for sandbox evidence, a harness trace (e.g. the subagent transcript), or `access-log.md` and confirm it against the run's allowlist. If isolation can't be verified for a run, flag that run to the user before grading rather than silently trusting it.

Two locations, and the split matters for source control and for what you keep improving over time.

- **Durable (committed with the skill):** `<skill>/evals/evals.json` plus input files under `<skill>/evals/files/`. This is the long-term eval specification — prompts, `expected_output`, assertions, and fixtures — co-developed alongside `SKILL.md`. It sets the stage for every future run; it does **not** store iteration history, benchmark scores, or notes about what changed in a past workspace pass.
- **Local (gitignored workspace):** `<skill>-workspace/iteration-N/` holds run outputs — `with_skill/` and `without_skill/` (or `old_skill/`), `grading.json`, `benchmark.json`, `review.md`, `review.html`, and the like. Iterations are disposable experiments aimed at improving the two durable artifacts (`SKILL.md` and `evals.json`). When a run teaches you something, fold it back into those files; do not treat the workspace as the source of truth.

Add `*-workspace/` to `.gitignore` if it isn't already. Don't build the whole workspace up front — create each `iteration-N/` and run directory as you reach it. For the exact workspace tree and the JSON each directory holds, read `SKILL_CREATOR` ("Running and evaluating test cases") and `SKILL_CREATOR/references/schemas.md`.

## The loop

### 1. Design test cases — needs the user

A test case is a **realistic prompt** + a human-readable **expected output** + optional **input files**. Start with 2-3; add more once results are in — in Activity 8, target a new case at any assertion category that tied or failed across both configs. Don't pad the suite for its own sake; a handful of sharp cases beats a dozen redundant ones. Vary phrasing, detail, and formality across them (one casual, one precise), cover at least one edge case (malformed input, ambiguous request), and ground every prompt in real context — file paths, column names, the user's actual situation. Vague prompts like "process this data" test nothing.

This is the activity where you most need the user: only they know what a realistic prompt and a real input file look like for their skill. Read the conversation and the skill itself first — if you can infer solid cases, draft them and ask the user to confirm or amend. If you genuinely can't (no example prompts, no sample inputs to work from), **stop and ask**: what are 2-3 things a real user would type to trigger this skill, and what input files (if any) should each work on? Either send those questions now or stop with that as the explicit follow-up.

Save prompts and `expected_output` to the skill's own `evals/evals.json` — i.e. `<skill-under-test>/evals/evals.json`, with any input files under `<skill-under-test>/evals/files/`, **not** in the workspace. Write `evals.json` in two passes: prompts and `expected_output` now; the `assertions` field on each record comes in Activity 3, after you have seen real output, by **updating** these same records (never overwriting the file and losing this pass). If `evals.json` already exists and holds cases, read it first and preserve them — append new cases rather than replacing, and if a new case conflicts with an existing one, show the user the difference and let them choose. Treat `evals.json` as the standing spec for the next run: prompts, expectations, assertions, and fixture paths only — no iteration numbers, benchmark scores, or changelog of past workspace passes. That file is committed with the skill, so **every path inside it must be repo-relative** (e.g. `evals/files/sample.calc`) — an absolute path like `/Users/you/...` leaks your machine's directory layout into the repository and breaks on every other checkout. When you launch a run (Activity 2), resolve those relative paths to absolute against the skill root for the subagent; the committed `evals.json` stays relative, and only the workspace (gitignored) ever holds absolute paths. **Done when** the user has signed off on the test cases.

### 2. Run against a baseline — needs subagents (Gate 2)

For each test case, launch **two runs in the same turn** so they finish together: one **with the skill**, one **baseline**. Both runs must actually *generate real outputs* (graded later, in Activity 4) — reading the skill under test and reasoning about what it probably does is **not** a baseline. A casual or skeptical ask ("is this even pulling its weight? lol") is still a request to *run* the comparison, not to review the skill's prose; the loop's entire value is empirical, so answering from the skill text, doing a gap analysis, or otherwise skipping the generation runs forfeits it regardless of how the request was phrased. The baseline depends on intent:

- **New skill** → no skill at all. Same prompt, save to `without_skill/outputs/`.
- **Improving a skill** → the previous version. Snapshot it before you edit (`cp -r <skill-path> <workspace>/skill-snapshot/`), point the baseline at the snapshot, save to `old_skill/outputs/`. Compare the two versions by *running* both — v2-with-skill and v1-as-baseline each generate and grade real outputs — never by diffing the two `SKILL.md` files. A "which version reads better" text comparison is the same forfeit as skipping the baseline.

Each run carries its skill path (or none), the task prompt, any input files, and its output directory. Two constraints keep the comparison fair:

- **Same model across runs.** Every subagent in a single benchmark must be driven by the same underlying model — the one that will run the skill in production. A with-skill run on one model and a baseline on another measures the models, not the skill. Record which model that was (see below) so the result is interpretable; a pass rate with no model attached can't be compared against anything.
- **Read-only, run-scoped paths.** Each run sees only its Gate 2 allowlist: the eval's input files and the one skill version under test — the snapshot for a baseline, the live skill for a with-skill run — plus its own output dir. Reading any other skill version (the live copy during a baseline, another snapshot, the main thread's working tree) contaminates the run.

The moment a run completes, capture its **timing** (`total_tokens`, `duration_ms`) into the run's `timing.json` — this arrives in the completion signal and is persisted nowhere else, so grab it immediately. The exact subagent prompt template, snapshot mechanics, and `timing.json` schema are in `SKILL_CREATOR`.

If a run fails to complete (crash, timeout, missing outputs), don't grade a partial result. Retry it once with the same configuration; if it fails again, note the failure in `methodology-and-isolation.md`, exclude that case from this iteration's benchmark, and tell the user before continuing.

**Verify isolation before grading.** As each run lands, check its loaded context against the allowlist — trust the sandbox if you allowlisted it, otherwise audit its harness trace, falling back to its `access-log.md` and `metrics.json`. The decisive checks: the **baseline did not read the skill under test, another version of it, or any path outside its allowlist**, and the with-skill run read only the version it was assigned. Record the verdict (a line per run in `methodology-and-isolation.md`). **Any contaminated run is discarded and rerun before grading** — noting the contamination in your write-up is not enough; a run that stays in the benchmark with a "contaminated" label erases the delta exactly as a silent one does. This rule extends to nested runs at every depth: if the with-skill agent itself spawns a nested eval (e.g., comparing two DSL skills), contaminated nested baselines must also be discarded and rerun, not merely flagged.

**Record the model.** Note the model id powering these runs — read it from the subagent/API metadata if you can. If you can't determine it reliably, **ask the user** for the exact id (e.g. `claude-sonnet-4-20250514`); never guess or fabricate one, since a wrong id silently corrupts every cross-run comparison. You'll write it into the benchmark metadata in Activity 5; the aggregation script can't infer it and otherwise leaves an `<model-name>` placeholder. A skill ideally proves itself across several models, but most agents can't switch the model mid-loop — so if the user wants multi-model coverage, treat each model as its own benchmark run (its own model id in the metadata) and compare them in review rather than mixing models within one benchmark.

**Fallback (no subagents)** — give the user one block per run to paste into a fresh session:

```
Execute this task with a clean context:
- Skill: <path to the skill, or "none — baseline run">
- Task: <the test prompt>
- Input files: <paths, or "none">
- Save all outputs to: <workspace>/iteration-<N>/eval-<name>/<with_skill|without_skill>/outputs/
- Read ONLY the skill and input files named above — do not open any other skill or version, and do not open the orchestrator's shared workspace notes (the allowlist / methodology files); everything you need is in this prompt. Append each file to access-log.md *as you read it*, not just at the end, so a late read can't slip past the log.
```

**Done when** every test case has a with-skill and a baseline output, **and** each run's isolation has been verified against its allowlist (or every fallback prompt has been handed over and its outputs collected).

### 3. Review results and write assertions

You usually don't know what "good" looks like until the skill has run, which is why assertions come *after* the first runs. An **assertion** is a verifiable statement about the output: programmatically checkable ("the file is valid JSON"), specific and observable ("both chart axes are labeled"), or countable ("at least 3 recommendations"). Avoid the vague ("the output is good") and the brittle (a required exact phrase that correct-but-reworded output would fail). Give each a descriptive name so it reads clearly in the benchmark later.

Assertions serve two complementary roles — use both:

- **Discriminating** — probe what the skill under test is meant to *add*: something the baseline would plausibly *fail*. These reveal the delta. An assertion that passes in both configurations measures the baseline's floor, not the skill's contribution, and will tie in the benchmark; rewrite it to target an outcome only the skill enables.
- **Regression** — lock in behavior that must *not break* as the skill evolves, especially when improving an existing skill. These need not discriminate today — both configs may pass now — but they guard the next edit: if a future with-skill run fails while the baseline still passes, you caught a regression. Keep a core set of regression assertions stable across iterations and add new discriminating ones as the skill grows.

When outputs are large and hard to skim by hand, assertions carry more of the burden — encode the skill's intent precisely rather than checking generic hygiene.

Not everything earns an assertion. Writing style, visual polish, whether the output "feels right" — leave those for the human review (Activity 7) rather than forcing a pass/fail onto them. Add durable assertions by updating each record in `evals/evals.json` — into `evals[].assertions` per-case, or shared across cases when appropriate — alongside the prompts and `expected_output` written in Activity 1. Per-run copies for the current iteration go in `eval_metadata.json` under the workspace only. You'll revisit and prune these in Activity 6; don't pre-apply that pruning here.

### 4. Grade outputs

Evaluate each assertion against the actual outputs and record **PASS/FAIL with concrete evidence** — quote or reference the output, don't state an opinion. Require real substance for a PASS: a section titled "Summary" holding one vague sentence is a FAIL when the assertion asked for a summary. For mechanical checks (valid JSON, row counts, file dimensions) write and run a script — it's faster, more reliable, and reusable across iterations than eyeballing. Save results per run to `grading.json` using the exact fields `text` / `passed` / `evidence` the grading schema and the aggregation script expect.

Grade the assertions while you grade the outputs: when one always passes, always fails, or can't be checked from the output alone, revise it in `evals/evals.json` before the next iteration — that file is what future runs will grade against. Spawn the grader per `SKILL_CREATOR/agents/grader.md`.

### 5. Aggregate results

Once every run is graded, compute per-configuration summary statistics into `benchmark.json` / `benchmark.md` — pass rate, time, and tokens for each config as mean ± stddev, plus the **delta** between with-skill and baseline. The delta is the whole point: it names what the skill costs and what it buys (13 seconds for +50 points of pass rate is a clear win; doubled tokens for +2 points may not be). Run the aggregation script in `SKILL_CREATOR/scripts/`; stddev only carries meaning with multiple runs per case, so in early iterations read the raw pass counts and the delta instead.

The script can't detect which model produced the runs, so it leaves `metadata.executor_model` as a `<model-name>` placeholder — overwrite it with the model id you recorded in Activity 2 before you report the benchmark. A pass rate is only meaningful next to the model that earned it, and it's what lets a reader tell a genuine regression from a result that simply ran on a different model.

### 6. Analyze patterns

Aggregates hide the patterns that actually tell you what to do next. Read the benchmark with these lenses:

- **Passes in both configs** → if it was meant to discriminate, it isn't — drop or replace it. If it is a **regression guard**, keep it: a tie today is fine; its job is to catch a future with-skill failure.
- **Fails in both configs** → the assertion is broken, the case is too hard, or it checks the wrong thing. Fix before the next iteration.
- **Passes with the skill, fails without** → this is where the skill earns its keep. Understand *why* — which instruction or script made the difference.
- **Flip-flops across runs** (high stddev) → the eval is flaky or the skill's instructions are ambiguous enough to be read differently each time. Tighten with an example or sharper guidance.
- **Time/token outliers** → read that run's transcript to find the bottleneck.

Use `SKILL_CREATOR/agents/analyzer.md` for the full analyst pass.

### 7. Review with a human — needs the user

Assertions only check what you thought to check; a human catches the technically-correct-but-misses-the-point and the problems you never wrote a check for. Produce the review in **two forms**:

1. **HTML** — launch `SKILL_CREATOR/eval-viewer/generate_review.py` against the iteration directory and `benchmark.json` (from iteration 2 on, pass `--previous-workspace` at the prior iteration). Use `--static <path>` when there is no browser. This is the rich browsable view skill-creator defines.
2. **Markdown** — also write `<workspace>/iteration-N/review.md` for IDE preview. Use the HTML output and `benchmark.md` as input when assembling it; you do not need to duplicate everything, but include the benchmark headline (or a link to `benchmark.md`), one section per test case with the prompt, relative links to each config's outputs and grades (and prior-iteration outputs from iteration 2 on), and an empty **Feedback:** line under each config.

Tell the user both exist: open `review.md` in the Markdown preview to skim and type feedback; the HTML viewer is there if they want the full interactive layout. If they submit via the HTML viewer's "Submit All Reviews", read `feedback.json` from the workspace; otherwise read the feedback they left in `review.md`.

Then **stop and wait**: this is a genuine handoff, not a step to run past. Do not start iterating until the user reports back. When they do, focus the next iteration on cases with specific complaints; empty feedback means that case looked fine. (For a rigorous A/B between two versions, the optional blind comparison in `SKILL_CREATOR/agents/comparator.md` judges the *generated outputs* of the two runs — it supplements the benchmark, it does not replace the generation runs.)

If benchmarks from different models are on the table — because the user ran the loop more than once to get multi-model coverage — surface the model id with each set of numbers and call out where the models disagree. A case that passes on one model and fails on another is a signal about the skill's robustness, not noise to average away; let the user judge whether that gap matters for where the skill will actually run.

### 8. Iterate on the skill

You now have three signals: **failed assertions** (specific gaps — a missing step, an unclear instruction), **human feedback** (broader quality — wrong approach, poor structure), and **transcripts** (the *why* — where the agent ignored or got lost in an instruction). Feed all three into revisions of **`SKILL.md` and `evals/evals.json`** — those are the durable artifacts the next iteration will run against. Hold to these while editing:

- **Generalize.** The skill will run on far more than these test cases — fix the underlying issue broadly, don't bolt on a patch for one example.
- **Keep it lean.** Fewer sharp instructions beat exhaustive rules. If transcripts show wasted work, cut the instruction causing it. If the pass rate plateaus as you add rules, the skill is over-constrained — remove some and see if results hold.
- **Explain the why.** "Do X because Y causes Z" is followed more reliably than a bare ALWAYS/NEVER.
- **Bundle repeated work.** If every run independently wrote the same helper script, that script belongs in the skill's `scripts/`.

Then rerun every test case into a fresh `iteration-<N+1>/`, regrade, aggregate, and review again. **Stop** when any of these holds: the user says they're satisfied; feedback comes back empty for two iterations in a row; or the pass-rate delta has flattened across the last two iterations with no offsetting drop in time or tokens. Diminishing returns, not a single magic threshold — when another iteration is unlikely to move the delta, say so and stop.

## After the loop

When the skill is in good shape, offer description optimization (skill-creator's triggering-accuracy loop) — a separate, optional pass that tunes the `description` field so the skill fires when it should and stays quiet when it shouldn't.
