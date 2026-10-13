# German-shaped patterns: style vs. error

A corpus written by a German-native author reliably shows German-shaped constructions. They fall into two kinds, and the skill treats them oppositely:

- **Correct but distinctive** — marked choices that are perfectly good English (*the respective X*, participles before the noun, *in order to*). These are among the best authorship signals a corpus can offer, precisely because machine prose almost never produces them. They are recorded as patterns; most live under the `grammar-habits` dimension in [taxonomy.md](taxonomy.md).
- **Errors and calques** — constructions that are wrong or clearly unidiomatic in English (*allows to define*, *since three years*). These are **never recorded as patterns and never applied in a rewrite**. This file lists them so that extraction recognizes them and can hand them back as feedback.

The boundary is per construction, not per author: the same corpus contributes to both sides. And the policy is not German-specific — apply the same split to any first-language transfer; this file details German because it is the documented case.

## How the skill handles the error side

- **Extraction** never writes an error-side construction into the DB, whatever its rate in the corpus — the DB holds only what processing may apply. When the reading notices such constructions, collect the occurrences separately (quotes redacted under rule 5 of [technique.md](technique.md)) and present them in the review round as feedback, with the corrections from the tables below. The author learns what their corpus shows; the profile stays clean.
- **Processing** derives rewrite rules only from DB patterns, so an error form can never be introduced into a rewrite — and no request or setting changes that, because there is nothing in the DB to apply. The reverse also holds: where the input already contains such a form, fixing it is grammar editing and outside this skill's scope; leave it and mention it in the report.

## Style, not error — do not over-reject

These read German-flavored but are correct English and stay recordable:

| construction | taxonomy marker |
|---|---|
| *the respective / the corresponding / the given* | `grammar-habits/back-reference-determiner` |
| pre-nominal participles ("the already discussed advantage") | `grammar-habits/participial-premodifier` |
| instrumental *with* ("implemented with") | `grammar-habits/instrumental-with` |
| *with respect to / regarding / concerning* | `grammar-habits/framing-preposition` |
| *in the following* as a hand-off | `grammar-habits/section-hand-off` |
| *in order to*, *such that* as the purpose form | `connectives/purpose-form` |
| *e.g.* / *i.e.* without a following comma (British convention) | `punctuation/latin-abbreviation-comma` |
| no comma after a short fronted adverbial | `punctuation/fronted-adverbial-comma` |
| comma splices in informal registers ("Please try again, it should work now.") | `punctuation/comma-splice` |
| requirement-spec *shall* and "Shall we …?" | `voice-and-person/modal-profile` |

Two forms sit on the line and are, by maintainer decision, flagged rather than recorded: *minimal/maximal* for *minimum/maximum* and *persons* for *people*. Both are standard in mathematical and legal registers but read stilted in business prose — mention them in the review round instead of building patterns on them.

## Error list — observed in German-authored corpora

Each row: the calque, its German source, the English form to suggest.

| pattern | example | German source | English form |
|---|---|---|---|
| verb + *to*-infinitive without an object (*allows to, enables to, requires to*) | "Eclipse allows to define extension points" | *erlaubt zu* | "allows you to define", "allows defining" |
| *the according X* as a determiner | "the according fitness function" | *entsprechend* | "the corresponding X" |
| article dropped after *as* in role phrases | "passed as parameter", "used as basis" | *als Parameter* | "as a parameter", "as a basis" (fixed unique roles like "as author of the paper" are fine) |
| preposition calques | "dependency to", "difference to", "compatible to", "depends from", "reacts on", "fits to", "in form of", "integrated in", "interesting for you", "within March" | *zu, von, auf, innerhalb* | dependency **on**, difference **from**, compatible **with**, depends **on**, reacts **to**, suits, in **the** form of, integrated **into**, interesting **to** you, **in** March / **by** end of March |
| adverb after the object or inside the verb cluster | "We use IDs also for…", "has still to be", "could be also developed" | German adverb slots | "We also use IDs for…", "still has to be", "could also be developed" |
| present perfect with a closed past time | "have not been addressed until 2009" | *Perfekt* as the default past | "were not addressed until 2009" |
| *will* in temporal clauses | "when other projects will introduce it" | *wenn … werden* | "when other projects introduce it" |
| descriptive *shall* | "how it shall be represented" | *soll* | "how it should be / is to be represented" |
| *compared to* for *than* | "much lower compared to the baseline" | *im Vergleich zu* | "much lower than the baseline" |
| false friends | "the actual version", "eventually we could", "made good experiences", "amount of hours" | *aktuell, eventuell, Erfahrungen machen, Anzahl* | "the current version", "possibly", "had good experiences", "number of hours" |
| degree and number forms | "only little", "several hundreds of" | *nur wenig, Hunderte von* | "only a little", "several hundred" |

## Classic German errors to watch for beyond the observed corpus

| pattern | example | German source | English form |
|---|---|---|---|
| plural mass nouns | "informations", "feedbacks", "softwares" | *Informationen* | information, feedback, software |
| temporal *since* for duration | "since three years" | *seit* | "for three years" |
| *until* for a deadline | "send it until Friday" | *bis* | "by Friday" |
| infinitive after prepositional *to* | "I look forward to hear from you" | *freue mich, zu hören* | "look forward to hearing" |
| *become* for receive | "I became an email from them" | *bekommen* | "I got an email" |
| *discuss about* | "we discussed about the design" | *diskutieren über* | "we discussed the design" |
| *how* + *look like* | "how it looks like" | *wie es aussieht* | "what it looks like", "how it looks" |
| *make* as the universal verb | "make a photo", "make a party" | *machen* | "take a photo", "have a party" |
| *billion* for 10¹² | "3 billions" | *Billion* = English **trillion** | check every large number, and no plural *-s* |
| pseudo-anglicisms | "on my handy", "connect the beamer", "in homeoffice" | *Handy, Beamer, Homeoffice* | mobile phone, projector, working from home |

Neither table is exhaustive; a construction that reads wrong to a careful native reader belongs on the feedback side even if no row names it, and a doubtful case goes to the review round as a question, not into the DB.
