# Processing procedure

Processing rewrites AI-generated text toward the author's voice, as the step *before* the author's own polish, never as a replacement for it. It reads the author's DB and the skill's AI DB (`data/ai-style-patterns.json`) and never writes either. Vocabulary is defined in [taxonomy.md](taxonomy.md) and [db-schema.md](db-schema.md); the mode rules, DB lookup, and strictness settings are in SKILL.md.

The stance that makes it work: the author's DB has veto power over every edit. Where the input already matches the author, nothing moves — even when the AI DB flags the construction as machine-typical. An author who genuinely writes with em dashes keeps them. And every rewrite targets the author's *rate*, never zero and never "always": the guard against caricature.

What that looks like in practice: the profile is a region in style space (SKILL.md), the input arrives with coordinates of its own, and processing moves the ones sitting outside — each in whichever direction it is off. Taking out what the machine put in is only half of that; the other half is bringing in what the author would have written instead, because a draft stripped of its machine tics still does not sound like anyone in particular. The two halves appear throughout as *remove* rows and *add* rows.

## Tone steering

Strictness and tone are the two dials of a processing run. Strictness says how much corpus evidence an edit needs (the settings are in SKILL.md); tone says which end of the author's own range to aim for. Most runs use neither: with no tone request the profile's rates are the targets, as they always were.

When the request does name one — "more formal", "warmer, less clinical", "keep it factual but friendly" — write it down before Step 2 as a **tone brief**: the axes it names, where the author wants this document on each, and one sentence of intent.

```
Tone brief: formal ↔ colloquial → slightly colloquial; factual ↔ warm → warm.
In one sentence: a friendly release note that still reads like docs.
```

Axes to offer when the request is vague: formal ↔ colloquial, factual ↔ warm, terse ↔ expansive, cautious ↔ assertive, plain ↔ playful. They are prompts for thinking, not an enum — a description that fits none of them is used as written, because the brief's job is to guide judgment, not to be looked up.

Four rules keep the brief inside the author's voice:

1. **The profile decides what is available; the tone decides which of it to prefer.** No tone request introduces a construction the profile has no evidence for — asking for formality does not hand a formal connective to an author who has none. The fallback is the one used everywhere else: the nearest attested form, or leave it and flag. It is also what keeps the grammar guarantee of Step 3 intact under tone: the DB stays the only source of replacement material, so no brief can reach a non-native form the DB does not hold.
2. **Tone moves a target inside the range, never outside it.** The DB carries per-document counts and each document's register, so "toward the formal end of your own writing" is measurable rather than imagined: take the sub-range of the documents whose register matches the requested pole and aim there instead of at the corpus rate. Where the tone would need a value the corpus never reaches, the profile cannot support the request — say so in the report instead of inventing the register.
3. **Absence patterns hold under every tone.** The do-not-introduce list is not negotiable: a warm brief is no licence for the exclamation marks the author never writes.
4. **Tone may move a do-not-touch row, within the range.** The veto answers "is this machine voice?", not "is this the register the author asked for", and an explicit request outranks it. Every row moved this way is named in the report, so the override is visible rather than silent.

Where the brief does its work: choosing which of the author's habits to bring in on add rows (Step 2), breaking the tie when a rule has two attested forms to pick from (Step 3), and every judged decision the rules leave open — hedging, warmth, jokes, sentence length, how a section opens and closes (Step 5). Carry it into Step 6, where convergence chases the shifted targets and not the corpus rates — otherwise the convergence pass quietly undoes the tone — and into every chunk subagent's brief, or the chunks drift apart in register.

## Step 1 — Measure

Run the counters over each input document (per document — different generators leave different marks, and the report is aggregated afterwards):

```sh
python3 scripts/textstats.py measure INPUT.md --db USER_DB.json --db data/ai-style-patterns.json --sort-gap --setting medium
```

`--setting` takes the strictness the request implies (SKILL.md), and the two flags add the columns Step 2 is built from — they cost nothing here, and one run is better than two.

The output has two parts: the built-in stats and counters, and every measurable DB pattern — the author's and the AI DB's — with the input's value, the DB rate and range, and a verdict. The AI DB's rows print without class or gap: their rates are the machine's, so `match` there means machine-typical, and they feed the AI-evidence column of Step 2 instead of being rewrite rows. The author-DB verdicts:

| verdict | meaning |
|---|---|
| `match` | the input is where the author would be |
| `gap` | outside the author's per-document range — the input does far more of this than the author, or far less |
| `absent` | the input has none of a habit the author shows in most of their documents (spread at least 60%). It earns a verdict of its own because a single corpus document without the habit puts 0 inside the range, which would file the strongest add rows under `low` and leave them alone |
| `low` / `high` | inside the range but under half or over twice the author's rate — a habit the author has, just not in every document |
| `too-short` | the input is too small for this rate to predict even one occurrence, so no count in it is evidence either way (see Short inputs, Step 2) |

Judged patterns (no regex or stat) get no verdict, but they are not missing: `measure` lists them under **read for these** at the end of each DB's block, with tier and description. Read the input for every name on that list and note your estimate. That list is the checklist Step 2 and the report answer to — a judged pattern is never dropped for being absent from the table.

## Step 2 — Three-way comparison table

Rows are patterns (and any built-in AI counter with a striking value), columns are AI evidence, input, author DB — each with rate and one example. Most of it is already on the screen: `--sort-gap` and `--setting` classified every measurable row, ordered them by gap, and applied the tier ceiling in Step 1's run.

**Gap** is the size of the edit a row asks for: how far the input sits from the author's rate, counted in occurrences of *this* document — ten sentences short of their short-sentence share, six em dashes to take out. Rows a rewrite has no business touching read 0, so the work is everything above them. It is a per-row number and never a document score: the axes measure different things, and a document has no single distance to the author (SKILL.md).

**Class** is what a rewrite would do with the row:

| class (verdict behind it) | action |
|---|---|
| do-not-touch (`match`) | none; list it in the report. Only an explicit tone request moves such a row |
| remove (`gap` above the author's range; for an absence pattern, any occurrence at all) | rewrite down to the author's rate, at the confidence the AI evidence gives it — below |
| add (`absent`, or `gap` below the range) | bring the habit in toward the low end of the range — by substitution wherever the family already appears, by manufacture only for a tier-1 pattern in a slot another rewrite opened |
| lean (`low` or `high`: the habit is there at the wrong intensity) | substitute where the family appears; move toward the rate only where the rewrite of another row opens a natural slot (a "So" where a formal connective came out); never manufacture occurrences |
| neutral (`too-short`, or nothing measurable) | none |

Three things the counters cannot see, and the table is not built until they are in it:

- **The AI-evidence column**, which splits every remove row by confidence. *High*: the construction is AI-typical — an AI DB row, a built-in `ai_*` counter, or the author's own absence pattern (rate 0, and any occurrence of one is high-confidence by rule). *Low*: no AI evidence, so the excess could be a generator quirk outside the AI corpus or an effect of the topic — rewrite it only when the author pattern is tier 1 (tier 2 in the hard setting), otherwise flag it for the manual pass. `[manual]` marks the setting's own ceiling; this stricter one is yours to apply.
- **Judged patterns**, which carry no regex or stat and so get no row in the script's table — only a name on its *read for these* list: place each of them by reading, with the estimate from Step 1 and the same five classes.
- **An example per row**, from the input and from the pattern's evidence quotes. Step 3 writes rules against examples; numbers alone produce rules that match the wrong thing.

Remove rows and add rows together are the *rewrite rows*: the ones that earn a rule in Step 3 and have to converge in Step 6.

**Substitution and manufacture.** There are two ways to close an add row, and only one of them risks caricature. *Substitution* is switching a family member the input already uses for the one the author uses: `-ize` where the author writes `-ise`, *for example* where they write *for instance*, *a number of* where they write *a bunch of*, *Therefore* where they write *So*. It adds nothing to the text — the slot was already filled, only in someone else's voice — so it applies wherever the family appears, at any tier the setting allows, and on `lean` rows too: a `low` verdict is no reason to leave the machine's member standing. *Manufacture* is creating an occurrence where the input offers no slot: dropping a "So" opener into a paragraph that never pivots. That is what turns a voice into a parody of itself, so it takes a tier-1 pattern and a slot some other rewrite has opened anyway. The pattern's `displaces` list names the forms to substitute out; where it is empty, the evidence quotes show the author's form and reading the input finds its counterpart.

**Short inputs.** Rates quantize: in a document of N words one occurrence is worth 1000/N, so a habit the author's rate predicts less than once here is no target in either direction — `measure` marks those rows `too-short`, and they are neither rewritten nor converged. In a 64-word note that is most of a profile: an author's 3.2-per-1k *So* predicts 0.2 occurrences, and putting one in would land the note at 15.6, five times their rate — the corner of the region, reached by following the procedure. What still applies at any length is every absence pattern, because zero is expressible in one line; the judged and discourse patterns, which are read rather than counted; and the few habits frequent enough to show up in a paragraph — first person, contractions. Rows the profile measures per document rather than per 1k words (list and heading densities) describe documents, and a note is not one: leave them.

The strictness setting arrives applied: `[manual]` marks every row with an action — remove, add, and lean alike — whose effective tier (the review round's override, else the derived one) is above the ceiling, soft 1 / medium 2 / hard 3. Those rows go in the report as "left for the manual pass", so the author sees what a harder setting would have touched. Do-not-touch and neutral rows never carry the mark; the setting has nothing to gate where no edit was going to happen anyway. The ceiling is the whole of what the setting does — every row below it is worked to its target in both directions, and the only thing that stops one short is the absence of a slot (Step 3). What is left for you is the tone brief: it picks the target inside each row's range, and may add do-not-touch rows to the work (rule 4 above).

## Step 3 — Rule derivation

One mechanical rule per rewrite row: *what to find, what to replace it with, how many to leave*. On an add row the three parts point the other way — what to find is the family member the author does not use (their `displaces` list) or the slot another rewrite opened, what to put there is the author's form, and the number is how many to reach rather than how many to leave.

The replacement construction comes from author-DB evidence — the pattern's own quotes, its `displaces` list, or the `instead` references of an absence pattern — never from invention. What a quote supplies is the *form*, never the words: transplanting a clause or a sentence out of the corpus imports the claim it made in its own document, which is a new claim under Step 4 and stays one when the corpus document happens to share the input's subject. If the DB offers no replacement (an absence pattern without `instead`, an evidence list that shows the habit but not a substitute), the rule is "remove where the sentence survives removal, otherwise flag", not "make something up". Where the profile attests two forms and the rule has to pick one, the tone brief breaks the tie; with no brief, take the more frequent form and note the choice.

**Where substitution ends and manufacture begins.** Manufacture is new *content*: a claim, a number, an incident, an example, an opinion the input did not carry. Everything short of that is substitution — re-punctuating a clause into a parenthetical aside, contracting a verb, splitting or joining sentences, swapping a connective for one the pattern's `instead` or `displaces` names, moving where a sentence puts its weight. A substitution lands in a slot the input already offers or in one a removal has just opened (the `So` that takes the vacated `However`'s place is a substitution; the same `So` opening a sentence that had no connective is not). The strictness setting does not move this line: it decides which rows are eligible, not how hard an eligible row is worked, so a soft pass works its tier-1 add rows with every slot the input gives it and reports the shortfall only when the slots run out. A light touch is a shorter list of rows, never a lighter hand on each.

Because rules come only from the DB, non-native grammar errors can never enter a rewrite: extraction keeps them out of the DB by design ([german-l1-guidance.md](german-l1-guidance.md)), so there is nothing to apply — and a request to write "with all my quirks" cannot widen that, since processing has no source for such forms. Where the input itself contains one, leave it (fixing grammar is outside this skill's scope) and note it in the report.

Targets are rates: for an em-dash row with author rate 0.4/1k and range 0–1.1, the rule leaves roughly 0–1 per 1,000 words in place, choosing the ones that read most like the author's own uses. A tone brief shifts that target within the range (see Tone steering above); a pattern with a `register_scope` is a target only for an input in one of those registers: an emails-only sign-off is not a target for a blog post.

## Step 4 — Invariants

Always: facts, numbers, links, citations, quoted material, code, tables, section order and headings, block sequence within every section, list item counts — and no new claims. Rewriting is rearranging the author's material, not adding to it: the rewrite moves the text along the style axes and nowhere else. `scripts/structure_check.py ORIGINAL REWRITTEN` enforces the structural part mechanically; the factual part (no new claims, no lost qualifications) is yours to check by reading the diff.

Subject vocabulary is content, not voice (rule 6 in [technique.md](technique.md)), so it is an invariant too: technical terms, product, library, and tool names, people's names, and code identifiers stay exactly as the input has them — not synonymized, not expanded, not abbreviated, not re-cased. The author's profile may say *how* such material is presented (`code-reference`: backticks vs. prose; `abbreviation`: "PRs" vs. "pull requests") and a rule may move an identifier into backticks or spell out an initialism the author never abbreviates; it never replaces the term itself. `structure_check.py` checks inline code spans mechanically (an identifier that vanished from its backticks is an error); names and terms in plain prose are checked by reading the diff. No rewrite row ever targets a term: a `favourite-word` or `author-specific` pattern whose word turns out to be a term of the input's subject is a topic effect — skip it and say so in the report.

Paragraphs: keep the paragraph count of every section where possible. Merging or splitting a paragraph is allowed only when the author's paragraph-shape patterns demand it (a tier-1 one-sentence-paragraph habit against a wall of five-sentence paragraphs) — `structure_check.py` reports it as a warning so the report can say where and why.

**Person is voice; agency is fact — and that binds in both directions.** First person is a style axis like any other, and moving a draft onto it is ordinary work: narration, opinion, evaluation and hypotheticals take the author's `I` wherever the rate asks for it. Who performed a stated action or took a stated decision is not on that axis — a team's *we stopped mocking the filesystem* stays the team's, and rewriting it to *I stopped* is a changed claim wearing a style change's clothes, however far the first-person row still sits from the author's rate. Nothing outside the input settles who acted, either: a corpus document covering the same episode is evidence about the author's forms, never about this draft's facts, so it cannot be cited to reassign an action.

The two failure modes are symmetric and both are capped:

- **Buying the rate with the facts.** The rewrite leaves the group at least as many stated actions as the input gave it. A conversion that ends with the first-plural row inside the author's range and the team gone from the body has moved a fact, and saying so in the report does not turn it back into a style edit.
- **Spending the licence on the whole row.** "Every action here belongs to the team" is a reason for the *remainder* of the row, never for skipping it. Every narration, opinion, evaluation and hypothetical still converts; what is left over is then named as a row left short, with the count it reached against the count the range asked for (Step 6). A run that ends with the first-singular row still `absent`, or the first-plural row still above the author's range maximum, has not worked the row — it has declined it, and the report says so in those words.

Input-specific invariants: ask once, up front, which earlier manual decisions must survive — kept phrasings, a table, a closing sentence. In an iterating workflow this is what prevents the rewrite from undoing the author's previous polish. If the user is not available, treat any passage that already reads like the author (verdict `match` at the sentence level) as protected.

## Step 5 — First pass: whole-body rewrite

Rewrite each document in one pass with the full rule set in view. Rhythm, paragraph openers, and discourse-level habits (story-first, concession, digression-and-return) do not respond to sentence patching — they need the whole section rewritten with the author's shape in mind. This is also where the add rows and the tone brief land: a habit introduced sentence by sentence reads pasted on, while a paragraph written from the shape outwards carries it with no seam to notice. Hold the invariants while doing it; the structure check afterwards is a net, not the plan.

## Step 6 — Convergence

Re-run the identical measurement on the rewritten text, plus the structure check:

```sh
python3 scripts/textstats.py measure INPUT.md REWRITTEN.md --db USER_DB.json --sort-gap --setting medium
python3 scripts/structure_check.py INPUT.md REWRITTEN.md
```

Class and gap stay pinned to the first file, so every row keeps the identity it had in Step 2 while the rewritten column moves — a remove row that now reads `match` is done, not reclassified. One caveat on `match`: it says the row's *counter* is at the author's rate, not that the habit is satisfied. Where the counter enumerates forms — a spelling list, a phrase list — it sees only the members it names, so before calling such a row done, read for the ones it does not (the `-ize` the spelling regex never listed). `measure` marks those rows `[enum]`.

Drive targeted edits from the deltas — each a uniqueness-asserted replacement of one passage — until no rewrite row still reads `absent` or `gap` (every remove row back to `match`, every add row inside the range), and the structure check reports no errors. Rows reading `too-short` are not convergence targets — the input cannot express them, and forcing one lands past the author's own rate. An add row that comes to rest inside the range but `low` is converged when the input simply offered no more slots; say which rows those were. Where a tone brief is in force the targets are the shifted ones, not the corpus rates — chasing the rate here is how a convergence pass undoes the tone. Check overlong sentences against the author's `long-tail` share, and the word-count change (turning fragments into sentences or the reverse shifts it) against reason. Stop when the remaining gaps are all in rows you deliberately left, or when a further edit would need invented material — and name those rows in the report, each with the reason it stopped there. A row still outside the author's range is not a converged row, so no report calls a run converged while one stands unnamed. That is the soft setting's own failure mode: a light touch legitimately leaves the tier-2 rows alone and legitimately says so, while the tier-1 rows it was allowed to move still have to move or be named. Two or three rounds are normal; more than five means a rule is wrong — revisit Step 3 rather than pushing harder.

**The structure check is a gate, not advice.** A non-zero exit means the rewrite changed the document rather than its voice: it is not deliverable, the fix is always to the rewrite, and no note in the report substitutes for one. No profile row licenses a structural change — `measure` marks the rows this is about `[structural]`, the `lists` and `headings` dimensions, which record what the author writes where the shape was theirs to choose and say nothing about the shape an input already has. Where such a row and the structure disagree, the row is inapplicable to this input and goes to the report as such, next to the register-scoped rows. Warnings are the other case and do ship: a paragraph split or merge that the author's own shape patterns justify, with the report saying where and why.

## Step 7 — Verification and handover

Where the rewrite goes follows the input. Text that lives in this session — pasted by the author, or drafted here in the conversation — comes back in the reply, printed once in full for proofreading: making a file out of text that never was one hands the author a chore. A file input gets `<name>.styled.<ext>` written beside it (never overwrite the input unless asked), and the reply says where it landed.

How much report it carries follows the length. A document gets the full report below. A short input — a note or a message rather than a document, where most of the profile's presence patterns came back `too-short` — gets one line instead, with the report itself available on request:

```
medium setting, no tone brief; dropped the em dash and "it's worth noting", kept your colon.
11 of 24 patterns need a longer text to measure. Full report on request.
```

A twelve-row before/after table under a rewritten chat message is noise, and noise is what stops an author reading the handover at all. Nothing is hidden by it: everything the full report would have said — the dropped rows, the `too-short` rows, the judgment calls — is still there to give when asked.

Every figure in the report is this run's own measurement of the file actually delivered — the `measure` after the last edit, not a number from an earlier convergence round and not one counted by eye. `textstats.py measure INPUT REWRITTEN --db USER_DB.json --db data/ai-style-patterns.json --setting SETTING --report-table` prints the measured sections — the before/after table with its AI-evidence column, the do-not-touch list, the manual-pass list, and the judged patterns as a checklist — as markdown to paste. What it cannot know stays yours to write: the not-converged rows and their reasons, the side effects, the open questions, and the example per row.

The full report, for anything longer:

```
# write-like-me report — <document name>

Setting: <soft|medium|hard>; tone: <brief in one line, or "none — profile rates">; profile: <path>, db_version <n>, review <status>.
<only when the profile carries corpus.register_weights: "Author rates are register-weighted (<shares>): balanced across the corpus's registers rather than pooled by its word counts. The ranges are not — they are the measured per-document band.">

## Before / after
| pattern | direction | tier | AI evidence | input | rewritten | author rate (range) | verdict |
...

## Do-not-touch (input already matched the author)
- ...
- moved for tone: <pattern> — <what the brief asked for>

## Left for the manual pass
- <pattern>: <why — tier above setting / low confidence / would have needed manufacture / no replacement in the DB>

## Not converged (rewrite rows that came to rest outside the range)
- <pattern>: <rewritten value vs. the range> — <no slot / would have needed manufacture / held back by an invariant>

## Side effects
- word count <n> → <m> (<why>)
- paragraph count changes: <section: n → m, why> or none
- structure check: <n> error(s), <m> warning(s)

## Open judgment calls
- <passage>: <what the rule wanted vs. what reads right>
- tone: <what the brief asked for that the profile has no register to support> or none
```

Direction is `add` (a habit of the author's that the input lacked), `remove` (something the input carried that the author does not, or not at that rate), or `keep` (a row moved only for tone) — the column exists so the author can see at a glance that the rewrite did more than subtract.

AI evidence is the confidence behind a remove row, from Step 2: `high` where the AI DB, a built-in `ai_*` counter, or one of the author's own absence patterns backs it, `low` where nothing machine-side does, `—` on every row that is not a removal. It is a column of the table and not a sentence underneath it, because a removal without it is a removal resting on intuition.

Every judged pattern in the profile appears somewhere above — a row of the table, the do-not-touch list, the manual-pass list, or the not-converged list. They carry no counter, so nothing else would notice their absence.

Say honestly what did not converge, in one line or in twenty.

## Chunking large inputs with subagents

A long document (more than ~3,000 words, or several documents in one request) is processed by section: the orchestrating run does Steps 1–4 on the whole document — measurement and rules are per document, not per chunk — and hands each subagent one chunk of whole sections plus the same rule set, the tone brief verbatim, the invariants, the do-not-touch list, and the instruction to return only the rewritten chunk with headings intact. Never split inside a section, and never let a subagent see the rules for a different setting than the one in force, or a paraphrase of the brief instead of the brief — chunks written to slightly different instructions read as slightly different people. Reassemble in order, then run Steps 6–7 on the whole document — convergence is measured on the assembled text because rates are per document, and a chunk can look converged while the whole does not.

Extraction has its own parallel protocol; see the last section of [technique.md](technique.md).
