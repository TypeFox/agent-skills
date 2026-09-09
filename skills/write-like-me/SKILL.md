---
name: write-like-me
description: >-
  Rewrite AI-generated text so it reads in the user's own writing voice, driven by a style profile extracted from the user's hand-written documents — or, on explicit request with named documents, build that profile. Use whenever the user asks to make a draft sound like them, match their style, voice, or tone, "de-AI" or humanize agent-written text, post-process a draft before publishing it under their name, or wants their writing style extracted or profiled from their own posts, emails, or docs — even when they don't say "style". Not for editing content, fixing grammar, writing new text from scratch, or imitating other people's or public authors' voices.
---

# Write like me

Machine-written drafts carry a recognizable voice that is not the user's. This skill moves a draft toward the user's own voice as the step *before* their manual polish — never a replacement for it — using a **style-pattern DB**: a JSON profile of the user's writing habits, each habit backed by counts and verbatim quotes from documents the user wrote by hand. The DB format is in [references/db-schema.md](references/db-schema.md); the dimensions along which habits are recorded in [references/taxonomy.md](references/taxonomy.md). Those files say **author** where this one says user — the same person, the one whose hand-written documents the profile is built from and who is asking for the rewrite.

**The picture behind both modes.** The taxonomy's dimensions are the axes of a style space, and a profile marks out the region of it the user's own writing occupies: one measured band per axis (a `range`, not a point), with the tier saying how well that band is known. Extraction draws the region; processing moves a draft into it, axis by axis and in whichever direction each axis is off — machine prose has a region of its own, and where the two overlap there is nothing to do. It is a map, not a metric: the axes carry different units and there is no distance to compute, so the comparison table ranks rows one at a time instead of scoring the document as a whole. Two founding rules follow. **The user's profile has veto power**: a coordinate already inside the region does not move, even where the construction is machine-typical — a user who writes with em dashes keeps them. **Converge on rates, not extremes**: the region is a box drawn around real documents, so its corners — every habit at once, each at its maximum — are precisely the places none of the user's writing occupies; that corner is caricature, and aiming at measured rates keeps a rewrite out of it. Inside the region a rewrite is free: strictness decides which axes it may move along at all, tone decides where along them to aim.

## Modes

| mode | when | reference |
|---|---|---|
| **process** (default) | any text the user hands over — pasted, or as file paths. Assume it is AI-generated; the task is to make it read like the user | [references/processing.md](references/processing.md) |
| **extract** | only when the user explicitly asks for their profile to be built or refreshed *and* names the documents to build it from | [references/technique.md](references/technique.md) |

Extraction is never implicit. A processing request with no profile does not turn into an extraction, and an extraction request without document pointers ("learn my style", "set this up for me") gets one question back — which documents, by path — and stops there. The skill does not scan disks or guess which files the user wrote: the corpus is the user's claim of authorship, and only the user can make it. Extraction writes the DB; processing only reads it.

## Before either mode: the profile

1. **Locate.** Use the path the request names, otherwise the default `$HOME/.agents/write-like-me/user-style.json`.
2. **Missing profile in process mode → stop.** Deliver no rewrite; a rewrite without a profile would be a generic "humanize" pass, which is precisely the caricature this skill exists to avoid. Reply with the path you checked and these instructions, then end the turn:
   - Gather 8 or more documents you wrote by hand — roughly 6,000 words; blog posts, emails, docs, notes; sole-authored; mixed lengths.
   - Ask for extraction with the paths, for example: _"write-like-me: extract my style from ~/writing/posts/*.md and ~/writing/emails/*.txt"_. The paths are required.
   - Review the rendered profile when asked, then repeat the rewrite request.
   In extract mode a missing file at the default path is the normal starting state; replacing a profile that *is* there has its own rules (technique.md, Step 6) — the short of it is that the old one is never gone.
3. **Version check.** Run `python3 scripts/styledb.py info PROFILE` (script paths in this file are relative to the skill directory; PROFILE is absolute — see Scripts). Exit 0: proceed. Exit 2: the DB is older than the skill — apply [references/migration.md](references/migration.md) first. Exit 3: the DB is newer than this skill — stop and tell the user to update the skill. A DB with `partial: true` is an unmerged extraction part; refuse it and point at the merge command in technique.md.
4. **Review status.** `review.status: pending` means the user never confirmed the profile. Proceed, but say so in the report and offer the review round.

**The AI DB.** Processing also reads the skill's own AI style-pattern DB, `data/ai-style-patterns.json` (path relative to the skill directory): its rows are the AI-evidence column of the comparison table, measured in the same run (`--db PROFILE --db data/ai-style-patterns.json`). Give it the same version check (`info`); it must have `kind: ai` and `partial: false`. It ships with the skill and is written by neither mode — if it is missing or fails its checks, the rewrite proceeds with the built-in `ai_*` counters of `scripts/textstats.py` as fallback evidence, and the report says so.

## Strictness settings (process mode)

Every pattern carries an evidence tier (1 strong, 2 moderate, 3 weak; rules in db-schema.md). The setting picks which tiers may drive a rewrite:

| setting | tiers applied | choose when the user says |
|---|---|---|
| soft | 1 | "light touch", "just the obvious", "gently", "only what you're sure about" |
| **medium** (default) | 1–2 | nothing about strength |
| hard | 1–3 | "go all in", "everything", "as close as you can get" |

A softer setting leaves more machine voice in place; a harder one risks applying a habit the corpus only weakly supports. Tiers gate *which* patterns are eligible **and nothing else**: a row inside the ceiling is worked as hard on soft as on hard, in both directions, so a light touch is a shorter list of rows and not a lighter hand on each. The gap between draft and profile still decides the order of work. What no setting ever licenses is inventing material — that line sits between substitution and manufacture, is the same at every setting, and is drawn in Step 3 of [references/processing.md](references/processing.md). Patterns dropped by the setting are listed in the report so the user sees what a harder run would touch.

## Tone steering (process mode)

Strictness is one dial, tone the other: strictness says how much evidence an edit needs, tone says which end of the user's own range to aim for. A request like "more formal", "warmer, less clinical", or "keep it factual but friendly" is written down as a short **tone brief** — the axes named, where the user wants this document on each, one sentence of intent — and carried through every step, including into chunk subagents. No request means no brief, and the profile's rates stay the targets. The brief steers selection among the forms the profile attests and never reaches past them: where a request needs a **register** the corpus does not contain, the report says so instead of inventing it. (A register is the document type each corpus document is tagged with — article, email, docs, note — and the profile's only record of how formal the user gets.) The brief's shape, the axes, and the four precedence rules — among them the one case in which tone outranks the do-not-touch veto — are in [references/processing.md](references/processing.md), Tone steering.

## Process mode

The procedure is [references/processing.md](references/processing.md); read it before Step 1. It defines the verdicts and marks `measure` prints, the table classes, the rule-derivation rules, the invariants, the convergence criteria, and the report template; where this spine and the reference disagree, the reference is right, and a change to one belongs in both. Its spine, per input document:

1. **Measure** — `python3 scripts/textstats.py measure INPUT --db PROFILE --db data/ai-style-patterns.json --sort-gap --setting SETTING --register REGISTER`. The output is the agenda: every measurable profile row with a verdict, class, and gap, the setting's `[manual]` marks, the input register's `[out of scope]` marks, and the judged patterns to read for under *read for these*.
2. **Compare** — the three-way table (AI evidence / draft / user), adding what no counter sees: the AI-evidence column, the judged patterns, an example per row, the tone brief's targets.
3. **Derive rules** — one per rewrite row, removals and additions alike; replacements come from the profile's evidence, `displaces`, and `instead` references, never from invention; targets are the user's rates, read per register where a description splits them, shifted inside the range by the tone brief.
4. **Fix invariants** — facts, structure, subject vocabulary, and who did what stay as the input has them; ask once which earlier manual decisions must survive.
5. **Rewrite the whole body** — rhythm and paragraph shape do not respond to sentence patching.
6. **Converge** — re-measure and run `python3 scripts/structure_check.py INPUT REWRITTEN`, with targeted edits until no rewrite row still reads `absent` or `gap` and the structure check has no errors. A non-zero exit is a gate, and every row left outside the range is named in the report with its reason.
7. **Hand over** — text that lives in this session comes back printed in the reply; a file input gets `<name>.styled.<ext>` beside it, never overwritten unless asked. The report's measured sections are printed by `textstats.py measure INPUT REWRITTEN --db … --report-table` and transcribed from it rather than recalled; a short input gets one line, and the report on request.

Inputs beyond ~3,000 words, or several documents at once, are processed in section-aligned chunks by subagents that receive the same rule set and the same tone brief; measurement, rules, and convergence stay on the whole document.

## Extract mode

The procedure is [references/technique.md](references/technique.md); read it before starting. Its six founding rules — evidence-paired patterns only, reading discovers and counters rank, rates not extremes, absences are data, nothing confidential, subject vocabulary is content — shape every step, and the DB fields and tier rules are in [references/db-schema.md](references/db-schema.md). Where this spine and the reference disagree, the reference is right, and a change to one belongs in both. Its spine:

1. **Intake** — `python3 scripts/styledb.py init DB --corpus-dir ROOT REGISTER=PATH...` writes the manifest and prints the register balance. A compilation is split into several files first, because tiers count documents; a corpus under the guidance (≥8 documents, ≥6,000 words) gets that stated and proceeds with the shortfall on record; a register carrying more than about half the words is a question to the user before reading — `corpus.register_weights` balances without discarding anything, capping costs words and tiers.
2. **Vet** — `python3 scripts/textstats.py measure FILE... --vet` lists the documents whose AI-marker rates stand out; the user confirms or drops, and the manifest's `vetting` records it.
3. **Read** — every document in full, along the taxonomy, capturing verbatim quotes (redacted as they are copied) and noting absences with what the user does *instead*; subject vocabulary and code examples are the topic, not the voice.
4. **Count and validate** — a counter per candidate, checked with `python3 scripts/textstats.py hits FILE... -e REGEX`, false positives subtracted with an `exclude` regex, and only what no exclude separates demoted to judged; `python3 scripts/styledb.py count DB --corpus-dir ROOT` writes the per-document counts, then `python3 scripts/styledb.py validate DB --fix --corpus-dir ROOT` computes rates, spread, coverage, and tiers and verifies every quote and count against the corpus.
5. **Review** — specific questions with a default each (redactions, near-absent rows — absences with a few residual hits, tier 2 by rule — boundary rows, judged counts, decisions taken), asked through the agent's built-in question tool where it has one and as a numbered list in the reply otherwise, with `styledb.py render` as supporting material that goes in the reply or a file that outlives the run; the answers go into a verdict file the agent writes and applies with `python3 scripts/styledb.py review DB --verdicts FILE` — the user never edits JSON; persist as reviewed, or as pending with that fact in the handover.
6. **Persist** — build in a scratch path, back up an existing destination as `<name>_old.json`, write, and `validate` the written file; on a reviewed profile offer `styledb.py seal DB -o DEFAULT_PATH`, which drops the corpus paths while the unsealed DB stays beside the corpus.

Large corpora are split across subagents that each write a partial DB, merged with `python3 scripts/styledb.py merge PART... -o DB` in two phases — discover, then count the merged candidates everywhere — so that tiers reflect full coverage.

## Scripts

All stdlib Python 3.8+, run from the skill directory; `--help` on each. Only the `scripts/…` paths are relative to it: resolve the input, the profile, and the output to absolute paths before running, or a relative input is looked for inside the skill folder and the rewrite lands beside the wrong file.

| script | purpose |
|---|---|
| `scripts/styledb.py` | `info` (version check), `init` (manifest from `REGISTER=PATH` specs), `validate [--fix] [--corpus-dir]`, `count --corpus-dir` (per-document counts from the corpus), `merge`, `review --verdicts` (apply the review round), `seal` (drop corpus paths from a reviewed DB), `render [--setting]`, `tiers` |
| `scripts/textstats.py` | `measure FILE... [--db DB]... [--sort-gap] [--setting S] [--register R] [--report-table] [--vet]` — counters per 1k words, DB patterns with a verdict each, and with the flags the comparison table's class and gap columns, the setting's tier ceiling, and the input's register; `--report-table` prints the report's measured sections as markdown with the AI-evidence column filled; `--vet` lists the corpus documents that stand out on the AI markers; `hits FILE... -e REGEX [-i] [-x EXCLUDE]` prints a candidate counter's matches with context and the DB fields to copy; `counters` lists definitions |
| `scripts/structure_check.py` | `ORIGINAL REWRITTEN` — outline, block sequence, list counts, verbatim blocks, inline code, links, numbers; exit 1 on a violation, and that exit is a gate |

## What this skill never does

- Rewrites without a profile, or builds a profile from documents the user did not name.
- Invents replacement phrasings the profile has no evidence for — the fallback is "remove or flag", not "make something up". A tone request steers among the forms the profile attests; it licenses no new ones. Evidence quotes supply the form, never the words: no clause or sentence is transplanted out of the corpus into a rewrite.
- Adds, drops, or reorders claims, sections, list items, code, tables, links, or numbers.
- Treats the subject as the style: no profile pattern is built on a technical term, a product or people's name, a code identifier, or a code example, and a rewrite never replaces one.
- Records or applies non-native grammar errors as style: the calques listed in [references/german-l1-guidance.md](references/german-l1-guidance.md) stay out of the profile and out of every rewrite (correct-but-distinctive constructions are style and stay in); when the corpus shows such errors, they come back as review-round feedback instead.
- Edits the profile during processing, or persists an extraction the user has not been told is unreviewed.
- Stores potentially confidential content in the profile: names of other people, companies, products, identifying figures. Evidence quotes are redacted with bracketed placeholders while the pattern is kept (rule 5 in technique.md); doubtful cases go to the user in the review round.
