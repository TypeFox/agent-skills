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
                                 document; --fix rewrites derived fields
                                 (rate, spread, range, coverage, tier)
  merge DB... -o OUT [--partial] union of corpus manifests and patterns from
                                 several (partial) DBs, derived fields
                                 recomputed from the merged per-document data
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
import json
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

CURRENT_DB_VERSION = 1

# Keep in sync with references/taxonomy.md (the taxonomy is the authority).
DIMENSIONS = [
    "punctuation",
    "sentence-rhythm",
    "paragraph-openers",
    "argument-structure",
    "connectives",
    "voice-and-person",
    "tone-markers",
    "imagery",
    "attitude-adverbs",
    "emphasis",
    "lists",
    "headings",
    "opener-closer",
    "spelling-lexical",
    "content-conventions",
    "negative-parallelism",
    "significance-tails",
    "false-ranges",
    "rule-of-three",
    "summaries",
    "scene-setting",
]

KINDS = ("presence", "absence")
MEASUREMENTS = ("counted", "judged")
UNITS = ("per_1k_words", "share_of_sentences", "share_of_paragraphs", "words", "count")
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


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------- derived fields

def compute_stats(pattern: Dict[str, Any], docs: Dict[str, Dict[str, Any]]) -> None:
    """Recompute rate, spread, range, coverage, registers from documents[]."""
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


def compute_tier(pattern: Dict[str, Any], docs: Dict[str, Dict[str, Any]]) -> Tuple[int, str]:
    """Evidence tier: 1 = strong, 2 = moderate, 3 = weak. See db-schema.md."""
    if "_present" not in pattern:
        compute_stats(pattern, docs)
    corpus_registers = {d.get("register", "unknown") for d in docs.values()}
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
    for p in db.get("patterns", []):
        compute_stats(p, docs)
        p["tier"], p["tier_reason"] = compute_tier(p, docs)
        p.pop("_present", None)
        p.pop("_measured_words", None)
    db["corpus"]["total_words"] = sum(d.get("words", 0) for d in docs.values())


# ---------------------------------------------------------------- validate

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
        docs[did] = d
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
        entries = p.get("documents", [])
        if not entries:
            e("pattern {}: documents[] is empty; every pattern needs per-document counts".format(pid))
        for entry in entries:
            if entry.get("id") not in docs:
                e("pattern {}: documents[] references unknown document {!r}".format(pid, entry.get("id")))
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
            elif corpus_dir and docs[ev["doc"]].get("path"):
                import os
                path = os.path.join(corpus_dir, docs[ev["doc"]]["path"])
                try:
                    with open(path, encoding="utf-8") as fh:
                        source = normalize_ws(fh.read())
                except OSError:
                    w("pattern {}: cannot open {} to verify quote".format(pid, path))
                    continue
                if normalize_ws(ev.get("quote", "")) not in source:
                    e("pattern {}: quote not found verbatim in {}: {!r}".format(
                        pid, docs[ev["doc"]]["path"], ev.get("quote", "")[:60]))
        if p.get("tier") not in (1, 2, 3):
            e("pattern {}: tier must be 1, 2, or 3 (run `validate --fix` to compute it)".format(pid))
        elif docs and all(entry.get("id") in docs for entry in entries):
            snapshot = dict(p)
            computed, _ = compute_tier(snapshot, docs)
            if computed != p["tier"]:
                w("pattern {}: stored tier {} but computed tier {} (run `validate --fix`)".format(
                    pid, p["tier"], computed))
        if p.get("tier_override") is not None and p["tier_override"] not in (1, 2, 3):
            e("pattern {}: tier_override must be 1, 2, 3, or null".format(pid))
        for ref in p.get("instead", []):
            if ref not in {q.get("id") for q in db.get("patterns", [])}:
                w("pattern {}: 'instead' references unknown pattern {}".format(pid, ref))
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
            if q.get("tier_override") is None and p.get("tier_override") is not None:
                q["tier_override"] = p["tier_override"]
            for ref in p.get("instead", []):
                q.setdefault("instead", [])
                if ref not in q["instead"]:
                    q["instead"].append(ref)
    for q in patterns.values():
        notes = q.pop("notes", [])
        if notes:
            q["note"] = " | ".join(notes)
    out["patterns"] = sorted(patterns.values(), key=lambda p: p["id"])
    recompute(out)
    return out


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
    lines.append("Corpus: {} documents, {} words; review: {}.".format(
        len(corpus.get("documents", [])), corpus.get("total_words", "?"),
        db.get("review", {}).get("status", "?")))
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
            lines.append("- **{}** — tier {}{}: {}{}; spread {:.0%}; registers: {}; {}".format(
                p["marker"], tier, " (overridden)" if p.get("tier_override") else "", tag, rng_s,
                p.get("spread", 0.0), regs, p.get("measurement", "?")))
            lines.append("  {}".format(p.get("description", "")))
            if p.get("instead"):
                lines.append("  Instead: {}".format(", ".join(p["instead"])))
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
        "total_words": corpus.get("total_words"),
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


def cmd_render(args: argparse.Namespace) -> int:
    print(render(load(args.db), args.setting, args.dimension), end="")
    return 0


def cmd_tiers(args: argparse.Namespace) -> int:
    db = load(args.db)
    docs = doc_index(db)
    for p in db.get("patterns", []):
        snapshot = dict(p)
        computed, why = compute_tier(snapshot, docs)
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
    s = sub.add_parser("render"); s.add_argument("db")
    s.add_argument("--setting", choices=sorted(SETTING_MAX_TIER), default="hard")
    s.add_argument("--dimension"); s.set_defaults(fn=cmd_render)
    s = sub.add_parser("tiers"); s.add_argument("db"); s.set_defaults(fn=cmd_tiers)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
