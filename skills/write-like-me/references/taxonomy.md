# Dimension taxonomy

The taxonomy is the shared coordinate system of every style-pattern DB. Both DBs (the author's and, once it ships, the AI corpus DB) record patterns along the same dimensions, which is what makes them comparable row by row during processing. The dimension list is **closed** — `scripts/styledb.py validate` rejects unknown dimensions — while the marker list under each dimension is **open**: the tables below define the standard markers so that DBs built by different runs stay joinable, and an extraction may add its own marker under any dimension as long as its `description` defines it and evidence backs it.

Vocabulary used throughout: a **pattern** is one measurable habit (dimension + marker) with its evidence; a **marker** is the concrete, observable form a habit takes; a **counter** is a mechanical measurement of a marker (a regex or a built-in statistic of `scripts/textstats.py`), and a marker with no reliable counter is **judged** by reading instead.

Changes to this file that rename or remove a dimension, or change what a unit means, break existing DBs and require a `db_version` bump (see [db-schema.md](db-schema.md)). Adding markers or dimensions does not.

Pattern ids are `dimension/marker`, lowercase with hyphens. The **measure** column gives the default counter: a regex (applied to prose with code, URLs, and tables removed — see textstats.py), a `stat:` name from `textstats.py counters`, or *judged*.

## Author-voice dimensions

### punctuation

| marker | definition | measure |
|---|---|---|
| em-dash | em dash or `--` used as a dash, in any role | `—\|--` |
| em-dash-pair | pair of em dashes bracketing an aside (parenthesis substitute) | `—[^—\n]{3,80}—` |
| en-dash-spaced | spaced en dash used as a dash | `(?<=\s)–(?=\s)` |
| semicolon | semicolon joining clauses | `;` |
| colon-elaboration | colon introducing an explanation or consequence in running prose | `:(?=\s)` |
| parenthetical-aside | aside in round brackets | `\(` |
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
| fragment | verbless or subjectless sentence used deliberately ("Not great.") | judged |
| one-sentence-paragraph | share of paragraphs that are a single sentence | `stat: one_sentence_paragraph_share` |
| paragraph-length | mean sentences per paragraph | `stat: paragraph_sentences_mean` |

### paragraph-openers

| marker | definition | measure |
|---|---|---|
| i-opener | paragraph opens with *I* | `stat: paragraph_opener_i_share` |
| the-opener | paragraph opens with *The/This/These/That* | `stat: paragraph_opener_the_share` |
| question-opener | paragraph opens with a question | judged, or regex on paragraphs with `share_of_paragraphs` |
| concrete-opener | paragraph opens with a concrete situation, object, or time ("Last Tuesday the build broke.") | judged |
| connective-opener | paragraph opens with a discourse connective (*So, But, And, However*) | `^(?:So\|But\|And\|However\|Now)\b` with `share_of_paragraphs` |

### argument-structure

| marker | definition | measure |
|---|---|---|
| claim-first | states the conclusion, then the reasons | judged |
| story-first | narrates an incident, then draws the point | judged |
| concession | grants the opposing view before rebutting ("Sure, X. But…") | judged |
| example-before-rule | shows a concrete case before the general statement | judged |
| digression-return | leaves the line of argument for an aside and returns explicitly | judged |

### connectives

| marker | definition | measure |
|---|---|---|
| so-initial | sentence starts with *So* | `(?:^\|(?<=[.!?]\s))So\b` |
| which-means | *which means* / *meaning* as a consequence connector | `\bwhich means\b` |
| because-initial | sentence starts with *Because* | `(?:^\|(?<=[.!?]\s))Because\b` |
| and-but-initial | sentence starts with *And* or *But* | `(?:^\|(?<=[.!?]\s))(?:And\|But)\b` |
| formal-connective | sentence-initial *Additionally, Furthermore, Moreover, However, Therefore, Thus, Consequently* | built-in `ai_connective_opener` |

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
| hedging | *perhaps, maybe, I think, arguably* | `\b(?:perhaps\|maybe\|I think\|arguably\|I suspect)\b` |
| enthusiasm | *love, great, brilliant, neat* | judged, or an author-specific regex |

### imagery

| marker | definition | measure |
|---|---|---|
| metaphor-density | figurative expressions per 1k words | judged |
| metaphor-domain | recurring source domain (kitchen, sports, plumbing) | judged |
| simile | *like a …*, *as if* | `\blike an? \|\bas if\b` |

### attitude-adverbs

| marker | definition | measure |
|---|---|---|
| stance-adverb | *actually, honestly, frankly, obviously, basically, simply, really, just* | `\b(?:actually\|honestly\|frankly\|obviously\|basically\|simply\|really\|just)\b` |
| author-specific | an adverb this author leans on (extraction names it) | regex for that word |

### emphasis

| marker | definition | measure |
|---|---|---|
| bold | bold spans | built-in `bold` |
| italic | italic spans | built-in `italic` |
| caps | all-caps words for emphasis | `\b[A-Z]{3,}\b` (exclude acronyms by reading) |
| intensifier | *very, extremely, incredibly, absolutely* | `\b(?:very\|extremely\|incredibly\|absolutely\|totally)\b` |
| repetition | deliberate word or structure repetition | judged |

### lists

| marker | definition | measure |
|---|---|---|
| bullet-density | list items per 1k words | `stat: list_items_per_1k` |
| no-lists | author does not use bullet lists in this register (absence) | `stat: list_items` equal 0 |
| inline-enumeration | series carried in prose ("two things: X and Y") | judged |
| numbered-vs-bulleted | preference when a list is used | judged |

### headings

| marker | definition | measure |
|---|---|---|
| heading-density | headings per 1k words | `stat: headings_per_1k` |
| heading-case | sentence case vs. title case | judged |
| heading-form | noun phrase, verb phrase, question, fragment | judged |
| heading-length | typical words per heading | judged |

### opener-closer

| marker | definition | measure |
|---|---|---|
| opener-type | how the piece starts: incident, question, claim, definition | judged |
| closer-type | how it ends: punchline, trailing thought, call to action, summary | judged |
| sign-off | email/letter sign-off form ("Cheers, Jo") | regex for the form |

### spelling-lexical

| marker | definition | measure |
|---|---|---|
| british-spelling | -ise, -our, -re spellings | `\b\w+(?:ise\|ising\|isation\|our\|ours\|tre)\b` (verify by reading) |
| american-spelling | -ize, -or, -er spellings | `\b\w+(?:ize\|izing\|ization)\b` |
| contraction | contractions | built-in `contraction` |
| favourite-word | a word the author overuses (*fiddly*, *neat*, *the trick is*) | regex for that word |
| numerals | digits vs. spelled-out numbers | judged |
| jargon-level | plain words vs. field terminology | judged |

### content-conventions

| marker | definition | measure |
|---|---|---|
| code-reference | how code identifiers appear (backticks, prose, both) | judged |
| link-placement | links inline on a phrase vs. bare URL vs. footnote | judged |
| citation | how sources are credited | judged |
| own-experience | references to the author's own projects or incidents | judged |
| date-format | date and number formatting | judged |

## AI-typical dimensions

Added because the author-contrast dimensions never needed them; an author DB will mostly record these as absences, which is exactly the evidence processing needs. The built-in counters of `textstats.py` (`ai_*`) implement the regexes below until the AI DB ships.

### negative-parallelism

| marker | definition | measure |
|---|---|---|
| not-but | "not X, but Y" | built-in `ai_not_but` |
| not-just | "not just X — it's Y" | built-in `ai_not_just` |

### significance-tails

| marker | definition | measure |
|---|---|---|
| significance-tail | "…, highlighting the importance of …" | built-in `ai_significance_tail` |
| worth-noting | "it's worth noting", "importantly", "crucially" | built-in `ai_worth_noting` |

### false-ranges

| marker | definition | measure |
|---|---|---|
| from-to | "from X to Y" spanning unrelated items | built-in `ai_false_range` (noisy; confirm by reading) |

### rule-of-three

| marker | definition | measure |
|---|---|---|
| triad | three coordinated items where two or four would do | built-in `ai_triad` |
| triple-adjective | three stacked adjectives | judged |

### summaries

| marker | definition | measure |
|---|---|---|
| summary-opener | *In conclusion, Overall, In summary* | built-in `ai_summary_opener` |
| closing-recap | final paragraph restating the piece | judged |
| section-recap | last sentence of a section restating the section | judged |

### scene-setting

| marker | definition | measure |
|---|---|---|
| era-opener | "In today's fast-paced world", "In the ever-evolving landscape" | `\b(?:in today[’']s\|in the (?:modern\|ever-evolving\|rapidly)\|in an era\|in a world where)\b` |
| imagine-opener | "Imagine …" as the first sentence | `(?:^\|\n\n)Imagine\b` |
| rhetorical-question-opener | piece opens with a rhetorical question | judged |
