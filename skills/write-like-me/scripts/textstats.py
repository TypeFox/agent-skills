#!/usr/bin/env python3
"""Measure style counters over Markdown/plain-text documents, per 1,000 words.

The write-like-me skill converges on *rates*: a rewrite is done when the
input's counters sit inside the range the author's own corpus shows, never at
zero and never at "always". Rates estimated by reading drift; this script makes
them reproducible so that measuring, rewriting, and re-measuring use the same
definitions. It carries a built-in set of generic counters (punctuation,
sentence and paragraph shape, person, contractions, emphasis, lexical habits,
and a stopgap set of AI-typical constructions), and it can evaluate the `regex` and `stat`
fields of style-DB patterns so DB rates and input rates are computed the same
way.

Usage
  textstats.py measure FILE... [--db DB...] [--json]
      One column per file. With --db, every DB pattern that carries a `regex`
      or `stat` field is measured on each file and shown next to the DB's rate
      and per-document range, with a verdict: `gap` when the input falls
      outside the per-document range (widened by a small tolerance); `low` or
      `high` when it is inside the range but under half or over twice the
      corpus rate (the author does this, just not in every document); `match`
      otherwise.
  textstats.py counters
      List the built-in counters and their definitions.

What is excluded before counting: fenced code, inline code (replaced by a
placeholder word), link URLs (link text stays), images, HTML tags, table rows,
and front matter. Headings and list items count toward words and punctuation
rates but not toward sentence-length or paragraph statistics, because they are
fragments by design.

The built-in AI-marker counters (ai_*) are a stopgap until the skill ships its
AI style-patterns DB; the DB replaces them with evidence-backed patterns. Their
definitions follow references/taxonomy.md, whose AI-typical dimensions name the
counter each marker uses; counters marked "noisy" there over-count by design
and their hits are confirmed by reading.

Stdlib only, Python 3.8+.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from typing import Any, Dict, List, Optional, Sequence

HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
TABLE_RE = re.compile(r"^\s*\|")
HR_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
BLOCKQUOTE_RE = re.compile(r"^\s*>\s?")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’\-]*")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])[\"'”’)\]]*\s+(?=[\"'“‘(\[]?[A-Z0-9])")

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
    "first_person_singular": (r"\b(?:I|I[’']m|I[’']ve|I[’']d|I[’']ll|me|my|mine|myself)\b", 0, "I / me / my"),
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
    "ai_not_just": (r"\bnot (?:just|only|merely|simply)\b[^.;!?\n]{1,80}?[,;—–-]\s*(?:it[’']s|but|rather)", re.I, "not just X — it's Y"),
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
        text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
        text = re.sub(r"<[^>\n]+>", "", text)
        text = re.sub(r"`[^`\n]*`", "code", text)
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


def measure_pattern(pattern: Dict[str, Any], result: Dict[str, Any]) -> Optional[float]:
    """Rate of a DB pattern on a measured document, in the pattern's unit."""
    doc: Document = result["_doc"]
    unit = pattern.get("unit", "per_1k_words")
    if pattern.get("stat"):
        return result["stats"].get(pattern["stat"])
    regex = pattern.get("regex")
    if not regex:
        return None
    flags = re.I if pattern.get("ignore_case") else 0
    if unit == "per_1k_words":
        return round(count(regex, flags | re.M, doc.prose) / (doc.words or 1) * 1000, 2)
    if unit == "share_of_sentences":
        units = doc.sentences
    elif unit == "share_of_paragraphs":
        units = doc.paragraphs
    else:
        return round(float(count(regex, flags | re.M, doc.prose)), 2)
    if not units:
        return 0.0
    return round(sum(1 for u in units if re.search(regex, u, flags)) / len(units), 3)


def verdict(value: Optional[float], pattern: Dict[str, Any]) -> str:
    if value is None or pattern.get("rate") is None:
        return "n/a"
    if pattern.get("kind") == "absence":
        return "match" if value == 0 else "gap"
    rng = pattern.get("range") or [pattern["rate"], pattern["rate"]]
    lo, hi = float(rng[0]), float(rng[1])
    tol = max(0.1 * max(abs(lo), abs(hi)), 0.5 if pattern.get("unit", "per_1k_words") == "per_1k_words" else 0.05)
    if not (lo - tol <= value <= hi + tol):
        return "gap"
    rate = float(pattern["rate"])
    if rate > 0 and value < 0.5 * rate:
        return "low"
    if rate > 0 and value > 2.0 * rate:
        return "high"
    return "match"


def fmt(v: Any) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return "{:g}".format(v)
    return str(v)


def cmd_measure(args: argparse.Namespace) -> int:
    results = []
    for path in args.files:
        with open(path, encoding="utf-8") as fh:
            results.append((path, measure(fh.read())))
    dbs = []
    for path in args.db or []:
        with open(path, encoding="utf-8") as fh:
            dbs.append((path, json.load(fh)))
    if args.json:
        out = {}
        for path, r in results:
            entry = {"stats": r["stats"], "per_1k": r["per_1k"], "patterns": {}}
            for _, db in dbs:
                for p in db.get("patterns", []):
                    v = measure_pattern(p, r)
                    if v is not None:
                        entry["patterns"][p["id"]] = {"value": v, "db_rate": p.get("rate"),
                                                      "db_range": p.get("range"), "tier": p.get("tier"),
                                                      "verdict": verdict(v, p)}
            out[path] = entry
        print(json.dumps(out, indent=2))
        return 0
    names = [p for p, _ in results]
    width = max(28, *(len(n) for n in names))
    print("{:<32}".format("stat") + "".join("{:>{w}}".format(n[-width:], w=width + 2) for n in names))
    for key in STATS_HELP:
        print("{:<32}".format(key) + "".join("{:>{w}}".format(fmt(r["stats"][key]), w=width + 2) for _, r in results))
    print()
    print("{:<32}".format("per 1k words") + "".join("{:>{w}}".format(n[-width:], w=width + 2) for n in names))
    for key in COUNTERS:
        print("{:<32}".format(key) + "".join("{:>{w}}".format(fmt(r["per_1k"][key]), w=width + 2) for _, r in results))
    for db_path, db in dbs:
        print()
        print("DB patterns from {} (measurable ones only)".format(db_path))
        head = "{:<40}{:>5}{:>12}{:>16}".format("pattern", "tier", "db rate", "db range")
        print(head + "".join("{:>{w}}".format(n[-width:], w=width + 2) for n in names))
        for p in db.get("patterns", []):
            values = [measure_pattern(p, r) for _, r in results]
            if all(v is None for v in values):
                continue
            rng = p.get("range")
            rng_s = "{}–{}".format(fmt(rng[0]), fmt(rng[1])) if rng else "-"
            row = "{:<40}{:>5}{:>12}{:>16}".format(p["id"][:40], p.get("tier", "-"), fmt(p.get("rate")), rng_s)
            row += "".join("{:>{w}}".format("{} {}".format(fmt(v), verdict(v, p)), w=width + 2) for v in values)
            print(row)
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
    s.add_argument("--db", action="append"); s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_measure)
    s = sub.add_parser("counters"); s.set_defaults(fn=cmd_counters)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
