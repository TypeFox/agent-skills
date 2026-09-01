# Extraction technique

One procedure builds every style-pattern DB: the author's DB from their hand-written documents, and (a maintainer task) the AI DB from a corpus of machine-generated documents. The corpus and the reviewer differ; the steps do not. Vocabulary (pattern, marker, counter, judged) is defined at the top of [taxonomy.md](taxonomy.md); the DB fields and tier rules in [db-schema.md](db-schema.md).

Six founding rules shape every step:

1. **Evidence-paired patterns only.** A pattern enters the DB with verbatim quotes and per-document counts, or not at all. `styledb.py validate --corpus-dir` checks the quotes; a quote that cannot be found is a fabricated pattern.
2. **Reading discovers, counters rank.** Counters do not find the voice — they cannot see a concession structure or a kitchen metaphor. Reading finds candidates; counters order them by size, make them reproducible, and later drive convergence.
3. **Rates, not extremes.** Record what the author does at the rate they do it. "Uses colons" is not a pattern; "3.1 colons per 1k words, range 1.2–4.8" is. The range is the point: each pattern fixes one band of the region the profile stands for (SKILL.md), and a band a rewrite can aim anywhere inside is worth more than a number it has to hit.
4. **What the author *doesn't* do is data.** Absence patterns (em dashes: 0 across 6,000 words) are the do-not-introduce list and are as valuable as presence patterns.
5. **Nothing confidential lands in the DB.** The DB outlives the corpus, gets rendered, merged, and quoted in reports, so a quote is copied into it only if it could be shown to a stranger. When the passage that evidences a pattern carries potentially confidential information — names of persons other than the author, companies, products, customers, internal project names, figures, dates that identify an event — rewrite the quote so the pattern stays intact and the information is gone: `"Sam needed the docs build"` becomes `"[colleague] needed the docs build"`, keeping the punctuation, rhythm, and construction the quote is there to show. Mark the entry `"redacted": true`; the validator then skips the verbatim check for it (and expects a bracketed placeholder). Redact rather than drop: a pattern whose only evidence was confidential still deserves its entry. The author's own name is not confidential in their own profile. When in doubt, redact, and raise it in the review round — the author decides what may stay.
6. **Subject vocabulary is content, not voice.** Technical terms, product, library, and tool names, code identifiers, and code examples belong to the topic the author happened to write about, and a second corpus on another topic would not repeat them. They never become a pattern: no `favourite-word` for a term of the field, no regex on a product name, no quote chosen *because* it shows a term. What the taxonomy does record is the author's *handling* of such material — `code-reference` (backticks or prose), `abbreviation`, `jargon-level`, `name-drop-list` — measured on any subject. Code blocks, inline code, URLs, and tables are already stripped before counting (`textstats.py`); this rule covers what the stripper cannot see: the terms and names inside plain prose. The test for a vocabulary candidate is "would this word still be a habit if the author wrote about cooking?" — if not, it is a topic effect and stays out.

## Step 1 — Corpus intake

The request names the documents (extraction never goes looking for documents on its own — see the mode rules in SKILL.md). Enumerate them into the corpus manifest: id, path, date if known, register, and the word count from `textstats.py measure` (rates are normalized against that count, so an editor's word count is the wrong number).

Guidance to state when the corpus falls short, then proceed anyway with the shortfall on record: at least ~8 documents and ~6,000 words, sole-authored, fully hand-written, mixed lengths, every document tagged with a register. A small corpus is not a reason to stop; it is a reason for lower tiers (the tier rules encode this: fewer documents means fewer patterns reach tier 1) and for a warning in the DB's `note`s.

**Register balance.** Corpora often mix sources of very different sizes — a thesis next to blog posts and emails. Rates are corpus-normalized, so a source carrying most of the words turns the DB into a profile of that register, with every other register's habits demoted to tier 3. When one register carries more than about half the words, stop and ask the user before reading: whether to cap the dominant source (keep its most prose-like parts and leave the rest out of the manifest), and whether to down-weight it deliberately — academic material such as a dissertation is a common candidate, because its register differs from the business writing the profile will mostly serve. Record the decision and the capping in the manifest and the DB `note`s; with a smaller imbalance, balancing by selection is a judgment call to make and report, not to ask about.

## Step 2 — Authenticity vetting

The corpus must be the author's own hand. Measure every document with `textstats.py measure` and look for outliers on high-signal AI markers — em dashes, `ai_colon_punchline`, `ai_comma_not`, `ai_rather_than`, `ai_verdict_opener`, `ai_authenticity`, `label_lead`, and `ai_vocabulary` for older-style output (the AI-typical dimensions in taxonomy.md rank them) — relative to the other documents: "this one has 12 em dashes per 1k words, your others have 0 — was it AI-assisted?" Pre-AI-era documents are the clean anchor; recent documents are admitted when the author certifies them as hand-written (`vetting: certified`) and they double as a drift check on the older anchor. Record the outcome per document; drop what the author drops. The shipped AI DB (`data/ai-style-patterns.json`) says which markers are high-signal and at what machine rates; its `ai_*` counters are the vetting instrument.

## Step 3 — Close reading

Read every document in full — paragraph shape, openers, and closers do not survive excerpting. Walk the taxonomy dimension by dimension and note candidates with the quote and the document they came from, as you go (a candidate without a quote is not a candidate). Note also the *absences*: constructions common in machine prose that never appear. Apply rule 6 while reading: a recurring word is a candidate only if it is independent of the subject, and code examples are skipped entirely — read past them to the prose that introduces and follows them, which is where the voice is.

One boundary on candidates: a construction that is a grammar error rather than a style choice — non-native calques above all — is never a candidate, no matter how often the corpus repeats it. Collect such findings separately (quotes redacted under rule 5) and bring them to the review round as feedback instead; [german-l1-guidance.md](german-l1-guidance.md) draws the style-vs-error boundary for German-native authors and lists the known calques with their corrections.

Capture quotes with rule 5 in force: redact while copying, not in a later sweep — a sweep over a finished DB reliably misses the name buried in the middle of a long quote. Keep a list of what you redacted for the review round.

Three reading habits matter. First, distinguish voice from format: a pattern that appears across registers (article and email and docs) is voice; a pattern confined to one register is a format convention — keep it, but restrict it in `note` ("emails only") so processing can respect the register of the input. Second, for every absence, note what the author does *instead* — the construction that occupies the slot an em dash or bullet list would occupy in machine prose. Those `instead` references are what the rewrite rules will use as replacement material. Third, for every family where the author's choice is near-categorical — *for instance* but never *for example*, *a bunch of* but never *a number of* — record the members they never use in the pattern's `displaces` list. A rewrite substitutes those out; recording them costs one line while reading and saves processing from rediscovering the family against a corpus it will not have.

## Step 4 — Quantification

Turn every strong impression into a counter: a regex, or a `textstats.py` statistic or built-in counter referenced by name in `stat`, applied to every document, normalized per 1k words (or the unit that fits). Sanity-check each new regex on two documents by printing its matches — a counter that fires on link URLs, code, or an unrelated construction is noisy. Demote noisy counters to `measurement: judged` with the count estimated from reading, and say so in `note`; a judged pattern is still a pattern, it just cannot reach tier 1.

Measure every candidate over every document, including the ones where the reading did not notice it — coverage is what makes spread and tiers meaningful. Then write the pattern entries and run:

```sh
python3 scripts/styledb.py validate DB.json --fix --corpus-dir CORPUS_ROOT
python3 scripts/styledb.py tiers DB.json
```

`--fix` computes rates, spread, ranges, coverage, and tiers from the per-document data; `--corpus-dir` verifies every quote. Fix every error; read every warning.

## Step 5 — Review round

Open the round with a short list of specific questions, each with a recommended default, so that one reply can close it: the redactions made under rule 5 and every name still in a quote, the rows at a tier boundary or under a `register_scope`, the judged rows whose counts are reading estimates, and the decisions taken along the way. The rendered profile (`styledb.py render DB.json`) is the supporting material behind the questions, not the ask — on its own it is long and leaves the author guessing what to do with it. Feedback lands in these categories, each with a concrete effect on the DB:

| verdict | meaning | effect |
|---|---|---|
| WRONG | not my habit (topic effect, quoted material, a phase I left behind) | remove the pattern |
| OVERSTATED | I do this, but not that much | `tier_override` down, or restrict `range`; note why |
| MISSING | I do this and you did not catch it (author points at evidence) | add the pattern with the quotes the author points to, then count it |
| NEEDS_NUANCE | only in emails / only when explaining code | `review.verdict: nuanced`, restriction in `note` |
| CONFIDENTIAL | this quote (or this pattern's regex, or this `note`) must not be stored as it is | redact further, or replace the quote with another occurrence, or drop the pattern; the author's word is final |

The redaction questions come first — the author is the only one who knows which names and figures matter. Deliver the non-native error findings in the same list (see [german-l1-guidance.md](german-l1-guidance.md)): what was noticed, with the suggested English forms. They are feedback about the corpus, not negotiable pattern candidates — they stay out of the DB either way.

Automated reading reliably finds habits the author is unaware of; the author reliably finds habits the reading missed. Neither replaces the other, and only the reviewed profile is persisted as `review.status: reviewed`. If the author is not available for the round, persist with `review.status: pending`, say so in the handover, and treat the DB as usable but unreviewed — processing works from it, and the report of the first processing run is a good moment to hold the review.

## Step 6 — Persist

Build and validate in a scratch path, and write the destination once, at the end. Everything before the review round is a draft — patterns get dropped, tiers get overridden, quotes get redacted — and a half-built DB sitting at the user's default path is a profile that processing would read and rewrite from without knowing any better.

Writing that destination is the one step of an extraction that can destroy something the author cannot reproduce, because a reviewed profile is the product of their attention and not only of the corpus. When a file is already there:

1. **Say what it is before touching it.** `styledb.py info PATH` prints db_version, corpus size, review status and creation date in one line. "Refreshing your profile" is not a decision to make on the author's behalf, and a profile they reviewed in an earlier session is worth more than a fresh one they have not seen.
2. **Copy it to `<name>_old.json` beside the destination** (`user-style_old.json` for the default path), then write the new file. The backup is a one-step undo, not a history: the next refresh overwrites it, which is what it is for. If the author is not available to answer point 1, the backup is what makes proceeding safe — take it, write, and put both facts in the handover rather than stopping.
3. **Run `validate` on the written file**, not only on the scratch copy. If it fails, restore the backup and report: a corrupt profile at the default path breaks every later processing run, while a stale one only makes it less accurate.

Growing a profile is a different operation from replacing it. When the author has simply written more since last time, extract the new documents into a partial DB and `styledb.py merge` it with the existing one: the old evidence survives, rates and tiers are recomputed over the union, and `review.status` returns to pending so the round happens again. Because tiers follow coverage, count the existing patterns on the new documents as well — the two-phase rule of the parallel protocol below applies to an incremental extraction too, or the old patterns are demoted for missing counts they could have had. Replace when the corpus is being redrawn; merge when it is growing.

Then hand over: the profile rendered as markdown, the list of tier-1 patterns in one line each, the shortfalls (corpus size, unreviewed status, judged-only dimensions), and the exact command that re-renders the profile later.

Offer sealing as the last step: `styledb.py seal DB` drops the corpus paths, the DB's only reference into the corpus filesystem, once the review round has settled the redactions. Sealing removes the filenames that rule 5 cannot redact (a path can name a customer or a client project), and costs quote re-verification: `validate --corpus-dir` on a sealed DB checks nothing and warns. It is the author's call, so ask rather than seal by default, and skip it while the corpus is still growing — an incremental re-extraction wants the paths. [db-schema.md](db-schema.md) has the rules; `seal` refuses an unreviewed or partial DB.

## Parallel extraction with subagents

A large corpus (roughly 50,000 words or more — below that one agent reads everything and Phase B below is redundant — or documents long enough that two of them fill a context window) is extracted by several subagents in parallel, each producing a *partial* DB, merged with `styledb.py merge`. Because tiers depend on coverage, run it in two phases:

**Phase A — discover.** Partition the corpus into subsets of roughly equal word count (3–6 documents each). Each subagent runs Steps 3–4 on its subset and writes `partial-A-<n>.json` with `partial: true`, listing only its own documents in the manifest. Merge the parts: `styledb.py merge partial-A-*.json -o candidates.json --partial`. The merged candidate list is the union of everything anyone noticed.

**Phase B — count.** Give every subagent the *full* candidate list (every pattern's id, description, and counter) and its subset of documents again; it measures every candidate on every document in its subset and writes `partial-B-<n>.json`. Merge again, this time without `--partial`, run `validate --fix --corpus-dir`, and proceed to the review round. Skip Phase B only when the corpus is small enough that one agent counted everything (then Phase A already has full coverage).

The subagent brief for either phase carries: the taxonomy and db-schema references (paths), the founding rules above (rules 5 and 6 spelled out — subagents copy quotes, so they are where redaction happens and where topic vocabulary would slip in), the document subset with ids and registers, the phase (discover or count), the candidate list for Phase B, the output path, and the instruction to run `styledb.py validate --corpus-dir` on its own part before finishing. Subagents never write the final DB path; the orchestrating run merges, validates, reviews, and persists.

## Maintainer note: the AI corpus

The AI DB is built with the same steps from a corpus of machine-generated documents: diverse model families and agent products, genre-matched to expected inputs (technical posts, documentation, reports), roughly 15–30 documents, including both plainly-prompted and style-prompted generations so that only markers surviving prompting variance are kept. The maintainers are corpus owners and reviewers; the completeness check runs against an external catalog of AI-writing signs, and catalog patterns absent from the corpus are either provoked with additional corpus tasks or entered at tier 3. The manifest records which model or agent produced each document (`generator`), and the DB is refreshed when a new model generation visibly shifts the distribution.

Three of the steps read differently for this corpus. Step 2's vetting is provenance, not authenticity: the `generator` field, taken on the maintainers' word, and a document produced by more than one model is `sole_authored: false`. Rule 4 yields no absence patterns — across a multi-model corpus nothing is exactly zero — so a near-absent tell (summary openers, sentence-initial *Furthermore*) is a tier-3 presence row whose note says that its presence in a draft marks older-generation output and its absence proves nothing. Rule 5 keeps people's names out of the quotes as usual, but product names may stay, because the corpus itself ships in the repository and the DB adds no exposure; for the same reason the DB is not sealed — its paths point into the public corpus, and re-verification wants them.

The first extraction (August 2026, 23 documents) ships at `data/ai-style-patterns.json`. Its corpus recorded the generator per document but not the prompt style, and its one email thread carries a fifth of the words; the plainly-prompted vs. style-prompted split and shorter email threads are the open items for the next refresh.
