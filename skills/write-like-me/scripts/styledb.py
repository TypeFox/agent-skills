#!/usr/bin/env python3
"""Validate, merge, render, and version-check write-like-me style-pattern DBs.

A style-pattern DB is the JSON file the write-like-me skill builds from a
corpus (a user's hand-written documents, or the maintainers' AI-generated
corpus) and reads while rewriting text. Its format is described in
references/db-schema.md; this script is the mechanical half of that document:
it enforces the schema, recomputes the derived fields (rates, spread, tiers),
merges partial DBs produced by parallel extraction runs, and reports version
drift between a DB and the skill.

Subcommands
  info DB [--json]               print header facts and compare db_version with
                                 the skill's; exit 0 = same, 2 = DB older
                                 (migrate, see references/migration.md),
                                 3 = DB newer (update the skill)
  validate DB [--corpus-dir DIR] [--fix]
                                 schema check; with --corpus-dir every evidence
                                 quote is verified verbatim against its source
                                 document (entries marked "redacted": true are
                                 exempt — see technique.md rule 5), a miss
                                 reports the nearest verbatim form, and every
                                 counted pattern's per-document counts are
                                 re-run from the corpus; a source the paths do
                                 not reach is an error, since nothing asked for
                                 was verified; --fix rewrites derived fields
                                 (rate, spread, range, coverage, tier), pooling
                                 rates under corpus.register_weights when the
                                 manifest carries one
  merge DB... -o OUT [--partial] union of corpus manifests and patterns from
                                 several (partial) DBs, derived fields
                                 recomputed from the merged per-document data
  seal DB [-o OUT]               finalize a reviewed DB: drop corpus.documents[]
                                 .path, the DB's only reference into the corpus
                                 filesystem, and stamp corpus.sealed. Ends quote
                                 re-verification; everything processing reads is
                                 untouched (see references/db-schema.md)
  render DB [--setting soft|medium|hard] [--dimension D]
                                 human-readable markdown profile, filtered to
                                 the tiers the setting applies
  tiers DB                       one line per pattern: id, computed tier,
                                 effective tier, and the reason

Exit codes: 0 ok, 1 validation errors or usage error, 2/3 as above for info.

Stdlib only, Python 3.8+.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

CURRENT_DB_VERSION = 1

try:  # ships next to this script; names a DB pattern may reference in `stat`
    import textstats
    KNOWN_STATS = set(textstats.STATS_HELP) | set(textstats.COUNTERS)
    BUILTIN_COUNTERS = set(textstats.COUNTERS)
except ImportError:  # pragma: no cover
    textstats = None
    KNOWN_STATS = BUILTIN_COUNTERS = None

# Keep in sync with references/taxonomy.md (the taxonomy is the authority).
DIMENSIONS = [
    "punctuation",
    "sentence-rhythm",
    "paragraph-openers",
    "argument-structure",
    "connectives",
    "grammar-habits",
    "voice-and-person",
    "tone-markers",
    "imagery",
    "emphasis",
    "lists",
    "headings",
    "opener-closer",
    "spelling-lexical",
    "content-conventions",
    "contrast-frames",
    "reveal-frames",
    "significance-tails",
    "rule-of-three",
    "signposting",
    "authenticity-stance",
    "stock-phrasing",
]

KINDS = ("presence", "absence")
MEASUREMENTS = ("counted", "judged")
UNITS = ("per_1k_words", "share_of_sentences", "share_of_paragraphs", "share_of_headings", "words", "count")
DB_KINDS = ("user", "ai")
SETTING_MAX_TIER = {"soft": 1, "medium": 2, "hard": 3}
ID_RE = re.compile(r"^[a-z0-9-]+/[a-z0-9-]+$")


# ---------------------------------------------------------------- helpers

def load(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save(path: str, db: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(db, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def doc_index(db: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {d["id"]: d for d in db.get("corpus", {}).get("documents", [])}


def scoped_docs(pattern: Dict[str, Any], docs: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """The corpus documents a pattern is derived over: all of them, or — with a
    `register_scope` — only those in the listed registers. Spread is otherwise
    corpus-wide, so a habit near-obligatory in one register could never leave tier 3."""
    scope = pattern.get("register_scope")
    if not scope:
        return docs
    return {did: d for did, d in docs.items() if d.get("register") in scope}


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


FOLD = {"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"', "\u2014": "-", "\u2013": "-"}


def nearest_quote(source: str, quote: str) -> Optional[str]:
    """The verbatim source span a quote was retyped from, or None.

    Folds what quote-copying most often drifts on — case, curly vs. straight
    quotes and apostrophes, dash kinds, Markdown emphasis markers — and returns
    the source text at the match so the DB entry can be corrected by pasting.
    """
    def fold(text: str):
        chars, index = [], []
        for i, ch in enumerate(text):
            if ch in "*_":
                continue
            chars.append(FOLD.get(ch, ch).lower())
            index.append(i)
        return "".join(chars), index

    needle, _ = fold(quote)
    haystack, index = fold(source)
    if not needle:
        return None
    at = haystack.find(needle)
    if at < 0:
        return None
    return source[index[at]:index[at + len(needle) - 1] + 1]


# ---------------------------------------------------------------- derived fields

DEFAULT_REGISTER_SHARE = 1.0


def register_weights(db: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The corpus's register weighting, or None when rates pool by words alone."""
    weights = (db.get("corpus") or {}).get("register_weights")
    return weights if isinstance(weights, dict) and weights else None


def pool_by_register(per_doc: List[float], words: List[int], registers: List[str],
                     weights: Dict[str, Any]) -> float:
    """Corpus rate under a register weighting: a share-weighted mean of the per-register
    rates, each of those the word-weighted mean of its own documents.

    Shares proportional to the registers' word counts reproduce the unweighted rate,
    which is what a corpus without `register_weights` computes; equal shares make a
    400-word email register count as much as a 40,000-word thesis. A register the
    weighting does not name falls back to share 1 so a malformed DB still produces
    numbers — `validate` reports the omission as an error rather than letting it stand.
    """
    totals: Dict[str, List[float]] = {}
    for rate, doc_words, register in zip(per_doc, words, registers):
        acc = totals.setdefault(register, [0.0, 0.0])
        acc[0] += rate * doc_words
        acc[1] += doc_words
    num = den = 0.0
    for register, (weighted, register_words) in totals.items():
        if not register_words:
            continue
        share = float(weights.get(register, DEFAULT_REGISTER_SHARE))
        num += share * (weighted / register_words)
        den += share
    return num / den if den else 0.0


def compute_stats(pattern: Dict[str, Any], docs: Dict[str, Dict[str, Any]],
                  weights: Optional[Dict[str, Any]] = None) -> None:
    """Recompute rate, spread, range, coverage, registers from documents[].

    `weights` is the corpus's `register_weights`, and it moves `rate` alone: `spread`,
    `range` and `coverage` count documents, and so do the tier rules that read them. A
    weight says how much a register should define the author's target rate, never how
    well a habit is evidenced.
    """
    docs = scoped_docs(pattern, docs)
    entries = [e for e in pattern.get("documents", []) if e.get("id") in docs]
    n_docs = len(docs)
    measured_words = sum(docs[e["id"]]["words"] for e in entries)
    unit = pattern.get("unit", "per_1k_words")
    if not entries:
        pattern.update({"rate": None, "spread": 0.0, "range": None, "coverage": 0.0,
                        "registers": []})
        return
    if unit == "per_1k_words":
        total = sum(e.get("count", 0) for e in entries)
        rate = total / measured_words * 1000 if measured_words else 0.0
        per_doc = [(e.get("count", 0) / docs[e["id"]]["words"] * 1000) for e in entries]
    else:
        per_doc = [float(e.get("rate", 0.0)) for e in entries]
        rate = (sum(r * docs[e["id"]]["words"] for r, e in zip(per_doc, entries))
                / measured_words) if measured_words else 0.0
    if weights:
        rate = pool_by_register(per_doc, [docs[e["id"]]["words"] for e in entries],
                                [docs[e["id"]].get("register", "unknown") for e in entries],
                                weights)
    if pattern.get("kind") == "absence":
        present = [e for e in entries if e.get("count", 0) == 0]
    else:
        present = [e for e in entries if e.get("count", 0) > 0 or e.get("rate", 0) > 0]
    registers = sorted({docs[e["id"]].get("register", "unknown") for e in present})
    pattern["rate"] = round(rate, 3)
    pattern["spread"] = round(len(present) / len(entries), 3)
    pattern["range"] = [round(min(per_doc), 3), round(max(per_doc), 3)]
    pattern["coverage"] = round(len(entries) / n_docs, 3) if n_docs else 0.0
    pattern["registers"] = registers
    pattern["_present"] = len(present)
    pattern["_measured_words"] = measured_words


def compute_tier(pattern: Dict[str, Any], docs: Dict[str, Dict[str, Any]],
                 weights: Optional[Dict[str, Any]] = None) -> Tuple[int, str]:
    """Evidence tier: 1 = strong, 2 = moderate, 3 = weak. See db-schema.md."""
    if "_present" not in pattern:
        compute_stats(pattern, docs, weights)
    corpus_registers = {d.get("register", "unknown") for d in scoped_docs(pattern, docs).values()}
    quotes = len(pattern.get("evidence", []))
    counted = pattern.get("measurement") == "counted"
    coverage = pattern.get("coverage", 0.0)
    spread = pattern.get("spread", 0.0)
    present = pattern.get("_present", 0)
    registers = pattern.get("registers", [])
    multi_register = len(registers) >= 2 or len(corpus_registers) <= 1
    if pattern.get("kind") == "absence":
        if counted and coverage >= 1.0 and spread >= 1.0 and pattern["_measured_words"] >= 3000:
            return 1, "counted as absent in every document over >=3000 words"
        if counted and coverage >= 0.5 and spread >= 1.0:
            return 2, "counted as absent in the measured documents (partial coverage or small corpus)"
        return 3, "absence not counted across the corpus"
    if (counted and coverage >= 1.0 and spread >= 0.6 and present >= 3
            and multi_register and quotes >= 3):
        return 1, "counted in every document, present in >=60% and >=3 docs, >=2 registers, >=3 quotes"
    if present >= 2 and spread >= 0.4 and quotes >= 2:
        why = []
        if not counted:
            why.append("judged, not counted")
        if coverage < 1.0:
            why.append("not measured in every document")
        if present < 3:
            why.append("present in fewer than 3 documents")
        if not multi_register:
            why.append("single register")
        if quotes < 3:
            why.append("fewer than 3 quotes")
        return 2, "; ".join(why) or "moderate evidence"
    return 3, "present in <2 documents, spread <40%, or fewer than 2 quotes"


def effective_tier(pattern: Dict[str, Any]) -> int:
    override = pattern.get("tier_override")
    if isinstance(override, int) and 1 <= override <= 3:
        return override
    return int(pattern.get("tier", 3))


def recompute(db: Dict[str, Any]) -> None:
    docs = doc_index(db)
    weights = register_weights(db)
    for p in db.get("patterns", []):
        compute_stats(p, docs, weights)
        p["tier"], p["tier_reason"] = compute_tier(p, docs, weights)
        p.pop("_present", None)
        p.pop("_measured_words", None)
    db["corpus"]["total_words"] = sum(d.get("words", 0) for d in docs.values())


# ---------------------------------------------------------------- validate

class CorpusReader:
    """Reads each corpus document once, for quote verification and for recounting."""

    def __init__(self, corpus_dir: str) -> None:
        self.root = corpus_dir
        self._text: Dict[str, Optional[str]] = {}
        self._measured: Dict[str, Any] = {}

    def text(self, doc: Dict[str, Any]) -> Optional[str]:
        did = doc["id"]
        if did not in self._text:
            try:
                with open(os.path.join(self.root, doc["path"]), encoding="utf-8") as fh:
                    self._text[did] = fh.read()
            except OSError:
                self._text[did] = None
        return self._text[did]

    def path(self, doc: Dict[str, Any]) -> str:
        return os.path.join(self.root, doc["path"])

    def measured(self, doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        did = doc["id"]
        if did not in self._measured:
            body = self.text(doc)
            self._measured[did] = None if body is None or textstats is None \
                else textstats.measure(body)
        return self._measured[did]


def recount(pattern: Dict[str, Any], entry: Dict[str, Any],
            measured: Dict[str, Any]) -> Optional[Tuple[float, float, str]]:
    """(recorded, from the corpus, unit) for one documents[] entry, or None when the
    counter cannot be re-run — a judged pattern, a pattern with neither regex nor stat,
    or a stat this build of textstats does not know."""
    if textstats is None or pattern.get("measurement") != "counted":
        return None
    if not (pattern.get("regex") or pattern.get("stat")):
        return None
    value = textstats.measure_pattern(pattern, measured)
    if value is None:
        return None
    unit = pattern.get("unit", "per_1k_words")
    if unit == "per_1k_words":
        words = measured["stats"].get("words") or 0
        return float(entry.get("count", 0)), value * words / 1000.0, "occurrences"
    recorded = entry.get("rate", entry.get("count"))
    if recorded is None:
        return None
    return float(recorded), float(value), unit


def validate(db: Dict[str, Any], corpus_dir: Optional[str] = None) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    e = errors.append
    w = warnings.append

    if not isinstance(db.get("db_version"), int):
        e("db_version must be an integer")
    elif db["db_version"] != CURRENT_DB_VERSION:
        w("db_version {} differs from the skill's {} (run `info`)".format(
            db["db_version"], CURRENT_DB_VERSION))
    if db.get("kind") not in DB_KINDS:
        e("kind must be one of {}".format(DB_KINDS))
    corpus = db.get("corpus")
    if not isinstance(corpus, dict) or not isinstance(corpus.get("documents"), list):
        e("corpus.documents must be a list")
        return errors, warnings
    docs = {}
    for d in corpus["documents"]:
        did = d.get("id")
        if not did or not isinstance(did, str):
            e("corpus document without string id: {!r}".format(d))
            continue
        if did in docs:
            e("duplicate corpus document id {}".format(did))
        if not isinstance(d.get("words"), int) or d["words"] <= 0:
            e("document {}: words must be a positive integer".format(did))
        if not d.get("register"):
            e("document {}: register is required".format(did))
        if db.get("kind") == "ai" and not d.get("generator"):
            w("document {}: no generator recorded; an AI corpus names the model or agent "
              "behind every document (technique.md, maintainer note)".format(did))
        docs[did] = d
    sealed = corpus.get("sealed")
    if sealed is not None:
        if not isinstance(sealed, str):
            e("corpus.sealed must be a date string")
        still_pathed = sorted(did for did, d in docs.items() if d.get("path"))
        if still_pathed:
            e("corpus is marked sealed but {} document(s) still carry a path: {}".format(
                len(still_pathed), ", ".join(still_pathed)))
    weights = corpus.get("register_weights")
    if weights is not None:
        present = {d.get("register") for d in docs.values() if d.get("register")}
        if not isinstance(weights, dict) or not weights:
            e("corpus.register_weights must be a non-empty object mapping register to share")
            weights = None
        else:
            for register in sorted(weights, key=str):
                share = weights[register]
                if isinstance(share, bool) or not isinstance(share, (int, float)) or share <= 0:
                    e("corpus.register_weights[{!r}] must be a positive number: the share of "
                      "the pooled rate that register carries".format(register))
                elif register not in present:
                    w("corpus.register_weights names register {!r}, which no corpus document "
                      "carries; it contributes nothing".format(register))
            for register in sorted(present - set(weights)):
                e("corpus.register_weights does not name register {!r}, which {} corpus "
                  "document(s) carry; an unnamed register falls back to share 1, so name "
                  "every register or drop the weighting (technique.md, Step 1)".format(
                      register, sum(1 for d in docs.values() if d.get("register") == register)))
        if db.get("partial"):
            w("corpus.register_weights on a partial DB: weighting is a whole-corpus "
              "decision and belongs on the merged DB, where every register is present")
    weights = register_weights(db)
    reader = CorpusReader(corpus_dir) if corpus_dir else None
    if reader:
        for did in sorted(docs):
            if docs[did].get("path") and reader.text(docs[did]) is None:
                e("cannot open {}; --corpus-dir must be the root the documents[].path "
                  "entries are relative to, and nothing in {} was verified against it"
                  .format(reader.path(docs[did]), did))
    if corpus_dir:
        unverifiable = sorted(did for did, d in docs.items() if not d.get("path"))
        if unverifiable:
            w("--corpus-dir given, but {} of {} documents carry no path{}; "
              "their evidence quotes were NOT verified: {}".format(
                  len(unverifiable), len(docs),
                  " (DB sealed {})".format(sealed) if sealed else "", ", ".join(unverifiable)))
    if db.get("kind") == "user" and not db.get("partial"):
        if len(docs) < 8:
            w("corpus has {} documents; guidance is >=8 for a stable profile".format(len(docs)))
        if sum(d.get("words", 0) for d in docs.values()) < 6000:
            w("corpus has {} words; guidance is >=6000".format(
                sum(d.get("words", 0) for d in docs.values())))
    review = db.get("review", {})
    if review.get("status") not in ("pending", "reviewed"):
        e("review.status must be 'pending' or 'reviewed'")

    seen = set()
    for p in db.get("patterns", []):
        pid = p.get("id", "<no id>")
        if not ID_RE.match(pid or ""):
            e("pattern {}: id must look like dimension/marker (lowercase, hyphens)".format(pid))
            continue
        if pid in seen:
            e("pattern {}: duplicate id".format(pid))
        seen.add(pid)
        dim, marker = pid.split("/", 1)
        if p.get("dimension") != dim or p.get("marker") != marker:
            e("pattern {}: dimension/marker fields must match the id".format(pid))
        if dim not in DIMENSIONS:
            e("pattern {}: unknown dimension {!r} (see references/taxonomy.md)".format(pid, dim))
        if p.get("kind") not in KINDS:
            e("pattern {}: kind must be one of {}".format(pid, KINDS))
        if p.get("measurement") not in MEASUREMENTS:
            e("pattern {}: measurement must be one of {}".format(pid, MEASUREMENTS))
        if p.get("unit", "per_1k_words") not in UNITS:
            e("pattern {}: unit must be one of {}".format(pid, UNITS))
        if not p.get("description"):
            e("pattern {}: description is required".format(pid))
        if p.get("regex"):
            try:
                re.compile(p["regex"])
            except re.error as exc:
                e("pattern {}: invalid regex: {}".format(pid, exc))
        stat = p.get("stat")
        if stat and KNOWN_STATS is not None:
            if stat not in KNOWN_STATS:
                e("pattern {}: unknown stat {!r} (see textstats.py counters)".format(pid, stat))
            elif stat in BUILTIN_COUNTERS and p.get("unit", "per_1k_words") != "per_1k_words":
                e("pattern {}: built-in counter {!r} counts per 1k words; unit must be per_1k_words".format(pid, stat))
        if p.get("measurement") == "counted" and not p.get("regex") and not stat:
            w("pattern {}: counted without regex or stat; processing cannot re-measure it".format(pid))
        entries = p.get("documents", [])
        if not entries:
            e("pattern {}: documents[] is empty; every pattern needs per-document counts".format(pid))
        for entry in entries:
            if entry.get("id") not in docs:
                e("pattern {}: documents[] references unknown document {!r}".format(pid, entry.get("id")))
            elif reader and docs[entry["id"]].get("path"):
                measured = reader.measured(docs[entry["id"]])
                if measured is None:
                    continue  # already reported once, against the document
                got = recount(p, entry, measured)
                if got is None:
                    continue
                recorded, measured_value, unit = got
                tol = 0.5 if unit == "occurrences" else max(0.02, 0.02 * abs(recorded))
                if abs(recorded - measured_value) > tol:
                    e("pattern {}: documents[{}] records {:g} {} but the counter finds "
                      "{:g} in the source; re-run the counter (the recorded numbers are "
                      "what rate, range and tier are computed from)".format(
                          pid, entry["id"], recorded, unit, round(measured_value, 2)))
        if p.get("kind") == "absence":
            if p.get("measurement") != "counted":
                e("pattern {}: absence patterns must be counted, not judged".format(pid))
            if any(entry.get("count", 0) > 0 for entry in entries):
                e("pattern {}: absence pattern has a document with count > 0".format(pid))
        else:
            if not p.get("evidence"):
                e("pattern {}: presence patterns need at least one verbatim evidence quote".format(pid))
        for ev in p.get("evidence", []):
            if ev.get("doc") not in docs:
                e("pattern {}: evidence references unknown document {!r}".format(pid, ev.get("doc")))
            elif ev.get("redacted"):
                if not re.search(r"\[[^\]]+\]", ev.get("quote", "")):
                    w("pattern {}: redacted quote has no [placeholder]; was anything actually removed? {!r}".format(
                        pid, ev.get("quote", "")[:60]))
            elif reader and docs[ev["doc"]].get("path"):
                body = reader.text(docs[ev["doc"]])
                if body is None:
                    continue  # already reported once, against the document
                source = normalize_ws(body)
                quote = normalize_ws(ev.get("quote", ""))
                if quote not in source:
                    near = nearest_quote(source, quote)
                    e("pattern {}: quote not found verbatim in {}: {!r}{}".format(
                        pid, docs[ev["doc"]]["path"], quote[:60],
                        "; nearest verbatim form: {!r}".format(near) if near else ""))
        if p.get("tier") not in (1, 2, 3):
            e("pattern {}: tier must be 1, 2, or 3 (run `validate --fix` to compute it)".format(pid))
        elif docs and all(entry.get("id") in docs for entry in entries):
            snapshot = dict(p)
            computed, _ = compute_tier(snapshot, docs, weights)
            if computed != p["tier"]:
                w("pattern {}: stored tier {} but computed tier {} (run `validate --fix`)".format(
                    pid, p["tier"], computed))
        if p.get("tier_override") is not None and p["tier_override"] not in (1, 2, 3):
            e("pattern {}: tier_override must be 1, 2, 3, or null".format(pid))
        for ref in p.get("instead", []):
            if ref not in {q.get("id") for q in db.get("patterns", [])}:
                w("pattern {}: 'instead' references unknown pattern {}".format(pid, ref))
        scope = p.get("register_scope")
        if scope is not None:
            if not isinstance(scope, list) or not all(isinstance(x, str) and x.strip() for x in scope):
                e("pattern {}: 'register_scope' must be a list of registers".format(pid))
            else:
                for reg in scope:
                    if reg not in {d.get("register") for d in docs.values()}:
                        w("pattern {}: 'register_scope' names register {!r}, which no corpus "
                          "document has".format(pid, reg))
        displaces = p.get("displaces")
        if displaces is not None:
            if not isinstance(displaces, list) or not all(
                    isinstance(x, str) and x.strip() for x in displaces):
                e("pattern {}: 'displaces' must be a list of the word forms the author "
                  "does not use".format(pid))
            elif p.get("kind") == "absence":
                w("pattern {}: 'displaces' on an absence pattern; absences name their "
                  "replacements in 'instead'".format(pid))
    return errors, warnings


# ---------------------------------------------------------------- merge

def merge(dbs: List[Dict[str, Any]], partial: bool = False) -> Dict[str, Any]:
    if not dbs:
        raise ValueError("nothing to merge")
    versions = {d.get("db_version") for d in dbs}
    kinds = {d.get("kind") for d in dbs}
    if len(versions) != 1:
        raise ValueError("cannot merge DBs with different db_version: {}".format(sorted(versions, key=str)))
    if len(kinds) != 1:
        raise ValueError("cannot merge DBs of different kind: {}".format(sorted(kinds, key=str)))
    out: Dict[str, Any] = {
        "db_version": dbs[0]["db_version"],
        "kind": dbs[0]["kind"],
        "partial": partial,
        "created": max(str(d.get("created", "")) for d in dbs),
        "tool": "write-like-me",
        "corpus": {"documents": [], "total_words": 0},
        "review": {"status": "pending"},
        "patterns": [],
    }
    docs: Dict[str, Dict[str, Any]] = {}
    for d in dbs:
        for doc in d.get("corpus", {}).get("documents", []):
            prev = docs.get(doc["id"])
            if prev and prev.get("words") != doc.get("words"):
                raise ValueError("document {} has conflicting word counts {} vs {}".format(
                    doc["id"], prev.get("words"), doc.get("words")))
            docs.setdefault(doc["id"], doc)
    out["corpus"]["documents"] = list(docs.values())
    sealed = [d.get("corpus", {}).get("sealed") for d in dbs]
    if all(sealed):  # a mixed merge keeps the paths it has and stays unsealed
        out["corpus"]["sealed"] = max(str(x) for x in sealed)
    weights: Dict[str, Any] = {}
    for d in dbs:
        for register, share in (d.get("corpus", {}).get("register_weights") or {}).items():
            if register in weights and weights[register] != share:
                raise ValueError("register {} has conflicting weights {} vs {}: a weighting "
                                 "is one decision about the whole corpus".format(
                                     register, weights[register], share))
            weights[register] = share
    if weights:
        out["corpus"]["register_weights"] = weights

    patterns: Dict[str, Dict[str, Any]] = {}
    for d in dbs:
        for p in d.get("patterns", []):
            pid = p["id"]
            if pid not in patterns:
                q = {k: v for k, v in p.items() if not k.startswith("_")}
                q["documents"] = list(p.get("documents", []))
                q["evidence"] = list(p.get("evidence", []))
                q["notes"] = [p["note"]] if p.get("note") else []
                q.pop("note", None)
                patterns[pid] = q
                continue
            q = patterns[pid]
            have = {entry["id"]: entry for entry in q["documents"]}
            for entry in p.get("documents", []):
                if entry["id"] in have and have[entry["id"]] != entry:
                    raise ValueError("pattern {}: conflicting counts for document {}".format(pid, entry["id"]))
                have.setdefault(entry["id"], entry)
            q["documents"] = list(have.values())
            seen = {(ev.get("doc"), normalize_ws(ev.get("quote", ""))) for ev in q["evidence"]}
            for ev in p.get("evidence", []):
                key = (ev.get("doc"), normalize_ws(ev.get("quote", "")))
                if key not in seen:
                    q["evidence"].append(ev)
                    seen.add(key)
            if p.get("measurement") == "judged":
                q["measurement"] = "judged"
            if p.get("note") and p["note"] not in q["notes"]:
                q["notes"].append(p["note"])
            if q.get("regex") and p.get("regex") and q["regex"] != p["regex"]:
                q["notes"].append("merge: differing regex dropped: {}".format(p["regex"]))
            if not q.get("regex") and p.get("regex"):
                q["regex"] = p["regex"]
            if q.get("stat") and p.get("stat") and q["stat"] != p["stat"]:
                q["notes"].append("merge: differing stat dropped: {}".format(p["stat"]))
            if not q.get("stat") and p.get("stat"):
                q["stat"] = p["stat"]
            if q.get("tier_override") is None and p.get("tier_override") is not None:
                q["tier_override"] = p["tier_override"]
            if q.get("register_scope") and p.get("register_scope") and q["register_scope"] != p["register_scope"]:
                q["notes"].append("merge: differing register_scope dropped: {}".format(p["register_scope"]))
            if not q.get("register_scope") and p.get("register_scope"):
                q["register_scope"] = p["register_scope"]
            for ref in p.get("instead", []):
                q.setdefault("instead", [])
                if ref not in q["instead"]:
                    q["instead"].append(ref)
            for form in p.get("displaces", []):
                q.setdefault("displaces", [])
                if form not in q["displaces"]:
                    q["displaces"].append(form)
    for q in patterns.values():
        notes = q.pop("notes", [])
        if notes:
            q["note"] = " | ".join(notes)
    out["patterns"] = sorted(patterns.values(), key=lambda p: p["id"])
    recompute(out)
    return out


# ---------------------------------------------------------------- seal

def seal(db: Dict[str, Any], date: Optional[str] = None) -> int:
    """Drop every corpus path and stamp corpus.sealed; return paths dropped.

    Sealing removes the DB's only dependency on the corpus filesystem — nothing
    else in the manifest points at a file, and processing never reads the
    manifest at all. It is irreversible: `validate --corpus-dir` can no longer
    check a quote, so it belongs after the review round, not before.
    """
    if db.get("partial"):
        raise ValueError("cannot seal a partial DB: merge the parts, review, then seal")
    status = db.get("review", {}).get("status")
    if status != "reviewed":
        raise ValueError(
            "cannot seal a DB with review.status {!r}: sealing ends quote verification, "
            "so the review round comes first (references/technique.md)".format(status))
    docs = db.setdefault("corpus", {}).setdefault("documents", [])
    dropped = sum(1 for d in docs if d.pop("path", None) is not None)
    db["corpus"]["sealed"] = date or datetime.date.today().isoformat()
    return dropped


# ---------------------------------------------------------------- render

def fmt_rate(p: Dict[str, Any]) -> str:
    unit = p.get("unit", "per_1k_words")
    rate = p.get("rate")
    if rate is None:
        return "n/a"
    if unit == "per_1k_words":
        return "{:.1f} per 1k words".format(rate)
    if unit.startswith("share_of_"):
        return "{:.0%} of {}".format(rate, unit[len("share_of_"):])
    return "{:.1f} {}".format(rate, unit)


def render(db: Dict[str, Any], setting: str = "hard", dimension: Optional[str] = None) -> str:
    max_tier = SETTING_MAX_TIER[setting]
    lines = ["# Style profile ({} DB, db_version {})".format(db.get("kind"), db.get("db_version")), ""]
    corpus = db.get("corpus", {})
    lines.append("Corpus: {} documents, {} words; review: {}{}.".format(
        len(corpus.get("documents", [])), corpus.get("total_words", "?"),
        db.get("review", {}).get("status", "?"),
        "; sealed {}".format(corpus["sealed"]) if corpus.get("sealed") else ""))
    weights = corpus.get("register_weights")
    if weights:
        lines.append("Rates are register-weighted ({}): every rate below is a "
                     "share-weighted mean across registers, not a word-weighted one.".format(
                         ", ".join("{} {:g}".format(r, weights[r]) for r in sorted(weights))))
    lines.append("Setting: {} (tiers <= {}).".format(setting, max_tier))
    lines.append("")
    by_dim: Dict[str, List[Dict[str, Any]]] = {}
    for p in db.get("patterns", []):
        if effective_tier(p) > max_tier:
            continue
        if dimension and p.get("dimension") != dimension:
            continue
        by_dim.setdefault(p["dimension"], []).append(p)
    for dim in DIMENSIONS:
        if dim not in by_dim:
            continue
        lines.append("## {}".format(dim))
        lines.append("")
        for p in sorted(by_dim[dim], key=effective_tier):
            tier = effective_tier(p)
            tag = "absent" if p.get("kind") == "absence" else fmt_rate(p)
            rng = p.get("range")
            rng_s = " (range {}–{})".format(rng[0], rng[1]) if rng and p.get("kind") != "absence" else ""
            regs = ", ".join(p.get("registers", [])) or "-"
            if p.get("register_scope"):
                regs += " (scope: {})".format(", ".join(p["register_scope"]))
            lines.append("- **{}** — tier {}{}: {}{}; spread {:.0%}; registers: {}; {}".format(
                p["marker"], tier, " (overridden)" if p.get("tier_override") else "", tag, rng_s,
                p.get("spread", 0.0), regs, p.get("measurement", "?")))
            lines.append("  {}".format(p.get("description", "")))
            if p.get("instead"):
                lines.append("  Instead: {}".format(", ".join(p["instead"])))
            if p.get("displaces"):
                lines.append("  Never uses: {}".format(", ".join(p["displaces"])))
            for ev in p.get("evidence", [])[:2]:
                lines.append("  > {} — *{}*".format(ev.get("quote", "").strip(), ev.get("doc", "?")))
            if p.get("note"):
                lines.append("  Note: {}".format(p["note"]))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------- CLI

def cmd_info(args: argparse.Namespace) -> int:
    db = load(args.db)
    version = db.get("db_version")
    tiers = {1: 0, 2: 0, 3: 0}
    for p in db.get("patterns", []):
        tiers[effective_tier(p)] = tiers.get(effective_tier(p), 0) + 1
    corpus = db.get("corpus", {})
    facts = {
        "path": args.db,
        "kind": db.get("kind"),
        "db_version": version,
        "skill_db_version": CURRENT_DB_VERSION,
        "partial": bool(db.get("partial")),
        "documents": len(corpus.get("documents", [])),
        "sealed": corpus.get("sealed"),
        "total_words": corpus.get("total_words"),
        "register_weights": corpus.get("register_weights"),
        "patterns": len(db.get("patterns", [])),
        "tier_counts": tiers,
        "review_status": db.get("review", {}).get("status"),
        "created": db.get("created"),
    }
    if not isinstance(version, int):
        facts["status"] = "invalid: db_version missing"
        code = 1
    elif version < CURRENT_DB_VERSION:
        facts["status"] = "older than skill: migrate (references/migration.md)"
        code = 2
    elif version > CURRENT_DB_VERSION:
        facts["status"] = "newer than skill: update the write-like-me skill before using this DB"
        code = 3
    else:
        facts["status"] = "ok"
        code = 0
    if args.json:
        print(json.dumps(facts, indent=2))
    else:
        for k, v in facts.items():
            print("{}: {}".format(k, v))
    return code


def cmd_validate(args: argparse.Namespace) -> int:
    db = load(args.db)
    if args.fix:
        recompute(db)
        save(args.db, db)
    errors, warnings = validate(db, args.corpus_dir)
    for msg in warnings:
        print("WARN: " + msg)
    for msg in errors:
        print("ERROR: " + msg)
    print("{}: {} error(s), {} warning(s){}".format(
        args.db, len(errors), len(warnings), " — derived fields rewritten" if args.fix else ""))
    return 1 if errors else 0


def cmd_merge(args: argparse.Namespace) -> int:
    try:
        merged = merge([load(p) for p in args.dbs], partial=args.partial)
    except ValueError as exc:
        print("ERROR: " + str(exc))
        return 1
    save(args.output, merged)
    errors, warnings = validate(merged)
    for msg in warnings:
        print("WARN: " + msg)
    for msg in errors:
        print("ERROR: " + msg)
    print("merged {} DB(s) -> {}: {} documents, {} patterns".format(
        len(args.dbs), args.output, len(merged["corpus"]["documents"]), len(merged["patterns"])))
    return 1 if errors else 0


def cmd_seal(args: argparse.Namespace) -> int:
    db = load(args.db)
    try:
        dropped = seal(db)
    except ValueError as exc:
        print("ERROR: " + str(exc))
        return 1
    out = args.output or args.db
    save(out, db)
    errors, warnings = validate(db)
    for msg in warnings:
        print("WARN: " + msg)
    for msg in errors:
        print("ERROR: " + msg)
    print("sealed {}: dropped {} corpus path(s); quotes can no longer be verified "
          "against the corpus".format(out, dropped))
    return 1 if errors else 0


def cmd_render(args: argparse.Namespace) -> int:
    print(render(load(args.db), args.setting, args.dimension), end="")
    return 0


def cmd_tiers(args: argparse.Namespace) -> int:
    db = load(args.db)
    docs = doc_index(db)
    weights = register_weights(db)
    for p in db.get("patterns", []):
        snapshot = dict(p)
        computed, why = compute_tier(snapshot, docs, weights)
        print("{}\tcomputed={}\teffective={}\t{}".format(p["id"], computed, effective_tier(p), why))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("info"); s.add_argument("db"); s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_info)
    s = sub.add_parser("validate"); s.add_argument("db"); s.add_argument("--corpus-dir")
    s.add_argument("--fix", action="store_true"); s.set_defaults(fn=cmd_validate)
    s = sub.add_parser("merge"); s.add_argument("dbs", nargs="+"); s.add_argument("-o", "--output", required=True)
    s.add_argument("--partial", action="store_true"); s.set_defaults(fn=cmd_merge)
    s = sub.add_parser("seal"); s.add_argument("db"); s.add_argument("-o", "--output")
    s.set_defaults(fn=cmd_seal)
    s = sub.add_parser("render"); s.add_argument("db")
    s.add_argument("--setting", choices=sorted(SETTING_MAX_TIER), default="hard")
    s.add_argument("--dimension"); s.set_defaults(fn=cmd_render)
    s = sub.add_parser("tiers"); s.add_argument("db"); s.set_defaults(fn=cmd_tiers)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
