#!/usr/bin/env python3
"""Measure style counters over Markdown/plain-text documents, per 1,000 words.

The write-like-me skill converges on *rates*: a rewrite is done when the
input's counters sit inside the range the author's own corpus shows, never at
zero and never at "always". Rates estimated by reading drift; this script makes
them reproducible so that measuring, rewriting, and re-measuring use the same
definitions. It carries a built-in set of generic counters (punctuation,
sentence and paragraph shape, person, contractions, emphasis, lexical habits,
and the AI-typical constructions of references/taxonomy.md), and it can
evaluate the `regex` and `stat` fields of style-DB patterns so DB rates and
input rates are computed the same way.

Usage
  textstats.py measure FILE... [--db DB...] [--sort-gap] [--setting S] [--register R] [--json]
      One column per file. With --db, every DB pattern that carries a `regex`
      or `stat` field (a statistic or a built-in counter, by name) is measured
      on each file and shown next to the DB's rate and per-document range, with
      a verdict: `too-short` when the input is too small for the pattern's rate
      to predict even one occurrence, so no count in it is evidence either way
      (unless the input overshoots the author's range maximum by more than one
      occurrence of its own: a removal is expressible at any length, and reads
      `gap`);
      `absent` when the input has none of a habit the author shows in most
      documents (the additive case, which the range test alone would miss
      whenever one corpus document put a 0 in the range); `gap` when the input
      falls outside the per-document range (widened by a small tolerance); `low`
      or `high` when it is inside the range but under half or over twice the
      corpus rate (the author does this, just not in every document); `match`
      otherwise. A DB of kind `ai` (the skill's data/ai-style-patterns.json)
      is measured the same way, but its rates are the machine's: `match` there
      means machine-typical, so its rows carry no class or gap — they are the
      AI-evidence column of the comparison table, not rewrite rows.
      --sort-gap and --setting add the two columns the processing comparison
      table is built from (references/processing.md, Step 2): each row's
      `class` — what a rewrite would do with it — and its `gap`, how big that
      edit is on the first file. --sort-gap orders rows by the gap, largest
      first; --setting soft|medium|hard marks `[manual]` every row whose
      evidence tier is above that setting's ceiling. Both are mechanical steps
      the rewrite would otherwise redo by hand for every pattern in the DB.
      --register R names the input's register (article, email, ...): a DB row
      whose `register_scope` excludes it is marked [out of scope] and classed
      neutral, since a scoped row is a target only for an input in one of its
      registers (references/processing.md, Step 3), and an out-of-scope AI row
      is not evidence. A register no profile document carries is accepted with
      a warning: the profile then has no evidence about it. With --sort-gap or
      --setting and several files, the first file is the input and every
      column's verdict is judged at its length, so a rewrite that came out
      shorter does not turn the rows it worked `too-short`. A row of the
      `lists` or `headings` dimensions is marked [structural], and classed
      neutral where the input has no list or heading at all: inapplicable. The
      tier column is the effective tier: the review round's override where one
      is set.
  textstats.py measure FILE... --vet
      Vetting view (references/technique.md, Step 2): every document whose rate
      on a high-signal AI marker stands out against the median of the others.
  textstats.py hits FILE... -e REGEX... [--stat NAME]... [-i] [-x EXCLUDE] [--unit U] [--matrix]
      Print a candidate counter's matches on corpus documents with context, on
      the same stripped prose `measure` and `styledb.py validate` count on: the
      raw count (what documents[].count records), the rate in the unit, hits an
      --exclude regex subtracts marked, and the DB fields to copy (ignore_case
      when -i was used). Several counters, or --matrix, print one line per
      counter with the count per file.
  textstats.py counters
      List the built-in counters and their definitions.

What is excluded before counting: front matter, fenced code, HTML comments and
block-level HTML elements (div, table, details, figure, script, style, iframe),
images, link URLs (link text stays), bare URLs, HTML tags, table rows, and
inline code, which becomes the placeholder `` (two backticks: not a word, so a
code span adds nothing to any rate, and a regex on `` counts the author's code
references); HTML entities are decoded. The prose a regex sees is the
paragraphs, then the list items, then the headings, each as its own block, so
a `^` anchor matches at the start of every one of them: a paragraph-opener
regex belongs in the share_of_paragraphs unit, which is evaluated over prose
paragraphs alone (share_of_sentences over their sentences). Headings and list
items count toward words and per-1k rates but not toward sentence-length or
paragraph statistics, because they are fragments by design.

A pattern's optional `exclude` regex subtracts false positives: a counter hit
that overlaps an `exclude` match is not counted, on the pattern's own regex or
on the built-in counter its `stat` names.

The built-in AI-marker counters (ai_*) are the executable definitions behind
the AI DB's `stat` fields — the DB carries their corpus rates and evidence — and
the fallback evidence when that DB is unavailable. Their definitions follow
references/taxonomy.md, whose AI-typical dimensions name the counter each marker
uses; counters marked "noisy" there over-count by design and their hits are
confirmed by reading.

Stdlib only, Python 3.8+.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import statistics
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
TABLE_RE = re.compile(r"^\s*\|")
HR_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
BLOCKQUOTE_RE = re.compile(r"^\s*>\s?")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’\-]*")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])[\"'”’)\]]*\s+(?=[\"'“‘(\[]?[A-Z0-9])")

# Inline code is replaced by this before counting: two backticks are not a word (WORD_RE never
# matches them), so a code span adds nothing to any rate, and a regex on `` counts the author's
# code references. The earlier placeholder, the word "code", counted as a word and fed every
# `\bcode\b` regex and the triad counter ("code, code and code").
CODE_PLACEHOLDER = "``"
BLOCK_HTML_RE = re.compile(r"<(div|table|details|figure|script|style|iframe)\b[^>]*>.*?</\1\s*>", re.S | re.I)
BARE_URL_RE = re.compile(r"https?://[^\s)>\]]+")

# The high-signal AI markers technique.md Step 2 vets a corpus document against the others on.
VET_MARKERS = ("em_dash", "ai_colon_punchline", "ai_comma_not", "ai_rather_than",
               "ai_verdict_opener", "ai_authenticity", "label_lead", "ai_vocabulary")

# Share of the author's documents that must show a habit before an input with none of it
# is called `absent` rather than merely low; matches the tier-1 spread rule in db-schema.md.
SPREAD_ABSENT = 0.6

# Strictness ceilings, mirroring SETTING_MAX_TIER in styledb.py (db-schema.md defines them).
# Duplicated rather than imported so that either script still runs on its own.
SETTING_MAX_TIER = {"soft": 1, "medium": 2, "hard": 3}

# The row classes that lead to an edit, and which the strictness setting therefore gates.
EDITING_CLASSES = ("remove", "add", "lean")

# name -> (regex, flags, description)
# Grouped by the taxonomy dimension that names the counter (references/taxonomy.md).
COUNTERS: Dict[str, Any] = {
    # punctuation
    "em_dash": (r"—|(?<=\S) -- (?=\S)|(?<=\S)--(?=\S)", 0, "em dashes (— or --)"),
    "em_dash_appositive": (r"(?:—|(?<=\S)--(?=\S))\s?(?:a|an|the|not|and|but|so|or) \w+", re.I, "em dash followed by a relabelling appositive or a coordinator"),
    "en_dash_spaced": (r"(?<=\s)–(?=\s)", 0, "spaced en dash used as a dash"),
    "semicolon": (r";", 0, "semicolons"),
    "colon": (r":(?=\s)", 0, "colons followed by whitespace"),
    "parenthesis": (r"\(", 0, "opening parentheses (asides)"),
    "scare_quote": (r"[\"“][\w'’ -]{2,25}[\"”]", 0, "short quoted phrase used as a coinage (noisy: short real quotes too)"),
    "exclamation": (r"!", 0, "exclamation marks"),
    "question": (r"\?", 0, "question marks"),
    "ellipsis": (r"\.\.\.|…", 0, "ellipses"),
    # voice, connectives, tone adverbs
    "contraction": (r"\b\w+n[’']t\b|\b(?:I|it|that|there|here|what|who|we|you|they|let)[’'](?:m|s|re|ve|ll|d)\b", re.I, "contractions"),
    "first_person_singular": (r"\b(?:I|I[’']m|I[’']ve|I[’']d|I[’']ll|me|my|mine|myself)\b(?!/)", 0, "I / me / my (not the I of I/O)"),
    "first_person_plural": (r"\b(?:we|we[’']re|we[’']ve|we[’']d|we[’']ll|our|ours|us|ourselves)\b", re.I, "we / our / us"),
    "second_person": (r"\b(?:you|you[’']re|you[’']ve|you[’']d|you[’']ll|your|yours|yourself)\b", re.I, "you / your"),
    "scholarly_connective": (r"(?:e\.g\.|i\.e\.|cf\.)|\b(?:in order to|in contrast|as well as|such as|for instance|for example)\b", re.I, "e.g., i.e., in order to, such as, as well as"),
    "deliberate_adverb": (r"\b(?:deliberately|deliberate|explicitly|precisely|intentionally|by design|on purpose)\b", re.I, "deliberately / explicitly / precisely / by design"),
    "quiet_adverb": (r"\b(?:quietly|silently|rarely|seldom|politely|happily)\b", re.I, "quietly / silently / rarely / politely"),
    # emphasis, lists, lexical
    "bold": (r"\*\*[^*\n]+\*\*|__[^_\n]+__", 0, "bold spans"),
    "italic": (r"(?<![*\w])\*[^*\n]+\*(?![*\w])|(?<![_\w])_[^_\n]+_(?![_\w])", 0, "italic spans"),
    "clause_bold": (r"\*\*[^*\n]{25,}\*\*|__[^_\n]{25,}__", 0, "bold applied to a whole clause or statistic (25+ chars)"),
    "label_lead": (r"^(?:\*\*|__|\*|_)[^*_\n]{1,60}(?:\*\*|__|\*|_)[.:]?\s", re.M, "list item or paragraph opening with a bold/italic label"),
    "hyphen_compound": (r"\b\w+-(?:aware|native|grade|first|ready|driven|centric|heavy|free|bound|compatible|facing|oriented|assisted|generated|augmented|powered|scale|class|copy|friction|overhead|agnostic|proof|safe)\b", re.I, "coined hyphenated modifiers (IDE-grade, theme-aware, agent-ready)"),
    "hedged_number": (r"\b(?:roughly|about|around|approximately|nearly|almost|close to|up to) [\$~]?\d|~\d", re.I, "precise figure behind a vagueness hedge (roughly 21%)"),
    "source_as_agent": (r"\b[A-Z]\w+(?: [A-Z]\w+)? (?:reports|finds|found|notes|says|describes|stresses|argues|warns|cautions|explicitly|puts|projects|estimates|suggests|has flagged)\b", 0, "institution as agent of a reporting verb (Gartner cautions) (noisy: people too)"),
    # contrast-frames
    "ai_not_but": (r"\b(?:not|isn[’']t|aren[’']t|wasn[’']t|weren[’']t|no longer)\b[^.;!?\n]{1,80}?[,;—–-]?\s+but\b", re.I, "negative parallelism: not X, but Y"),
    "ai_comma_not": (r", not (?:an? |the |just |merely |simply |yet another )?[\w'’-]+(?:[ \w'’-]){0,60}[.;:—]", re.I, "sentence-final negated foil: a feature, not an afterthought"),
    "ai_split_reframe": (r"\b(?:is|are|was|were|does|do|did)(?:n[’']t| not)\b[^.!?\n]{3,120}[.!?]\s+(?:It|They|That|This)(?:[’']s| is| are| was| means)\b", 0, "X is not A. It is B. (negation and reframe in two sentences)"),
    "ai_rather_than": (r"\brather than\b|\binstead of\b|(?:^|(?<=[.!?]\s))Instead\b", re.I | re.M, "rather than / instead of / Instead,"),
    "ai_without_benefit": (r"\bwithout (?:\w+ ){0,2}(?!(?:some|any|no|every)?things?\b|during\b|(?:s|w|br|th)ing\b)\w+ing\b", re.I, "benefit as avoided cost: without building X (noisy)"),
    # reveal-frames
    "ai_colon_punchline": (r"(?:^|(?<=[.!?] ))[A-Z][^.:!?\n]{2,45}: [a-z]", re.M, "short setup, colon, payoff: The first proof: an OCT plugin"),
    "ai_nominal_reveal": (r"(?:^|(?<=[.!?] ))(?:The (?:result|good news|bad news|catch|flip side|upshot|bottom line|practical rule|broader lesson|key|idea|answer|point|goal|difference|takeaway|(?:important|interesting|unexpected|real|hard|short|honest|useful) (?:part|answer|question|thing|test|lesson|story))|Here[’']s (?:the|a|what|where|why|how)|That(?:[’']s| is) the (?:idea|question|thinking|principle) behind)\b", re.M, "abstract-noun payoff: The result is…, Here's the unexpected part:"),
    "ai_verdict_opener": (r"(?:^|(?<=[.!?] ))(?:That|This)(?:[’']s| is| was| means| matters| changes| makes| favou?rs| creates| explains| gives| keeps| leaves| alone)\b", re.M, "sentence-initial That/This + verdict verb: That changes today."),
    "ai_question_answer": (r"\?\s+[A-Z][^?.!\n]{3,120}[.!]", 0, "rhetorical question answered by the next sentence (noisy)"),
    "ai_what_if": (r"\bWhat (?:if|happens when|about)\b", re.I, "What if / What happens when hooks"),
    "ai_enumeration_announcement": (r"(?:^|(?<=[.!?] ))(?:Two|Three|Four|Five|Six|Several|A few) [\w-]+ (?:are|is|carry|decide|complete|keep|multiply|drive|share|stand|make|matter|get|follow|explain|come|emerge|help|define|remain|deserve|solve)\b|\b(?:two|three|four|five) (?:things|reasons|principles|forces|concerns|questions|directions|ways|halves|parts|lessons)\b", re.I | re.M, "counted promise before a list: Four principles carry…"),
    # significance-tails
    "ai_significance_tail": (r"\b(?:highlight(?:s|ing)?|underscor(?:es|ing)|emphasiz(?:es|ing)|showcas(?:es|ing)|demonstrat(?:es|ing))\s+(?:the\s+)?(?:importance|significance|need|value|role|power|potential)\b|\b(?:that|this|it|which) matters\b|\bmatters? (?:because|more than|especially|commercially|most)\b|\bwhy [\w -]{1,40} matters?\b|(?:^|(?<=[.!?] ))For [\w -]{3,40}, (?:this|that) \w+", re.I | re.M, "significance-flagging tails: highlighting the importance, that matters because, why X matters"),
    "ai_worth_noting": (r"\b(?:it[’']s worth noting|it is worth noting|it[’']s important to note|it is important to note|notably|importantly|crucially|worth (?:noting|knowing|flagging|weighing|asking|stating|mentioning|remembering|a look|a lot)|deserves? (?:special |a )?(?:respect|attention|mention|a closer look))\b", re.I, "worth-noting hedges: it's worth noting, worth knowing, deserves special respect"),
    "ai_participial_tail": (r"[,—] (?:enabling|eliminating|allowing|giving|making|reducing|ensuring|accelerating|removing|leaving|keeping|turning|letting|freeing|unlocking|empowering|creating|delivering|providing) ", re.I, "present-participle benefit tail: …, enabling X and eliminating Y"),
    # rule-of-three
    "ai_triad": (r"\b[\w'’-]+, [\w'’-]+,? and [\w'’-]+\b", 0, "word triads (rule of three)"),
    "ai_adjective_stack": (r"\b(?:clean|robust|predictable|natural|flexible|sleek|rich|deliberate|lightweight|simple|fast|small|modern|powerful|accurate|reliable|scalable|elegant|seamless|thoughtful|practical|concrete|serious|honest|dense|polished), [\w-]+ [a-z]+\b", re.I, "stacked evaluative adjectives: clean, human-readable rules (seed list)"),
    # signposting, paragraph-openers
    "ai_summary_opener": (r"(?:^|(?<=[.!?]\s))(?:in conclusion|in summary|to sum up|overall|ultimately|to summarize|in short|all in all)\b", re.I | re.M, "summary openers"),
    "ai_meta_signpost": (r"\b(?:this|the) (?:article|talk|session|post|piece|report|series|section|guide) (?:looks|shows|walks|explains|lays|covers|explores|opens|kicks|is about|shares|presents|provides|dissects|introduces|describes|argues)\b|\bwe[’']ll (?:also )?(?:look|walk|show|cover|close|talk|see|start)\b|\bin (?:this|the following) (?:article|post|section|talk)\b", re.I, "the text announcing its own plan: This article looks at…, We'll close with…"),
    "ai_scene_imperative": (r"(?:^|(?<=[.!?] ))(?:Imagine|Consider|Picture|Suppose|Think of)\b", re.M, "Imagine / Consider / Picture / Suppose as a scene-setting imperative"),
    "ai_negated_opener": (r"^[^.!?\n]{0,60}\b(?:shouldn[’']t|should not|doesn[’']t have to|does not have to|is not something|isn[’']t something|rarely|no longer)\b", re.I | re.M, "paragraph opens by negating a status quo: X shouldn't be limited to Y"),
    # connectives (AI-typical placements)
    "ai_connective_opener": (r"(?:^|(?<=[.!?]\s))(?:additionally|furthermore|moreover|however|therefore|thus|consequently|in addition)\b", re.I | re.M, "sentence-initial formal connectives"),
    "ai_medial_therefore": (r"\b(?!(?:and|or|but|is|are|was|were|will|can|should|would|may|might)\b)\w+ (?:therefore|consequently|thus) \w+", re.I, "therefore / consequently / thus after the subject: Custom development therefore shifts"),
    # authenticity-stance
    "ai_authenticity": (r"\b(?:actually|actual|genuinely|genuine|honest|honestly|real|truly|plainly)\b", re.I, "authenticity words: actually, genuinely, real, honest"),
    "ai_absolutizer": (r"\b(?:every|everyone|everything|entire|entirely|never|always|exactly|completely|all of|none of|nothing|anyone who)\b", re.I, "flat universals: every, everyone, never, always, exactly"),
    "ai_anti_hype": (r"\b(?:hype|hyped|magic|magical|magically|slop|silver bullet|buzzwords?|wishlist|snake oil|(?:built|run) on hope|no magic)\b", re.I, "anti-hype stance: no hype, no magic; not magic"),
    # stock-phrasing
    "ai_vocabulary": (r"\b(?:delv(?:e|es|ing)|tapestry|landscape|seamless(?:ly)?|robust(?:ly|ness)?|leverag(?:e|es|ing)|crucial(?:ly)?|pivotal|vibrant|multifaceted|navigat(?:e|es|ing)|foster(?:s|ing)?|comprehensive|streamlin(?:e|es|ing)|realm|testament|embark(?:s|ing)?|elevat(?:e|es|ing)|unlock(?:s|ed|ing)?|harness(?:es|ing)?|empower(?:s|ed|ing)?|game-chang(?:er|ing)|cutting-edge|transformative|state-of-the-art|blazing-fast|next-generation|paradigm|holistic|actionable|supercharg(?:e|es|ing)|frictionless(?:ly)?|democratiz(?:e|es|ing|ation))\b", re.I, "marketing buzzwords (strongest for Gemini-class output)"),
    "ai_trend_word": (r"\b(?:increasingly|rapidly|dramatically|drastically|sharply|exponentially|ever-evolving|evolving|transformation|revolution(?:iz\w+)?|reshap(?:e|es|ing)|accelerat(?:e|es|ing|ion)|surg(?:e|es|ing)|explod(?:e|es|ed|ing)|no longer|than ever)\b", re.I, "unfalsifiable change words: increasingly, rapidly, transformation, than ever"),
    "ai_spatial_metaphor": (r"\b(?:bridg(?:e|es|ing)|gaps?|silos?|siloed|friction|barriers?|divide|boundaries|island|bottleneck)\b", re.I, "the problem as a space to cross: bridge, gap, silo, friction (noisy)"),
    "ai_stock_idiom": (r"\b(?:table stakes|heavy lifting|under the hood|from scratch|out of the box|on the rails|load-bearing|connective tissue|first-class citizen|plug-and-play|silver bullet|low-hanging fruit|moving parts|double-edged sword|best of both worlds|at the end of the day|in the driver[’']s seat|the hard parts?|pain points?|north star|guardrails)\b", re.I, "borrowed idioms: table stakes, heavy lifting, under the hood"),
    "ai_false_range": (r"\bfrom [\w'’-]+(?: [\w'’-]+)? to [\w'’-]+(?: [\w'’-]+)?\b", re.I, "from X to Y ranges (noisy: includes real ranges)"),
    "ai_same_x": (r"\bthe same [\w-]+(?: [\w-]+)? (?:that|as|which|to|for)\b", re.I, "the unity trope: the same X that / as"),
}

STATS_HELP = {
    "words": "word count",
    "sentences": "sentence count (prose paragraphs only)",
    "sentence_len_mean": "mean words per sentence",
    "sentence_len_median": "median words per sentence",
    "sentence_len_p90": "90th percentile words per sentence",
    "sentence_len_max": "longest sentence, words",
    "short_sentence_share": "share of sentences with <= 8 words",
    "long_sentence_share": "share of sentences with >= 30 words",
    "paragraphs": "prose paragraph count",
    "paragraph_sentences_mean": "mean sentences per paragraph",
    "one_sentence_paragraph_share": "share of paragraphs with one sentence",
    "paragraph_opener_i_share": "share of paragraphs opening with I/I'm/I've",
    "paragraph_opener_the_share": "share of paragraphs opening with The/This/These",
    "headings": "heading count",
    "colon_heading_share": "share of headings of the form 'Hook: Subtitle'",
    "heading_title_case_share": "share of multi-word headings in Title Case",
    "list_items": "list item count",
    "list_items_per_1k": "list items per 1k words",
    "headings_per_1k": "headings per 1k words",
}

# The unit each statistic's value is in, which is the unit a DB pattern naming it in `stat` must
# carry: `styledb.py validate` rejects a mismatch, because a per-1k statistic filed under `count`
# validates and is wrong (references/db-schema.md, Pattern entries). Built-in counters count per
# 1k words. Length statistics are in `words` — sentence length literally, sentences per paragraph
# as the same kind of number.
STAT_UNITS = {
    "words": "count", "sentences": "count", "paragraphs": "count", "headings": "count",
    "list_items": "count",
    "sentence_len_mean": "words", "sentence_len_median": "words", "sentence_len_p90": "words",
    "sentence_len_max": "words", "paragraph_sentences_mean": "words",
    "short_sentence_share": "share_of_sentences", "long_sentence_share": "share_of_sentences",
    "one_sentence_paragraph_share": "share_of_paragraphs",
    "paragraph_opener_i_share": "share_of_paragraphs", "paragraph_opener_the_share": "share_of_paragraphs",
    "colon_heading_share": "share_of_headings", "heading_title_case_share": "share_of_headings",
    "list_items_per_1k": "per_1k_words", "headings_per_1k": "per_1k_words",
}


class Document:
    def __init__(self, text: str) -> None:
        self.raw = text
        self.headings: List[str] = []
        self.list_items: List[str] = []
        self.paragraphs: List[str] = []
        self._parse(text)
        self.prose = "\n\n".join(self.paragraphs + self.list_items + self.headings)
        self.sentences: List[str] = []
        for para in self.paragraphs:
            self.sentences.extend(split_sentences(para))
        self.words = len(WORD_RE.findall(self.prose))

    def _parse(self, text: str) -> None:
        text = text.replace("\r\n", "\n")
        if text.startswith("---\n"):
            end = text.find("\n---", 4)
            if end != -1:
                text = text[end + 4:]
        text = re.sub(r"^(```|~~~).*?^\1\s*$", "\n", text, flags=re.S | re.M)
        # Comments first: the tag stripper alone stops at the first `>` inside one ("publisher =>
        # namespace") and leaks the rest into the prose. Block-level HTML is layout, not prose.
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        text = BLOCK_HTML_RE.sub("", text)
        text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
        text = re.sub(r"<[^>\n]+>", "", text)
        text = BARE_URL_RE.sub("", text)
        text = re.sub(r"`[^`\n]*`", CODE_PLACEHOLDER, text)
        # Entities last, once the tags are gone, so a literal `&lt;div&gt;` in prose stays text.
        # Undecoded, their `;` counted as semicolons and `&mdash;` was invisible to em_dash.
        text = html.unescape(text)
        buf: List[str] = []

        def flush() -> None:
            if buf:
                self.paragraphs.append(" ".join(s.strip() for s in buf))
                buf.clear()

        for line in text.split("\n"):
            if not line.strip() or HR_RE.match(line) or TABLE_RE.match(line):
                flush()
                continue
            m = HEADING_RE.match(line)
            if m:
                flush()
                self.headings.append(m.group(1))
                continue
            m = LIST_ITEM_RE.match(line)
            if m:
                flush()
                self.list_items.append(m.group(1))
                continue
            line = BLOCKQUOTE_RE.sub("", line)
            buf.append(line)
        flush()


def is_title_case(heading: str) -> bool:
    """True when a heading of 2+ words capitalizes every word longer than three letters."""
    words = [w for w in re.findall(r"[A-Za-z][\w'’-]*", heading) if len(w) > 3]
    return len(words) >= 2 and all(w[0].isupper() for w in words)


def split_sentences(paragraph: str) -> List[str]:
    text = re.sub(r"\b(?:e\.g|i\.e|etc|vs|cf|approx|Mr|Ms|Dr|Prof|St|No)\.", lambda m: m.group(0).replace(".", ""), paragraph)
    parts = [s.strip() for s in SENTENCE_SPLIT_RE.split(text)]
    return [s for s in parts if WORD_RE.search(s)]


def count(regex: str, flags: int, text: str) -> int:
    return len(re.findall(regex, text, flags))


def percentile(values: Sequence[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, int(round(pct / 100 * (len(ordered) - 1)))))
    return float(ordered[idx])


def measure(text: str) -> Dict[str, Any]:
    doc = Document(text)
    words = doc.words or 1
    lens = [len(WORD_RE.findall(s)) for s in doc.sentences]
    paras = [split_sentences(p) for p in doc.paragraphs]
    n_par = len(paras) or 1
    first_words = [re.match(r"\W*([\w'’]+)", p).group(1) if re.match(r"\W*([\w'’]+)", p) else "" for p in doc.paragraphs]
    stats: Dict[str, Any] = {
        "words": doc.words,
        "sentences": len(lens),
        "sentence_len_mean": round(statistics.mean(lens), 1) if lens else 0.0,
        "sentence_len_median": float(statistics.median(lens)) if lens else 0.0,
        "sentence_len_p90": percentile(lens, 90),
        "sentence_len_max": float(max(lens)) if lens else 0.0,
        "short_sentence_share": round(sum(1 for n in lens if n <= 8) / (len(lens) or 1), 3),
        "long_sentence_share": round(sum(1 for n in lens if n >= 30) / (len(lens) or 1), 3),
        "paragraphs": len(paras),
        "paragraph_sentences_mean": round(sum(len(p) for p in paras) / n_par, 2) if paras else 0.0,
        "one_sentence_paragraph_share": round(sum(1 for p in paras if len(p) == 1) / n_par, 3) if paras else 0.0,
        "paragraph_opener_i_share": round(sum(1 for w in first_words if re.match(r"I(?:[’']\w+)?$", w)) / n_par, 3) if paras else 0.0,
        "paragraph_opener_the_share": round(sum(1 for w in first_words if w in ("The", "This", "These", "That")) / n_par, 3) if paras else 0.0,
        "headings": len(doc.headings),
        "colon_heading_share": round(sum(1 for h in doc.headings if ": " in h) / (len(doc.headings) or 1), 3),
        "heading_title_case_share": round(sum(1 for h in doc.headings if is_title_case(h)) / (len(doc.headings) or 1), 3),
        "list_items": len(doc.list_items),
        "list_items_per_1k": round(len(doc.list_items) / words * 1000, 2),
        "headings_per_1k": round(len(doc.headings) / words * 1000, 2),
    }
    per_1k: Dict[str, float] = {}
    for name, (regex, flags, _) in COUNTERS.items():
        per_1k[name] = round(count(regex, flags, doc.prose) / words * 1000, 2)
    return {"stats": stats, "per_1k": per_1k, "_doc": doc}


def compiled_counter(pattern: Dict[str, Any]) -> Optional[Tuple[str, int]]:
    """(regex, flags) of a pattern's counter when it is a regex over the prose: the pattern's own
    `regex`, or the built-in counter its `stat` names. None for a statistic or a judged pattern."""
    if pattern.get("regex"):
        return pattern["regex"], (re.I if pattern.get("ignore_case") else 0) | re.M
    name = pattern.get("stat")
    if name in COUNTERS:
        regex, flags, _ = COUNTERS[name]
        return regex, flags
    return None


def matches(regex: str, flags: int, text: str, exclude: Optional[str] = None) -> List[Tuple[int, int, bool]]:
    """Every match span of a counter on `text`, flagged True when an `exclude` match overlaps it.

    The overlap rule is what lets an `exclude` name a false positive by its context rather than
    by the counter's own match: `This is (?:caused|done) by` overlaps the `This is` a verdict-opener
    counter matched, and the hit is dropped.
    """
    spans = [(m.start(), m.end()) for m in re.finditer(regex, text, flags)]
    if not exclude or not spans:
        return [(s, e, False) for s, e in spans]
    banned = [(m.start(), max(m.end(), m.start() + 1)) for m in re.finditer(exclude, text, flags)]
    return [(s, e, any(bs < max(e, s + 1) and be > s for bs, be in banned)) for s, e in spans]


def count_pattern(pattern: Dict[str, Any], result: Dict[str, Any]) -> Optional[int]:
    """Raw occurrences of a pattern in a measured document: the number a per-1k pattern's
    documents[].count records and `styledb.py validate --corpus-dir` re-runs.

    The counter's matches minus the ones `exclude` overlaps, or the numerator of a per-1k
    statistic (`list_items` for `list_items_per_1k`). None when nothing counts occurrences: a
    judged pattern, or a statistic that is not a per-1k one.
    """
    counter = compiled_counter(pattern)
    if counter:
        regex, flags = counter
        return sum(1 for _, _, excluded in matches(regex, flags, result["_doc"].prose, pattern.get("exclude"))
                   if not excluded)
    name = pattern.get("stat") or ""
    if name.endswith("_per_1k") and name[:-len("_per_1k")] in result["stats"]:
        return int(result["stats"][name[:-len("_per_1k")]])
    return None


def measure_pattern(pattern: Dict[str, Any], result: Dict[str, Any]) -> Optional[float]:
    """Rate of a DB pattern on a measured document, in the pattern's unit."""
    doc: Document = result["_doc"]
    unit = pattern.get("unit", "per_1k_words")
    counter = compiled_counter(pattern)
    if counter is None:
        if pattern.get("stat"):
            return result["stats"].get(pattern["stat"])  # a statistic, in its own unit; None if unknown
        return None
    regex, flags = counter
    if unit == "per_1k_words":
        return round((count_pattern(pattern, result) or 0) / (doc.words or 1) * 1000, 2)
    if unit == "share_of_sentences":
        units = doc.sentences
    elif unit == "share_of_paragraphs":
        units = doc.paragraphs
    elif unit == "share_of_headings":
        units = doc.headings
    else:
        return round(float(count_pattern(pattern, result) or 0), 2)
    if not units:
        return 0.0
    exclude = pattern.get("exclude")
    hit = sum(1 for u in units if any(not x for _, _, x in matches(regex, flags, u, exclude)))
    return round(hit / len(units), 3)


def unit_denominator(pattern: Dict[str, Any], stats: Optional[Dict[str, Any]]) -> Optional[float]:
    """The factor that turns this pattern's rate into a count of occurrences in a document.

    None when the unit is not a rate over the document (raw counts, length stats in words),
    or when the document's stats are not at hand — in both cases the pattern's own value is
    already the comparable number.
    """
    if not stats:
        return None
    unit = pattern.get("unit", "per_1k_words")
    if unit == "per_1k_words":
        return stats.get("words", 0) / 1000.0
    if unit == "share_of_sentences":
        return float(stats.get("sentences", 0))
    if unit == "share_of_paragraphs":
        return float(stats.get("paragraphs", 0))
    if unit == "share_of_headings":
        return float(stats.get("headings", 0))
    return None


def expected_occurrences(pattern: Dict[str, Any], stats: Optional[Dict[str, Any]]) -> Optional[float]:
    """How many occurrences the author's own rate predicts in a document this size.

    Below one, the rate says nothing about this document: the author would have produced
    none either, so a zero count is not evidence of anything and neither is a single one.
    """
    if not stats or pattern.get("rate") is None or pattern.get("kind") == "absence":
        return None
    denom = unit_denominator(pattern, stats)
    return None if denom is None else float(pattern["rate"]) * denom


def verdict(value: Optional[float], pattern: Dict[str, Any],
            stats: Optional[Dict[str, Any]] = None) -> str:
    if value is None or pattern.get("rate") is None:
        return "n/a"
    if pattern.get("kind") == "absence":
        return "match" if value == 0 else "gap"
    rate = float(pattern["rate"])
    rng = pattern.get("range") or [rate, rate]
    lo, hi = float(rng[0]), float(rng[1])
    tol = max(0.1 * max(abs(lo), abs(hi)), 0.5 if pattern.get("unit", "per_1k_words") == "per_1k_words" else 0.05)
    # Rates quantize: in a document of N words one occurrence is worth 1000/N, so a habit
    # the author's rate predicts less than once here cannot be a target in either
    # direction — chasing it would put the text far past the author's own rate. Removal is
    # the exception: the author's range maximum is expressible at any length, as zero is
    # for an absence pattern, so an input that overshoots it by more than one occurrence
    # of its own is judged like any other. One occurrence is the slack, because that is
    # what an author at their maximum could have put into a document this size.
    expected = expected_occurrences(pattern, stats)
    if expected is not None and expected < 1.0:
        denom = unit_denominator(pattern, stats) or 0.0
        if denom <= 0 or value <= hi + max(tol, 1.0 / denom):
            return "too-short"
    # A habit the author shows in most documents and the input shows not at all is the
    # additive case, and it needs its own verdict: one corpus document without the habit
    # puts 0 inside the range, so the range test below would report "inside the range,
    # merely low" and the rewrite would leave the author's most recognizable habits out.
    # The 0.6 spread is the one the tier-1 rule already asks for (db-schema.md).
    if value == 0 and rate > 0 and float(pattern.get("spread") or 0.0) >= SPREAD_ABSENT:
        return "absent"
    if not (lo - tol <= value <= hi + tol):
        return "gap"
    if rate > 0 and value < 0.5 * rate:
        return "low"
    if rate > 0 and value > 2.0 * rate:
        return "high"
    return "match"


def effective_tier(pattern: Dict[str, Any]) -> int:
    """The tier a strictness setting is compared against: the review round's override, else
    the derived tier. Mirrors effective_tier in styledb.py."""
    override = pattern.get("tier_override")
    if isinstance(override, int) and 1 <= override <= 3:
        return override
    return int(pattern.get("tier", 3))


def classify(value: Optional[float], pattern: Dict[str, Any], verd: str) -> str:
    """What a rewrite would do with this row — the Step 2 classes of processing.md.

    `remove` and `add` are the rewrite rows, `lean` the ones a substitution can shift where
    the input already offers a slot, `do-not-touch` a coordinate already inside the author's
    region, `neutral` a row that says nothing either way. The high- against low-confidence
    split inside `remove` needs the AI-evidence column and stays with the reader; an absence
    row (author rate 0) is the high-confidence case by rule.
    """
    if verd == "match":
        return "do-not-touch"
    if verd == "absent":
        return "add"
    if verd in ("low", "high"):
        return "lean"
    if verd == "gap":
        rate = float(pattern.get("rate") or 0.0)
        rng = pattern.get("range") or [rate, rate]
        return "remove" if float(value) > float(rng[1]) else "add"
    return "neutral"


WORD_ALTERNATION_RE = re.compile(r"[\w' -]+(?:\|[\w' -]+)+")


def group_bodies(rx: str) -> List[str]:
    """The body of every parenthesised group in `rx`, innermost first.

    A hand-rolled scan rather than a regex, because groups nest: it skips escaped
    characters and the insides of character classes, so a `[.!?]` or a `\\(` never opens
    or closes a group. `(?:` is stripped from the body it introduces; every other group
    prefix (a lookaround's `?<=`, `?=`, `?!`) is left in place, which is what keeps such
    a group from reading as a word list.
    """
    bodies, stack, i, in_class = [], [], 0, False
    while i < len(rx):
        ch = rx[i]
        if ch == "\\":
            i += 2
            continue
        if in_class:
            in_class = ch != "]"
        elif ch == "[":
            in_class = True
        elif ch == "(":
            stack.append(i)
        elif ch == ")" and stack:
            body = rx[stack.pop() + 1:i]
            bodies.append(body[2:] if body.startswith("?:") else body)
        i += 1
    return bodies


def is_enumeration(pattern: Dict[str, Any]) -> bool:
    """True when the counter names a closed list of literal forms somewhere in its rule.

    Such a counter sees only the members it names, so `match` on its row says the named
    forms are at the author's rate and says nothing about the rest of the family — the
    `-ize` a British-spelling alternation never listed. Detected structurally: an
    alternation whose branches are plain words, either as the whole regex or as one group
    inside it. The group case is the common one and the easiest to miss by eye: the closed
    list is a verb or modal slot embedded in a general rule, as in `, which (?:is|means|
    allows)` or `(?:can|cannot|must) … be \\w+ed`, where the surrounding structure is
    genuinely general and only the listed slot is closed. Reading such a row as a general
    rule is how a real instance of the habit — a `, which enables`, a `can't be mapped` —
    comes back `absent` and pushes a rewrite to swap a word that was already the author's.
    """
    rx = pattern.get("regex")
    if not rx or "|" not in rx:
        return False
    bare = re.sub(r"\\b|\(\?:|\(\?i\)|[()]", "", rx)
    if WORD_ALTERNATION_RE.fullmatch(bare):
        return True
    return any(WORD_ALTERNATION_RE.fullmatch(body) for body in group_bodies(rx))


def ai_evidence(pattern: Dict[str, Any], direction: str, ai_verdicts: Dict[str, str]) -> str:
    """The confidence behind a remove row — the comparison table's AI-evidence column.

    `high` where the machine side backs the removal: an AI DB row of the same taxonomy id
    measuring the input at machine-typical rates, or one of the author's own absence
    patterns (rate 0, high-confidence by rule). `low` where nothing machine-side does, so
    the excess could be a generator quirk or an effect of the topic. Only removals carry
    one; processing.md Step 2.
    """
    if direction != "remove":
        return "—"
    if pattern.get("kind") == "absence" or not float(pattern.get("rate") or 0.0):
        return "high"
    return "high" if ai_verdicts.get(pattern["id"]) in ("match", "high") else "low"


def row_direction(cls: str, verd: str) -> Tuple[str, str]:
    """(direction, table label) of a rewrite row. A lean row moves the way its verdict says —
    `high` is worked down like a removal and carries AI evidence, `low` up like an addition —
    and the label says so. `keep` is a do-not-touch row a tone brief moved, which no counter
    can see, so the table never prints it."""
    if cls == "lean":
        d = "remove" if verd == "high" else "add"
        return d, d + " (lean)"
    return cls, cls

# The two taxonomy dimensions whose rows describe document shape rather than prose. What
# the author does when they choose the shape says nothing about the shape an input already
# has, and structure_check.py owns that: a row here never licenses adding or removing a
# list or a heading (processing.md Step 6).
STRUCTURAL_DIMENSIONS = ("lists", "headings")


def is_structural(pattern: Dict[str, Any]) -> bool:
    return pattern["id"].split("/", 1)[0] in STRUCTURAL_DIMENSIONS


def is_inapplicable(pattern: Dict[str, Any], stats: Dict[str, Any]) -> bool:
    """True for a structural row when the input has none of the shape it is about — no list
    for a `lists` row, no heading for a `headings` row. Such a row could only be met by adding
    a block, which the structure invariant forbids, so where it asks for an edit it is neutral:
    inapplicable to this input, and reported as such rather than worked. Where it already
    matches it stays a do-not-touch row."""
    dim = pattern["id"].split("/", 1)[0]
    if dim == "lists":
        return not stats.get("list_items")
    if dim == "headings":
        return not stats.get("headings")
    return False


def in_scope(pattern: Dict[str, Any], register: Optional[str]) -> bool:
    """False when the input's register is known and the pattern's `register_scope` excludes it —
    a scoped row is a target only for an input in one of its registers (processing.md Step 3)."""
    scope = pattern.get("register_scope")
    return not (register and scope) or register in scope


def scope_mark(pattern: Dict[str, Any], register: Optional[str]) -> str:
    """The name suffix that keeps a scoped row visible: its scope when the input's register is
    unknown, [out of scope] when it is known and excluded, nothing when it is known and inside."""
    scope = pattern.get("register_scope")
    if not scope:
        return ""
    if register:
        return "" if register in scope else " [out of scope]"
    return " [scope: {}]".format(", ".join(scope))


def cmd_report_table(args: argparse.Namespace, results: List[Tuple[str, Dict[str, Any]]],
                     dbs: List[Tuple[str, Dict[str, Any]]], max_tier: int) -> int:
    """The report's measured sections as markdown, so no figure in them is retyped.

    Everything here is a transcription of this run's own measurement of the delivered
    file; the sections the counters cannot fill — not-converged, side effects, open
    questions — stay with the writer (processing.md Step 7).
    """
    _, first = results[0]
    ai_verdicts = {}
    for _, db in dbs:
        if db.get("kind") != "ai":
            continue
        for p in db.get("patterns", []):
            v = measure_pattern(p, first)
            if v is not None and in_scope(p, args.register):
                ai_verdicts[p["id"]] = verdict(v, p, first["stats"])
    two = len(results) > 1
    rows, keep, manual, judged = [], [], [], []
    enum = structural = False
    for _, db in dbs:
        if db.get("kind") == "ai":
            continue
        for p in db.get("patterns", []):
            values = [measure_pattern(p, r) for _, r in results]
            name = p["id"] + (" [enum]" if is_enumeration(p) else "") + scope_mark(p, args.register)
            if values[0] is None:
                if all(v is None for v in values):
                    judged.append((p, name))
                continue
            verd = verdict(values[0], p, first["stats"])
            cls = classify(values[0], p, verd)
            enum = enum or is_enumeration(p)
            if is_structural(p):
                name += " [structural]"
                structural = True
            rng = p.get("range")
            rate = "{} ({})".format(fmt(p.get("rate")),
                                    "{}–{}".format(fmt(rng[0]), fmt(rng[1])) if rng else "-")
            if not in_scope(p, args.register):
                if cls in EDITING_CLASSES:
                    manual.append("- {} — scoped to {}; the input is {} and a scoped row is a "
                                  "target only inside its registers".format(
                                      name, ", ".join(p["register_scope"]), args.register))
                continue
            if cls == "do-not-touch":
                keep.append("- {} — input {}, author {}".format(name, fmt(values[0]), rate))
                continue
            if cls not in EDITING_CLASSES:
                continue
            if is_inapplicable(p, first["stats"]):
                manual.append("- {} — a shape row, and the input has no {}: inapplicable, the "
                              "structure invariant wins".format(
                                  name, "list" if p["id"].startswith("lists/") else "heading"))
                continue
            if args.setting and effective_tier(p) > max_tier:
                manual.append("- {} — tier {} is above the {} setting's ceiling of {}"
                              .format(name, effective_tier(p), args.setting, max_tier))
                continue
            d, label = row_direction(cls, verd)
            cells = [name, label, str(effective_tier(p)), ai_evidence(p, d, ai_verdicts), fmt(values[0])]
            if two:
                cells.append(fmt(values[-1]))
            # judged at the input's length: the rewrite's own shorter count must not turn a
            # row it worked `too-short` (processing.md, Step 6)
            cells += [rate, verdict(values[-1], p, first["stats"]) if values[-1] is not None else "-"]
            rows.append((gap_size(values[0], p, first["stats"], verd) or 0.0, cells))
    rows.sort(key=lambda t: -t[0])
    head = ["pattern", "direction", "tier", "AI evidence", "input"]
    if two:
        head.append("rewritten")
    head += ["author rate (range)", "verdict"]
    sys.stderr.write(
        "report table: measured from {}. Paste it; do not retype a figure, and do not "
        "carry one over from an earlier convergence round. The not-converged, side-effect "
        "and open-question sections are yours to write. The tier column is the effective "
        "tier (the review round's override where set).\n".format(
            " and ".join(n for n, _ in results)))
    if enum:
        sys.stderr.write(
            "[enum] marks a counter that enumerates forms: `match` there covers only the "
            "forms it names, so read for the rest of the family before calling it done.\n")
    if structural:
        sys.stderr.write(
            "[structural] marks a row about document shape. It describes what the author "
            "writes when the shape is theirs to choose, and never licenses adding or "
            "removing a list or a heading the input has: the structure invariant wins and "
            "the row goes to the report as inapplicable to this input — where the input has "
            "no list or heading at all it is already listed there, under the manual pass.\n")
    if not args.register and any("[scope:" in c[0] for _, c in rows):
        sys.stderr.write(
            "[scope: ...] marks a register-scoped row; pass --register with the input's "
            "register to have the out-of-scope ones set aside mechanically.\n")
    print("## Before / after")
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    for _, cells in rows:
        print("| " + " | ".join(cells) + " |")
    print()
    print("## Do-not-touch (input already matched the author)")
    print("\n".join(keep) if keep else "- none")
    print()
    print("## Left for the manual pass")
    print("\n".join(manual) if manual else "- none")
    print()
    print("## Read for these (judged patterns — no counter, so no row above)")
    print("\n".join("- {} (tier {}) — {}".format(name, effective_tier(p), p.get("description", ""))
                    for p, name in judged) if judged else "- none")
    return 0


def gap_size(value: Optional[float], pattern: Dict[str, Any],
             stats: Optional[Dict[str, Any]] = None,
             verd: Optional[str] = None) -> Optional[float]:
    """How big the edit is: the distance from the author's rate, in occurrences of this document.

    This is the comparison table's sort key and only that — a per-row number, never summed
    across rows, because the axes measure different things and a document has no single
    distance to the author (SKILL.md). Eight missing "I"s outrank one stray em dash because
    eight sentences are involved, not because the em dash matters less; the class says what
    kind of edit it is. Rows a rewrite has no business touching are 0 whatever the arithmetic
    says — `match` is already the author's, and in a `too-short` row no count is evidence —
    so a gap above 0 means exactly "this row asks for an edit".
    """
    if value is None or pattern.get("rate") is None:
        return None
    if verd is None:
        verd = verdict(value, pattern, stats)
    if verd in ("match", "too-short"):
        return 0.0
    delta = abs(float(value) - float(pattern["rate"]))
    denom = unit_denominator(pattern, stats)
    return round(delta * denom if denom is not None else delta, 2)


def fmt(v: Any) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return "{:g}".format(v)
    return str(v)


def vet_outliers(results: List[Tuple[str, Dict[str, Any]]]) -> List[Tuple[str, str, float, float, float]]:
    """(file, marker, value, median of the others, max of the others) for every document whose
    rate on a high-signal AI marker is half again the highest of the other documents and at least
    one per 1k words above their median — technique.md Step 2's "your others have 0, this one
    has 12 — was it AI-assisted?". A question for the author, not a verdict; against the
    highest of the rest rather than the median, or a marker most documents show a little of
    lists a third of the corpus."""
    out = []
    for i, (name, r) in enumerate(results):
        for marker in VET_MARKERS:
            others = [q["per_1k"][marker] for j, (_, q) in enumerate(results) if j != i]
            if not others:
                continue
            med, top = float(statistics.median(others)), max(others)
            value = r["per_1k"][marker]
            if value >= 1.5 * top and value - med >= 1.0:
                out.append((name, marker, value, med, top))
    return sorted(out, key=lambda t: -(t[2] - t[3]))


def cmd_vet(results: List[Tuple[str, Dict[str, Any]]]) -> int:
    print("vetting: {} document(s); a document is listed where its rate on a high-signal AI "
          "marker is half again the highest of the others and a point above their median".format(len(results)))
    outliers = vet_outliers(results)
    if len(results) < 2:
        print("  nothing to compare against: vetting needs at least two documents")
    elif not outliers:
        print("  no outliers on {}".format(", ".join(VET_MARKERS)))
    for name, marker, value, med, top in outliers:
        print("  {}  {}  {} per 1k  (others: median {}, max {})".format(
            name, marker, fmt(value), fmt(med), fmt(top)))
    return 0


def cmd_measure(args: argparse.Namespace) -> int:
    results = []
    for path in args.files:
        with open(path, encoding="utf-8") as fh:
            results.append((path, measure(fh.read())))
    if args.vet:
        return cmd_vet(results)
    dbs = []
    for path in args.db or []:
        with open(path, encoding="utf-8") as fh:
            dbs.append((path, json.load(fh)))
    if args.register:
        known = set()
        for _, db in dbs:
            if db.get("kind") == "ai":
                continue
            corpus = db.get("corpus") or {}
            known.update(d["register"] for d in corpus.get("documents", []) if d.get("register"))
            known.update(corpus.get("register_weights") or {})
        if known and args.register not in known:
            sys.stderr.write(
                "register {!r} appears in no profile document (the profile has {}): every "
                "register-scoped row is set aside, and what the profile says about this register "
                "is a judgment call — references/processing.md, Step 1.\n".format(
                    args.register, ", ".join(sorted(known))))
    max_tier = SETTING_MAX_TIER.get(args.setting or "", 3)
    if args.json:
        out = {}
        for path, r in results:
            rows = []
            ai_rows = []  # machine rates: verdicts only, and keyed apart so ids can repeat
            for _, db in dbs:
                for p in db.get("patterns", []):
                    v = measure_pattern(p, r)
                    if v is None:
                        continue
                    verd = verdict(v, p, r["stats"])
                    row = {"value": v, "db_rate": p.get("rate"), "db_range": p.get("range"),
                           "tier": effective_tier(p), "verdict": verd}
                    if args.register:
                        row["out_of_scope"] = not in_scope(p, args.register)
                    if db.get("kind") == "ai":
                        ai_rows.append((p["id"], row))
                        continue
                    cls = classify(v, p, verd)
                    gap = gap_size(v, p, r["stats"], verd)
                    if is_structural(p):
                        row["inapplicable"] = is_inapplicable(p, r["stats"])
                    if row.get("out_of_scope") or (row.get("inapplicable") and cls in EDITING_CLASSES):
                        cls, gap = "neutral", 0.0
                    row.update({"gap": gap, "class": cls})
                    if args.setting:
                        row["dropped_by_setting"] = (cls in EDITING_CLASSES
                                                     and effective_tier(p) > max_tier)
                    rows.append((p["id"], row))
            if args.sort_gap:
                rows.sort(key=lambda t: -(t[1]["gap"] or 0.0))
            entry = {"stats": r["stats"], "per_1k": r["per_1k"],
                     "patterns": {pid: row for pid, row in rows}}
            if ai_rows:
                entry["ai_patterns"] = {pid: row for pid, row in ai_rows}
            judged = {}
            for _, db in dbs:
                if db.get("kind") == "ai":
                    continue
                for p in db.get("patterns", []):
                    if measure_pattern(p, r) is None:
                        judged[p["id"]] = {"tier": effective_tier(p),
                                           "description": p.get("description", "")}
                        if args.register:
                            judged[p["id"]]["out_of_scope"] = not in_scope(p, args.register)
            if judged:
                entry["judged_patterns"] = judged
            out[path] = entry
        print(json.dumps(out, indent=2))
        return 0
    if args.report_table:
        return cmd_report_table(args, results, dbs, max_tier)
    names = [p for p, _ in results]
    width = max(28, *(len(n) for n in names))
    # With the comparison flags the first file is the input and the rest are its rewrites:
    # class and gap are pinned to it (processing.md, Step 6), and so is the length the
    # verdicts are judged at, or a rewrite that came out shorter would turn the rows it
    # worked `too-short`.
    pinned = results[0][1]["stats"] if (args.sort_gap or args.setting) else None
    print("{:<32}".format("stat") + "".join("{:>{w}}".format(n[-width:], w=width + 2) for n in names))
    for key in STATS_HELP:
        print("{:<32}".format(key) + "".join("{:>{w}}".format(fmt(r["stats"][key]), w=width + 2) for _, r in results))
    print()
    print("{:<32}".format("per 1k words") + "".join("{:>{w}}".format(n[-width:], w=width + 2) for n in names))
    for key in COUNTERS:
        print("{:<32}".format(key) + "".join("{:>{w}}".format(fmt(r["per_1k"][key]), w=width + 2) for _, r in results))
    for db_path, db in dbs:
        ai = db.get("kind") == "ai"
        classified = bool(args.sort_gap or args.setting) and not ai
        print()
        if ai:
            print("AI DB patterns from {} (machine rates: match = machine-typical; "
                  "evidence, not rewrite rows)".format(db_path))
        else:
            print("DB patterns from {} (measurable ones only)".format(db_path))
        rows = []
        for p in db.get("patterns", []):
            values = [measure_pattern(p, r) for _, r in results]
            if all(v is None for v in values):
                continue
            verdicts = [verdict(v, p, pinned or r["stats"]) for v, (_, r) in zip(values, results)]
            gap = cls = None
            name = p["id"] + scope_mark(p, args.register)
            if not ai:
                name += (" [enum]" if is_enumeration(p) else "") + (" [structural]" if is_structural(p) else "")
                gap = gap_size(values[0], p, results[0][1]["stats"], verdicts[0])
                cls = classify(values[0], p, verdicts[0])
                if not in_scope(p, args.register):
                    cls, gap = "neutral", 0.0
                elif cls in EDITING_CLASSES and is_inapplicable(p, results[0][1]["stats"]):
                    cls, gap = "neutral", 0.0
                elif args.setting and cls in EDITING_CLASSES and effective_tier(p) > max_tier:
                    cls += " [manual]"
            rows.append((p, name, values, verdicts, gap, cls))
        if classified:
            note = ["class and gap for {}".format(names[0])]
            if len(results) > 1:
                note.append("later columns judged at its length")
            if args.setting:
                note.append("setting {} ([manual] = tier above {})".format(args.setting, max_tier))
            if args.sort_gap:
                rows.sort(key=lambda t: -(t[4] or 0.0))
                note.append("largest gap first")
            print("  " + "; ".join(note))
        pid_w = max([40] + [len(name) for _, name, _, _, _, _ in rows])
        head = "{:<16}{:>6}  ".format("class", "gap") if classified else ""
        head += "{:<{pw}}{:>5}{:>12}{:>16}".format("pattern", "tier", "db rate", "db range", pw=pid_w)
        print(head + "".join("{:>{w}}".format(n[-width:], w=width + 2) for n in names))
        for p, name, values, verdicts, gap, cls in rows:
            rng = p.get("range")
            rng_s = "{}–{}".format(fmt(rng[0]), fmt(rng[1])) if rng else "-"
            row = "{:<16}{:>6}  ".format(cls, fmt(gap)) if classified else ""
            row += "{:<{pw}}{:>5}{:>12}{:>16}".format(name, effective_tier(p), fmt(p.get("rate")), rng_s, pw=pid_w)
            row += "".join("{:>{w}}".format("{} {}".format(fmt(v), vd), w=width + 2)
                           for v, vd in zip(values, verdicts))
            print(row)
        marks = []
        if not ai and any(is_enumeration(p) for p, _, _, _, _, _ in rows):
            marks.append("[enum] = the counter enumerates forms; `match` covers only the ones it "
                         "names, so read for the rest of the family")
        if not ai and any(is_structural(p) for p, _, _, _, _, _ in rows):
            marks.append("[structural] = a row about document shape; it never licenses adding or "
                         "removing a list or a heading the input has, and where the input has "
                         "none it is neutral: inapplicable")
        if any("[scope:" in name for _, name, _, _, _, _ in rows):
            marks.append("[scope: ...] = a register-scoped row, a target only for an input in one "
                         "of those registers; pass --register to set the others aside")
        if any("[out of scope]" in name for _, name, _, _, _, _ in rows):
            marks.append("[out of scope] = the input's register is outside this row's scope: "
                         "not a rewrite row, and not evidence")
        for mark in marks:
            print("  " + mark)
        if not ai:
            judged = [p for p in db.get("patterns", [])
                      if all(measure_pattern(p, r) is None for _, r in results)]
            if judged:
                print()
                print("  read for these — no counter, so no row above and no verdict; "
                      "each one still gets a class and a line in the report")
                for p in judged:
                    print("  {:<{pw}}{:>5}  {}".format(
                        p["id"] + scope_mark(p, args.register), effective_tier(p),
                        p.get("description", ""), pw=pid_w))
    print("  tier = effective tier: the review round's override where one is set")
    return 0


def cmd_hits(args: argparse.Namespace) -> int:
    counters: List[Tuple[str, Dict[str, Any]]] = []
    for rx in args.regex or []:
        counters.append((rx, {"regex": rx, "ignore_case": args.ignore_case,
                              "exclude": args.exclude, "unit": args.unit}))
    for name in args.stat or []:
        if name not in STATS_HELP and name not in COUNTERS:
            sys.stderr.write("unknown stat {!r}; `textstats.py counters` lists them\n".format(name))
            return 1
        unit = args.unit if name in COUNTERS or name.endswith("_per_1k") else STAT_UNITS.get(name, args.unit)
        counters.append((name, {"stat": name, "exclude": args.exclude, "unit": unit}))
    if not counters:
        sys.stderr.write("nothing to count: give -e REGEX or --stat NAME\n")
        return 1
    for _, p in counters:
        for key in ("regex", "exclude"):
            if p.get(key):
                try:
                    re.compile(p[key])
                except re.error as exc:
                    sys.stderr.write("invalid {} {!r}: {}\n".format(key, p[key], exc))
                    return 1
    results = []
    for path in args.files:
        with open(path, encoding="utf-8") as fh:
            results.append((path, measure(fh.read())))
    if args.matrix or len(counters) > 1:
        width = max(12, *(min(len(n), 24) for n, _ in results))
        label_w = max(24, *(min(len(label), 60) for label, _ in counters))
        print("{:<{lw}}".format("counter (raw count per file)", lw=label_w)
              + "".join("{:>{w}}".format(n[-width:], w=width + 2) for n, _ in results))
        for label, p in counters:
            cells = []
            for _, r in results:
                c = count_pattern(p, r)
                cells.append(fmt(measure_pattern(p, r)) if c is None else str(c))
            print("{:<{lw}}".format(label[:label_w], lw=label_w)
                  + "".join("{:>{w}}".format(c, w=width + 2) for c in cells))
    else:
        label, p = counters[0]
        for path, r in results:
            doc: Document = r["_doc"]
            value = measure_pattern(p, r)
            counter = compiled_counter(p)
            if counter is None:
                print("{}: words={}  {}={}".format(path, doc.words, label, fmt(value)))
                continue
            regex, flags = counter
            spans = matches(regex, flags, doc.prose, p.get("exclude"))
            kept = sum(1 for _, _, excluded in spans if not excluded)
            dropped = len(spans) - kept
            print("{}: words={}  count={}{}  {}={}".format(
                path, doc.words, kept, " ({} excluded)".format(dropped) if dropped else "",
                p["unit"], fmt(value)))
            for s, e, excluded in spans[:args.max]:
                ctx = (doc.prose[max(0, s - args.context):s] + "«" + doc.prose[s:e] + "»"
                       + doc.prose[e:e + args.context]).replace("\n", " ")
                print("  {}…{}…".format("(excluded) " if excluded else "", ctx))
            if len(spans) > args.max:
                print("  … {} more".format(len(spans) - args.max))
    for label, p in counters:
        fields = {k: p[k] for k in ("regex", "stat", "ignore_case", "exclude", "unit") if p.get(k)}
        print("DB fields for {}: {}".format(label[:60], json.dumps(fields, ensure_ascii=False)[1:-1]))
    return 0


def cmd_counters(args: argparse.Namespace) -> int:
    for key, desc in STATS_HELP.items():
        print("{:<32} {}".format(key, desc))
    print()
    for key, (regex, _, desc) in COUNTERS.items():
        print("{:<32} {}  /{}/".format(key, desc, regex))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("measure"); s.add_argument("files", nargs="+")
    s.add_argument("--db", action="append")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--json", action="store_true")
    g.add_argument("--report-table", action="store_true",
                   help="the report's measured sections as markdown, AI-evidence column "
                        "filled, so no figure in the report is retyped")
    g.add_argument("--vet", action="store_true",
                   help="vetting view: per-document outliers on the high-signal AI markers")
    s.add_argument("--sort-gap", action="store_true",
                   help="order DB rows by the size of the edit they ask for, largest first")
    s.add_argument("--setting", choices=sorted(SETTING_MAX_TIER),
                   help="strictness ceiling: mark [manual] the rows whose tier is above it")
    s.add_argument("--register",
                   help="the input's register (article, email, ...): rows whose register_scope "
                        "excludes it are marked [out of scope] and are not rewrite rows")
    s.set_defaults(fn=cmd_measure)
    s = sub.add_parser("hits"); s.add_argument("files", nargs="+")
    s.add_argument("-e", "--regex", action="append", help="a candidate regex (repeatable)")
    s.add_argument("--stat", action="append", help="a statistic or built-in counter by name (repeatable)")
    s.add_argument("-i", "--ignore-case", action="store_true",
                   help="match case-insensitively; the DB field is ignore_case: true")
    s.add_argument("-x", "--exclude", help="regex whose matches subtract overlapping hits; the DB field is exclude")
    s.add_argument("--unit", default="per_1k_words",
                   choices=("per_1k_words", "share_of_sentences", "share_of_paragraphs", "share_of_headings", "count"))
    s.add_argument("--matrix", action="store_true",
                   help="one line per counter with the raw count per file (the default with several counters)")
    s.add_argument("--max", type=int, default=12, help="hits to print per file (default 12)")
    s.add_argument("--context", type=int, default=40, help="characters of context around a hit")
    s.set_defaults(fn=cmd_hits)
    s = sub.add_parser("counters"); s.set_defaults(fn=cmd_counters)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
