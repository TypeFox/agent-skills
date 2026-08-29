import copy
import json

import pytest

import styledb

DOCS = [
    {"id": "d1", "path": "d1.md", "words": 1000, "register": "article"},
    {"id": "d2", "path": "d2.md", "words": 1000, "register": "article"},
    {"id": "d3", "path": "d3.md", "words": 1000, "register": "email"},
    {"id": "d4", "path": "d4.md", "words": 1000, "register": "email"},
    {"id": "d5", "path": "d5.md", "words": 1000, "register": "docs"},
]


def pattern(pid, counts, kind="presence", measurement="counted", quotes=3, **extra):
    dim, marker = pid.split("/")
    p = {
        "id": pid, "dimension": dim, "marker": marker, "description": "desc",
        "kind": kind, "measurement": measurement, "unit": "per_1k_words",
        "documents": [{"id": d, "count": c} for d, c in counts.items()],
        "evidence": [{"doc": list(counts)[0], "quote": "q{}".format(i)} for i in range(quotes)],
        "tier": 3,
    }
    p.update(extra)
    return p


def make_db(patterns, docs=DOCS, **extra):
    db = {"db_version": styledb.CURRENT_DB_VERSION, "kind": "user", "partial": False,
          "created": "2026-08-28", "tool": "write-like-me",
          "corpus": {"documents": copy.deepcopy(docs), "total_words": 0},
          "review": {"status": "pending"}, "patterns": copy.deepcopy(patterns)}
    db.update(extra)
    return db


def test_stats_rate_is_corpus_normalized_per_1k():
    db = make_db([pattern("punctuation/colon", {"d1": 4, "d2": 0, "d3": 2, "d4": 2, "d5": 2})])
    styledb.recompute(db)
    p = db["patterns"][0]
    assert p["rate"] == 2.0
    assert p["spread"] == 0.8
    assert p["range"] == [0.0, 4.0]
    assert p["coverage"] == 1.0
    assert sorted(p["registers"]) == ["article", "docs", "email"]
    assert db["corpus"]["total_words"] == 5000


def test_tier_1_requires_full_coverage_spread_registers_counted_and_quotes():
    strong = pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})
    db = make_db([strong])
    styledb.recompute(db)
    assert db["patterns"][0]["tier"] == 1


@pytest.mark.parametrize("change,expected", [
    ({"measurement": "judged"}, 2),
    ({"evidence": [{"doc": "d1", "quote": "only one"}, {"doc": "d2", "quote": "two"}]}, 2),
    ({"documents": [{"id": "d1", "count": 4}, {"id": "d2", "count": 1}, {"id": "d3", "count": 2}]}, 2),
    ({"documents": [{"id": "d1", "count": 4}, {"id": "d2", "count": 1}]}, 2),
    ({"documents": [{"id": "d1", "count": 4}, {"id": "d2", "count": 0}]}, 3),
])
def test_tier_demotions(change, expected):
    p = pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})
    p.update(change)
    db = make_db([p])
    styledb.recompute(db)
    assert db["patterns"][0]["tier"] == expected, db["patterns"][0]["tier_reason"]


def test_single_register_pattern_is_at_most_tier_2():
    p = pattern("headings/question-headings", {"d1": 3, "d2": 3, "d3": 0, "d4": 0, "d5": 0})
    db = make_db([p])
    styledb.recompute(db)
    assert db["patterns"][0]["tier"] == 2
    assert "single register" in db["patterns"][0]["tier_reason"]


def test_absence_pattern_tiers():
    absent = pattern("punctuation/em-dash", {d["id"]: 0 for d in DOCS}, kind="absence", quotes=0)
    db = make_db([absent])
    styledb.recompute(db)
    assert db["patterns"][0]["tier"] == 1
    absent_half = pattern("punctuation/em-dash", {"d1": 0, "d2": 0, "d3": 0}, kind="absence", quotes=0)
    db = make_db([absent_half])
    styledb.recompute(db)
    assert db["patterns"][0]["tier"] == 2


def test_tier_override_wins_in_effective_tier():
    p = pattern("punctuation/colon", {"d1": 4}, quotes=1)
    p["tier"] = 3
    p["tier_override"] = 1
    assert styledb.effective_tier(p) == 1


def test_validate_catches_schema_errors():
    bad = pattern("punctuation/colon", {"d1": 1, "zz": 2}, quotes=0)
    bad["dimension"] = "nope"
    db = make_db([bad, pattern("lists/bogus", {"d1": 1})])
    db["patterns"][1]["id"] = "bogus"
    errors, _ = styledb.validate(db)
    joined = "\n".join(errors)
    assert "unknown document" in joined
    assert "need at least one verbatim evidence quote" in joined
    assert "dimension/marker fields must match" in joined
    assert "must look like dimension/marker" in joined


def test_validate_absence_must_be_counted_and_zero():
    p = pattern("punctuation/em-dash", {"d1": 0, "d2": 1}, kind="absence", measurement="judged", quotes=0)
    errors, _ = styledb.validate(make_db([p]))
    assert any("must be counted" in e for e in errors)
    assert any("count > 0" in e for e in errors)


def test_validate_verifies_quotes_against_corpus(tmp_path):
    (tmp_path / "d1.md").write_text("I write short sentences.\nLike this one.\n", encoding="utf-8")
    p = pattern("sentence-rhythm/short-sentences", {"d1": 2},
                quotes=0, evidence=[{"doc": "d1", "quote": "Like  this one."},
                                    {"doc": "d1", "quote": "not in the corpus"}])
    db = make_db([p], docs=DOCS[:1])
    errors, _ = styledb.validate(db, corpus_dir=str(tmp_path))
    assert len([e for e in errors if "not found verbatim" in e]) == 1
    assert "not in the corpus" in "\n".join(errors)


def test_validate_exempts_redacted_quotes_from_verbatim_check(tmp_path):
    (tmp_path / "d1.md").write_text("Sam needed the docs build, so I waited.\n", encoding="utf-8")
    p = pattern("connectives/so-initial", {"d1": 1}, quotes=0,
                evidence=[{"doc": "d1", "quote": "[colleague] needed the docs build, so I waited.", "redacted": True},
                          {"doc": "d1", "quote": "Someone needed the docs build, so I waited.", "redacted": True}])
    errors, warnings = styledb.validate(make_db([p], docs=DOCS[:1]), corpus_dir=str(tmp_path))
    assert not any("not found verbatim" in e for e in errors)
    assert len([w for w in warnings if "no [placeholder]" in w]) == 1


def test_validate_warns_on_small_corpus_and_stale_tier():
    p = pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})
    p["tier"] = 3
    _, warnings = styledb.validate(make_db([p]))
    joined = "\n".join(warnings)
    assert "guidance is >=8" in joined
    assert "computed tier 1" in joined


def test_merge_unions_documents_and_evidence_and_recomputes_tiers():
    part_a = make_db([pattern("punctuation/colon", {"d1": 4, "d2": 1}, quotes=2)], docs=DOCS[:2], partial=True)
    part_b = make_db([pattern("punctuation/colon", {"d3": 2, "d4": 2, "d5": 2}, quotes=2),
                      pattern("lists/no-bullets", {"d3": 0, "d4": 0, "d5": 0}, kind="absence", quotes=0)],
                     docs=DOCS[2:], partial=True)
    part_b["patterns"][0]["evidence"] = [{"doc": "d3", "quote": "x"}, {"doc": "d4", "quote": "y"}]
    part_b["patterns"][0]["note"] = "from b"
    merged = styledb.merge([part_a, part_b])
    assert merged["partial"] is False
    assert {d["id"] for d in merged["corpus"]["documents"]} == {"d1", "d2", "d3", "d4", "d5"}
    colon = next(p for p in merged["patterns"] if p["id"] == "punctuation/colon")
    assert len(colon["documents"]) == 5
    assert len(colon["evidence"]) == 4
    assert colon["tier"] == 1
    assert colon["note"] == "from b"
    absence = next(p for p in merged["patterns"] if p["id"] == "lists/no-bullets")
    assert absence["coverage"] == 0.6 and absence["tier"] == 2
    errors, _ = styledb.validate(merged)
    assert errors == []


def test_merge_rejects_conflicts():
    a = make_db([pattern("punctuation/colon", {"d1": 4})], docs=DOCS[:1])
    b = make_db([pattern("punctuation/colon", {"d1": 5})], docs=DOCS[:1])
    with pytest.raises(ValueError, match="conflicting counts"):
        styledb.merge([a, b])
    b = make_db([], docs=[dict(DOCS[0], words=999)])
    with pytest.raises(ValueError, match="conflicting word counts"):
        styledb.merge([a, b])
    b = make_db([], docs=DOCS[:1], db_version=styledb.CURRENT_DB_VERSION + 1)
    with pytest.raises(ValueError, match="different db_version"):
        styledb.merge([a, b])


def test_render_filters_by_setting():
    t1 = pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})
    t3 = pattern("imagery/kitchen-metaphors", {"d1": 1}, quotes=1)
    db = make_db([t1, t3])
    styledb.recompute(db)
    soft = styledb.render(db, "soft")
    hard = styledb.render(db, "hard")
    assert "colon" in soft and "kitchen-metaphors" not in soft
    assert "kitchen-metaphors" in hard


def test_info_exit_codes(tmp_path, capsys):
    db = make_db([])
    path = tmp_path / "db.json"
    for version, code in [(styledb.CURRENT_DB_VERSION, 0), (styledb.CURRENT_DB_VERSION - 1, 2),
                          (styledb.CURRENT_DB_VERSION + 1, 3)]:
        db["db_version"] = version
        path.write_text(json.dumps(db), encoding="utf-8")
        assert styledb.main(["info", str(path)]) == code
    out = capsys.readouterr().out
    assert "newer than skill" in out and "migrate" in out


def test_cli_validate_fix_and_merge_roundtrip(tmp_path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    out = tmp_path / "out.json"
    a.write_text(json.dumps(make_db([pattern("punctuation/colon", {"d1": 4, "d2": 1})], docs=DOCS[:2], partial=True)))
    b.write_text(json.dumps(make_db([pattern("punctuation/colon", {"d3": 2, "d4": 2, "d5": 2})], docs=DOCS[2:], partial=True)))
    assert styledb.main(["merge", str(a), str(b), "-o", str(out)]) == 0
    assert styledb.main(["validate", str(out), "--fix"]) == 0
    merged = json.loads(out.read_text())
    assert merged["patterns"][0]["tier"] == 1
    assert styledb.main(["tiers", str(out)]) == 0
    assert styledb.main(["render", str(out), "--setting", "soft"]) == 0
