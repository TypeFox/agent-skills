# Style-pattern DB format

The DB is JSON, written only by extraction (`styledb.py init` and `count`), by `merge`, by `review`, and by `seal`, read by processing. Users never edit it; `scripts/styledb.py render` produces the human-readable profile whenever someone needs to see what is in it. `scripts/styledb.py validate` is the authority on what is legal; this document explains the fields and the rules behind them.

## Versioning

`db_version` is an integer format version. The skill's current value is `CURRENT_DB_VERSION` in `scripts/styledb.py` (currently 1). `styledb.py info DB` compares the two and exits 0 (same), 2 (DB older — apply [migration.md](migration.md)), or 3 (DB newer — the skill must be updated before the DB is used). Both modes run this check before reading a DB.

Bump the version when an old DB would be read incorrectly by the new skill: a renamed or removed field, a renamed or removed taxonomy dimension, a change in what a `unit` means, or a change to the tier rules that must be applied uniformly. Do not bump for additive changes (new optional fields, new markers, new dimensions). Every bump adds a section to migration.md.

## Locations

- User DB default: `$HOME/.agents/write-like-me/user-style.json`. Voice belongs to the person, not to a project, so the default is user-scoped. A request can name another path ("use the profile at …"); the named path then wins for that invocation only.
- AI DB: `data/ai-style-patterns.json` inside the skill (shipped with the skill; see the README in `data/`).
- Partial DBs from parallel extraction: anywhere the orchestrating run chooses (a scratch directory), merged into the final path with `styledb.py merge`.
- `<name>_old.json` beside a destination that already held a profile: the previous file, kept by extraction as a one-step undo before it overwrites (Step 6 of [technique.md](technique.md)).

## Header

```json
{
  "db_version": 1,
  "kind": "user",
  "partial": false,
  "created": "2026-08-28",
  "tool": "write-like-me",
  "corpus": {
    "documents": [
      {"id": "blog-fs-mocks", "path": "posts/fs-mocks.md", "date": "2019-04-02",
       "words": 1180, "register": "article", "sole_authored": true, "vetting": "confirmed"}
    ],
    "total_words": 1180
  },
  "review": {"status": "reviewed", "date": "2026-08-28", "reviewer": "the author"},
  "patterns": []
}
```

| field | meaning |
|---|---|
| `kind` | `user` or `ai` |
| `partial` | true for a subagent's partial result that still awaits merge; processing refuses partial DBs |
| `corpus.documents[].id` | stable slug, used by every `documents[]` and `evidence[]` entry |
| `corpus.documents[].path` | optional: path relative to the corpus root the DB was built from; needed for `validate --corpus-dir` quote verification, otherwise informational. `styledb.py seal` drops it — see [Sealing](#sealing) |
| `corpus.documents[].words` | word count as `textstats.py` counts it — rates are normalized against this number, so use the script, not an editor's count; `styledb.py init` writes it and `count` refreshes it |
| `corpus.documents[].register` | document type: `article`, `email`, `docs`, `note`, `thesis`, … (free string, consistent within a DB) |
| `corpus.documents[].sole_authored`, `vetting` | intake facts: sole-authored flag; vetting outcome `confirmed`, `certified` (recent, author certified as hand-written), or `dropped`; `pending` is what `styledb.py init` writes until Step 2 of technique.md records the outcome, and `validate` warns while it stands |
| `corpus.documents[].generator` | for `kind: ai`: the model or agent product that produced the document, as the maintainer note in technique.md requires; `validate` warns when an AI corpus document lacks it |
| `corpus.sealed` | date the DB was sealed, meaning every `path` has been dropped on purpose; absent while the DB still carries paths |
| `corpus.register_weights` | optional: register → the share of every pooled rate that register carries, when the author asked for the corpus to be balanced by register instead of by words. Absent means pooled by words. See [Register weighting](#register-weighting) |
| `review.status` | `pending` until the author has walked through the rendered profile, then `reviewed` |

## Register weighting

A corpus is rarely balanced: a thesis, a year of blog posts and a handful of emails put wildly different word counts behind each register, and because rates are corpus-normalized the biggest source defines the profile. `corpus.register_weights` is the answer to "weight my registers equally" (or "count the dissertation for a quarter"):

```json
"register_weights": {"article": 1, "email": 1, "docs": 1}
```

The numbers are **shares, not multipliers**. Each register's rate is the word-weighted mean of its own documents, and the corpus rate is those per-register rates averaged by share — so equal shares make 400 words of email count as much as 40,000 words of thesis, and shares proportional to the registers' word counts reproduce exactly the unweighted number. Every register the corpus carries must be named: `validate` reports an omission as an error, because an unnamed register falls back to share 1 and a partial weighting is a silent one.

**A weighting moves `rate` and nothing else.** `spread`, `range`, `coverage`, `registers` and every tier rule count documents, and they stay unweighted on purpose: a weight says how much a register should define the author's *target rate*, never how well a habit is *evidenced*. Two consequences worth knowing before setting one:

- it cannot promote anything. A thin register stays thin evidence, so weighting is not a way to talk a two-document habit into tier 1;
- processing converges on `range`, the measured per-document band, which a weighting does not move. It shifts where inside that band a rewrite aims, not how wide the band is.

For a pattern with a `register_scope` the weighting is a no-op — inside one register every document already carries the same share.

It is one decision about the whole corpus, so it belongs on the finished DB rather than on the parts: `merge` unions the weightings of its inputs and refuses a register with conflicting shares, and `validate` warns when a `partial` DB carries one. `styledb.py info` prints it, and `render` says on its corpus line that the rates below are weighted — a reader who does not know that would take them for word-pooled numbers.

## Pattern entries

```json
{
  "id": "punctuation/em-dash",
  "dimension": "punctuation",
  "marker": "em-dash",
  "description": "Never uses em dashes; asides go in parentheses, consequences after a colon.",
  "kind": "absence",
  "measurement": "counted",
  "stat": "em_dash",
  "unit": "per_1k_words",
  "documents": [{"id": "blog-fs-mocks", "count": 0}, {"id": "email-release", "count": 0}],
  "evidence": [],
  "instead": ["punctuation/parenthetical-aside", "punctuation/colon-elaboration"],
  "rate": 0.0, "spread": 1.0, "range": [0.0, 0.0], "coverage": 1.0,
  "registers": ["article", "email"],
  "tier": 2, "tier_reason": "counted as absent in the measured documents (partial coverage or small corpus)",
  "tier_override": null,
  "review": {"verdict": "confirmed", "note": ""},
  "note": ""
}
```

| field | meaning |
|---|---|
| `id` | `dimension/marker`; dimension must be in the taxonomy, marker is free but should use the taxonomy's standard name when one exists |
| `description` | one sentence that defines the habit plainly; this is what the rewrite rule is derived from, so say what the author does, not only what they avoid |
| `kind` | `presence` (the author does this) or `absence` (the author does not — the do-not-introduce list). An absence tolerates a few residual hits and is then *near-absent*: under 0.1 per 1k measured words, in at most a fifth of the measured documents (`NEAR_ABSENCE_MAX_RATE` and `NEAR_ABSENCE_MAX_SPREAD` in `styledb.py`; per-1k unit only). Any more and the row is a presence — `validate` enforces the line — and what the hits are belongs in `note` for the review round. The line matters in the other direction too, and there `validate` only warns: a *presence* row whose numbers land inside the same tolerance is a habit the author almost never has, and the presence tier rules below read that rarity as weak evidence — low spread, tier 3, out of scope on the medium setting — while the same numbers under `absence` are near-absent and tier 2. Which side a rare habit belongs on is the author's call and usually visible in the description ("bold is rare" is a presence; "never bolds a whole clause" is an absence written on the wrong side), so the warning is review-round material and never a `--fix` |
| `measurement` | `counted` when a regex or stat produced the numbers; `judged` when reading produced them and the counts are estimates. Counted beats judged in tiering because judged rates drift |
| `regex` / `stat` / `ignore_case` / `exclude` | the counter: a regex, or in `stat` the name of a statistic or built-in counter from `textstats.py counters` — `validate` rejects unknown names, a built-in counter with a unit other than `per_1k_words`, and a statistic under a unit that is not its own (`STAT_UNITS` in `textstats.py`), and warns when a counted pattern has neither. `measure --db` evaluates it on any input, so DB rates and input rates use the same definition. Absent for judged patterns. `exclude` is a regex whose matches subtract: a counter hit that overlaps one is not counted, which takes a known false positive (`This is (?:caused\|done) by` under `ai_verdict_opener`) out of a noisy counter instead of demoting the row to judged; it needs a regex or a built-in counter to subtract from. A regex tested with `textstats.py hits -i` carries `ignore_case: true` |
| `unit` | `per_1k_words` (default), `share_of_sentences`, `share_of_paragraphs`, `share_of_headings`, `words` (for length stats), `count` |
| `documents[]` | per-document evidence, keyed by the unit: `per_1k_words` carries `count`, the raw occurrences; every other unit carries `rate`, the per-document value in that unit (`count` optional). A per-1k statistic (`list_items_per_1k`) is filed under `per_1k_words` with the raw item count as `count`; `validate` rejects an entry without its unit's field. `styledb.py count` writes these from the corpus. They are measurements, not estimates: for a `counted` pattern `validate --corpus-dir` re-runs the counter over each document and reports an entry the corpus does not reproduce, because everything derived — `rate`, `range`, `spread`, and through them the tier — is computed from these numbers. One entry per document *measured*; a document with no entry was not measured for this pattern, which lowers coverage. For a judged pattern an entry with `count: 0` asserts that the document was read in full for this habit and shows none of it — a document not read for it gets no entry |
| `evidence[]` | verbatim quotes, each `{"doc": <document id>, "quote": "…"}`. Required for presence patterns; `validate --corpus-dir` checks each quote appears in its source; a source that `--corpus-dir` does not reach is an error rather than a warning, since a run that verified nothing must not look like a run that verified everything. An entry with `"redacted": true` had confidential content replaced by a bracketed placeholder (`[colleague]`, `[company]`, `[product]`) under rule 5 of technique.md; the validator skips the verbatim check for it and warns if no placeholder is present. Absence patterns carry none — their evidence is the zero counts |
| `instead` | for absence patterns: ids of the constructions the author uses where the absent one would appear. The rewrite rule takes its replacement from these, never from invention |
| `displaces` | for presence patterns: the word forms the author does *not* use in the slot this pattern fills (`["for example", "e.g."]` under a *for instance* pattern). The mirror of `instead`, and what makes a rewrite a substitution the DB can point at instead of a family processing has to rediscover by reading a corpus it no longer has |
| `register_scope` | optional list of registers a pattern is confined to (an email sign-off, the meta-signposts of a talk abstract). The derived fields and the tier are computed over the corpus documents of those registers only, and the tier-1 register condition is waived — otherwise a habit near-obligatory in one register never leaves tier 3, because spread is corpus-wide. Processing treats such a pattern as a target only for an input in one of those registers |
| `rate`, `spread`, `range`, `coverage`, `registers` | derived over the corpus documents (or the `register_scope` ones); recomputed by `validate --fix` and by `merge`. `rate` is corpus-normalized (total count / total measured words × 1000 for per-1k units, word-weighted mean otherwise; the register-weighted mean instead when the manifest carries `corpus.register_weights`); `spread` is the share of measured documents where the pattern occurs (for absences: where it is absent); `range` is the min–max per-document rate and is the convergence target band in processing; `coverage` is measured documents / corpus documents |
| `tier`, `tier_reason` | derived evidence tier, see below |
| `tier_override` | set by the review round; wins over `tier` |
| `review` | verdict from the review round: `confirmed`, `overstated`, `nuanced` (with the restriction in `note`), or absent if not reviewed. `validate` rejects any other verdict; a reviewed DB needs `review.date` and `review.reviewer` in the header and warns about rows without a verdict. `styledb.py review` writes all of it from a verdict file |
| `note` | free text: counter caveat, model split, anything the next reader needs |

## Evidence tiers

Tiers order patterns by how much corpus evidence stands behind them, and processing uses them as the strictness dial: **soft** applies tier 1 only, **medium** (default) tiers 1–2, **hard** all three. The tier says how *sure* the DB is that a habit is the author's voice; it says nothing about how *large* the habit's gap to the input is — the processing table sorts rows by that gap and marks the ones the ceiling drops, both from `textstats.py measure --sort-gap --setting`. `styledb.py tiers DB` prints the computed tier and the reason per pattern.

Presence patterns:

| tier | rule |
|---|---|
| 1 | counted; measured in every corpus document (coverage 1.0); present in at least 60% of them and in at least 3; seen in at least 2 registers (or the corpus — or the pattern's `register_scope` — has only one); at least 3 verbatim quotes |
| 2 | present in at least 2 documents, spread at least 40%, at least 2 quotes — and at least one tier-1 condition unmet |
| 3 | everything else that still has one quote |

Absence patterns:

| tier | rule |
|---|---|
| 1 | counted as zero in every document, corpus of at least 3,000 measured words |
| 2 | counted as zero in every measured document, but coverage below 1.0 or fewer than 3,000 words; or near-absent (see `kind`) with at least half the documents counted — the default for a near-absence, which the review round moves with `tier_override`: 1 removes it at every setting, 3 only on the hard one |
| 3 | absence asserted without a corpus-wide count |

Why tiers work as the strictness dial: a low-evidence pattern is exactly the one most likely to be a topic effect or a single-document quirk, so applying it risks caricature — rewriting toward a habit the author does not actually have. Restricting a soft pass to tier 1 removes that risk at the cost of leaving more of the machine voice in place. Two consequences to keep in mind: (1) tiers must be *derived*, not authored, so that a merge with more documents can promote or demote a pattern — never hand-edit `tier`, use `tier_override` and say why in `review.note`; (2) the do-not-touch classification in processing is independent of tiers: where the input already matches the author, nothing is rewritten regardless of setting.

## Merge semantics

`styledb.py merge A.json B.json … -o OUT.json` produces one DB from several partial ones (same `db_version`, same `kind`):

- corpus documents are unioned by id; the same id with different word counts is an error (the parts measured different files under one name); `register_weights` are unioned too, and a register the parts weight differently is an error — a weighting is one decision about the whole corpus;
- patterns are unioned by id; `documents[]` entries are unioned by document id (conflicting counts for one document are an error — two parts measured the same document differently, which means their counters differ), `evidence[]` is unioned with duplicates dropped, `registers` recomputed, `measurement` becomes `judged` if any part judged, `instead` and `displaces` unioned, notes concatenated, the first non-null `tier_override` kept, differing regexes, stat names, `exclude`s, or `register_scope`s reported in `note` and the first kept;
- derived fields and tiers are recomputed from the merged per-document data;
- the result is `partial: false` unless `--partial` is given, and `review.status` is `pending` — a merge always precedes the review round, never replaces it.

Because tiers depend on coverage, a two-phase parallel extraction (discover candidates in parallel, then count the merged candidate list over every document, then merge again) yields far better tiers than a single parallel pass — see [technique.md](technique.md).

## Sealing

`styledb.py seal DB [-o OUT]` finalizes a reviewed DB: it drops `path` from every corpus document and stamps `corpus.sealed` with the date.

`path` is the DB's only reference into the corpus filesystem — nothing else in the manifest points at a file, and processing never reads the manifest at all: a rewrite works from the pattern entries alone (`description`, the counter, `rate`, `range`, `spread`, `tier`, `instead`, `displaces`, `evidence`). Sealing is therefore not what makes processing corpus-independent; it makes the *file names* go away. That is worth doing because filenames are the one place rule 5 of [technique.md](technique.md) cannot reach: `clients/acme/proposal-v3.md` names a customer that no redacted quote would have kept.

What sealing keeps, and why none of it is a dependency on the corpus:

- `id`, `words`, `register` are the keys and denominators of every derived number — `register` also keys `corpus.register_weights`, which survives sealing for the same reason. `rate`, `spread`, `range`, `coverage`, `registers`, and every tier are computed from `patterns[].documents[]` against them, so dropping them would leave `validate --fix` unable to recompute and turn the numbers into assertions nobody can check.
- `date`, `sole_authored`, `vetting` (and `generator` in an AI DB) are the record that intake vetting happened — some thirty bytes per document, and the only evidence in the DB that the corpus was the author's own hand.

The cost is verification. On a sealed DB `validate --corpus-dir` can check no quote; it now warns instead of passing silently, so a clean run never means "verified" when nothing was verifiable. Seal with `-o` into the default location and leave the unsealed DB beside the corpus: a revised verdict or an incremental extraction re-verifies against it, and sealing in place is what makes that impossible. Seal after the review round for the same reason: `seal` refuses a DB whose `review.status` is still `pending`, and refuses a partial DB, because merging is where document entries from the other parts still arrive. Re-extraction stays possible after sealing, but the author has to name the documents again (see [migration.md](migration.md)).

A merge of sealed parts stays sealed; a merge mixing sealed and unsealed parts keeps the paths it has and drops the stamp, because some quotes are verifiable again.
