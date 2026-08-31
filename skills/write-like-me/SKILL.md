---
name: write-like-me
description: >-
  Rewrite AI-generated text so it reads in the user's own writing voice, driven by a style profile extracted from the user's hand-written documents — or, on explicit request with named documents, build that profile. Use whenever the user asks to make a draft sound like them, match their style, voice, or tone, "de-AI" or humanize agent-written text, post-process a draft before publishing it under their name, or wants their writing style extracted or profiled from their own posts, emails, or docs — even when they don't say "style". Not for editing content, fixing grammar, writing new text from scratch, or imitating other people's or public authors' voices.
---

# Write like me

Machine-written drafts carry a recognizable voice that is not the user's. This skill moves a draft toward the user's own voice as the step *before* their manual polish — never a replacement for it — using a **style-pattern DB**: a JSON profile of the user's writing habits, each habit backed by counts and verbatim quotes from documents the user wrote by hand. The DB format is in [references/db-schema.md](references/db-schema.md); the dimensions along which habits are recorded in [references/taxonomy.md](references/taxonomy.md).

Two founding rules sit under everything. **The user's profile has veto power**: where the draft already matches the user, nothing moves, even if the construction is machine-typical — a user who writes with em dashes keeps them. **Converge on rates, not extremes**: every rewrite targets the user's measured frequency, never zero and never "always"; that is the guard against caricature.

## Modes

| mode | when | reference |
|---|---|---|
| **process** (default) | any text the user hands over — pasted, or as file paths. Assume it is AI-generated; the task is to make it read like the user | [references/processing.md](references/processing.md) |
| **extract** | only when the user explicitly asks for their profile to be built or refreshed *and* names the documents to build it from | [references/technique.md](references/technique.md) |

Extraction is never implicit. A processing request with no profile does not turn into an extraction, and an extraction request without document pointers ("learn my style", "set this up for me") gets one question back — which documents, by path — and stops there. The skill does not scan disks or guess which files the user wrote: the corpus is the user's claim of authorship, and only the user can make it. Extraction writes the DB; processing only reads it.

## Before either mode: the profile

1. **Locate.** Use the path the request names, otherwise the default `$HOME/.skills/write-like-me/user-style.json`.
2. **Missing profile in process mode → stop.** Deliver no rewrite; a rewrite without a profile would be a generic "humanize" pass, which is precisely the caricature this skill exists to avoid. Reply with the path you checked and these instructions, then end the turn:
   - Gather 8 or more documents you wrote by hand — roughly 6,000 words; blog posts, emails, docs, notes; sole-authored; mixed lengths.
   - Ask for extraction with the paths, for example: _"write-like-me: extract my style from ~/writing/posts/*.md and ~/writing/emails/*.txt"_. The paths are required.
   - Review the rendered profile when asked, then repeat the rewrite request.
   In extract mode a missing file at the default path is the normal starting state; an existing one is refreshed only after saying so, with the old file backed up beside it (`user-style_old.json`).
3. **Version check.** Run `python3 scripts/styledb.py info PROFILE` (paths in this file are relative to the skill directory). Exit 0: proceed. Exit 2: the DB is older than the skill — apply [references/migration.md](references/migration.md) first. Exit 3: the DB is newer than this skill — stop and tell the user to update the skill. A DB with `partial: true` is an unmerged extraction part; refuse it and point at the merge command in technique.md.
4. **Review status.** `review.status: pending` means the user never confirmed the profile. Proceed, but say so in the report and offer the review round.

**TODO (maintainers):** the AI style-pattern DB does not ship yet — see the README in `data/`. Until it does, the AI-evidence column of the comparison table comes from the built-in `ai_*` counters in `scripts/textstats.py` and from the user's absence patterns.

## Strictness settings (process mode)

Every pattern carries an evidence tier (1 strong, 2 moderate, 3 weak; rules in db-schema.md). The setting picks which tiers may drive a rewrite:

| setting | tiers applied | choose when the user says |
|---|---|---|
| soft | 1 | "light touch", "just the obvious", "gently", "only what you're sure about" |
| **medium** (default) | 1–2 | nothing about strength |
| hard | 1–3 | "go all in", "everything", "as close as you can get" |

A softer setting leaves more machine voice in place; a harder one risks applying a habit the corpus only weakly supports. Tiers gate *which* patterns are eligible; the gap between draft and profile still decides the order of work. Patterns dropped by the setting are listed in the report so the user sees what a harder run would touch.

## Process mode in brief

Full procedure with the table classes, rule-derivation rules, and the report template: [references/processing.md](references/processing.md). The spine, per input document:

1. **Measure** — `python3 scripts/textstats.py measure INPUT --db PROFILE`: built-in counters plus every measurable profile pattern with a match/gap verdict. Read for the judged patterns.
2. **Compare** — a three-way table (AI evidence / draft / user), sorted by draft-vs-user gap; classify rows as do-not-touch, rewrite (high or low confidence), or neutral; apply the setting.
3. **Derive rules** — one per rewrite row; replacements come from the profile's evidence and `instead` references, never from invention; targets are the user's rates.
4. **Fix invariants** — facts, numbers, links, quotes, code, tables, heading outline, block sequence per section, list item counts, no new claims; subject vocabulary (technical terms, product and people's names, identifiers) stays verbatim — the profile decides how it is presented, never what it is; paragraph count per section wherever possible. Ask once which earlier manual decisions must survive.
5. **Rewrite the whole body** — rhythm and paragraph shape do not respond to sentence patching.
6. **Converge** — re-measure and run `python3 scripts/structure_check.py INPUT REWRITTEN`; targeted edits until rewrite rows match and the structure check has no errors.
7. **Report and hand over** — before/after table, do-not-touch list, rows left for the manual pass, side effects, open judgment calls. Write `<name>.styled.<ext>` next to a file input (never overwrite the input unless asked); print the body once when the input was pasted.

Inputs beyond ~3,000 words, or several documents at once, are processed in section-aligned chunks by subagents that receive the same rule set; measurement, rules, and convergence stay on the whole document. Protocol in processing.md.

## Extract mode in brief

Full procedure, review protocol, and the parallel-extraction protocol: [references/technique.md](references/technique.md). The spine:

1. **Intake** — enumerate the named documents with register and the word count from `textstats.py`; state the corpus-size guidance (≥8 documents, ≥6,000 words) when the corpus falls short, and continue with the shortfall on record (it lowers tiers, it does not block). When one register carries more than about half the words (a thesis next to posts and emails), ask the user how to cap or down-weight it before reading — rates are corpus-normalized, so the big source would otherwise define the profile (technique.md).
2. **Vet** — flag documents whose AI-marker counts are outliers against the rest; the user confirms or drops.
3. **Read** — every document in full, along the taxonomy, capturing verbatim quotes as you go; note absences and what the user does *instead*. Subject vocabulary and code examples are skipped: terms, names, and identifiers are the topic, not the voice (rule 6 in technique.md); only the user's handling of them (backticks, abbreviations, jargon level) is a pattern.
4. **Count** — a counter per candidate, run over every document; noisy counters demoted to judged.
5. **Validate** — `python3 scripts/styledb.py validate DB --fix --corpus-dir ROOT` computes rates, spread, coverage, tiers, and verifies every quote.
6. **Review** — render with `styledb.py render`, walk the user through WRONG / OVERSTATED / MISSING / NEEDS_NUANCE; persist as reviewed, or as pending with that fact in the handover if the user is unavailable.
7. **Persist** — to the named path or the default, then `validate` once more.

Large corpora are split across subagents that each write a partial DB, merged with `python3 scripts/styledb.py merge PART... -o DB` — two phases (discover, then count the merged candidates everywhere) so that tiers reflect full coverage.

## Scripts

All stdlib Python 3.8+, run from the skill directory; `--help` on each.

| script | purpose |
|---|---|
| `scripts/styledb.py` | `info` (version check), `validate [--fix] [--corpus-dir]`, `merge`, `render [--setting]`, `tiers` |
| `scripts/textstats.py` | `measure FILE... [--db DB]` — counters per 1k words, DB patterns with match/gap; `counters` lists definitions |
| `scripts/structure_check.py` | `ORIGINAL REWRITTEN` — outline, block sequence, list counts, verbatim blocks, inline code, links, numbers; exit 1 on a violation |

## What this skill never does

- Rewrites without a profile, or builds a profile from documents the user did not name.
- Invents replacement phrasings the profile has no evidence for — the fallback is "remove or flag", not "make something up".
- Adds, drops, or reorders claims, sections, list items, code, tables, links, or numbers.
- Treats the subject as the style: no profile pattern is built on a technical term, a product or people's name, a code identifier, or a code example, and a rewrite never replaces one.
- Records or applies non-native grammar errors as style: the calques listed in [references/german-l1-guidance.md](references/german-l1-guidance.md) stay out of the profile and out of every rewrite (correct-but-distinctive constructions are style and stay in); when the corpus shows such errors, they come back as review-round feedback instead.
- Edits the profile during processing, or persists an extraction the user has not been told is unreviewed.
- Stores potentially confidential content in the profile: names of other people, companies, products, identifying figures. Evidence quotes are redacted with bracketed placeholders while the pattern is kept (rule 5 in technique.md); doubtful cases go to the user in the review round.
