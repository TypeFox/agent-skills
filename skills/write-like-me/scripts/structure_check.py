#!/usr/bin/env python3
"""Check that a rewritten Markdown document kept the original's structure and facts.

write-like-me rewrites voice, never shape or content: the heading outline, the
sequence of blocks inside every section (paragraphs, lists, code, tables,
quotes), list item counts, and verbatim material (code, tables, quotes, URLs,
numbers) must survive a rewrite, and paragraph counts should where possible.
Reading two versions side by side does not reliably catch a merged paragraph
or a dropped list item; this check does, mechanically, so the rewrite loop can
run it after every pass.

Usage
  structure_check.py ORIGINAL REWRITTEN [--json]

Reports ERROR lines for hard violations (outline, block sequence, list item
counts, code/table/quote text, URLs, numbers dropped) and WARN lines for soft
ones (paragraph count per section, heading wording, numbers added). Exit 1 when
any ERROR was found, 0 otherwise.

Stdlib only, Python 3.8+.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
TABLE_RE = re.compile(r"^\s*\|")
HR_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
BLOCKQUOTE_RE = re.compile(r"^\s*>")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
URL_RE = re.compile(r"https?://[^\s)>\]]+|\]\(([^)\s]+)\)")
NUMBER_RE = re.compile(r"(?<![\w/])\d[\d,.]*\d|(?<![\w/])\d")


def parse(text: str) -> List[Dict[str, Any]]:
    """Return a flat list of blocks: {type, text, level?, items?}."""
    lines = text.replace("\r\n", "\n").split("\n")
    blocks: List[Dict[str, Any]] = []
    i = 0
    n = len(lines)
    if lines and lines[0].strip() == "---":
        j = 1
        while j < n and lines[j].strip() != "---":
            j += 1
        if j < n:
            blocks.append({"type": "frontmatter", "text": "\n".join(lines[: j + 1])})
            i = j + 1
    para: List[str] = []

    def flush() -> None:
        if para:
            blocks.append({"type": "paragraph", "text": " ".join(s.strip() for s in para)})
            para.clear()

    while i < n:
        line = lines[i]
        m = FENCE_RE.match(line)
        if m:
            flush()
            fence = m.group(1)
            j = i + 1
            while j < n and not lines[j].strip().startswith(fence):
                j += 1
            blocks.append({"type": "code", "text": "\n".join(lines[i: j + 1])})
            i = j + 1
            continue
        if not line.strip():
            flush()
            i += 1
            continue
        m = HEADING_RE.match(line)
        if m:
            flush()
            blocks.append({"type": "heading", "level": len(m.group(1)), "text": m.group(2)})
            i += 1
            continue
        if HR_RE.match(line):
            flush()
            blocks.append({"type": "hr", "text": ""})
            i += 1
            continue
        if TABLE_RE.match(line):
            flush()
            j = i
            while j < n and TABLE_RE.match(lines[j]):
                j += 1
            blocks.append({"type": "table", "text": "\n".join(l.strip() for l in lines[i:j])})
            i = j
            continue
        if BLOCKQUOTE_RE.match(line):
            flush()
            j = i
            while j < n and BLOCKQUOTE_RE.match(lines[j]):
                j += 1
            blocks.append({"type": "blockquote",
                           "text": " ".join(re.sub(r"^\s*>\s?", "", l).strip() for l in lines[i:j])})
            i = j
            continue
        if LIST_ITEM_RE.match(line):
            flush()
            j = i
            items = 0
            while j < n and lines[j].strip() and not HEADING_RE.match(lines[j]) and not FENCE_RE.match(lines[j]):
                if LIST_ITEM_RE.match(lines[j]):
                    items += 1
                j += 1
            blocks.append({"type": "list", "items": items, "text": "\n".join(lines[i:j])})
            i = j
            continue
        if line.lstrip().startswith("<"):
            flush()
            j = i
            while j < n and lines[j].strip():
                j += 1
            blocks.append({"type": "html", "text": "\n".join(lines[i:j])})
            i = j
            continue
        para.append(line)
        i += 1
    flush()
    return blocks


def sections(blocks: List[Dict[str, Any]]) -> List[Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]]:
    out: List[Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]] = [(None, [])]
    for b in blocks:
        if b["type"] == "heading":
            out.append((b, []))
        else:
            out[-1][1].append(b)
    return out


def collapse_runs(types: List[str]) -> List[str]:
    """Collapse consecutive paragraphs into one token so only their placement counts."""
    out: List[str] = []
    for t in types:
        if t == "paragraph" and out and out[-1] == "paragraph":
            continue
        out.append(t)
    return out


def prose_text(blocks: List[Dict[str, Any]]) -> str:
    return "\n".join(b["text"] for b in blocks if b["type"] in ("paragraph", "list", "blockquote", "heading", "table"))


def compare(original: str, rewritten: str) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    a_blocks, b_blocks = parse(original), parse(rewritten)
    a_secs, b_secs = sections(a_blocks), sections(b_blocks)

    a_heads = [(b["level"], b["text"]) for b in a_blocks if b["type"] == "heading"]
    b_heads = [(b["level"], b["text"]) for b in b_blocks if b["type"] == "heading"]
    if [h[0] for h in a_heads] != [h[0] for h in b_heads]:
        errors.append("heading outline changed: {} heading(s) at levels {} -> {} heading(s) at levels {}".format(
            len(a_heads), [h[0] for h in a_heads], len(b_heads), [h[0] for h in b_heads]))
    else:
        for (lvl, at), (_, bt) in zip(a_heads, b_heads):
            if at != bt:
                warnings.append("heading text changed (h{}): {!r} -> {!r}".format(lvl, at, bt))

    for idx, ((a_head, a_body), (b_head, b_body)) in enumerate(zip(a_secs, b_secs)):
        label = "section {} ({})".format(idx, a_head["text"] if a_head else "preamble")
        a_types = [b["type"] for b in a_body]
        b_types = [b["type"] for b in b_body]
        a_struct = [t for t in a_types if t != "paragraph"]
        b_struct = [t for t in b_types if t != "paragraph"]
        if a_struct != b_struct:
            errors.append("{}: block sequence changed: {} -> {}".format(label, a_types, b_types))
            continue
        if collapse_runs(a_types) != collapse_runs(b_types):
            errors.append("{}: paragraphs moved across non-paragraph blocks: {} -> {}".format(label, a_types, b_types))
            continue
        a_pars = a_types.count("paragraph")
        b_pars = b_types.count("paragraph")
        if a_pars != b_pars:
            warnings.append("{}: paragraph count {} -> {}".format(label, a_pars, b_pars))
        for a_b, b_b in zip([b for b in a_body if b["type"] != "paragraph"],
                            [b for b in b_body if b["type"] != "paragraph"]):
            if a_b["type"] == "list" and a_b["items"] != b_b["items"]:
                errors.append("{}: list item count {} -> {}".format(label, a_b["items"], b_b["items"]))
            if a_b["type"] in ("code", "table", "html", "frontmatter") and a_b["text"].strip() != b_b["text"].strip():
                errors.append("{}: {} block text changed (must stay verbatim)".format(label, a_b["type"]))
            if a_b["type"] == "blockquote" and a_b["text"] != b_b["text"]:
                errors.append("{}: quoted material changed (must stay verbatim)".format(label))
    if len(a_secs) != len(b_secs):
        errors.append("section count {} -> {}".format(len(a_secs), len(b_secs)))

    a_urls = Counter(m.group(1) or m.group(0) for m in URL_RE.finditer(original))
    b_urls = Counter(m.group(1) or m.group(0) for m in URL_RE.finditer(rewritten))
    for url in a_urls:
        if b_urls[url] < a_urls[url]:
            errors.append("link dropped or changed: {}".format(url))
    for url in b_urls:
        if a_urls[url] < b_urls[url]:
            warnings.append("link added: {}".format(url))

    a_text = prose_text([b for b in a_blocks if b["type"] not in ("code", "html", "frontmatter")])
    b_text = prose_text([b for b in b_blocks if b["type"] not in ("code", "html", "frontmatter")])
    a_nums = Counter(NUMBER_RE.findall(a_text))
    b_nums = Counter(NUMBER_RE.findall(b_text))
    missing = [n for n in a_nums if b_nums[n] < a_nums[n]]
    added = [n for n in b_nums if a_nums[n] < b_nums[n]]
    if missing:
        errors.append("numbers missing from rewrite: {}".format(", ".join(sorted(missing))))
    if added:
        warnings.append("numbers not in original: {}".format(", ".join(sorted(added))))
    return errors, warnings


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("original")
    ap.add_argument("rewritten")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    with open(args.original, encoding="utf-8") as fh:
        original = fh.read()
    with open(args.rewritten, encoding="utf-8") as fh:
        rewritten = fh.read()
    errors, warnings = compare(original, rewritten)
    if args.json:
        print(json.dumps({"errors": errors, "warnings": warnings}, indent=2))
    else:
        for msg in warnings:
            print("WARN: " + msg)
        for msg in errors:
            print("ERROR: " + msg)
        print("structure check: {} error(s), {} warning(s)".format(len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
