# Dimension taxonomy

The taxonomy is the shared coordinate system of every style-pattern DB — the axes of the style space a profile marks its region in (SKILL.md): the author's DB and the AI corpus DB record patterns along the same dimensions, which is what makes them comparable row by row during processing. The dimension list is **closed** — the 22 `###` headings below, mirrored in order by `DIMENSIONS` in `scripts/styledb.py` (a unit test keeps the two in sync, and `styledb.py validate` rejects unknown dimensions). The marker list under each dimension is **open**: the tables define standard names so that DBs built by different runs stay joinable, and an extraction adds its own marker under the closest dimension whenever the corpus shows a habit no row names — its `description` defines it and evidence backs it.

Vocabulary: a **pattern** is one measurable habit (dimension + marker) with its evidence; a **marker** is the concrete, observable form a habit takes; a **counter** is a mechanical measurement of a marker (a regex, or a statistic or built-in counter of `scripts/textstats.py`); a marker with no reliable counter is **judged** by reading instead.

**How to use the tables.** They are a map of where to look and a naming standard, not a checklist to fill in. A normal author DB holds 20–40 patterns: the habits this corpus shows clearly, and the machine-typical constructions it conspicuously lacks (absences, each with what the author does *instead*). For every recorded marker, note *which form* the author uses and which members of the family never appear (*for instance* but never *for example*; *quite* but never *perhaps*) — member preferences are near-categorical, so the zero members go in the pattern's `displaces` list, which is both processing's do-not-introduce list for that family and the set of forms a rewrite substitutes out. A marker enters this file only when both DBs need the shared name, or when a second author shows the same habit; everything else lives in the individual DB.

Every dimension measures *how* an author writes, never *what about*: subject vocabulary — technical terms, product and people's names, code identifiers, code examples — is content and never a marker (rule 6 in [technique.md](technique.md)). `favourite-word`, `abbreviation`, and `code-reference` record the author's handling of words, not the terms of their field.

**Measure column.** A regex is applied to prose with code, URLs, and tables removed (what `textstats.py` counts on) unless the row says *raw source*. `stat: name` is a statistic and `built-in name` a regex counter of `textstats.py`; both are referenced from a DB pattern as `"stat": "name"` (built-in counters count per 1k words), and `textstats.py counters` lists them with their definitions. *Judged* means reading, with the count estimated. *Noisy* counters over-count by design — confirm their hits by reading. *Per member* means one pattern, or one count, per listed word rather than one for the family. Regexes given as seeds are starting points: extend them with the corpus's own members.

The two halves below are not "human" and "machine" markers. Author-voice dimensions are where an author's habits show most; AI-typical dimensions are where machine prose shows most, and an author DB usually records them as absences. Both DBs record both halves. Renaming or removing a dimension, or changing what a unit means, requires a `db_version` bump (see [db-schema.md](db-schema.md)); adding markers or dimensions does not.

## Author-voice dimensions

### punctuation

| marker | definition | measure |
|---|---|---|
| em-dash | em dash or `--` used as a dash, in any role | built-in `em_dash` |
| em-dash-pair | two em dashes bracketing an aside | `—[^—\n]{3,80}—` |
| em-dash-appositive | em dash followed by a relabelling appositive or a coordinator ("— and it compounds") | built-in `em_dash_appositive` |
| em-dash-spacing | spaced vs. unspaced dashes, and `—` vs. `--` in the source | judged (raw source) |
| en-dash-spaced | spaced en dash used as a dash | built-in `en_dash_spaced` |
| semicolon | semicolon joining clauses | built-in `semicolon` |
| semicolon-antithesis | semicolon balancing two short contrasting clauses as an epigram | judged |
| colon-elaboration | colon introducing an explanation in running prose | built-in `colon` |
| lead-in-colon | colon-terminated line leading into a block (code, list, image); record the wording (*like so:* vs. *as follows:*) | `:\s*$` per raw-source line |
| parenthetical-aside | aside in round brackets | built-in `parenthesis` |
| scare-quote | short quoted phrase as a coinage or distancing device ("citizen developers") | built-in `scare_quote` (noisy) |
| exclamation | exclamation mark; record the placement — frame (title, kickoff, closing line) vs. body prose | built-in `exclamation` |
| question-mark | question mark in prose | built-in `question` |
| ellipsis | ellipsis | built-in `ellipsis` |
| oxford-comma | comma before the final *and* of a series; may depend on series length | judged |
| quote-style | straight vs. curly, single vs. double quotes | judged (raw source) |
| fronted-adverbial-comma | comma or none after a fronted adverbial ("Therefore the aim…" vs. "Therefore, the aim…"); per adverbial | no-comma form: `(?:^\|(?<=[.!?]\s))(?:Therefore\|Hence\|Thus\|Otherwise\|Overall\|Originally\|Currently\|Recently)\s+(?!,)[a-z]` |
| connective-comma | which sentence-initial connectives take the comma (*However,* yes, *Therefore* no); per member | `(?:^\|(?<=[.!?]\s))(?:However\|Furthermore\|Moreover\|Additionally\|In addition),` |
| latin-abbreviation-comma | comma or none after mid-sentence *e.g.* / *i.e.* | `\b(?:e\.g\.\|i\.e\.)\s+\w` vs. `\b(?:e\.g\.\|i\.e\.),` |
| comma-splice | independent clauses joined by a bare comma; an informal-register habit | judged |
| subordinator-comma | comma habit per subordinator or coordinator (before every *since* but never *because*; before *and* joining two predicates) | judged |
| slash-alternative | spaced ("X / Y") or unspaced ("vitest/jest") slash for alternatives; record which | `\s/\s` vs. `(?<=[A-Za-z])/(?=[A-Za-z])` |
| symbol-conjunction | `&` or `+` for *and* between words ("thought & effort"); record the symbol | `(?<=\w)\s[&+]\s(?=\w)` |

### sentence-rhythm

| marker | definition | measure |
|---|---|---|
| median-length | median words per sentence | `stat: sentence_len_median` |
| long-tail | share of sentences with 30+ words | `stat: long_sentence_share` |
| short-punch | share of sentences with 8 or fewer words | `stat: short_sentence_share` |
| fragment | deliberate verbless or subjectless sentence ("Not great.") | judged |
| long-short-alternation | a long explanatory sentence followed by a short verdict, as a recurring rhythm | judged |
| one-sentence-paragraph | share of one-sentence paragraphs | `stat: one_sentence_paragraph_share` |
| paragraph-length | mean sentences per paragraph | `stat: paragraph_sentences_mean` |

### paragraph-openers

How paragraphs open (rows that say *sentence* count every sentence); the last three rows are the openers machine prose favours.

| marker | definition | measure |
|---|---|---|
| pronoun-opener | paragraph opens with *I* — or *We* in a team voice, *You*; record which | `stat: paragraph_opener_i_share`; *We*: `^We\b` with `share_of_paragraphs` |
| the-opener | paragraph opens with *The/This/These/That* | `stat: paragraph_opener_the_share` |
| question-opener | paragraph opens with a question; note when it is the piece's first sentence | `^[^.!?\n]{3,120}\?` with `share_of_paragraphs` |
| concrete-opener | paragraph opens with a concrete situation, object, or time ("Last Tuesday the build broke.") | judged |
| topic-opener | paragraph opens with the topic noun and a fact about it | judged |
| meta-opener | paragraph opens by announcing or evaluating its own topic ("One limit is worth stating plainly.") | judged |
| connective-opener | paragraph opens with a discourse connective (*So, But, And, However, Now, Still*) | `^(?:So\|But\|And\|However\|Now\|Still\|Granted\|Of course)\b` with `share_of_paragraphs` |
| fronted-adjunct | sentence opens with an adjunct before its subject — *In*-phrase, participial, *By*-gerund, purpose infinitive, subordinate clause ("Since we moved to ESM, …"); record the share and the preferred forms (comma habit: `fronted-adverbial-comma`) | judged (share of sentences); seed: `(?:^\|(?<=[.!?]\s))(?:In\|By\|To\|Since\|While\|If\|When\|Once\|Depending on\|Speaking of)\b[^.!?]{2,60},` |
| existential-opener | sentence opens with *There is/are* or *There's* | `(?:^\|(?<=[.!?]\s))There(?:[’']s\| (?:is\|are\|was\|were\|exists?))\b` |
| demonstrative-subject | sentence opens with anaphoric *This* + verb as a hand-off ("This means that…"); the evaluative subset is `reveal-frames/verdict-opener` | `(?:^\|(?<=[.!?]\s))This\s+(?:is\|was\|means\|allows\|enables\|makes\|leads\|results)\b` |
| era-opener | time-anchoring change claim ("In today's fast-paced world", "Until now, …", "That changes today.") | `\b(?:in today[’']s\|in an era\|in a world where\|(?:has\|have) quietly become\|until now\|that changes today)\b` |
| imagine-opener | *Imagine / Consider / Picture / Suppose* as a scene-setting imperative | built-in `ai_scene_imperative` |
| negated-opener | piece or paragraph opens by negating a status quo ("X shouldn't stop at the edge of…") | built-in `ai_negated_opener` |

### argument-structure

| marker | definition | measure |
|---|---|---|
| claim-first | the conclusion first, then the reasons | judged |
| story-first | an incident first, then the point | judged |
| concession | grants the opposing view before rebutting ("Sure, X. But…") | judged |
| example-before-rule | a concrete case before the general statement | judged |
| digression-return | leaves the argument for an aside and returns explicitly | judged |
| balanced-caveat | a one-sentence counterweight after every strong claim ("This does not mean X disappears, but…") | judged |
| before-after | the previous state, then the new one with *now* ("Previously … Now the language server…") — the release-note contrast | `\bPreviously\b\|\bno longer\b\|\b(?:is\|are\|can\|will) now\b` |
| benefit-frame | a benefit argued as ease or capability ("makes it easier to", "allows you to", "so you can") — the author-side counterpart of `contrast-frames/without-benefit` | `\bmak(?:es\|ing) it (?:much )?easier to\b\|\ballows? (?:you\|us) to\b\|\bso (?:you\|we) can\b` |

### connectives

Class rows (`formal-connective`, `scholarly-connective`) give a family's rate; `-form` rows record which member the author prefers — often the stronger signal, since member preferences are near-categorical.

| marker | definition | measure |
|---|---|---|
| so-initial | sentence starts with *So* | `(?:^\|(?<=[.!?]\s))So\b` |
| medial-so | clauses joined with *, so* | `,\s+so\b` |
| which-means | *which / this / that means* as a consequence connector | `\b(?:which\|this\|that) means\b` |
| because-initial | sentence starts with *Because* | `(?:^\|(?<=[.!?]\s))Because\b` |
| and-but-initial | sentence starts with *And* or *But* | `(?:^\|(?<=[.!?]\s))(?:And\|But)\b` |
| formal-connective | sentence-initial *Additionally, Furthermore, Moreover, However, Therefore, Thus, Consequently* | built-in `ai_connective_opener` |
| medial-therefore | *therefore / thus / consequently* after the subject ("Custom development therefore shifts…") | built-in `ai_medial_therefore` |
| informal-pivot | spoken-register transition at sentence start (*That being said, Speaking of X, Granted, Thankfully, By the way, Anyway*) | `(?:^\|(?<=[.!?]\s))(?:(?:With )?[Tt]hat being said\|With that said\|Speaking of\|Going back to\|By the way\|Granted\|Thankfully\|Anyway)\b` |
| scholarly-connective | *e.g., i.e., in order to, in contrast, as well as, such as, for instance* | built-in `scholarly_connective` |
| purpose-form | *in order to* vs. *so that* vs. *such that* vs. bare *to*; per member | `\bin order to\b`, `\bso that\b`, `\bsuch that\b` |
| example-introducer | *For instance* vs. *For example* vs. *e.g.* vs. *such as* vs. *like*; per member | `\bfor instance\b`, `\bfor example\b`, `\bsuch as\b`, `\be\.g\.` |
| causal-form | *since* vs. *because* vs. *, as*; per member | `,\s+since\b\|(?:^\|(?<=[.!?]\s))Since\b`, `\bbecause\b`, `,\s+as (?:it\|this\|we\|they\|you\|the)\b` (noisy) |
| contrast-form | *, while* vs. *whereas* vs. *although* vs. *, but*; per member | `,\s+while\b`, `\bwhereas\b`, `\b[Aa]lthough\b`, `,\s+but\b` |
| additive-form | sentence-initial *Furthermore* vs. *Moreover* vs. *In addition* vs. *Additionally*; per member | `(?:^\|(?<=[.!?]\s))(?:Furthermore\|Moreover\|Additionally\|In addition)\b` |
| additive-tail | clause-final *as well* or *too* ("open to feedback as well."), including *also … as well*; per member | `\bas well(?=[.,;!?)])`, `\btoo(?=[.,;!?)])` |
| comma-hence | consequence attached with *, hence / thus / therefore* | `,\s+(?:hence\|thus\|therefore)\b` |
| sentential-which | *, which* clause on the whole preceding clause ("…, which means that…") | `,\s+which (?:is\|was\|means\|makes\|leads\|allows\|would\|can)\b` |
| anaphoric-such | sentence opens with *Such (a)* picking up the previous sentence | `(?:^\|(?<=[.!?]\s))Such\b` |

### grammar-habits

Marked but correct grammatical constructions the author reaches for, shaped by a first language or by register. Errors are never patterns: [german-l1-guidance.md](german-l1-guidance.md) draws the boundary and lists the known calques, which go to the review round as feedback instead.

| marker | definition | measure |
|---|---|---|
| participial-premodifier | participle before the noun instead of a relative clause after it ("the already discussed advantage", "the resulting diagram") | `\b(?:the\|these\|those\|its\|our) (?:already \|newly \|previously )?(?:discussed\|mentioned\|presented\|described\|proposed\|resulting\|remaining\|required\|aforementioned) \w+` (seed) |
| instrumental-with | *with* where *by* or *using* is the plainer choice ("implemented with", "represented with bars") | `\b(?:implemented\|realized\|represented\|encoded\|defined\|generated\|built\|configured\|specified)\s+with\b` |
| back-reference-determiner | *the respective / the corresponding / the given* as a back-reference | `\bthe (?:respective\|corresponding\|given)\b` |
| framing-preposition | *with respect to / regarding / in the context of / concerning* framing a clause's topic | `\b(?:with respect to\|regarding\|in the context of\|concerning)\b` |
| section-hand-off | *in the following* as a forward hand-off | `\bin the following\b` |
| relative-pronoun | *that* vs. *who* for people ("those of you that…"), *that* vs. *which* for restrictive clauses; per antecedent type | `\b(?:those(?: of you)?\|people\|users\|developers\|anyone) that\b` vs. the same with `who` |

### voice-and-person

| marker | definition | measure |
|---|---|---|
| first-singular | I / me / my | built-in `first_person_singular` |
| first-plural | we / our / us | built-in `first_person_plural` |
| second-person | you / your | built-in `second_person` |
| audience-noun | how the readership is named beyond *you* — *everyone, you all, folks*, class nouns (*developers, the community*); record the members | `\b(?:everyone\|everybody\|you all\|y[’']all\|folks\|the community)\b` (class nouns by reading) |
| passive | passive constructions | judged (`modal-passive` counts the modal subset) |
| modal-passive | modal + passive infinitive ("can be embedded") | `\b(?:can\|cannot\|could\|may\|might\|should\|must)\s+(?:not\s+)?be\s+\w+(?:ed\|en\|wn\|lt\|t)\b` |
| modal-profile | rate per modal (*can, could, would, should, may, might, must, will/'ll*) and *need to*; per member, zeros included | `\bwould\b`, `\bcan\b`, `\bwill\b\|[’']ll\b`, `\bneeds? to\b`, … |
| pronoun-roles | which person does which job (*I* for claims, *we* for procedure, passive for the rest), and person switching within a document | judged |
| tense-profile | the tense for the author's own work — present perfect ("We've added…") vs. simple past ("We added…") vs. present; the progressive for ongoing work ("We've been working on…") | `\b[Ww]e[’']?(?:ve\| have) (?:also \|just )?(?!been\b)\w+(?:ed\|en\|wn)\b` vs. `\b[Ww]e (?:added\|made\|introduced\|changed\|fixed\|built)\b` |
| imperative | imperative addressed to the reader ("Run the generator"); softened offers are `tone-markers/invitation-form`, *Please* forms `tone-markers/request-form` | judged (verb-initial sentences) |
| impersonal | *one*, *the reader*, agentless constructions | judged |

### tone-markers

| marker | definition | measure |
|---|---|---|
| humor-aside | joke or wry remark, usually parenthetical | judged |
| self-deprecation | the author at their own expense | judged |
| bluntness | flat verdicts ("This is wrong.") | judged |
| hedging | *perhaps, maybe, I think, probably, possibly, quite, rather, somewhat, a bit, or so, might*; per member | `\b(?:perhaps\|maybe\|I think\|probably\|possibly\|somewhat\|quite\|a bit\|a little\|or so\|might)\b\|\brather\b(?! than)` |
| opinion-marker | explicit opinion tag, singular or team-voiced (*I think, we believe, we'd recommend, in my opinion*) | `\b(?:I\|[Ww]e) (?:think\|believe\|feel\|guess\|assume\|hope)\b\|\bin (?:my\|our) (?:opinion\|view)\b` |
| litotes | understatement by negation ("not ideal", "not too big") | `\bnot (?:too\|that\|very\|so\|really\|quite\|ideal\|perfect)\b` (noisy) |
| politeness-formula | the courtesy profile: thanks form ("Thanks for the [noun]!", "We'd like to thank…"), apology, greeting; register-bound | judged; thanks: `\b[Tt]hank(?:s\|ing)?\b` |
| request-form | how the author asks: *Please* + imperative, *Could you*, *It would be great if*; register-bound (email) | `(?:^\|(?<=[.!?]\s))Please [a-z]+\|\bCould you\b\|\b[Ii]t would be (?:great\|nice\|helpful)\b` |
| invitation-form | optional reader actions offered rather than commanded: *feel free to*, *check out*, *you can (now)*, *If you're curious, …*, *For those of you that …*; the counterpart of `request-form` | `\bfeel free to\b\|\bcheck (?:it )?out\b\|\bif you[’']re (?:curious\|interested\|new)\b\|\bfor those(?: of you)? (?:that\|who)\b` (ignore case) |
| enthusiasm | *love, great, neat, happy to, excited to*; record the key — high (*awesome, huge*) vs. low (*useful, handy*) — and the recurring carrier ("We're happy to announce") | seed: `\b(?:happy\|excited\|proud\|glad\|thrilled) to\b` |
| reassurance | comforting the reader ("that's a normal place to be"), including backward-compatibility reassurance after a change ("still supported, so you can continue…") | judged; compatibility: `\b(?:still supported\|as it[’']s always been\|don[’']t need to worry\|continue to use)\b` |
| stance-adverb | *actually, honestly, obviously, basically, simply, really, just, of course, particularly, especially, even, literally*; per member | `\b(?:actually\|honestly\|obviously\|basically\|simply\|really\|just\|of course\|particularly\|especially\|even\|literally)\b` |
| deliberate-adverb | *deliberately, explicitly, precisely, by design* — every choice marked as intended | built-in `deliberate_adverb` |
| quiet-adverb | *quietly, silently, rarely, seldom* — understated drama ("has quietly become") | built-in `quiet_adverb` |
| colloquialism | spoken-register idioms and particle verbs where a plain verb exists (*hard at work, spit out, wire it up, dig into, run into a snag*), as a density; the machine-favoured fixed list is `stock-phrasing/stock-idiom` | judged (list the corpus's idioms; regex for the list once found) |

### imagery

| marker | definition | measure |
|---|---|---|
| metaphor-density | figurative expressions per 1k words (idioms count under `tone-markers/colloquialism`) | judged |
| metaphor-domain | recurring source domain (kitchen, sports, plumbing) | judged |
| simile | *like a …*, *as if* | `\blike an? \|\bas if\b` |
| anthropomorphism | tools or code given human verbs and motives ("unit tests happily stay green") | judged |

### emphasis

| marker | definition | measure |
|---|---|---|
| bold | bold spans | built-in `bold` |
| italic | italic spans | built-in `italic` |
| stress-italic | italic on a function word or auxiliary for spoken stress ("there _are_ other solutions"), as opposed to italic at a term's first definition | `(?<![\w*_])[_*](?:not\|none\|is\|are\|very\|quite\|only\|about\|any\|all\|even)[_*](?![\w*_])` (seed; raw source) |
| emphasis-syntax | `_x_` vs. `*x*`, `**x**` vs. `__x__` in the source; may drift over time | judged (raw source) |
| clause-bold | bold on a whole clause or statistic (25+ characters) rather than a term | built-in `clause_bold` |
| caps | all-caps words for emphasis | `\b[A-Z]{3,}\b` (exclude acronyms by reading) |
| intensifier | *very, extremely, incredibly, absolutely*; per member | `\b(?:very\|extremely\|incredibly\|absolutely\|totally)\b` |
| repetition | deliberate word or structure repetition, including anaphoric runs | judged |

### lists

| marker | definition | measure |
|---|---|---|
| bullet-density | list items per 1k words | `stat: list_items_per_1k` |
| no-lists | no bullet lists in this register (absence) | `stat: list_items` equal 0 |
| label-led-item | list item or paragraph opening with a bold or italic label ("**Verify by execution.** Never…"); record bold vs. italic, colon vs. period | built-in `label_lead` |
| inline-enumeration | a series carried in prose ("two things: X and Y") | judged |
| open-list-terminator | how an open series ends — *, and more* vs. *etc.* vs. *and so on* vs. an ellipsis; per member | `,? and (?:many )?more\b`, `\betc\.`, `\band so on\b` |
| numbered-vs-bulleted | preference when a list is used | judged |
| parallel-grammar | every list item shares one syntactic shape; record the shape (noun phrase, full sentence, continuation of a lead-in) | judged |
| correlative-pair | *both/either/neither* with the preposition repeated ("both with X and with Y") | `\b(?:both\|either\|neither)\s+(?:in\|with\|for\|on\|at\|by\|from\|to)\b` |

### headings

| marker | definition | measure |
|---|---|---|
| heading-density | headings per 1k words | `stat: headings_per_1k` |
| heading-case | sentence case vs. title case | `stat: heading_title_case_share` |
| colon-heading | "Hook: Subtitle" headings | `stat: colon_heading_share` |
| heading-form | noun phrase, gerund, question, imperative ("Try it!"), full-sentence claim, "Why X matters" | judged |
| heading-length | typical words per heading | judged |
| heading-depth | the level the body starts at (`##` vs. `###`) and how deep headings nest | `^#{1,6}\s` per raw-source line |

### opener-closer

| marker | definition | measure |
|---|---|---|
| opener-type | how the piece — and each section — starts: incident, question, claim, definition, status report, announcement ("We're happy to announce…"), negated premise, bridge from the previous section ("Speaking of …") | judged; announcement: `^We(?:[’']re\| are) (?:happy\|excited\|proud\|pleased) to (?:announce\|share)\b` |
| closer-type | how the piece — and each section — ends: punchline, trailing thought, call to action, summary, check-question ("What do you think?"), invitation ("we look forward to seeing what you build"), compatibility reassurance, or a block with no closing prose; note a generic closing heading (*Conclusion*, *Wrapping Up*) | judged; closing heading: `^#{1,6}\s*(?:Conclusion\|Wrapping [Uu]p\|Summary)` |
| pointer-closer | paragraph or section closes on a cross-reference ("as shown in the figure below") | judged (`content-conventions/artifact-pointer` counts the references) |
| slogan-closer | the final line is a detachable aphorism or verbless slogan ("Map, not manual.") | judged |
| sign-off | email sign-off ("Cheers, Jo") or blog sign-off slogan ("Happy language building!") | regex for the form |

### spelling-lexical

| marker | definition | measure |
|---|---|---|
| british-spelling | -ise, -our, -re spellings | `\b\w+(?:ise\|ising\|isation\|our\|ours\|tre)\b` (verify by reading) |
| american-spelling | -ize, -or, -er spellings | `\b\w+(?:ize\|izing\|ization)\b` |
| contraction | contractions | built-in `contraction` |
| contraction-selectivity | which contractions appear and which never do (*don't, it's* freely; *isn't, can't* never) | `\b(?:isn\|aren\|wasn\|can\|couldn\|doesn\|didn\|hasn\|shouldn\|wouldn)['’]t\b` against built-in `contraction` |
| favourite-word | a topic-independent word or phrase the author overuses (*fiddly*, *neat*, *the trick is*) | regex for that word |
| quantifier-form | colloquial (*a lot of, a ton of, quite a bit, a bunch of*) vs. formal (*numerous, a number of, a wide range of, several*) vague quantities; per member | `\b(?:a ton of\|a lot of\|lots of\|quite a (?:bit\|lot\|few)\|a bunch of\|plenty of\|a couple of)\b` vs. `\b(?:numerous\|a (?:large )?number of\|a (?:wide )?range of\|several\|various)\b` |
| compound-spelling | open vs. closed vs. hyphenated compounds ("code base" / "codebase"; "LSP related" / "LSP-related") | judged; regex for the pair once found |
| abbreviation | initialisms vs. written-out terms ("PRs" vs. "pull requests") | judged; regex for the pair once found |
| hyphen-compound | coined hyphenated modifiers (*IDE-grade, agent-ready*) | built-in `hyphen_compound` |
| based-compound | *-based / -driven / -oriented* as the default modifier | `\b\w+-(?:based\|driven\|oriented)\b` |
| numerals | digits vs. spelled-out numbers | judged |
| hedged-number | a precise figure behind a vagueness hedge ("roughly 21%") | built-in `hedged_number` |
| jargon-level | plain words vs. field terminology | judged |

### content-conventions

| marker | definition | measure |
|---|---|---|
| code-reference | how identifiers appear (backticks, prose, both) | judged |
| link-placement | inline on a phrase vs. bare URL on its own line vs. footnote; anchor text descriptive vs. "here" | judged (raw source) |
| term-introduction | how coinages are introduced: *called / so-called / we call*, italics or quotes at first definition | `\b(?:so-called\|called\|we call)\b` (noisy) |
| artifact-pointer | capitalized cross-references ("Figure 4.5", "Section 2.3") | `\b(?:Section\|Figure\|Table\|Chapter\|Listing)\s+\d` |
| self-reference | how the author refers to the current and their own prior work ("this thesis", "the post we wrote up"), and intra-document deixis (*below*, *above*, *as mentioned earlier*) | judged; deixis: `\b(?:below\|above\|as mentioned (?:earlier\|above))\b` |
| time-anchoring | dated history recaps and concrete time anchors ("In January 2017 we released…") | judged |
| semantic-line-breaks | one sentence per line in the source | `[.!?]\n(?=[A-Z])` on the raw source |
| block-handling | which block elements the source uses or never uses — tables, blockquotes, footnotes, rules, callout labels (*Note:*), images (alt text as a word vs. a sentence) — and how a block is led in (`punctuation/lead-in-colon`) and followed up ("This will give you…", "As you can see"); the absences are processing's do-not-introduce list | judged (raw source); per element: `^\|`, `^>`, `^\[\^`, `!\[`, `^(?:\*\*)?(?:Note\|TL;DR\|Important\|Warning\|Tip)\b` |
| citation | how sources are credited: link, title, name in prose | judged |
| source-as-agent | an institution as the agent of a reporting verb, unlinked ("Gartner cautions") | built-in `source_as_agent` (noisy) |
| name-drop-list | a comma list of vendors or tools as credibility | judged |
| own-experience | references to the author's own projects or incidents | judged |
| date-format | date and number formatting | judged |

## AI-typical dimensions

Where machine prose shows most; an author DB records these mostly as absences, which is the evidence processing needs. The built-in `ai_*` counters of `textstats.py` implement the counters; the shipped AI DB (`data/ai-style-patterns.json`) is the authoritative record of their rates, spreads, tiers, and evidence on the maintainers' current corpus. Figures in the definitions — rate per 1k words and the number of documents showing the marker — are what the counter measured on the earlier 19-document 2026 corpus (~26k words; GPT, Claude, and Gemini output), for calibration, not as thresholds. In that corpus the 2023-era vocabulary (*delve, tapestry, "In conclusion"*) is nearly gone; the signal is syntactic and rhetorical — contrast frames, colon reveals, verdict sentences, authenticity words, label-led emphasis.

### contrast-frames

Defining a thing by what it is not, or by what it replaces.

| marker | definition | measure |
|---|---|---|
| not-but | "not X, but Y" or "not just X, but Y" in one sentence (0.4/1k, 6 docs) | built-in `ai_not_but` |
| comma-not | sentence-final negated foil: "a tested feature, not an afterthought" (0.8/1k, 10 docs) | built-in `ai_comma_not` |
| split-reframe | "X is not A. It is B." across two sentences (0.3/1k, 7 docs) | built-in `ai_split_reframe` |
| rather-than | *rather than / instead of / Instead,* as the default contrast connector (2.4/1k, 16 docs) | built-in `ai_rather_than` |
| without-benefit | a benefit stated as an avoided cost: "without building everything from scratch" (1.1/1k, 16 docs) | built-in `ai_without_benefit` (noisy) |

### reveal-frames

Setup-then-payoff sentence shapes that tell the reader what to find significant.

| marker | definition | measure |
|---|---|---|
| colon-punchline | short setup, colon, payoff: "The first proof: an OCT plugin." (2.5/1k, 13 docs) | built-in `ai_colon_punchline` |
| nominal-reveal | abstract-noun subject announcing the payoff: "The result is…", "Here's the unexpected part:" (0.9/1k, 10 docs); also an author habit ("The only problem is that…") — record on both sides | built-in `ai_nominal_reveal` (seed nouns; extend per corpus) |
| verdict-opener | sentence-initial *That/This* + evaluative verb: "That changes today." (1.9/1k, 11 docs) | built-in `ai_verdict_opener` |
| question-answer | a rhetorical question answered by the next sentence (0.7/1k, 10 docs) | built-in `ai_question_answer` (noisy) |
| what-if | "What if…?", "What happens when…?" as a hook (0.4/1k, 7 docs) | built-in `ai_what_if` |
| enumeration-announcement | a counted promise before a list: "Four principles carry the sensor side." (0.7/1k, 9 docs) | built-in `ai_enumeration_announcement` |

### significance-tails

| marker | definition | measure |
|---|---|---|
| significance-tail | a tail saying why to care: "That matters because…", "Why X matters", "…, highlighting the importance of…" (0.4/1k, 6 docs) | built-in `ai_significance_tail` |
| worth-noting | "it's worth noting", "deserves special respect", *notably, crucially* (0.4/1k, 5 docs) | built-in `ai_worth_noting` |
| participial-tail | main clause plus a present-participle benefit: "…, enabling X and eliminating Y" (0.6/1k, 8 docs); also an author result tail ("…, thus decoupling…") — record on both sides | built-in `ai_participial_tail` (seed verbs; extend per corpus) |

### rule-of-three

| marker | definition | measure |
|---|---|---|
| triad | three coordinated items where two or four would do | built-in `ai_triad` |
| adjective-stack | stacked evaluative adjectives: "clean, human-readable grammar rules" (1/1k, 10 docs) | built-in `ai_adjective_stack` (seed list) |
| long-enumeration | an asyndetic series of five or more abstract nouns as evidence | judged |

### signposting

The text describing or recapping itself.

| marker | definition | measure |
|---|---|---|
| summary-opener | *In conclusion, Overall, In summary, All in all, Ultimately* (0 in the 2026 corpus; kept for older drafts, and because hand-written prose uses *Overall,* and *All in all*) | built-in `ai_summary_opener` |
| closing-recap | the final paragraph restating the piece | judged |
| section-recap | the last sentence of a section restating the section | judged |
| meta-signpost | the text announcing its own plan: "This article looks at…", "We'll close with…", and the hortative "Let's dig into the features!" (1.1/1k, 7 docs; also an author habit — record on both sides) | built-in `ai_meta_signpost`; *Let's* form: `\bLet[’']s (?:dig\|dive\|take a look\|look\|start)\b` |
| ordinal-sequencer | sentence-initial *First(ly), … Second(ly), … Finally* as prose list steps | `(?:^\|(?<=[.!?]\s))(?:First(?:ly)?\|Second(?:ly)?\|Third(?:ly)?\|Finally\|Lastly),` |

### authenticity-stance

The writer certifying its own sincerity — the strongest lexical signal in current output.

| marker | definition | measure |
|---|---|---|
| authenticity-word | *actually, genuinely, real, honest(ly), truly* against an implied fake ("what the software actually does") (4.1/1k, 16 docs; *real* is noisy) | built-in `ai_authenticity` (overlaps `tone-markers/stance-adverb` on *actually*) |
| absolutizer | *every, everyone, entire, never, always, exactly, completely* where hand-written prose hedges (5.2/1k, 18 docs) | built-in `ai_absolutizer` |
| anti-hype | disavowing hype in its own cadence: "No hype, no magic", "not a wishlist" (0.5/1k, 8 docs) | built-in `ai_anti_hype` |
| candor-claim | announced honesty: "An honest maturity check", "we'd rather tell you that up front" | judged |

### stock-phrasing

Words, idioms, and templates recurring across models regardless of topic; the signal is the cluster, not any one item.

| marker | definition | measure |
|---|---|---|
| buzzword | marketing register: *seamless, robust, leverage, empower, unlock, cutting-edge, delve, …* (1.5/1k, 12 docs; mostly Gemini) | built-in `ai_vocabulary` |
| trend-word | unfalsifiable change words: *increasingly, rapidly, evolving, transformation, than ever* (2.4/1k, 12 docs) | built-in `ai_trend_word` |
| spatial-metaphor | the problem as a space to cross: *bridge, gap, silo, friction, barrier* (2.1/1k, 15 docs) | built-in `ai_spatial_metaphor` (noisy) |
| stock-idiom | a borrowed idiom once or twice per piece: *table stakes, heavy lifting, under the hood, from scratch* (0.9/1k, 14 docs) | built-in `ai_stock_idiom` |
| same-x | the unity trope "the same X that / as" (0.3/1k, 6 docs) | built-in `ai_same_x` |
| from-to | "from X to Y" spanning unrelated items or narrating a trajectory (0.6/1k, 10 docs) | built-in `ai_false_range` (noisy) |
