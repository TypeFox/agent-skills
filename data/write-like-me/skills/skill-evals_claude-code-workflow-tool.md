# Running generation through Claude Code's Workflow tool

This covers Activity 2/4 generation subagents spawned via Claude Code's `Workflow` tool — typically used to run generation on a different (often cheaper) model than the one doing design, isolation audit, grading, and reporting. `Workflow` is one of the two run mechanisms in Gate 2's choice (see `SKILL.md`); the other — out-of-process headless runs (`claude -p --model ...`) — covers the same cheaper-model use case. Prefer `Workflow` for its orchestration: parallel fan-out under one journal, and cached targeted reruns via `resumeFromRunId` (below). Prefer headless when the orchestrating session is contaminated with project memory (headless makes that channel verifiable; `Workflow` cannot, see below) or when the benchmark needs measured per-run token costs, which `Workflow` does not surface (see Timing below). This doc assumes `SKILL.md`'s Gate 1, Gate 2, and Activities 2/4 are already read; everything here is the delta specific to `Workflow`, not a restatement of the general procedure.

## Isolation always lands on tier 2 — and transcripts nest one level deeper

`Workflow`-spawned agents have the same unrestricted tool access as any Claude Code subagent. There's no per-run sandbox or read-scope at the `Workflow` layer — `opts.isolation: 'worktree'` isolates concurrent *writes* between agents, it does nothing to hide files from *reads*. So Gate 2 always lands on tier 2 (deterministic tracing) here; don't spend time looking for an allowlist option that doesn't exist for this tool. Decide this up front and write it into `methodology-and-isolation.md` before launching.

Transcripts live one level deeper than a direct spawn: `<session-dir>/subagents/workflows/wf_<run-id>/agent-<id>.jsonl`, not the flat `subagents/agent-<id>.jsonl`. The `Workflow` call's own result reports this directory (a `Transcript dir:` line) — capture it the moment you launch.

`opts.label` is write-only: `journal.jsonl` records only `{type, key, agentId, result}` per agent, with no label, model, or timing field to map an agent id back to the job it ran. So embed a unique, greppable string — the run's own absolute output directory is a natural choice, since the agent needs it anyway — in the first line of every generation prompt, then identify each `agent-<id>.jsonl` by matching its first user message against that string.

When scanning a transcript for the isolation audit, check every `Bash` command string too, not just typed `Read`/`Glob`/`Grep`/`Write`/`Edit` calls — a `cat`, `find`, `ls`, or `grep -r` inside `Bash` is just as real a file read and is easy to miss if you only scan the dedicated tools.

## Self-report is unreliable in both directions

If you fall back to a run's own `access-log.md`, don't treat it as the verdict — it can fail both ways. A run can delete its own log during end-of-run cleanup, leaving nothing on disk even though the transcript trace shows a clean run; a run can also log a path it never actually read (written reflexively to satisfy a "log what you read" instruction, with no matching `Read` call anywhere in the transcript). Treat `access-log.md` as a **corroborating signal to cross-check, never as the verdict** — the transcript trace is what you trust. If you reconstruct a missing log for continuity, label it explicitly as reconstructed, not as the agent's own report.

## Three contamination flavors — check for all of them

- **Path-allowlist violations**: a run reads something outside its assigned scope (e.g. the shared eval source instead of its own pre-seeded copy). Discard and rerun regardless of how harmless the specific leak looks — Gate 2's rule has no "but the content was identical" exception. If an indirect instruction ("don't reference any other copy of these files") isn't landing with a cheaper model, name the literal forbidden path instead.
- **Fixture-freshness violations**: a run's `outputs/` directory isn't actually pristine when it starts — most often from re-seeding one job but not its sibling, or from an unexpected `Workflow` re-execution (see caching below). This stays entirely inside the run's own allowlist, so a naive "did every read stay in scope" check misses it, but it still invalidates the run — e.g. it edits already-fixed code instead of the original flawed fixture. **Reset a job's `outputs/` from the pristine fixture before every rerun**, for any reason — a fresh agent invocation does not imply a fresh filesystem, and `Workflow`'s caching has no effect on what's actually sitting in the workspace directories.
- **Harness-injected project memory**: the repo's root AGENTS.md/CLAUDE.md reaches every `Workflow`-spawned agent through the harness itself, not through a tool call — so the transcript audit above cannot detect it and a contaminated run's trace comes back clean. Within `Workflow` this flavor is prevented, never traced: Gate 2's project-memory step in `SKILL.md` (root instruction files absent since the eval session started) must be cleared before any generation run launches. If the session cannot clear it — contamination discovered after the session started — `Workflow` is off the table for this eval: switch the runs to out-of-process headless sessions per `SKILL.md`'s escape hatch, where the channel becomes verifiable in each child's own transcript.

## Cheap targeted reruns, and a caching gotcha

`resumeFromRunId` caches each `agent()` call by its `(prompt, opts)` pair, so you can fix one contaminated job without re-running the whole batch: change only that job's prompt (e.g. gate an added note on the eval name, rather than editing a shared prompt-building function unconditionally) and resume with the same run ID — unaffected calls replay instantly from cache.

The cache key isn't purely value-based, though: it can key closer to source position or an AST fingerprint of the surrounding code region, so an edit meant for one call can invalidate a neighbor's cache entry too, even when that neighbor's `(prompt, opts)` content is byte-for-byte unchanged. After any `resumeFromRunId` edit, check which `agent-<id>.jsonl` files are newer than expected (`ls -la` on the transcript directory, sorted by time) rather than assuming only your intended target re-ran. Treat any unexpected rerun exactly like an intentional one: verify its isolation and confirm its `outputs/` was pristine at the start (the fixture-freshness check above).

## Timing: what Workflow actually gives you

`journal.jsonl` carries no per-agent token or duration field — only the cached return value. Don't assume a `tokens`/`durationMs` completion field will surface the way a direct `Agent`-tool spawn's does; check the actual tool result and journal before building a methodology around it, and write `timing.json`'s `source` field honestly if it isn't exposed.

What the harness does persist reliably, straight from each agent's own transcript:

- **Duration** — the first-to-last event timestamp in `agent-<id>.jsonl` is a real, harness-recorded wall-clock figure.
- **Tool-call counts** — counting `tool_use` blocks is equally trustworthy.

**Don't reconstruct total tokens by summing each turn's `usage` block.** In a multi-turn agentic conversation, context keeps growing and re-billing turn over turn, so summing overcounts by an order of magnitude or more — and how much depends on an arbitrary dedup choice (by message id or not), so there's no way to tell which number, if any, matches what a human would mean by "how many tokens did this cost." Write `total_tokens: null` with a `source` field naming why instead; a specific-looking wrong number is worse than an honest gap because it reads as measured when it isn't. If measured per-run tokens are a hard requirement, that is a reason to pick headless `claude -p --output-format json` runs over `Workflow` in Gate 2's run-mechanism choice, not a reason to reconstruct.

## Keep grading on your own model, not the cheap generation model

When using `Workflow`'s per-call `model` override for **generation only**, grade with plain `Agent`-tool calls at the orchestrating session's own (usually stronger) model and effort — no override. Grading already demands real rigor (claim extraction, critiquing the assertions themselves, actually re-running builds/tests rather than trusting a summary); a cheap model checking a cheap peer's work is the weakest possible version of that check, right where you need it strongest. A stronger grader can catch what the generation model's own verification missed — e.g. an independent test that exposes a bug the generation run's own passing test suite didn't.

## Design prompts assuming write-ups may get skipped

A smaller or cheaper generation model, given more to read up front (a skill plus reference material) before it gets to the task itself, can treat its final chat reply as satisfying a "write up what you changed" request instead of also persisting the requested file — even with a generic "reply with a summary" instruction present. This isn't evidence the skill discourages write-ups; it's a context-budget effect more likely to show up on cheaper models carrying more upfront reading.

If any assertion grades a persisted write-up rather than the chat reply, say so by name in the operational instructions given to every generation run, independent of what the eval prompt itself says — e.g. "write your explanation to `explanation.md` in your outputs directory; your final chat reply is a separate, shorter summary, not a substitute for that file."
