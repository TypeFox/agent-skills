import json

import styledb
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
    assert r["per_1k"]["ai_not_but"] == 0  # the comma form is split-reframe territory, not not-but
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
    counter = {"id": "punctuation/colon-elaboration", "stat": "colon", "unit": "per_1k_words", "rate": 200.0}
    assert textstats.measure_pattern(counter, r) == r["per_1k"]["colon"] == v
    assert textstats.measure_pattern({"id": "x/unknown", "stat": "no_such_counter"}, r) is None
    assert textstats.verdict(0.0, absent) == "match"
    assert textstats.verdict(1.2, absent) == "gap"
    assert textstats.verdict(400.0, per_1k) == "gap"
    wide = {"id": "connectives/so-initial", "unit": "per_1k_words", "rate": 3.2, "range": [0.0, 5.5]}
    assert textstats.verdict(0.0, wide) == "low"  # no spread recorded: the range test decides
    assert textstats.verdict(3.0, wide) == "match"
    assert textstats.verdict(5.4, wide) == "match"
    assert textstats.verdict(9.0, wide) == "gap"


def test_share_of_headings_is_a_unit():
    r = textstats.measure("# Hook: Subtitle\n\n## Plain heading\n\nBody text here.")
    colon = {"id": "headings/colon-heading", "regex": ":", "unit": "share_of_headings",
             "rate": 0.5, "range": [0.2, 1.0], "spread": 1.0}
    assert textstats.measure_pattern(colon, r) == 0.5
    assert textstats.verdict(0.5, colon, r["stats"]) == "match"
    # the gap counts headings, the unit's own denominator
    assert textstats.gap_size(0.0, colon, {"headings": 4}) == 2.0


def test_zero_against_a_habit_of_most_documents_is_absent_not_low():
    # One corpus document without the habit puts 0 into the range, so the range test alone
    # calls an input with none of it "low" — and processing leaves lean rows alone. These are
    # the additive rows, the ones that make a rewrite sound like the author, so they get a
    # verdict of their own.
    habitual = {"id": "connectives/so-initial", "unit": "per_1k_words", "rate": 3.2,
                "range": [0.0, 5.5], "spread": 0.8}
    assert textstats.verdict(0.0, habitual) == "absent"
    assert textstats.verdict(0.4, habitual) == "low"  # present but thin: still a lean row
    assert textstats.verdict(3.0, habitual) == "match"
    occasional = dict(habitual, spread=0.4)
    assert textstats.verdict(0.0, occasional) == "low"  # not a habit of most documents
    absence = {"id": "punctuation/em-dash", "kind": "absence", "rate": 0.0,
               "range": [0.0, 0.0], "spread": 1.0}
    assert textstats.verdict(0.0, absence) == "match"  # zero is the point of an absence


def test_a_pattern_the_input_is_too_short_to_express_is_not_a_target():
    # 3.2 per 1k predicts 0.2 occurrences in a 64-word note, so neither the zero the input
    # has nor the one a rewrite would add says anything about the author's habit — and the
    # one would land at 15.6 per 1k, five times their rate.
    habitual = {"id": "connectives/so-initial", "unit": "per_1k_words", "rate": 3.2,
                "range": [0.0, 5.5], "spread": 0.8}
    short = {"words": 64, "sentences": 5, "paragraphs": 1}
    assert textstats.verdict(0.0, habitual, short) == "too-short"
    assert textstats.verdict(15.6, habitual, short) == "too-short"  # neither is evidence
    assert textstats.verdict(0.0, habitual, {"words": 1000}) == "absent"  # expressible again
    assert textstats.verdict(0.0, habitual) == "absent"  # no stats: length unknown
    # absences hold at any length — zero is expressible in a one-line note
    absence = {"id": "punctuation/em-dash", "kind": "absence", "regex": "—", "rate": 0.0,
               "range": [0.0, 0.0], "spread": 1.0}
    assert textstats.verdict(15.6, absence, short) == "gap"
    # a share over five sentences or one paragraph is as coarse as its denominator
    share = {"id": "sentence-rhythm/one-sentence-paragraph", "unit": "share_of_paragraphs",
             "rate": 0.19, "range": [0.0, 0.33], "spread": 0.8}
    assert textstats.verdict(0.0, share, short) == "too-short"
    assert textstats.verdict(0.0, share, {"paragraphs": 12}) == "absent"


def test_cli_json_with_db(tmp_path, capsys):
    doc = tmp_path / "doc.md"
    doc.write_text("Plain text: one sentence with a colon. And another one after it.", encoding="utf-8")
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


def test_gap_is_the_size_of_the_edit_in_occurrences():
    # The comparison table sorts by gap, so gap has to mean the same thing on every axis:
    # how many places a rewrite would have to change. Rows nothing should touch are 0.
    stats = {"words": 500, "sentences": 40, "paragraphs": 10}
    habit = {"id": "voice-and-person/first-singular", "unit": "per_1k_words", "rate": 45.0,
             "range": [22.0, 76.0], "spread": 1.0}
    assert textstats.gap_size(0.0, habit, stats) == 22.5   # 45 per 1k over 500 words
    assert textstats.gap_size(20.0, habit, stats) == 12.5  # thin: still 12 places short
    assert textstats.gap_size(45.0, habit, stats) == 0.0   # match: nothing to edit
    share = {"id": "sentence-rhythm/short-punch", "unit": "share_of_sentences", "rate": 0.4,
             "range": [0.3, 0.5], "spread": 1.0}
    assert textstats.gap_size(0.15, share, stats) == 10.0  # ten sentences short of the share
    absence = {"id": "punctuation/em-dash", "kind": "absence", "unit": "per_1k_words",
               "rate": 0.0, "range": [0.0, 0.0], "spread": 1.0}
    assert textstats.gap_size(6.0, absence, stats) == 3.0  # three em dashes to take out
    length = {"id": "sentence-rhythm/median", "stat": "sentence_len_median", "unit": "words",
              "rate": 12.0, "range": [10.0, 14.0]}
    assert textstats.gap_size(19.0, length, stats) == 7.0  # not a count: the axis's own scale
    occasional = {"id": "connectives/so-initial", "unit": "per_1k_words", "rate": 3.2,
                  "range": [0.0, 5.5], "spread": 0.8}
    assert textstats.gap_size(0.0, occasional, {"words": 64}) == 0.0  # too-short: no evidence
    assert textstats.gap_size(0.0, {"id": "x/judged"}, stats) is None  # no rate to compare to


def test_classes_say_what_the_rewrite_would_do_with_each_row():
    habit = {"id": "voice-and-person/first-singular", "unit": "per_1k_words", "rate": 45.0,
             "range": [22.0, 76.0], "spread": 1.0}
    assert textstats.classify(45.0, habit, "match") == "do-not-touch"
    assert textstats.classify(0.0, habit, "absent") == "add"
    assert textstats.classify(20.0, habit, "low") == "lean"
    assert textstats.classify(90.0, habit, "high") == "lean"
    # `gap` splits by side: over the author's range is a removal, under it is the additive half
    assert textstats.classify(120.0, habit, "gap") == "remove"
    assert textstats.classify(5.0, habit, "gap") == "add"
    absence = {"id": "punctuation/em-dash", "kind": "absence", "rate": 0.0, "range": [0.0, 0.0]}
    assert textstats.classify(6.0, absence, "gap") == "remove"
    assert textstats.classify(0.0, habit, "too-short") == "neutral"


def test_strictness_ceilings_agree_with_the_db_script():
    # The tables are duplicated so that either script runs on its own; a change to one that
    # missed the other would gate rewrites differently depending on which one was asked.
    assert textstats.SETTING_MAX_TIER == styledb.SETTING_MAX_TIER
    overridden = {"tier": 3, "tier_override": 1}
    assert textstats.effective_tier(overridden) == styledb.effective_tier(overridden) == 1
    assert textstats.effective_tier({"tier": 2}) == styledb.effective_tier({"tier": 2}) == 2


def comparison_rows(out):
    """The classified DB rows of a measure run, in the order they were printed."""
    return [l for l in out.splitlines()
            if l.startswith(("add", "remove", "lean", "do-not-touch", "neutral"))]


def test_ai_db_rows_are_evidence_not_rewrite_rows(tmp_path, capsys):
    # The AI DB's rates are the machine's, so `match` there means machine-typical; classing
    # its rows as if they were targets would tell the rewrite to keep the machine's em dashes.
    doc = tmp_path / "draft.md"
    doc.write_text("A draft \u2014 with one dash. " + "More words follow here. " * 60, encoding="utf-8")
    user = tmp_path / "user.json"
    user.write_text(json.dumps({"kind": "user", "patterns": [
        {"id": "punctuation/em-dash", "regex": "\u2014", "kind": "absence", "unit": "per_1k_words",
         "rate": 0.0, "range": [0.0, 0.0], "spread": 1.0, "tier": 1}]}), encoding="utf-8")
    ai = tmp_path / "ai.json"
    ai.write_text(json.dumps({"kind": "ai", "patterns": [
        {"id": "punctuation/em-dash", "regex": "\u2014", "unit": "per_1k_words",
         "rate": 7.5, "range": [0.0, 15.0], "spread": 0.95, "tier": 1}]}), encoding="utf-8")

    assert textstats.main(["measure", str(doc), "--db", str(user), "--db", str(ai),
                           "--sort-gap", "--setting", "medium"]) == 0
    out = capsys.readouterr().out
    assert len(comparison_rows(out)) == 1 and comparison_rows(out)[0].startswith("remove")
    assert "AI DB patterns from" in out
    assert any(l.startswith("punctuation/em-dash") and l.rstrip().endswith("match") for l in out.splitlines())

    assert textstats.main(["measure", str(doc), "--db", str(user), "--db", str(ai),
                           "--setting", "medium", "--json"]) == 0
    entry = json.loads(capsys.readouterr().out)[str(doc)]
    assert entry["patterns"]["punctuation/em-dash"]["class"] == "remove"  # the same id, kept apart
    ai_row = entry["ai_patterns"]["punctuation/em-dash"]
    assert ai_row["verdict"] == "match" and "class" not in ai_row and "gap" not in ai_row


def test_sort_gap_and_setting_build_the_comparison_table(tmp_path, capsys):
    doc = tmp_path / "note.md"
    doc.write_text("Notes: I fixed it. The cause: DNS, not a timeout — the retry backs off "
                   "now. One more thing: I push the follow-up tomorrow after the review.",
                   encoding="utf-8")
    db = tmp_path / "db.json"
    db.write_text(json.dumps({"patterns": [
        {"id": "punctuation/colon-elaboration", "regex": r":(?=\s)", "unit": "per_1k_words",
         "rate": 100.0, "range": [50.0, 150.0], "spread": 1.0, "tier": 1},
        {"id": "punctuation/em-dash", "regex": "—", "kind": "absence", "unit": "per_1k_words",
         "rate": 0.0, "range": [0.0, 0.0], "spread": 1.0, "tier": 3},
        {"id": "connectives/so-initial", "regex": r"(?:^|(?<=[.!?]\s))So", "unit": "per_1k_words",
         "rate": 200.0, "range": [100.0, 300.0], "spread": 1.0, "tier": 1},
    ]}), encoding="utf-8")

    assert textstats.main(["measure", str(doc), "--db", str(db), "--sort-gap",
                           "--setting", "medium"]) == 0
    rows = comparison_rows(capsys.readouterr().out)
    ids = [next(t for t in r.split() if "/" in t) for r in rows]
    # the missing habit is the biggest edit, the one em dash the smallest, the colons no edit
    assert ids == ["connectives/so-initial", "punctuation/em-dash", "punctuation/colon-elaboration"]
    assert rows[0].startswith("add ")            # tier 1: inside the medium ceiling
    assert rows[1].startswith("remove [manual]")  # tier 3: above it, so the author's call
    assert rows[2].startswith("do-not-touch")

    # the columns are opt-in: without the flags the table is the one the other steps read
    assert textstats.main(["measure", str(doc), "--db", str(db)]) == 0
    plain = capsys.readouterr().out
    assert comparison_rows(plain) == []
    assert "punctuation/em-dash" in plain

    assert textstats.main(["measure", str(doc), "--db", str(db), "--setting", "soft",
                           "--json"]) == 0
    patterns = json.loads(capsys.readouterr().out)[str(doc)]["patterns"]
    for row in patterns.values():
        # a gap above zero means exactly "this row asks for an edit"
        assert (row["gap"] > 0) == (row["class"] in textstats.EDITING_CLASSES)
    assert patterns["connectives/so-initial"]["dropped_by_setting"] is False
    assert patterns["punctuation/em-dash"]["dropped_by_setting"] is True
    assert patterns["punctuation/colon-elaboration"]["dropped_by_setting"] is False


def test_judged_patterns_are_listed_even_though_they_have_no_row(tmp_path, capsys):
    # A judged pattern carries no counter, so it gets no verdict and no row — and a rewrite
    # driven by the table alone would never hear of it. `measure` names it instead.
    doc = tmp_path / "draft.md"
    doc.write_text("A draft. " + "More words follow here. " * 60, encoding="utf-8")
    db = tmp_path / "user.json"
    db.write_text(json.dumps({"kind": "user", "patterns": [
        {"id": "punctuation/colon", "regex": ":", "unit": "per_1k_words",
         "rate": 5.0, "range": [1.0, 9.0], "spread": 1.0, "tier": 1},
        {"id": "opener-closer/closer-punch", "measurement": "judged", "tier": 2,
         "description": "Ends on a one-line punch, never a summary paragraph.",
         "unit": "per_1k_words", "rate": 2.4, "range": [0.0, 4.5], "spread": 0.6}]}),
        encoding="utf-8")

    assert textstats.main(["measure", str(doc), "--db", str(db)]) == 0
    out = capsys.readouterr().out
    assert "read for these" in out
    assert "opener-closer/closer-punch" in out
    assert "Ends on a one-line punch" in out

    assert textstats.main(["measure", str(doc), "--db", str(db), "--json"]) == 0
    entry = json.loads(capsys.readouterr().out)[str(doc)]
    assert "opener-closer/closer-punch" not in entry["patterns"]
    assert entry["judged_patterns"]["opener-closer/closer-punch"]["tier"] == 2


def test_ai_db_judged_patterns_are_not_offered_as_a_reading_list(tmp_path, capsys):
    doc = tmp_path / "draft.md"
    doc.write_text("A draft. " + "More words follow here. " * 60, encoding="utf-8")
    ai = tmp_path / "ai.json"
    ai.write_text(json.dumps({"kind": "ai", "patterns": [
        {"id": "tone-markers/vagueness", "measurement": "judged", "tier": 1,
         "description": "Judged on the machine side.", "unit": "per_1k_words",
         "rate": 3.0, "range": [0.0, 6.0], "spread": 0.8}]}), encoding="utf-8")
    assert textstats.main(["measure", str(doc), "--db", str(ai)]) == 0
    assert "read for these" not in capsys.readouterr().out


def _db(patterns):
    return {"db_version": 1, "patterns": patterns}


REPORT_DB = _db([
    {"id": "punctuation/em-dash", "kind": "absence", "measurement": "counted",
     "stat": "em_dash", "unit": "per_1k_words", "tier": 2, "rate": 0.0,
     "range": [0.0, 0.0], "spread": 1.0, "description": "No em dashes."},
    {"id": "voice-and-person/first-plural", "kind": "presence", "measurement": "counted",
     "stat": "first_person_plural", "unit": "per_1k_words", "tier": 2, "rate": 4.0,
     "range": [0.0, 8.0], "spread": 0.8, "description": "Rare team we."},
    {"id": "spelling-lexical/british-spelling", "kind": "presence", "measurement": "counted",
     "regex": r"\b(?:behaviour|colour|organised)\b", "ignore_case": True,
     "unit": "per_1k_words", "tier": 2, "rate": 5.0, "range": [2.0, 9.0], "spread": 0.8,
     "description": "British spelling."},
    {"id": "lists/no-lists", "kind": "absence", "measurement": "counted",
     "stat": "list_items", "unit": "per_1k_words", "tier": 1, "rate": 0.0,
     "range": [0.0, 0.0], "spread": 1.0, "description": "A series is carried in prose."},
    {"id": "opener-closer/closer-punch", "kind": "presence", "measurement": "judged",
     "unit": "per_1k_words", "tier": 2, "rate": 1.0, "range": [0.0, 2.0], "spread": 0.6,
     "description": "Ends on a punch."},
])


def test_is_enumeration_separates_a_word_list_from_a_general_rule():
    named = {"id": "x/y", "regex": r"\b(?:behaviour|colour|organised)\b"}
    general = {"id": "x/z", "regex": r"(?:^|(?<=[.!?]\s))(?:And|But)\b"}
    assert textstats.is_enumeration(named)
    assert not textstats.is_enumeration(general)
    assert not textstats.is_enumeration({"id": "x/w", "stat": "em_dash"})


def test_structural_rows_are_the_shape_dimensions_only():
    assert textstats.is_structural({"id": "lists/no-lists"})
    assert textstats.is_structural({"id": "headings/colon-heading"})
    assert not textstats.is_structural({"id": "punctuation/em-dash"})


def test_report_table_fills_the_ai_evidence_column_and_marks_the_risky_rows(tmp_path, capsys):
    doc = tmp_path / "draft.md"
    doc.write_text("We shipped it — twice. " + "We measured the thing again here. " * 200
                   + "\n\n- one\n- two\n", encoding="utf-8")
    db = tmp_path / "user.json"
    db.write_text(json.dumps(REPORT_DB), encoding="utf-8")
    ai = tmp_path / "ai.json"
    ai.write_text(json.dumps({"kind": "ai", "patterns": [
        {"id": "punctuation/em-dash", "measurement": "counted", "stat": "em_dash",
         "unit": "per_1k_words", "tier": 1, "rate": 3.0, "range": [1.0, 6.0],
         "spread": 0.9, "description": "Machine em dashes."}]}), encoding="utf-8")
    assert textstats.main(["measure", str(doc), "--db", str(db), "--db", str(ai),
                           "--setting", "medium", "--report-table"]) == 0
    cap = capsys.readouterr()
    out, err = cap.out, cap.err
    # the author's own absence row is high-confidence by rule, and so is the AI-corroborated one
    assert "| punctuation/em-dash | remove | 2 | high |" in out
    # a presence row with no machine-side backing is a low-confidence removal
    assert "| voice-and-person/first-plural | remove | 2 | low |" in out
    # add rows carry no AI evidence at all
    assert "| spelling-lexical/british-spelling [enum] | add | 2 | — |" in out
    # the shape row is marked, and the judged pattern still gets its checklist line
    assert "lists/no-lists [structural]" in out
    assert "- opener-closer/closer-punch (tier 2)" in out
    assert "## Do-not-touch" in out and "## Left for the manual pass" in out
    # the guidance is on stderr, so a redirected table stays paste-ready
    assert "do not retype a figure" in err
    assert "[enum]" in err and "[structural]" in err
    assert "do not retype" not in out


def test_report_table_adds_a_rewritten_column_for_a_second_file(tmp_path, capsys):
    db = tmp_path / "user.json"
    db.write_text(json.dumps(REPORT_DB), encoding="utf-8")
    before = tmp_path / "a.md"
    before.write_text("We shipped it — twice. " + "We measured it again here. " * 200,
                      encoding="utf-8")
    after = tmp_path / "b.md"
    after.write_text("I shipped it, twice. " + "I measured it again here. " * 200,
                     encoding="utf-8")
    assert textstats.main(["measure", str(before), str(after), "--db", str(db),
                           "--report-table"]) == 0
    out = capsys.readouterr().out
    assert "| pattern | direction | tier | AI evidence | input | rewritten |" in out
    row = [ln for ln in out.splitlines() if ln.startswith("| punctuation/em-dash |")][0]
    assert row.split("|")[6].strip() == "0"      # the rewritten column, measured not recalled
    assert row.rstrip("| ").endswith("match")


# --- stripping fixes from the field report --------------------------------------

def test_stripper_drops_comments_block_html_bare_urls_and_decodes_entities():
    raw = ("<!-- Comment: publisher => namespace -->\n"
           "Use `foo` here &rarr; there, see https://example.com/a?b=c for details.\n\n"
           "<div class=\"note\">Editorial notice with many words</div>\n\n"
           "One &mdash; dash and one; semicolon.\n")
    r = textstats.measure(raw)
    prose = r["_doc"].prose
    assert "namespace" not in prose and "notice" not in prose and "example.com" not in prose
    assert "\u2192" in prose  # the entity is decoded, not counted as a word plus a semicolon
    assert r["stats"]["words"] == 11
    assert r["per_1k"]["semicolon"] == round(1 / 11 * 1000, 2)
    assert r["per_1k"]["em_dash"] == round(1 / 11 * 1000, 2)
    # inline code is a non-word placeholder: it adds no word and feeds no `\bcode\b` regex,
    # and a regex on the placeholder counts the author's code references
    assert textstats.CODE_PLACEHOLDER in prose and "code" not in prose
    assert textstats.count_pattern({"regex": "``"}, r) == 1


def test_first_person_singular_skips_the_i_of_io():
    assert hits("Reads from standard I/O and I/O streams.", "first_person_singular") == 0
    assert hits("I read it; give me the file.", "first_person_singular") == 2


def test_exclude_subtracts_overlapping_hits_from_regex_and_built_in_counters():
    text = "This is caused by the cache. This changes everything. That is the idea."
    r = textstats.measure(text)
    built_in = {"id": "reveal-frames/verdict-opener", "stat": "ai_verdict_opener", "unit": "per_1k_words"}
    assert textstats.count_pattern(built_in, r) == 3
    assert textstats.count_pattern(dict(built_in, exclude=r"This is caused"), r) == 2
    assert textstats.measure_pattern(dict(built_in, exclude=r"This is caused"), r) == round(2 / r["stats"]["words"] * 1000, 2)
    own = {"id": "paragraph-openers/demonstrative-subject", "regex": r"(?:^|(?<=[.!?] ))(?:This|That)\b", "unit": "per_1k_words"}
    assert textstats.count_pattern(own, r) == 3
    assert textstats.count_pattern(dict(own, exclude=r"This is caused"), r) == 2
    # an exclude that does not overlap the counter's own match subtracts nothing
    assert textstats.count_pattern(dict(own, exclude=r"cache"), r) == 3
    share = {"id": "x/y", "regex": r"\bThis\b", "unit": "share_of_sentences", "exclude": r"This is caused"}
    assert textstats.measure_pattern(share, r) == round(1 / 3, 3)


def test_count_pattern_gives_the_numerator_of_a_per_1k_statistic():
    r = textstats.measure("Intro.\n\n- one\n- two\n- three\n")
    assert textstats.count_pattern({"stat": "list_items_per_1k", "unit": "per_1k_words"}, r) == 3
    assert textstats.count_pattern({"stat": "sentence_len_median", "unit": "words"}, r) is None
    assert textstats.count_pattern({"id": "x/judged"}, r) is None


def test_hits_prints_counts_context_and_the_db_fields(tmp_path, capsys):
    doc = tmp_path / "d.md"
    doc.write_text("So I waited. So did the build. Even so, fine.", encoding="utf-8")
    assert textstats.main(["hits", str(doc), "-e", r"\bso\b", "-i", "-x", r"Even so"]) == 0
    out = capsys.readouterr().out
    assert "count=2 (1 excluded)  per_1k_words=" in out
    assert "\u00abSo\u00bb I waited" in out and "(excluded)" in out
    assert '"regex": "\\\\bso\\\\b", "ignore_case": true, "exclude": "Even so", "unit": "per_1k_words"' in out
    # several counters, or --matrix: one line per counter with the raw count per file
    assert textstats.main(["hits", str(doc), "-e", r"\bSo\b", "--stat", "em_dash"]) == 0
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if l.startswith(("\\bSo", "em_dash"))]
    assert lines[0].split()[-1] == "2" and lines[1].split()[-1] == "0"
    assert textstats.main(["hits", str(doc), "--stat", "sentence_len_median"]) == 0
    assert "sentence_len_median=" in capsys.readouterr().out
    assert textstats.main(["hits", str(doc), "--stat", "no_such"]) == 1
    assert textstats.main(["hits", str(doc)]) == 1


def test_vet_lists_the_document_that_stands_out(tmp_path, capsys):
    plain = "Plain prose sentence here. " * 30
    a, b, c = (tmp_path / n for n in ("a.md", "b.md", "c.md"))
    a.write_text(plain, encoding="utf-8")
    b.write_text(plain, encoding="utf-8")
    c.write_text("A dash \u2014 here, and honestly a real one. " * 30, encoding="utf-8")
    assert textstats.main(["measure", str(a), str(b), str(c), "--vet"]) == 0
    out = capsys.readouterr().out
    flagged = [l for l in out.splitlines() if "em_dash" in l]
    assert len(flagged) == 1 and str(c) in flagged[0] and "others: median 0" in flagged[0]
    assert not [l for l in out.splitlines() if str(a) in l]
    assert textstats.main(["measure", str(a), "--vet"]) == 0
    assert "at least two documents" in capsys.readouterr().out


SCOPED_DB = {"kind": "user", "patterns": [
    {"id": "opener-closer/sign-off", "regex": "Cheers", "unit": "per_1k_words", "rate": 10.0,
     "range": [6.0, 14.0], "spread": 1.0, "tier": 3, "register_scope": ["email"]},
    {"id": "punctuation/em-dash", "regex": "\u2014", "unit": "per_1k_words", "rate": 8.0,
     "range": [0.0, 12.0], "spread": 0.5, "tier": 3, "tier_override": 1},
    {"id": "tone-markers/warmth", "measurement": "judged", "unit": "per_1k_words", "rate": 1.0,
     "tier": 2, "description": "Warm.", "register_scope": ["email"]}]}
SCOPED_AI = {"kind": "ai", "patterns": [
    {"id": "punctuation/em-dash", "regex": "\u2014", "unit": "per_1k_words", "rate": 20.0,
     "range": [3.0, 60.0], "spread": 0.9, "tier": 1, "register_scope": ["email"]}]}
SCOPED_DOC = "A draft \u2014 with \u2014 dashes. " * 5 + "More words follow here. " * 40


def test_register_sets_scoped_rows_aside_and_shows_the_effective_tier(tmp_path, capsys):
    doc = tmp_path / "post.md"
    doc.write_text(SCOPED_DOC, encoding="utf-8")
    user, ai = tmp_path / "user.json", tmp_path / "ai.json"
    user.write_text(json.dumps(SCOPED_DB), encoding="utf-8")
    ai.write_text(json.dumps(SCOPED_AI), encoding="utf-8")
    # without --register the scope is shown and the reader judges
    assert textstats.main(["measure", str(doc), "--db", str(user), "--sort-gap"]) == 0
    out = capsys.readouterr().out
    assert [l for l in out.splitlines() if l.startswith("add") and "sign-off [scope: email]" in l]
    assert [l for l in out.splitlines() if "tone-markers/warmth [scope: email]" in l]
    # with it, an out-of-scope row is neutral and the override is the tier shown
    assert textstats.main(["measure", str(doc), "--db", str(user), "--sort-gap", "--register", "article"]) == 0
    out = capsys.readouterr().out
    row = [l for l in out.splitlines() if "sign-off [out of scope]" in l][0]
    assert row.startswith("neutral") and row.split()[1] == "0"
    dash = [l for l in out.splitlines() if "punctuation/em-dash" in l][0]
    assert dash.startswith("remove") and dash.split()[3] == "1"
    assert textstats.main(["measure", str(doc), "--db", str(user), "--register", "email", "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)[str(doc)]
    assert rows["patterns"]["opener-closer/sign-off"]["out_of_scope"] is False
    assert rows["patterns"]["opener-closer/sign-off"]["class"] == "add"
    assert rows["patterns"]["punctuation/em-dash"]["tier"] == 1
    assert rows["judged_patterns"]["tone-markers/warmth"]["out_of_scope"] is False
    assert textstats.main(["measure", str(doc), "--db", str(user), "--register", "article", "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)[str(doc)]["patterns"]["opener-closer/sign-off"]
    assert rows["out_of_scope"] is True and rows["class"] == "neutral" and rows["gap"] == 0.0


def test_report_table_lists_out_of_scope_rows_and_ignores_out_of_scope_ai_evidence(tmp_path, capsys):
    doc = tmp_path / "post.md"
    doc.write_text(SCOPED_DOC, encoding="utf-8")
    user, ai = tmp_path / "user.json", tmp_path / "ai.json"
    user.write_text(json.dumps(SCOPED_DB), encoding="utf-8")
    ai.write_text(json.dumps(SCOPED_AI), encoding="utf-8")
    assert textstats.main(["measure", str(doc), "--db", str(user), "--db", str(ai), "--report-table"]) == 0
    out = capsys.readouterr().out
    assert "| punctuation/em-dash | remove | 1 | high |" in out  # register unknown: the AI row counts
    assert textstats.main(["measure", str(doc), "--db", str(user), "--db", str(ai), "--report-table",
                           "--register", "article"]) == 0
    out = capsys.readouterr().out
    assert "| punctuation/em-dash | remove | 1 | low |" in out  # the email-scoped AI row is no evidence
    assert "- opener-closer/sign-off [out of scope] — scoped to email; the input is article" in out
    assert "- tone-markers/warmth [out of scope] (tier 2)" in out
