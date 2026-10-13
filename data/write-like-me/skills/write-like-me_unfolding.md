# Unfolding a profile into a user-specific skill

An *unfolding* turns one author's reviewed profile, joined with the skill's AI DB, into a stand-alone skill of their own — `write-like-<name>/SKILL.md`, one file, no scripts, no DBs, no taxonomy — that runs process mode for that author alone. It happens on explicit request only (SKILL.md, Modes), at one of three levels of detail (below). The run computes once what a generic process run computes at every invocation — the join of the two DBs, the per-register rates, the rule per row — and writes the result down as prose. Everything the generic skill defines is pointed to from here, never restated: the unfolded skill is a rendering of those definitions for one author, not a second version of them.

**The trade.** A generic run spends most of its tokens and wall-clock time on the machinery around the rewrite: two reference files, `measure` over both DBs in several rounds, `structure_check`, `--report-table`. An unfolded skill carries the rules pre-derived, so a run reads one file and rewrites; what it gives up is measurement. Counts are estimated by reading, with one grep-based check block over the raw source as the net, and there is no report: the rewrite is the whole output. The author accepts that loss knowingly when they ask for the unfolding, the unfolded skill states it in its own first paragraph, and it points back to write-like-me for everything that needs the machinery — a profile refresh, a review round, exact figures — and for regeneration when either DB changes.

## Preconditions

- Both DBs pass `styledb.py info` (SKILL.md, Before either mode); the AI DB is the skill's own `data/ai-style-patterns.json`.
- The profile is **reviewed** (`review.status: reviewed`). The unfolded skill copies evidence fragments into prose, and the review round is where redactions and tier overrides are settled ([technique.md](technique.md), Step 5); a pending profile gets its round first. Sealing is not required, but a sealed profile is the natural source, since the unfolded skill leaves the corpus behind for good.
- Rule 5 of technique.md carries over: every fragment the unfolded skill quotes comes from the DB's evidence, placeholders included, and nothing from the corpus that is not in the DB reaches it. It is the author's profile in prose, so it lives where the profile lives — the author's personal skills directory, or a repository of theirs — and enters a shared repository only when the author says so.

## Level of detail

The request names the level — *low*, *medium* or *high* — and nothing named means medium. The unfolded skill states its level in its first paragraph, and another level is another unfolding. Every level carries the removals, the shared habits, the no-verdict list, the register table, the procedure and the check block; what the levels change is how much of the bring-in side is written out and how many figures each rule carries — which is what a run reasons over, and so what it costs.

| | low | medium (default) | high |
|---|---|---|---|
| bring-in side | the register table alone: person, contractions, questions, sentence and paragraph shape, hedges, modals, colons, brackets, lists, links, headings, opener, closer | every bring-in row as a rule line | every bring-in row as a rule line |
| figures on a rule | none — the table carries them | the pooled rate and range; a register split only where the description or the table has one | the per-register rate and range on every rule, and the machine's rate on every shared habit |
| example fragments | on the removals' replacements only | at most one per rule | one per rule |
| check block | the absences, the table's counters, the never-used members, the structure diffs | plus one line per shared habit the author's rate bounds from above, with the target in its label | plus the sentence-rhythm shares, per-register targets in every label, and diffs of quotes, tables and fenced code |
| what it buys | the cheapest run: the draft comes out clean and roughly the author's shape | the author's texture wherever the draft offers a slot | the most faithful rendering, at more reasoning per run |

Low is the *both directions* principle at its thinnest: the machine's habits come out and the big axes of the voice are held, but the finer texture — the grammar habits, the favourite words, the connective preferences — is not brought in. Medium is the level the sizes and costs elsewhere in this file describe. High buys precision: a rule with three register figures and a machine rate lets a run place a habit exactly, and a fuller check block sees more, but a run reasons over all of it and writes more for it — the same draft costs noticeably more output at high than at medium for a modest gain in what converges.

## Step 1 — Gather

`styledb.py render PROFILE` and `render data/ai-style-patterns.json` print what the rules are written from: id, effective tier (the override applied), rate, range, spread, registers, scope, description, never-used members, `instead` references, evidence, notes. Two things `render` does not print, and the unfolding computes with a throwaway script over the JSON — nothing is shipped:

- **Per-register rates for every row**, from `patterns[].documents` keyed by `corpus.documents[].register`: for a per-1k row the register's summed counts over its summed words, for a share or length unit the word-weighted mean, and in both cases the per-document minimum and maximum inside the register as its range. This is what `measure --register` does at run time for a register with three or more documents ([processing.md](processing.md), Step 1); the unfolding does it once, for every row, and labels a one-document register a sketch.
- **The join** with the AI DB, below.

The same script fills every figure the rules and the register table carry, at every level: a figure transcribed by hand is rounded, and a rounded figure drifts from the DB it claims to render. At high, the filled figures are also checked against `measure --register` for every register with three or more documents.

## Step 2 — The join

For every AI row, look for a profile row under the AI row's own id or under any id in its `covered_by` list ([db-schema.md](db-schema.md)). Three outcomes, and each becomes a section of the unfolded skill:

| the profile has | the unfolded skill says | confidence |
|---|---|---|
| an absence row (near-absent included) | *never introduce; remove any occurrence*, at the profile row's effective tier, with its `instead` forms as the replacement | high: both DBs agree |
| a presence row | *the author shares this machine habit in a narrower form*: the author's form at the author's rate is the veto, the description names the machine's wider form, and that excess is the removal | high on the excess |
| no row | *a machine tell the profile has no verdict on*: nothing vetoes it and nothing targets it, so a default run leaves it — and, with no report to list it in, does not read for it; only an AI-only run, where every machine tell is a removal (processing.md, Single-DB runs), works this section | none |

The third list is a side product worth handing back with the skill: it names the machine constructions the corpus was never counted for, which is the candidate list for absence rows in the profile's next review round.

Every profile row no AI row reached — most of them — goes into a *bring in, or keep at the author's rate* section. The profile's own absence rows without an AI counterpart (a summary opener, an ordinal sequencer) join the first section: an absence is expressible at any length, whatever the machine's rate.

## Step 3 — Write the rules

One line per row, with the description rewritten as an instruction rather than copied: the description says what the author does, the rule says what to look for in a draft, what form to put there, and how many.

- The tier in brackets — `[1]`, `[2]`, `[3]` — so that the strictness settings (SKILL.md) gate rules exactly as they gate rows; the `[3]` rules go into a section of their own, for the reason given below.
- The target as a rate per 1k words with the per-document range — pooled at medium, split by register where the description or the register table has a split; per register on every rule at high; on no rule at low, where the table is the only source (Level of detail); share and length units stay in their own unit.
- The never-used members (`displaces`) as *never …* on a presence rule and the `instead` references as the replacement on an absence rule, so that substitution has its material without a DB to look in.
- At most one example fragment per rule (Level of detail), from the evidence, under about ten words, chosen to show the form; a fragment that would read as a transplantable sentence is cut down or left out (processing.md, Step 3: quotes supply the form, never the words).
- A *judged* mark on rows with no counter, so that a reader knows they are placed by reading and never by the check block.
- Register-scoped rows placed where their register is named.
- Where two rows speak to one construction, the edit needs both inside the ceiling, and the rule says so: a never-used member of a [2] rule that is also a [3] absence row (*rather than* under an *instead of* rule), or a never-used member of a [1] rule that a [3] presence row still records (a bold list label), is worked on the hard setting only. The join surfaces such pairs; left unresolved, a run applies the lower tier's reading and reverts it in the check.

Group by action, not by dimension: an agent rewriting reads *what comes out, what stays narrow, what goes in*, not the taxonomy's headings, and the taxonomy is one of the things the unfolded skill does not carry. Inside the bring-in section, loose groups (punctuation and sentence shape; voice and modality; connectives and argument; grammar habits; wording; tone; content conventions) keep it scannable.

## Step 4 — The register table

The unfolded skill's replacement for `measure --register`: one column per register in the corpus, one row per register-sensitive habit — person (I / we / you), contractions, questions, sentence length and the short and long shares, paragraph length and the one-sentence share, hedges, the modals, colons, bracketed asides, list items, links, heading case, the opener, the closer — filled from the Step 1 figures with the register's range in brackets, and a one-document register labelled a sketch. It is the same at every level; at low it is the whole bring-in side. A register the corpus does not have gets the rule processing.md gives an unseen register: steered by the request's own statement of tone and intent, with the nearest column as a sketch.

The table is also where the tone brief gets its poles: the formal end is the article and thesis columns, the warm end the email and issue columns, and a brief moves targets between them and never past them (processing.md, Tone steering, rule 2).

## Step 5 — Procedure and checks

The seven processing steps collapse to four — intake, rewrite, check, hand over — stated in the unfolded skill's own words because processing.md does not ship with it:

- **Intake** keeps Step 4's one question about protected passages and Step 7's file-or-reply rule, and adds the register choice — the register the finished piece is *for*, not the one the draft imitates.
- **Rewrite** replaces Steps 1–5: the check block run once on the draft for the removals' numbers, then the whole body rewritten in one pass with the rules of the sections the setting allows in mind — no written agenda. An agenda is, after the rewrite itself, the largest thing a run writes, and for the removals the block's draft counts already are one; the bring-in rows are placed while writing. The price is that rule selection is implicit, so the bring-in side is worked less systematically than a generic run's comparison table would have it. The short-input rule and the structural-row rule of Step 2 are restated in two sentences.
- **Check** replaces Step 6 with the check block, run once on draft and rewrite, and a structure-and-facts checklist. Targeted edits follow only for an absence still above zero and a structure diff no shape rule justifies; a frequency counter that landed inside the range but high is left, and there is no second round — the skill is the step before the author's own polish, and a second round buys a rate for the price of a whole pass. The block is one shell command of patterns `grep -E` can run — no lookarounds, so every profile regex that uses one is rewritten or replaced by a word list: one line per absence with target 0, one per counter of the register table (person, contractions, brackets, colons, questions), one for the never-used members, and the mechanical invariants (headings, list items, code, links, numbers) as diffs between draft and rewrite; medium adds a line per shared habit bounded from above (absolutizers, authenticity words, verdict openers, formal connectives), high the rhythm shares and the fuller diffs (Level of detail). It counts on the raw source, code and URLs included, and the block says so. The checklist is the rest of Step 4's invariants as bullets, walked on the diff, with the gate wording kept: a violation is not deliverable.
- **Hand over** is Step 7 without its report: the rewrite where Step 7 says it goes, and one line naming the setting and register used. The report is the first thing an unfolding drops — after the rewrite itself it is the largest artifact a run writes, paid for in output tokens every time, and the check block has already shown the run what converged. The price is that the manual-pass list, the rows that did not converge and the judged habits are not accounted for; the author reads the diff instead.

Settings, tone steering, the single-DB variants, chunking and the never-does list carry over in a paragraph or a line each; a chunk subagent's brief carries the rule file, the setting and the tone brief, and the check block runs on the reassembled whole.

## What makes an unfolded run cheap — and what does not

A smaller skill file does not by itself make a run faster. Wall-clock time follows the tokens the model *writes* — thinking and rewrite — and the file size only sets what it reads, which is cached and cheap; the per-turn context is mostly the draft, the rewrite and the tool results, whatever the skill file weighs. What the generic run's machinery does for the model, an unfolded skill has to replace with something bounded, or the model reinvents it by reasoning at a higher price:

- `measure --sort-gap` is an **agenda generator**, not only a verifier: it hands the model a short, ordered list of rows to work. Left without one, a model measures every rule with ad-hoc greps before touching the draft, and that costs more output than the rewrite. The check block is the only counting the unfolded skill allows, run once on the draft for the removals' numbers; there is no written agenda, every other rule is placed while rewriting, and the skill says in words that measuring everything is what the scripts are for.
- The tier ceiling has to bind **before** the rewrite. With the [3] rules inline, a model applies some of them on the default setting, catches it in the check, and spends a round reverting. Rules above the default ceiling go into a section of their own that the default setting does not read as instructions — which also makes the default run's read shorter.
- `structure_check` is one command; a checklist walked by hand is several. The check block prints the mechanical part of the invariants (headings, list items, code, links, numbers) as diffs next to the counters, so one command is the whole check, and there is one round: the rewrite, the block, targeted edits for absences and structure only.
- The report is a written artifact the model pays for on every run, and it is gone (Step 5).
- Density is a cost too: every figure on a rule and every line in the check block is something the run reasons over before and after writing. That is the dial the level of detail turns, and the reason medium is the default.

The check block also decides what the run can see. A habit with no line in it, or a line narrower than the profile's counter, does not converge however clear its rule — the machine's verdict openers stand at twice the author's rate, a significance tail survives because the line names "that matters" but not "matters more than". So every shared-habit row the author's rate bounds from above earns a counting line with the target in its label, and each line carries the profile counter's members, not a shorter list from memory.

## What is lost

The unfolded skill's first paragraph says it, and its author should know it: rates are estimates from raw-source greps and reading; the `[enum]` caveat of processing.md, Step 6, applies to every line of the check block; there is no report, so what a run left alone shows only in the diff; there is one check round, so frequency habits land inside the author's range rather than at the rate; judged rows have no counter at all; nothing is re-rated at run time; and there is no version check — the header names the profile and AI DB dates the skill was unfolded from, and the fix for a changed DB is regeneration. The unfolded skill is never the place to correct a rule: the profile is, through a review round, followed by regeneration, or a rule that is right for one draft becomes a fork that drifts from the profile it claims to render.

## Size

A profile of a hundred-odd rows over five registers, joined with the AI DB, comes to about 7,000 words in one SKILL.md at medium, roughly a third of that at low, and 9,000 to 10,000 at high, where most of the growth is figures and the check block. One file holds all three; a profile well beyond that size moves the bring-in section to `references/habits.md` at medium and high and keeps the removals, the shared habits, the no-verdict list, the register table and the procedure in SKILL.md, so that a short input still costs one file.
