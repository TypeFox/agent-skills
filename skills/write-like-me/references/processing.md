# Processing procedure

Processing rewrites AI-generated text toward the author's voice, as the step *before* the author's own polish, never as a replacement for it. It reads the author's DB (and the AI DB once it ships) and never writes either. Vocabulary is defined in [taxonomy.md](taxonomy.md) and [db-schema.md](db-schema.md); the mode rules, DB lookup, and strictness settings are in SKILL.md.

The stance that makes it work: the author's DB has veto power over every edit. Where the input already matches the author, nothing moves — even when the AI DB (or the built-in AI counters) flags the construction as machine-typical. An author who genuinely writes with em dashes keeps them. And every rewrite targets the author's *rate*, never zero and never "always": the guard against caricature.

## Step 1 — Measure

Run the counters over each input document (per document — different generators leave different marks, and the report is aggregated afterwards):

```sh
python3 scripts/textstats.py measure INPUT.md --db USER_DB.json
```

The output has two parts: the built-in stats and counters (the `ai_*` rows stand in for the AI DB until it ships), and every measurable DB pattern with the input's value, the DB rate and range, and a verdict: `gap` (outside the author's per-document range), `low` or `high` (inside the range but under half or over twice the author's rate — a habit the author has, just not in every document), or `match`. Judged patterns (no regex or stat) do not appear there; read the input for them with the pattern descriptions in hand and note your estimate.

## Step 2 — Three-way comparison table

Build one table: rows are patterns (and any built-in AI counter with a striking value), columns are AI evidence, input, author DB — each with rate and one example — sorted by the input-vs-author gap, largest first. Classify every row:

| class | condition | action |
|---|---|---|
| do-not-touch | input ≈ author (verdict `match`), whatever the AI evidence says | none; list it in the report |
| rewrite, high confidence | input ≉ author (verdict `gap`), and the construction is AI-typical (AI DB row, or a built-in `ai_*` counter, or an author absence pattern) | rewrite to the author's rate |
| rewrite, low confidence | input ≉ author (verdict `gap`), no AI evidence — could be a generator quirk outside the AI corpus, could be topic-driven | rewrite only when the author pattern is tier 1 (tier 2 in the hard setting); otherwise flag for the manual pass |
| lean | verdict `low` or `high`: inside the author's range, far from the rate | move toward the rate only where the rewrite of another row opens a natural slot (a "So" where a formal connective came out); never manufacture occurrences |
| neutral | everything else | none |

Then apply the strictness setting: drop rewrite rows whose effective tier exceeds the setting's ceiling (soft 1, medium 2, hard 3). Dropped rows go in the report as "left for the manual pass", so the author sees what a harder setting would have touched.

## Step 3 — Rule derivation

One mechanical rule per rewrite row: *what to find, what to replace it with, how many to leave*. The replacement construction comes from author-DB evidence — the pattern's own quotes, or the `instead` references of an absence pattern — never from invention. If the DB offers no replacement (an absence pattern without `instead`, an evidence list that shows the habit but not a substitute), the rule is "remove where the sentence survives removal, otherwise flag", not "make something up".

Targets are rates: for an em-dash row with author rate 0.4/1k and range 0–1.1, the rule leaves roughly 0–1 per 1,000 words in place, choosing the ones that read most like the author's own uses. Register restrictions in `note` apply: a pattern marked "emails only" is not a target for a blog post.

## Step 4 — Invariants

Always: facts, numbers, links, citations, quoted material, code, tables, section order and headings, block sequence within every section, list item counts — and no new claims. Rewriting is rearranging the author's material, not adding to it. `scripts/structure_check.py ORIGINAL REWRITTEN` enforces the structural part mechanically; the factual part (no new claims, no lost qualifications) is yours to check by reading the diff.

Paragraphs: keep the paragraph count of every section where possible. Merging or splitting a paragraph is allowed only when the author's paragraph-shape patterns demand it (a tier-1 one-sentence-paragraph habit against a wall of five-sentence paragraphs) — `structure_check.py` reports it as a warning so the report can say where and why.

Input-specific invariants: ask once, up front, which earlier manual decisions must survive — kept phrasings, a table, a closing sentence. In an iterating workflow this is what prevents the rewrite from undoing the author's previous polish. If the user is not available, treat any passage that already reads like the author (verdict `match` at the sentence level) as protected.

## Step 5 — First pass: whole-body rewrite

Rewrite each document in one pass with the full rule set in view. Rhythm, paragraph openers, and discourse-level habits (story-first, concession, digression-and-return) do not respond to sentence patching — they need the whole section rewritten with the author's shape in mind. Hold the invariants while doing it; the structure check afterwards is a net, not the plan.

## Step 6 — Convergence

Re-run the identical measurement on the rewritten text, plus the structure check:

```sh
python3 scripts/textstats.py measure INPUT.md REWRITTEN.md --db USER_DB.json
python3 scripts/structure_check.py INPUT.md REWRITTEN.md
```

Drive targeted edits from the deltas — each a uniqueness-asserted replacement of one passage — until the rewrite rows read `match` and the structure check reports no errors. Check overlong sentences against the author's `long-tail` share, and the word-count change (turning fragments into sentences or the reverse shifts it) against reason. Stop when the remaining gaps are all in rows you deliberately left, or when a further edit would need invented material. Two or three rounds are normal; more than five means a rule is wrong — revisit Step 3 rather than pushing harder.

## Step 7 — Verification and report

The handover to the author's manual polish is the rewritten text plus this report:

```
# write-like-me report — <document name>

Setting: <soft|medium|hard>; profile: <path>, db_version <n>, review <status>.

## Before / after
| pattern | tier | input | rewritten | author rate (range) | verdict |
...

## Do-not-touch (input already matched the author)
- ...

## Left for the manual pass
- <pattern>: <why — tier above setting / low confidence / no replacement in the DB>

## Side effects
- word count <n> → <m> (<why>)
- paragraph count changes: <section: n → m, why> or none
- structure check: <n> error(s), <m> warning(s)

## Open judgment calls
- <passage>: <what the rule wanted vs. what reads right>
```

Print the full rewritten body once, for proofreading, when the input was pasted or is short; for file inputs write `<name>.styled.<ext>` next to the input (never overwrite the input unless asked) and print the report. Say honestly what did not converge.

## Chunking large inputs with subagents

A long document (more than ~3,000 words, or several documents in one request) is processed by section: the orchestrating run does Steps 1–4 on the whole document — measurement and rules are per document, not per chunk — and hands each subagent one chunk of whole sections plus the same rule set, the invariants, the do-not-touch list, and the instruction to return only the rewritten chunk with headings intact. Never split inside a section, and never let a subagent see the rules for a different setting than the one in force. Reassemble in order, then run Steps 6–7 on the whole document — convergence is measured on the assembled text because rates are per document, and a chunk can look converged while the whole does not.

Extraction has its own parallel protocol; see the last section of [technique.md](technique.md).
