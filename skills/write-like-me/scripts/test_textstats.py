import json

import textstats

SAMPLE = """---
title: x
---

# A heading

This is a sentence — with an em dash. Here is another one; it has a semicolon. Short.

- item one
- item two: with colon

```python
x = "not — counted"
```

I think [the link](https://example.com/a—b) counts its text only. Don't you?

| a | b |
|---|---|
| 1 | 2 |
"""


def test_word_and_sentence_counts_exclude_code_tables_and_urls():
    r = textstats.measure(SAMPLE)
    s = r["stats"]
    assert s["headings"] == 1
    assert s["list_items"] == 2
    assert s["paragraphs"] == 2
    assert s["sentences"] == 5
    assert s["sentence_len_max"] == 8
    # "not — counted" inside code and the URL em dash are excluded
    assert r["per_1k"]["em_dash"] == round(1 / s["words"] * 1000, 2)
    assert r["per_1k"]["semicolon"] > 0
    assert r["per_1k"]["contraction"] > 0
    assert r["per_1k"]["second_person"] > 0


def test_ai_markers():
    text = ("This is not just a tool, it's a philosophy. It highlights the importance of care. "
            "Additionally, we ship fast, cheap, and reliable code. In conclusion, delve into the robust landscape.")
    r = textstats.measure(text)
    assert r["per_1k"]["ai_not_just"] > 0
    assert r["per_1k"]["ai_significance_tail"] > 0
    assert r["per_1k"]["ai_connective_opener"] > 0
    assert r["per_1k"]["ai_triad"] > 0
    assert r["per_1k"]["ai_summary_opener"] > 0
    assert r["per_1k"]["ai_vocabulary"] >= 3 / r["stats"]["words"] * 1000 - 0.01


def hits(text, name):
    r = textstats.measure(text)
    return round(r["per_1k"][name] * r["stats"]["words"] / 1000)


def test_contrast_frames():
    assert hits("Performance has to be a tested feature, not an afterthought.", "ai_comma_not") == 1
    assert hits("The scarce resource is not typing speed. It is judgment.", "ai_split_reframe") == 1
    assert hits("We built a bridge rather than an agent. Instead of guessing, measure. Instead, we removed it.", "ai_rather_than") == 3
    assert hits("It runs without building everything from scratch.", "ai_without_benefit") == 1
    assert hits("It works without the whole thing.", "ai_without_benefit") == 0


def test_reveal_frames():
    assert hits("Here is the point. The first proof: an OCT plugin for IntelliJ.", "ai_colon_punchline") == 1
    assert hits("Requirements: Node 18 and npm. A very long setup clause that runs well past the length limit before the colon: no.", "ai_colon_punchline") == 0
    assert hits("The result is a faster parser. Here's the unexpected part: it also helps agents. "
                "That is the idea behind Baukasten.", "ai_nominal_reveal") == 3
    assert hits("That changes today. This is where LLVM comes in. This matters commercially.", "ai_verdict_opener") == 3
    assert hits("What if the agent joined the session instead? That is the idea behind the OCT Agent.", "ai_question_answer") == 1
    assert hits("What happens when a coding agent joins your session?", "ai_what_if") == 1
    assert hits("Four principles carry the sensor side. We learned two things the hard way.", "ai_enumeration_announcement") == 2


def test_significance_and_signposting():
    assert hits("That matters because these decisions run often. Why notebooks matter now.", "ai_significance_tail") == 2
    assert hits("For DSL architects, this is the relevant question.", "ai_significance_tail") == 1
    assert hits("The serializer is the one worth weighing most carefully. Specs deserve special respect here.", "ai_worth_noting") == 2
    assert hits("It resolves left recursion natively, eliminating the need to refactor.", "ai_participial_tail") == 1
    assert hits("This article looks at three of them. We'll close with the open problem.", "ai_meta_signpost") == 2
    assert hits("Consider a state machine. Picture the tooling you'd want.", "ai_scene_imperative") == 2
    assert hits("Real-time collaboration shouldn't stop at the edge of the ecosystem.\n\nParser performance rarely "
                "determines the architecture.", "ai_negated_opener") == 2
    assert hits("Custom development therefore shifts toward integration. Therefore, we stop.", "ai_medial_therefore") == 1
    assert hits("It is fast, and therefore cheap.", "ai_medial_therefore") == 0


def test_stance_and_vocabulary():
    assert hits("What the software actually does is genuinely useful; real expertise solves real problems.", "ai_authenticity") == 4
    assert hits("Every fact traces to a source; it never guesses and always runs exactly once.", "ai_absolutizer") == 4
    assert hits("No hype, no magic. Software engineering, not magic.", "ai_anti_hype") == 3
    assert hits("Adoption is increasingly rapid; the transformation is faster than ever.", "ai_trend_word") == 3
    assert hits("It bridges the gap between silos and removes friction.", "ai_spatial_metaphor") == 4
    assert hits("Table stakes by now; it does the heavy lifting under the hood.", "ai_stock_idiom") == 3
    assert hits("Different windows into the same domain that experts share.", "ai_same_x") == 1
    assert hits("Clean, human-readable rules and a sleek, robust interface.", "ai_adjective_stack") == 2
    assert hits("A transformative, blazing-fast engine with actionable insights.", "ai_vocabulary") == 3


def test_generic_counters_and_heading_stats():
    text = ("# Delete the Tree: Rethinking Language Tooling\n\n## What it takes\n\n"
            "- **Native performance.** Programs run as machine code.\n- *Panels.* Each panel is a widget.\n\n"
            "**Verify by execution.** Never trust prose — a rule, not a suggestion — and it compounds. "
            "Gartner explicitly cautions against roughly 21% overhead, i.e. an IDE-grade, theme-aware \"citizen developer\" "
            "experience built deliberately and quietly, **which is the whole point of the exercise** in order to ship.")
    r = textstats.measure(text)
    s = r["stats"]
    assert s["colon_heading_share"] == 0.5
    assert s["heading_title_case_share"] == 0.5
    n = lambda name: round(r["per_1k"][name] * s["words"] / 1000)
    assert n("label_lead") == 3
    assert n("clause_bold") == 1
    assert n("em_dash_appositive") == 2
    assert n("source_as_agent") == 1
    assert n("hedged_number") == 1
    assert n("scholarly_connective") == 2
    assert n("hyphen_compound") == 2
    assert n("scare_quote") == 1
    assert n("deliberate_adverb") == 2
    assert n("quiet_adverb") == 1
    assert textstats.is_title_case("Delete the Tree: Rethinking Language Tooling")
    assert not textstats.is_title_case("What this means if you're evaluating language tooling")


def test_measure_pattern_units_and_verdict():
    r = textstats.measure("First: one. Second: two. Third thing.\n\nAnother paragraph here.")
    per_1k = {"id": "punctuation/colon", "regex": ":", "unit": "per_1k_words", "rate": 200.0, "range": [150.0, 260.0]}
    share = {"id": "punctuation/colon-sentences", "regex": ":", "unit": "share_of_sentences", "rate": 0.5, "range": [0.4, 0.6]}
    stat = {"id": "sentence-rhythm/median", "stat": "sentence_len_median", "unit": "words", "rate": 2.0, "range": [2.0, 3.0]}
    absent = {"id": "punctuation/em-dash", "regex": "—", "kind": "absence", "rate": 0.0, "range": [0.0, 0.0]}
    v = textstats.measure_pattern(per_1k, r)
    assert v == round(2 / r["stats"]["words"] * 1000, 2)
    assert textstats.verdict(v, per_1k) == "match"
    assert textstats.measure_pattern(share, r) == 0.5
    assert textstats.verdict(0.5, share) == "match"
    assert textstats.measure_pattern(stat, r) == r["stats"]["sentence_len_median"]
    assert textstats.verdict(0.0, absent) == "match"
    assert textstats.verdict(1.2, absent) == "gap"
    assert textstats.verdict(400.0, per_1k) == "gap"
    wide = {"id": "connectives/so-initial", "unit": "per_1k_words", "rate": 3.2, "range": [0.0, 5.5]}
    assert textstats.verdict(0.0, wide) == "low"
    assert textstats.verdict(3.0, wide) == "match"
    assert textstats.verdict(5.4, wide) == "match"
    assert textstats.verdict(9.0, wide) == "gap"


def test_cli_json_with_db(tmp_path, capsys):
    doc = tmp_path / "doc.md"
    doc.write_text("Plain text: one sentence with a colon. And another.", encoding="utf-8")
    db = tmp_path / "db.json"
    db.write_text(json.dumps({"patterns": [
        {"id": "punctuation/colon", "regex": ":", "unit": "per_1k_words", "rate": 100.0, "range": [50.0, 150.0], "tier": 1},
        {"id": "voice-and-person/judged-only", "unit": "per_1k_words", "rate": 1.0, "tier": 2},
    ]}), encoding="utf-8")
    assert textstats.main(["measure", str(doc), "--db", str(db), "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    entry = out[str(doc)]
    assert entry["patterns"]["punctuation/colon"]["verdict"] == "match"
    assert "voice-and-person/judged-only" not in entry["patterns"]
    assert textstats.main(["measure", str(doc), "--db", str(db)]) == 0
    assert "punctuation/colon" in capsys.readouterr().out
    assert textstats.main(["counters"]) == 0
