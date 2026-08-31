# Style-pattern DB format

The DB is JSON, written only by extraction, by merge, and by `seal`, read by processing. Users never edit it; `scripts/styledb.py render` produces the human-readable profile whenever someone needs to see what is in it. `scripts/styledb.py validate` is the authority on what is legal; this document explains the fields and the rules behind them.

## Versioning

`db_version` is an integer format version. The skill's current value is `CURRENT_DB_VERSION` in `scripts/styledb.py` (currently 1). `styledb.py info DB` compares the two and exits 0 (same), 2 (DB older — apply [migration.md](migration.md)), or 3 (DB newer — the skill must be updated before the DB is used). Both modes run this check before reading a DB.

Bump the version when an old DB would be read incorrectly by the new skill: a renamed or removed field, a renamed or removed taxonomy dimension, a change in what a `unit` means, or a change to the tier rules that must be applied uniformly. Do not bump for additive changes (new optional fields, new markers, new dimensions). Every bump adds a section to migration.md.

## Locations

- User DB default: `$HOME/.skills/write-like-me/user-style.json`. Voice belongs to the person, not to a project, so the default is user-scoped. A request can name another path ("use the profile at …"); the named path then wins for that invocation only.
- AI DB: `data/ai-style-patterns.json` inside the skill (not shipped yet — see the README in `data/`).
- Partial DBs from parallel extraction: anywhere the orchestrating run chooses (a scratch directory), merged into the final path with `styledb.py merge`.

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
| `corpus.documents[].words` | word count as `textstats.py` counts it — rates are normalized against this number, so use the script, not an editor's count |
| `corpus.documents[].register` | document type: `article`, `email`, `docs`, `note`, `thesis`, … (free string, consistent within a DB) |
| `corpus.documents[].sole_authored`, `vetting` | intake facts: sole-authored flag; vetting outcome `confirmed`, `certified` (recent, author certified as hand-written), or `dropped` |
| `corpus.sealed` | date the DB was sealed, meaning every `path` has been dropped on purpose; absent while the DB still carries paths |
| `review.status` | `pending` until the author has walked through the rendered profile, then `reviewed` |

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
| `kind` | `presence` (the author does this) or `absence` (the author never does this — the do-not-introduce list) |
| `measurement` | `counted` when a regex or stat produced the numbers; `judged` when reading produced them and the counts are estimates. Counted beats judged in tiering because judged rates drift |
| `regex` / `stat` / `ignore_case` | the counter: a regex, or in `stat` the name of a statistic or built-in counter from `textstats.py counters` — `validate` rejects unknown names and a built-in counter with a unit other than `per_1k_words`, and warns when a counted pattern has neither. `measure --db` evaluates it on any input, so DB rates and input rates use the same definition. Absent for judged patterns |
| `unit` | `per_1k_words` (default), `share_of_sentences`, `share_of_paragraphs`, `words` (for length stats), `count` |
| `documents[]` | per-document evidence: `count` (and `rate` for non-per-1k units). One entry per document *measured*; a document with no entry was not measured for this pattern, which lowers coverage |
| `evidence[]` | verbatim quotes with their document id. Required for presence patterns; `validate --corpus-dir` checks each quote appears in its source. An entry with `"redacted": true` had confidential content replaced by a bracketed placeholder (`[colleague]`, `[company]`, `[product]`) under rule 5 of technique.md; the validator skips the verbatim check for it and warns if no placeholder is present. Absence patterns carry none — their evidence is the zero counts |
| `instead` | for absence patterns: ids of the constructions the author uses where the absent one would appear. The rewrite rule takes its replacement from these, never from invention |
| `rate`, `spread`, `range`, `coverage`, `registers` | derived; recomputed by `validate --fix` and by `merge`. `rate` is corpus-normalized (total count / total measured words × 1000 for per-1k units, word-weighted mean otherwise); `spread` is the share of measured documents where the pattern occurs (for absences: where it is absent); `range` is the min–max per-document rate and is the convergence target band in processing; `coverage` is measured documents / corpus documents |
| `tier`, `tier_reason` | derived evidence tier, see below |
| `tier_override` | set by the review round; wins over `tier` |
| `review` | verdict from the review round: `confirmed`, `overstated`, `nuanced` (with the restriction in `note`), or absent if not reviewed |
| `note` | free text: register restriction, counter caveat, anything the next reader needs |

## Evidence tiers

Tiers order patterns by how much corpus evidence stands behind them, and processing uses them as the strictness dial: **soft** applies tier 1 only, **medium** (default) tiers 1–2, **hard** all three. The tier says how *sure* the DB is that a habit is the author's voice; it says nothing about how *large* the habit's gap to the input is — the processing table still sorts rows by gap. `styledb.py tiers DB` prints the computed tier and the reason per pattern.

Presence patterns:

| tier | rule |
|---|---|
| 1 | counted; measured in every corpus document (coverage 1.0); present in at least 60% of them and in at least 3; seen in at least 2 registers (or the corpus has only one); at least 3 verbatim quotes |
| 2 | present in at least 2 documents, spread at least 40%, at least 2 quotes — and at least one tier-1 condition unmet |
| 3 | everything else that still has one quote |

Absence patterns:

| tier | rule |
|---|---|
| 1 | counted as zero in every document, corpus of at least 3,000 measured words |
| 2 | counted as zero in every measured document, but coverage below 1.0 or fewer than 3,000 words |
| 3 | absence asserted without a corpus-wide count |

Why tiers work as the strictness dial: a low-evidence pattern is exactly the one most likely to be a topic effect or a single-document quirk, so applying it risks caricature — rewriting toward a habit the author does not actually have. Restricting a soft pass to tier 1 removes that risk at the cost of leaving more of the machine voice in place. Two consequences to keep in mind: (1) tiers must be *derived*, not authored, so that a merge with more documents can promote or demote a pattern — never hand-edit `tier`, use `tier_override` and say why in `review.note`; (2) the do-not-touch classification in processing is independent of tiers: where the input already matches the author, nothing is rewritten regardless of setting.

## Merge semantics

`styledb.py merge A.json B.json … -o OUT.json` produces one DB from several partial ones (same `db_version`, same `kind`):

- corpus documents are unioned by id; the same id with different word counts is an error (the parts measured different files under one name);
- patterns are unioned by id; `documents[]` entries are unioned by document id (conflicting counts for one document are an error — two parts measured the same document differently, which means their counters differ), `evidence[]` is unioned with duplicates dropped, `registers` recomputed, `measurement` becomes `judged` if any part judged, `instead` unioned, notes concatenated, the first non-null `tier_override` kept, differing regexes or stat names reported in `note` and the first kept;
- derived fields and tiers are recomputed from the merged per-document data;
- the result is `partial: false` unless `--partial` is given, and `review.status` is `pending` — a merge always precedes the review round, never replaces it.

Because tiers depend on coverage, a two-phase parallel extraction (discover candidates in parallel, then count the merged candidate list over every document, then merge again) yields far better tiers than a single parallel pass — see [technique.md](technique.md).

## Sealing

`styledb.py seal DB [-o OUT]` finalizes a reviewed DB: it drops `path` from every corpus document and stamps `corpus.sealed` with the date.

`path` is the DB's only reference into the corpus filesystem — nothing else in the manifest points at a file, and processing never reads the manifest at all: a rewrite works from the pattern entries alone (`description`, the counter, `rate`, `range`, `tier`, `instead`, `evidence`). Sealing is therefore not what makes processing corpus-independent; it makes the *file names* go away. That is worth doing because filenames are the one place rule 5 of [technique.md](technique.md) cannot reach: `clients/acme/proposal-v3.md` names a customer that no redacted quote would have kept.

What sealing keeps, and why none of it is a dependency on the corpus:

- `id`, `words`, `register` are the keys and denominators of every derived number. `rate`, `spread`, `range`, `coverage`, `registers`, and every tier are computed from `patterns[].documents[]` against them, so dropping them would leave `validate --fix` unable to recompute and turn the numbers into assertions nobody can check.
- `date`, `sole_authored`, `vetting` are the record that intake vetting happened — some thirty bytes per document, and the only evidence in the DB that the corpus was the author's own hand.

The cost is verification. On a sealed DB `validate --corpus-dir` can check no quote; it now warns instead of passing silently, so a clean run never means "verified" when nothing was verifiable. Seal after the review round for that reason: `seal` refuses a DB whose `review.status` is still `pending`, and refuses a partial DB, because merging is where document entries from the other parts still arrive. Re-extraction stays possible after sealing, but the author has to name the documents again (see [migration.md](migration.md)).

A merge of sealed parts stays sealed; a merge mixing sealed and unsealed parts keeps the paths it has and drops the stamp, because some quotes are verifiable again.
