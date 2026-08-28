#!/usr/bin/env python3
"""Measure style counters over Markdown/plain-text documents, per 1,000 words.

The write-like-me skill converges on *rates*: a rewrite is done when the
input's counters sit inside the range the author's own corpus shows, never at
zero and never at "always". Rates estimated by reading drift; this script makes
them reproducible so that measuring, rewriting, and re-measuring use the same
definitions. It carries a built-in set of generic counters (punctuation,
sentence and paragraph shape, person, contractions, emphasis, and a stopgap
list of AI-typical constructions), and it can evaluate the `regex` and `stat`
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
AI style-patterns DB; the DB replaces them with evidence-backed patterns.

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
COUNTERS: Dict[str, Any] = {
    "em_dash": (r"—|(?<=\S) -- (?=\S)|(?<=\S)--(?=\S)", 0, "em dashes (— or --)"),
    "en_dash_spaced": (r"(?<=\s)–(?=\s)", 0, "spaced en dash used as a dash"),
    "semicolon": (r";", 0, "semicolons"),
    "colon": (r":(?=\s)", 0, "colons followed by whitespace"),
    "parenthesis": (r"\(", 0, "opening parentheses (asides)"),
    "exclamation": (r"!", 0, "exclamation marks"),
    "question": (r"\?", 0, "question marks"),
    "ellipsis": (r"\.\.\.|…", 0, "ellipses"),
    "contraction": (r"\b\w+n[’']t\b|\b(?:I|it|that|there|here|what|who|we|you|they|let)[’'](?:m|s|re|ve|ll|d)\b", re.I, "contractions"),
    "first_person_singular": (r"\b(?:I|I[’']m|I[’']ve|I[’']d|I[’']ll|me|my|mine|myself)\b", 0, "I / me / my"),
    "first_person_plural": (r"\b(?:we|we[’']re|we[’']ve|we[’']d|we[’']ll|our|ours|us|ourselves)\b", re.I, "we / our / us"),
    "second_person": (r"\b(?:you|you[’']re|you[’']ve|you[’']d|you[’']ll|your|yours|yourself)\b", re.I, "you / your"),
    "bold": (r"\*\*[^*\n]+\*\*|__[^_\n]+__", 0, "bold spans"),
    "italic": (r"(?<![*\w])\*[^*\n]+\*(?![*\w])|(?<![_\w])_[^_\n]+_(?![_\w])", 0, "italic spans"),
    "ai_not_but": (r"\b(?:not|isn[’']t|aren[’']t|wasn[’']t|weren[’']t|no longer)\b[^.;!?\n]{1,80}?[,;—–-]?\s+but\b", re.I, "negative parallelism: not X, but Y"),
    "ai_not_just": (r"\bnot (?:just|only|merely|simply)\b[^.;!?\n]{1,80}?[,;—–-]\s*(?:it[’']s|but|rather)", re.I, "not just X — it's Y"),
    "ai_significance_tail": (r"\b(?:highlight(?:s|ing)?|underscor(?:es|ing)|emphasiz(?:es|ing)|showcas(?:es|ing)|demonstrat(?:es|ing))\s+(?:the\s+)?(?:importance|significance|need|value|role|power|potential)\b", re.I, "significance-flagging tails"),
    "ai_worth_noting": (r"\b(?:it[’']s worth noting|it is worth noting|it[’']s important to note|it is important to note|notably|importantly|crucially)\b", re.I, "worth-noting hedges"),
    "ai_summary_opener": (r"(?:^|(?<=[.!?]\s))(?:in conclusion|in summary|to sum up|overall|ultimately|to summarize|in short|all in all)\b", re.I | re.M, "summary openers"),
    "ai_connective_opener": (r"(?:^|(?<=[.!?]\s))(?:additionally|furthermore|moreover|however|therefore|thus|consequently|in addition)\b", re.I | re.M, "sentence-initial formal connectives"),
    "ai_vocabulary": (r"\b(?:delv(?:e|es|ing)|tapestry|landscape|seamless(?:ly)?|robust|leverag(?:e|es|ing)|crucial|pivotal|vibrant|multifaceted|navigat(?:e|es|ing)|foster(?:s|ing)?|comprehensive|streamlin(?:e|es|ing)|realm|testament|embark(?:s|ing)?|elevat(?:e|es|ing)|unlock(?:s|ing)?|harness(?:es|ing)?|empower(?:s|ing)?|game-changer|cutting-edge)\b", re.I, "AI-typical vocabulary"),
    "ai_triad": (r"\b[\w'’-]+, [\w'’-]+,? and [\w'’-]+\b", 0, "word triads (rule of three)"),
    "ai_false_range": (r"\bfrom [\w'’-]+(?: [\w'’-]+)? to [\w'’-]+(?: [\w'’-]+)?\b", re.I, "from X to Y ranges (noisy: includes real ranges)"),
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
