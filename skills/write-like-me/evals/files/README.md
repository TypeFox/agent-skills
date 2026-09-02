# Eval fixtures

A fictional author, **Jo**, and the material the evals measure against. Nothing here is
real writing; the corpus was written to give the profile a distinctive, checkable voice.

## `corpus/` — Jo's hand-written documents (5 files, 1,259 words)

| file | register | words | notes |
|---|---|---|---|
| `fs-mocks.md` | article | 307 | same subject as `ai-draft.md`, told in Jo's voice |
| `conference-talk.md` | article | 327 | |
| `readme-tidy.md` | docs | 221 | the only document with a bullet list |
| `email-release.md` | email | 183 | the only sign-off; names a colleague, "Sam" |
| `retro-note.md` | note | 221 | uses "we" for team decisions |

Jo's voice: colons and parenthetical asides, no em dashes and no semicolons, `So` openers,
`which means` consequences, first person singular, contractions, British spelling,
short verdict sentences, self-deprecation.

The corpus is **deliberately below the skill's own guidance** (≥8 documents, ≥6,000 words).
That is load-bearing, not an oversight: it keeps the absence patterns at **tier 2**, which
is what makes the soft-setting eval (`soft-setting-gates-by-tier`) a real test — a tier-1
ceiling must leave them alone. Adding a corpus document can promote those tiers and silently
invert that eval. If you grow the corpus, re-check `styledb.py tiers` and re-read eval 3.

## `user-style.json` — the reviewed profile extracted from `corpus/`

Every row carries a `confirmed` verdict, as a reviewed DB must. 29 patterns: 9 at tier 1, 17 at tier 2, 3 at tier 3. 24 counted, 5 judged
(`opener-incident`, `closer-punch`, `self-deprecation`, `fragment`, `gambling-metaphor`) —
the judged ones carry no counter, so they get no row and no verdict in `textstats.py measure`,
only a name on the list it prints under *read for these*. No assertion grades whether a run
picks them up: the accounting is left to the human review, because a rate-free habit has no
bar a grader can check without becoming a taste judgement.

Two patterns are register-restricted **in `note` only**, not via `register_scope`
(technique.md Step 3 endorses either): `lists/bullet-density` (docs) and
`opener-closer/sign-off` (email), both tier 3. `textstats.py --register` sets aside only `register_scope` rows, so
on an article it prints both as **`add` rows** — it will suggest adding bullets and
"Cheers, Jo" to a blog post. That is intentional: only judgment stops those edits, which is
what `register-respected` tests.

Validates clean: `styledb.py validate evals/files/user-style.json --corpus-dir evals/files`
→ 0 errors, 2 warnings (both the corpus-size shortfall). The corpus root is `evals/files`
because the manifest's paths read `corpus/<file>.md`; every quote verifies and every counted
pattern's per-document counts reproduce when the counter is re-run over the corpus.

## `ai-draft.md` — the AI-written input (925 measured words, 988 raw)

`textstats.py` strips code blocks, tables, and link URLs, so **925 is the denominator every
rate is computed against** — not `wc -w`.

Structure to preserve: 6 headings, a 3-item bullet list, one Python code block, one 3-row
table, two links (Fowler, pytest), and the numbers `41, 4, 7, 2, 12, 3, 0.1, 0`.

Machine markers planted in it: 7 em dashes, 3 semicolons, 6 sentence-initial
However/Furthermore/Additionally, "In today's", "In conclusion", "It's worth noting" ×3,
"highlighting the importance of", a triad, a significance tail. Zero prose parentheses and
zero first-person singular, so the profile's biggest **add** rows have nowhere to hide.

American spellings available for substitution: `behavior` ×4, `standardized`, `recognizing`.
The profile's British-spelling counter is an alternation of named words, so it can only ever
see the family members it lists — `measure` marks that row `[enum]`, and a `match` on it is
not evidence the unlisted `-ize` forms were caught. That gap is what eval 2's
`american-spellings-substituted` probes.

Contractions available for substitution: the draft carries 16 (as `textstats.py` counts
them) and offers exactly 6 more uncontracted forms, one of which ("we had to handle") has no
idiomatic contraction. **Pure substitution therefore tops out at 21**, below the author's
range floor of 31.674 per 1k (≈29 here) — which is why eval 3's soft pass is asked for 20
and not for the author's rate: closing the rest would mean writing new sentences, and that
is manufacture at every setting.

Against `user-style.json` at `--setting medium` the draft yields one `do-not-touch` row
(`colon-elaboration`, 8.65/1k, match), the two tier-3 `[manual]` rows above, and everything
else actionable. At `--setting soft` the tier-2 absences (em dash, semicolon, formal
connective, summary opener, worth-noting) all go `[manual]` while the tier-1 add rows stay.

Facts a rewrite must keep: mocked tests stayed green through a rename while production
failed **twice**; suite 4 s → 7 s; 2 real bugs in 12 months; 41 mocked tests; the Windows
`PermissionError` retry (3 attempts, 0.1 s); the migration took 3 weeks; attributions to
Martin Fowler and the pytest `tmp_path` docs.

## `profiles/jo.json` — does not exist, deliberately

The `missing-profile-stops` eval points at this path. Do not create it.

`user-style.json` sits one directory above it and is a valid, complete profile — a decoy the
prompt never names. Adopting it, or offering to run with it on a one-word go-ahead, is the
same failure as building a profile from documents the user did not name, and it is what eval
0's `no-decoy-profile-adopted` tests. A baseline that has never heard of the skill reaches
for it readily.
