# Dimension taxonomy

The taxonomy is the shared coordinate system of every style-pattern DB. Both DBs (the author's and, once it ships, the AI corpus DB) record patterns along the same dimensions, which is what makes them comparable row by row during processing. The dimension list is **closed** — `scripts/styledb.py validate` rejects unknown dimensions — while the marker list under each dimension is **open**: the tables below define the standard markers so that DBs built by different runs stay joinable, and an extraction may add its own marker under any dimension as long as its `description` defines it and evidence backs it.

Vocabulary used throughout: a **pattern** is one measurable habit (dimension + marker) with its evidence; a **marker** is the concrete, observable form a habit takes; a **counter** is a mechanical measurement of a marker (a regex or a built-in statistic of `scripts/textstats.py`), and a marker with no reliable counter is **judged** by reading instead.

Every dimension measures *how* an author writes, never *what about*: subject vocabulary — technical terms, product and people's names, code identifiers, code examples — is content and is never a marker (rule 6 in [technique.md](technique.md)). The word-level markers below (`favourite-word`, `author-specific`, `abbreviation`, `code-reference`) record the author's handling of words and the topic-independent words they lean on, not the terms of their field.

Changes to this file that rename or remove a dimension, or change what a unit means, break existing DBs and require a `db_version` bump (see [db-schema.md](db-schema.md)). Adding markers or dimensions does not. `DIMENSIONS` in `scripts/styledb.py` mirrors the `###` headings below in order; a unit test keeps the two in sync.

Pattern ids are `dimension/marker`, lowercase with hyphens. The **measure** column gives the default counter: a regex (applied to prose with code, URLs, and tables removed — see textstats.py), a `stat:` name from `textstats.py counters`, a `built-in` counter name from the same list, or *judged*. A counter marked *noisy* over-counts by design; confirm its hits by reading before recording a presence pattern on it.

The two halves below are not "human" and "machine" markers. Author-voice dimensions are where an author's habits show most; AI-typical dimensions are where machine prose shows most and an author DB usually records absences. Both DBs record both halves — that is what makes the row-by-row comparison work. Every author's DB will hit some AI-typical markers (a colon punchline is not an AI invention), and the rate comparison, not the marker's placement, decides whether a rewrite is due.

## Author-voice dimensions

### punctuation

| marker | definition | measure |
|---|---|---|
| em-dash | em dash or `--` used as a dash, in any role | `—\|--` |
| em-dash-pair | pair of em dashes bracketing an aside (parenthesis substitute) | `—[^—\n]{3,80}—` |
| em-dash-appositive | em dash followed by a relabelling appositive or a tacked-on coordinator ("— a bridge, and deliberately not much more", "— and it compounds") | built-in `em_dash_appositive` |
| em-dash-spacing | spaced (" — ") vs. unspaced ("word—word") em dashes; a model fingerprint as much as an author one | judged |
| en-dash-spaced | spaced en dash used as a dash | `(?<=\s)–(?=\s)` |
| semicolon | semicolon joining clauses | `;` |
| semicolon-antithesis | semicolon balancing two short contrasting clauses as an epigram ("Prose is for judgment; machines are for rules.") — as opposed to a semicolon joining two ordinary clauses | judged |
| colon-elaboration | colon introducing an explanation or consequence in running prose | `:(?=\s)` |
| parenthetical-aside | aside in round brackets | `\(` |
| scare-quote | short quoted phrase used as a coinage or distancing device ('"citizen developers"', '"helpfully"') rather than a quotation | built-in `scare_quote` (noisy: includes short real quotes) |
| exclamation | exclamation mark | `!` |
| question-mark | question mark in prose | `\?` |
| ellipsis | ellipsis | `\.\.\.\|…` |
| oxford-comma | comma before the final *and* in a series | judged (sample series) |
| quote-style | straight vs. curly quotes, single vs. double | judged |

### sentence-rhythm

| marker | definition | measure |
|---|---|---|
| median-length | median words per sentence | `stat: sentence_len_median` |
| long-tail | share of sentences with 30+ words | `stat: long_sentence_share` |
| short-punch | share of sentences with 8 or fewer words | `stat: short_sentence_share` |
| fragment | verbless or subjectless sentence used deliberately ("Not great.", "Open protocols, no vendor silos.") | judged |
| long-short-alternation | a long explanatory sentence followed by a short verdict ("… start becoming noticeable. Correctness comes first.") as a recurring rhythm, versus even sentence lengths | judged |
| one-sentence-paragraph | share of paragraphs that are a single sentence | `stat: one_sentence_paragraph_share` |
| paragraph-length | mean sentences per paragraph | `stat: paragraph_sentences_mean` |

### paragraph-openers

How paragraphs and the piece open; the last three rows are the openers machine prose favours.

| marker | definition | measure |
|---|---|---|
| i-opener | paragraph opens with *I* | `stat: paragraph_opener_i_share` |
| the-opener | paragraph opens with *The/This/These/That* | `stat: paragraph_opener_the_share` |
| question-opener | paragraph opens with a question; note when it is the piece's first sentence (rhetorical hook) | judged, or regex on paragraphs with `share_of_paragraphs` |
| concrete-opener | paragraph opens with a concrete situation, object, or time ("Last Tuesday the build broke.") | judged |
| topic-opener | paragraph opens with the topic noun and states a fact about it ("The language server runs in a web worker…") | judged |
| meta-opener | paragraph opens by announcing or evaluating its own topic instead of stating it ("Specs deserve special respect here.", "One limit is worth stating plainly.") | judged; `significance-tails/worth-noting` catches part of it |
| connective-opener | paragraph opens with a discourse connective (*So, But, And, However*) | `^(?:So\|But\|And\|However\|Now)\b` with `share_of_paragraphs` |
| era-opener | time-anchoring change claims: "In today's fast-paced world", "As development environments become increasingly fragmented", "Notebooks have quietly become", "Until now, …", "That changes today." (11 hits in 9 docs; the 2023 "ever-evolving landscape" form is absent) | `\b(?:in today[’']s\|in the (?:modern\|ever-evolving\|rapidly)\|in an era\|in a world where\|as \w+ (?:become\|becomes\|grow\|grows) increasingly\|(?:has\|have) quietly become\|until now\|that changes today)\b` |
| imagine-opener | "Imagine / Consider / Picture / Suppose / Think of …" as a scene-setting imperative (0.3/1k, 7 docs) | built-in `ai_scene_imperative` |
| negated-opener | piece or paragraph opens by negating a status quo: "Real-time collaboration shouldn't stop at the edge of the TypeScript ecosystem.", "Parser performance rarely determines…" (0.5/1k, 7 docs; all five short-form documents open this way) | built-in `ai_negated_opener` with `share_of_paragraphs` |

### argument-structure

| marker | definition | measure |
|---|---|---|
| claim-first | states the conclusion, then the reasons | judged |
| story-first | narrates an incident, then draws the point | judged |
| concession | grants the opposing view before rebutting ("Sure, X. But…") | judged |
| example-before-rule | shows a concrete case before the general statement | judged |
| digression-return | leaves the line of argument for an aside and returns explicitly | judged |
| balanced-caveat | a one-sentence counterweight attached to every strong claim ("This does not mean X disappears, but…", "None of these should be applied mechanically.") | judged |

### connectives

| marker | definition | measure |
|---|---|---|
| so-initial | sentence starts with *So* | `(?:^\|(?<=[.!?]\s))So\b` |
| which-means | *which means* / *meaning* as a consequence connector | `\bwhich means\b` |
| because-initial | sentence starts with *Because* | `(?:^\|(?<=[.!?]\s))Because\b` |
| and-but-initial | sentence starts with *And* or *But* | `(?:^\|(?<=[.!?]\s))(?:And\|But)\b` |
| formal-connective | sentence-initial *Additionally, Furthermore, Moreover, However, Therefore, Thus, Consequently* | built-in `ai_connective_opener` |
| medial-therefore | *therefore / consequently / thus* placed after the subject instead of sentence-initially ("Custom development therefore shifts toward…") | built-in `ai_medial_therefore` |
| scholarly-connective | *e.g., i.e., in order to, in contrast, as well as, such as, for instance* | built-in `scholarly_connective` |

### voice-and-person

| marker | definition | measure |
|---|---|---|
| first-singular | I / me / my | built-in `first_person_singular` |
| first-plural | we / our / us | built-in `first_person_plural` |
| second-person | you / your | built-in `second_person` |
| passive | passive constructions | judged (regexes are too noisy) |
| impersonal | *one*, *the reader*, agentless constructions | judged |

### tone-markers

| marker | definition | measure |
|---|---|---|
| humor-aside | joke or wry remark, usually parenthetical | judged |
| self-deprecation | author at own expense | judged |
| bluntness | flat verdicts ("This is wrong.") | judged |
| hedging | *perhaps, maybe, I think, arguably, probably, relatively, comparatively* | `\b(?:perhaps\|maybe\|I think\|arguably\|I suspect\|probably\|likely\|relatively\|comparatively\|somewhat)\b` |
| enthusiasm | *love, great, brilliant, neat* | judged, or an author-specific regex |
| reassurance | comforting the reader ("If you're not sure, that's a normal place to be.") | judged |
| stance-adverb | *actually, honestly, frankly, obviously, basically, simply, really, just* | `\b(?:actually\|honestly\|frankly\|obviously\|basically\|simply\|really\|just)\b` |
| deliberate-adverb | *deliberately, explicitly, precisely, intentionally, by design* — marking every choice as intended | built-in `deliberate_adverb` |
| quiet-adverb | *quietly, silently, rarely, seldom, politely, happily* — understated drama ("has quietly become", "rarely determines") | built-in `quiet_adverb` |
| author-specific | an adverb this author leans on (extraction names it) | regex for that word |

### imagery

| marker | definition | measure |
|---|---|---|
| metaphor-density | figurative expressions per 1k words | judged |
| metaphor-domain | recurring source domain (kitchen, sports, plumbing) | judged |
| simile | *like a …*, *as if* | `\blike an? \|\bas if\b` |
| anthropomorphism | tools, code, or models given human verbs and motives ("the parser's antagonist", "unit tests happily stay green", "we taught monaco-editor to speak LSP") | judged |

### emphasis

| marker | definition | measure |
|---|---|---|
| bold | bold spans | built-in `bold` |
| italic | italic spans | built-in `italic` |
| clause-bold | bold applied to a whole clause, thesis sentence, or statistic (25+ characters) rather than a term | built-in `clause_bold` |
| caps | all-caps words for emphasis | `\b[A-Z]{3,}\b` (exclude acronyms by reading) |
| intensifier | *very, extremely, incredibly, absolutely* | `\b(?:very\|extremely\|incredibly\|absolutely\|totally)\b` |
| repetition | deliberate word or structure repetition, including anaphoric runs ("It means… It means… It means…") | judged |

### lists

| marker | definition | measure |
|---|---|---|
| bullet-density | list items per 1k words | `stat: list_items_per_1k` |
| no-lists | author does not use bullet lists in this register (absence) | `stat: list_items` equal 0 |
| label-led-item | list item or paragraph opening with a bold or italic label ("**Verify by execution.** Never trust prose…", "*Panels.* Each panel…") — record which: bold vs. italic, colon vs. period, bullet vs. run-in paragraph | built-in `label_lead` |
| inline-enumeration | series carried in prose ("two things: X and Y") | judged |
| numbered-vs-bulleted | preference when a list is used | judged |
| parallel-grammar | every item in a list shares one syntactic shape ("Label: verb + object" throughout) | judged |

### headings

| marker | definition | measure |
|---|---|---|
| heading-density | headings per 1k words | `stat: headings_per_1k` |
| heading-case | sentence case vs. title case | `stat: heading_title_case_share` (confirm by reading) |
| colon-heading | "Hook: Subtitle" headings ("Delete the Tree: Rethinking Language Tooling", "The problem: no single tool does it all") | `stat: colon_heading_share` |
| heading-form | noun phrase, verb phrase, gerund ("Architecting the guides"), question, full-sentence claim ("Parser performance is an architectural concern"), "Why X matters" | judged |
| heading-length | typical words per heading | judged |

### opener-closer

| marker | definition | measure |
|---|---|---|
| opener-type | how the piece starts: incident, question, claim, definition, negated premise (see `paragraph-openers/negated-opener`) | judged |
| closer-type | how it ends: punchline, trailing thought, call to action, summary | judged |
| slogan-closer | final line is a detachable aphorism or verbless slogan ("There is no plug-and-play AI solution. There is engineering.", "Map, not manual.") | judged |
| sign-off | email/letter sign-off form ("Cheers, Jo") | regex for the form |

### spelling-lexical

| marker | definition | measure |
|---|---|---|
| british-spelling | -ise, -our, -re spellings | `\b\w+(?:ise\|ising\|isation\|our\|ours\|tre)\b` (verify by reading) |
| american-spelling | -ize, -or, -er spellings | `\b\w+(?:ize\|izing\|ization)\b` |
| contraction | contractions | built-in `contraction` |
| favourite-word | a topic-independent word the author overuses (*fiddly*, *neat*, *the trick is*) — never a term of the subject | regex for that word |
| compound-spelling | open vs. closed compounds ("code base" vs. "codebase", "web site" vs. "website") | judged; regex for the pair once found |
| abbreviation | initialisms vs. written-out terms ("PRs" vs. "pull requests", "LSP" vs. "the Language Server Protocol") | judged; regex for the pair once found |
| hyphen-compound | coined hyphenated modifiers (*IDE-grade, theme-aware, agent-ready, seat-priced*) | built-in `hyphen_compound` (noisy: *-based* and *-specific* are excluded as ordinary) |
| numerals | digits vs. spelled-out numbers | judged |
| hedged-number | a precise figure wrapped in a vagueness hedge ("roughly $6.3–6.4 trillion", "approximately 21%") | built-in `hedged_number` |
| jargon-level | plain words vs. field terminology | judged |

### content-conventions

| marker | definition | measure |
|---|---|---|
| code-reference | how code identifiers appear (backticks, prose, both) | judged |
| link-placement | links inline on a phrase vs. bare URL vs. footnote | judged |
| citation | how sources are credited: link, title, name in prose | judged |
| source-as-agent | an institution as grammatical agent of a reporting verb, unlinked ("Gartner explicitly cautions", "Deloitte says") | built-in `source_as_agent` (noisy: also matches people) |
| name-drop-list | a comma list of vendors, tools, or companies as credibility ("Arduino, ARM, Smartface, and VUEngine") | judged |
| own-experience | references to the author's own projects or incidents | judged |
| date-format | date and number formatting | judged |

## AI-typical dimensions

Where machine prose shows most; an author DB will mostly record these as absences, which is exactly the evidence processing needs. The built-in `ai_*` counters of `textstats.py` implement the counters below until the AI DB ships.

Evidence basis: the maintainers' AI corpus (see the maintainer note in [technique.md](technique.md)) — 19 documents, ~26k words, generated in 2026 by GPT, Claude, and Gemini models across blog posts, reports, LinkedIn posts, and talk abstracts, read in full by five independent reviewers and re-counted corpus-wide. Two results shaped this section. First, the 2023-era vocabulary (*delve, tapestry, realm, pivotal, "in today's fast-paced world", "In conclusion"*) is nearly absent from current output — `stock-phrasing/buzzword` keeps it because Gemini-class output still uses it and because older drafts circulate, but it is no longer the primary signal. Second, what replaced it is syntactic and rhetorical rather than lexical: contrast frames, colon reveals, verdict sentences, authenticity words, label-led emphasis. Those are the dimensions and markers below. Figures in the definitions are what the named counter measures on that corpus — rate per 1k words and how many of the 19 documents show the marker — for calibration; they are not thresholds, and a judged reading finds more than the counter does.

### contrast-frames

Contrast frames: defining a thing by what it is not, or by what it replaces.

| marker | definition | measure |
|---|---|---|
| not-but | "not X, but Y" inside one sentence (0.4/1k, 6 docs) | built-in `ai_not_but` |
| not-just | "not just X — it's Y" | built-in `ai_not_just` |
| comma-not | sentence ending in a negated foil: "a tested feature, not an afterthought" (0.8/1k, 10 docs) | built-in `ai_comma_not` |
| split-reframe | negation and reframe split across two sentences: "X is not A. It is B." (0.3/1k, 7 docs; strongest in GPT reports) | built-in `ai_split_reframe` |
| rather-than | *rather than / instead of / Instead,* as the default contrast connector (2.4/1k, 16 docs) | built-in `ai_rather_than` |
| without-benefit | benefit stated as an avoided cost: "without building everything from scratch" (1.1/1k, 16 docs) | built-in `ai_without_benefit` (noisy) |

### reveal-frames

Setup-then-payoff sentence shapes that tell the reader what to find significant.

| marker | definition | measure |
|---|---|---|
| colon-punchline | short setup, colon, payoff in running prose: "The first proof: an OCT plugin for IntelliJ." (2.5/1k, 13 docs for the sentence-initial form the counter measures; any prose colon before a lowercase payoff runs at 8/1k in all 19 docs) | built-in `ai_colon_punchline` |
| nominal-reveal | abstract-noun subject announcing the payoff: "The result is…", "The good news:", "Here's the unexpected part:", "That is the idea behind X" (0.9/1k, 10 docs) | built-in `ai_nominal_reveal` |
| verdict-opener | sentence-initial *That/This* + evaluative verb: "That changes today.", "This is where LLVM comes in.", "That favors businesses selling capability" (1.9/1k, 11 docs) | built-in `ai_verdict_opener` |
| question-answer | a rhetorical question immediately answered by the next sentence: "What if the agent joined the session instead? That is the idea behind…" (0.7/1k, 10 docs) | built-in `ai_question_answer` (noisy: also counts structuring questions) |
| what-if | "What if…?", "What happens when…?" as a hook (0.4/1k, 7 docs; produced by every model for the same brief) | built-in `ai_what_if` |
| enumeration-announcement | a counted promise before a list: "Four principles carry the sensor side.", "Five forces are driving this shift" (0.7/1k, 9 docs) | built-in `ai_enumeration_announcement` |

### significance-tails

| marker | definition | measure |
|---|---|---|
| significance-tail | a tail telling the reader why to care: "…, highlighting the importance of …", "That matters because…", "Why X matters", "For decision makers, this signals…" (0.4/1k, 6 docs; the *matters* family — the 2023 *highlighting* form is absent) | built-in `ai_significance_tail` |
| worth-noting | "it's worth noting", "worth knowing / weighing / flagging", "deserves special respect", *notably, importantly, crucially* (0.4/1k, 5 docs) | built-in `ai_worth_noting` |
| participial-tail | main clause plus a present-participle benefit: "…, enabling natural language design and eliminating manual refactoring" (0.6/1k, 8 docs) | built-in `ai_participial_tail` |

### rule-of-three

| marker | definition | measure |
|---|---|---|
| triad | three coordinated items where two or four would do | built-in `ai_triad` |
| adjective-stack | two or three stacked evaluative adjectives before a noun: "clean, human-readable grammar rules", "sleek, robust user interfaces" (1/1k, 10 docs; doublets far outnumber triples) | built-in `ai_adjective_stack` (seed word list; extend per corpus) |
| long-enumeration | asyndetic series of five or more abstract nouns as evidence ("context, architecture, verification, tests, semantics, security, auditability and lifecycle management") | judged |

### signposting

The text describing or recapping itself.

| marker | definition | measure |
|---|---|---|
| summary-opener | *In conclusion, Overall, In summary* (0 in the 2026 corpus; kept because hand-written prose uses "Summing up" and older drafts use the rest) | built-in `ai_summary_opener` |
| closing-recap | final paragraph restating the piece; includes the bookend that repeats the executive summary's thesis | judged |
| section-recap | last sentence of a section restating the section | judged |
| meta-signpost | the text announcing its own plan: "This article looks at three of them:", "This talk walks through…", "We'll close with…", "In this post I want to…" (1.1/1k, 7 docs; also an author habit — record it on both sides) | built-in `ai_meta_signpost` |

### authenticity-stance

The writer certifying its own sincerity — the strongest lexical signal in current output, replacing the 2023 buzzwords.

| marker | definition | measure |
|---|---|---|
| authenticity-word | *actually, genuinely, real, honest(ly), actual, truly, plainly* — insisting this is the real thing against an implied fake ("what the software actually does", "a genuinely easy thing", "real expertise solves real problems") (4.1/1k, 16 docs; *real* is the noisy member) | built-in `ai_authenticity` (overlaps `tone-markers/stance-adverb` on *actually*) |
| absolutizer | *every, everyone, everything, entire, never, always, exactly, completely* — flat universals where hand-written prose hedges (5.2/1k, 18 docs, against 1.1/1k hedges) | built-in `ai_absolutizer` |
| anti-hype | disavowing hype while using its cadence: "No hype, no magic", "software engineering, not magic", "cannot be built on hope", "not a wishlist" (0.5/1k, 8 docs) | built-in `ai_anti_hype` |
| candor-claim | announced honesty as a section or sentence: "An honest maturity check", "One honest limitation:", "we'd rather tell you that up front", "Two things we learned the hard way" | judged |

### stock-phrasing

Words, idioms, and phrase templates that recur across models regardless of topic. Rates are low per item; the signal is the cluster.

| marker | definition | measure |
|---|---|---|
| buzzword | marketing register: *seamless, robust, leverage, landscape, empower, unlock, harness, cutting-edge, transformative, blazing-fast, delve, tapestry, …* (1.5/1k, 12 docs; concentrated in Gemini output — weak for current GPT and Claude output) | built-in `ai_vocabulary` |
| trend-word | unfalsifiable change words: *increasingly, rapidly, dramatically, sharply, evolving, transformation, no longer, than ever* (2.4/1k, 12 docs; *increasingly* alone 1/1k in 7) | built-in `ai_trend_word` |
| spatial-metaphor | the problem as a space to cross: *bridge, gap, silo, friction, barrier, divide, island* (2.1/1k, 15 docs) | built-in `ai_spatial_metaphor` (noisy in tooling prose: "gap buffer") |
| stock-idiom | a borrowed idiom sprinkled once or twice per piece: *table stakes, heavy lifting, under the hood, from scratch, load-bearing, connective tissue, plug-and-play* (0.9/1k, 14 docs) | built-in `ai_stock_idiom` |
| same-x | the unity trope "the same X that / as": "different windows into the same domain", "the same protocol messages as human peers" (0.3/1k, 6 docs) | built-in `ai_same_x` |
| from-to | "from X to Y" spanning unrelated items or narrating a trajectory ("from bridge to toolbox", "from seats to usage to outcomes") (0.6/1k, 10 docs) | built-in `ai_false_range` (noisy; confirm by reading) |
