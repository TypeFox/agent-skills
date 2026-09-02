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
    ({"documents": [{"id": "d1", "count": 4}, {"id": "d2", "count": 1}, {"id": "d3", "count": 0},
                    {"id": "d4", "count": 0}, {"id": "d5", "count": 0}]}, 2),
])
def test_tier_demotions(change, expected):
    p = pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})
    p.update(change)
    db = make_db([p])
    styledb.recompute(db)
    assert db["patterns"][0]["tier"] == expected, db["patterns"][0]["tier_reason"]


def test_low_spread_is_named_in_the_tier_reason():
    p = pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 0, "d4": 0, "d5": 0})
    db = make_db([p])
    styledb.recompute(db)
    assert db["patterns"][0]["tier"] == 2
    assert "under 60%" in db["patterns"][0]["tier_reason"]


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
    assert any("1 hit(s) in 1 document(s)" in e and "tolerates" in e for e in errors)


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


def test_displaces_lists_the_forms_the_author_never_uses():
    # The mirror of `instead`: an absence names the patterns that fill its slot, a presence
    # pattern names the family members it displaces, so a rewrite can substitute without
    # re-reading the corpus.
    a = make_db([pattern("connectives/example-introducer", {"d1": 4},
                         displaces=["for example"])], docs=DOCS[:1])
    b = make_db([pattern("connectives/example-introducer", {"d2": 2},
                         displaces=["for example", "e.g."])], docs=DOCS[1:2])
    merged = styledb.merge([a, b])
    assert merged["patterns"][0]["displaces"] == ["for example", "e.g."]
    assert styledb.validate(merged)[0] == []
    assert 'Never uses: "for example", "e.g."' in styledb.render(merged)
    broken = make_db([pattern("connectives/example-introducer", {"d1": 4}, displaces="for example")])
    assert any("'displaces' must be a list" in msg for msg in styledb.validate(broken)[0])
    misplaced = make_db([pattern("punctuation/em-dash", {"d1": 0}, kind="absence", quotes=0,
                                 displaces=["—"])])
    assert any("absences name their replacements in 'instead'" in msg
               for msg in styledb.validate(misplaced)[1])


def test_validate_checks_stat_names_and_units():
    ok = pattern("punctuation/em-dash", {"d1": 0, "d2": 0}, kind="absence", quotes=0, stat="em_dash")
    typo = pattern("punctuation/semicolon", {"d1": 1}, stat="semi_colon")
    unit = pattern("punctuation/colon-elaboration", {"d1": 1}, stat="colon", unit="share_of_sentences")
    median = pattern("sentence-rhythm/median-length", {"d1": 1}, stat="sentence_len_median", unit="words",
                     documents=[{"id": "d1", "rate": 12.0}])
    heads = pattern("headings/colon-heading", {"d1": 1}, stat="colon_heading_share", unit="share_of_headings",
                    documents=[{"id": "d1", "rate": 0.5}])
    errors, warnings = styledb.validate(make_db([ok, typo, unit, median, heads]))
    joined = "\n".join(errors)
    assert "em-dash" not in joined and "median-length" not in joined and "colon-heading" not in joined
    assert "unknown stat 'semi_colon'" in joined
    assert "unit must be per_1k_words" in joined
    assert not any("counted without regex or stat" in w for w in warnings)
    _, warnings = styledb.validate(make_db([pattern("punctuation/colon", {"d1": 1})]))
    assert any("counted without regex or stat" in w for w in warnings)


def test_merge_keeps_first_stat_and_notes_conflicts():
    a = make_db([pattern("punctuation/colon", {"d1": 4}, stat="colon", register_scope=["article"])], docs=DOCS[:1])
    b = make_db([pattern("punctuation/colon", {"d2": 2}, stat="semicolon", register_scope=["email"])], docs=DOCS[1:2])
    merged = styledb.merge([a, b])
    p = merged["patterns"][0]
    assert p["stat"] == "colon"
    assert "differing stat dropped: semicolon" in p["note"]
    assert p["register_scope"] == ["article"]
    assert "differing register_scope dropped: ['email']" in p["note"]


def test_register_scope_derives_the_tier_inside_the_register():
    # Spread is corpus-wide, so a habit near-obligatory in one register (a sign-off, the
    # meta-signposts of a talk abstract) never leaves tier 3 unless the scope says which
    # documents it is derived over.
    docs = DOCS[:2] + [{"id": "e{}".format(i), "path": "e{}.md".format(i), "words": 1000, "register": "email"}
                       for i in range(1, 4)]
    counts = {"d1": 0, "d2": 0, "e1": 5, "e2": 5, "e3": 5}
    unscoped = pattern("opener-closer/sign-off", counts)
    scoped = pattern("opener-closer/sign-off", counts, register_scope=["email"])
    db = make_db([unscoped, scoped], docs=docs)
    styledb.recompute(db)
    wide, narrow = db["patterns"]
    assert wide["tier"] == 2 and "single register" in wide["tier_reason"]
    assert wide["spread"] == 0.6 and wide["rate"] == 3.0
    assert narrow["tier"] == 1, narrow["tier_reason"]
    assert narrow["spread"] == 1.0 and narrow["coverage"] == 1.0 and narrow["rate"] == 5.0
    assert narrow["registers"] == ["email"]
    assert "scope: email" in styledb.render(db)
    # the field is checked: a list of registers the corpus actually has
    db["patterns"][1]["register_scope"] = "email"
    assert any("must be a list of registers" in e for e in styledb.validate(db)[0])
    db["patterns"][1]["register_scope"] = ["thesis"]
    assert any("no corpus document has" in w for w in styledb.validate(db)[1])


# --- register weighting -------------------------------------------------------

LOPSIDED = [
    {"id": "a1", "path": "a1.md", "words": 4000, "register": "article"},
    {"id": "e1", "path": "e1.md", "words": 500, "register": "email"},
]


def weighted(db, weights):
    db["corpus"]["register_weights"] = weights
    styledb.recompute(db)
    return db["patterns"][0]


def test_equal_register_shares_give_a_small_register_the_same_pull_as_a_large_one():
    # 4,000 words of articles next to 500 words of email: pooled by words the articles
    # define the rate, which is what makes an unbalanced corpus a profile of its biggest
    # register. Equal shares are the answer to "weight my registers equally".
    counts = {"a1": 4, "e1": 5}  # 1.0 per 1k in articles, 10.0 in email
    plain = make_db([pattern("punctuation/colon", counts)], docs=LOPSIDED)
    styledb.recompute(plain)
    assert plain["patterns"][0]["rate"] == 2.0

    p = weighted(make_db([pattern("punctuation/colon", counts)], docs=LOPSIDED),
                 {"article": 1, "email": 1})
    assert p["rate"] == 5.5


def test_shares_proportional_to_words_reproduce_the_unweighted_rate():
    p = weighted(make_db([pattern("punctuation/colon", {"a1": 4, "e1": 5})], docs=LOPSIDED),
                 {"article": 4000, "email": 500})
    assert p["rate"] == 2.0


def test_weighting_moves_the_rate_and_leaves_the_evidence_alone():
    # A weight says how much a register should define the target rate, never how well the
    # habit is evidenced: spread, range, coverage and the tier count documents either way.
    counts = {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2}
    plain = make_db([pattern("punctuation/colon", counts)])
    styledb.recompute(plain)
    before = plain["patterns"][0]
    assert (before["rate"], before["tier"]) == (2.2, 1)

    after = weighted(make_db([pattern("punctuation/colon", counts)]),
                     {"article": 1, "email": 1, "docs": 1})
    assert after["rate"] == 2.167
    assert after["tier"] == 1
    for field in ("spread", "range", "coverage", "registers"):
        assert after[field] == before[field]


def test_weighting_is_a_no_op_inside_a_register_scoped_pattern():
    docs = [{"id": "e1", "path": "e1.md", "words": 500, "register": "email"},
            {"id": "e2", "path": "e2.md", "words": 1500, "register": "email"},
            {"id": "a1", "path": "a1.md", "words": 4000, "register": "article"}]
    scoped = pattern("opener-closer/sign-off", {"e1": 5, "e2": 3}, register_scope=["email"])
    p = weighted(make_db([scoped], docs=docs), {"article": 1, "email": 1})
    assert p["rate"] == 4.0  # the word-weighted mean of the two email documents


def test_validate_requires_the_weighting_to_name_every_register():
    db = make_db([pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})])
    db["corpus"]["register_weights"] = {"article": 1, "email": 1}
    errors, _ = styledb.validate(db)
    assert [e for e in errors if "does not name register 'docs'" in e]


def test_validate_checks_the_shares_and_flags_a_register_no_document_carries():
    db = make_db([pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})])
    db["corpus"]["register_weights"] = {"article": 1, "email": 0, "docs": 1, "thesis": 2}
    errors, warnings = styledb.validate(db)
    assert [e for e in errors if "register_weights['email'] must be a positive number" in e]
    assert [w for w in warnings if "names register 'thesis'" in w]
    db["corpus"]["register_weights"] = []
    assert [e for e in styledb.validate(db)[0] if "must be a non-empty object" in e]


def test_a_partial_db_is_told_to_leave_the_weighting_to_the_merge():
    db = make_db([pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})],
                 partial=True)
    db["corpus"]["register_weights"] = {"article": 1, "email": 1, "docs": 1}
    assert [w for w in styledb.validate(db)[1] if "whole-corpus decision" in w]


def test_merge_unions_the_weighting_and_refuses_a_conflict():
    a = make_db([pattern("punctuation/colon", {"d1": 4})], docs=DOCS[:1])
    a["corpus"]["register_weights"] = {"article": 1}
    b = make_db([pattern("punctuation/colon", {"d3": 2})], docs=DOCS[2:3])
    b["corpus"]["register_weights"] = {"email": 1}
    assert styledb.merge([a, b])["corpus"]["register_weights"] == {"article": 1, "email": 1}

    b["corpus"]["register_weights"] = {"article": 3}
    with pytest.raises(ValueError, match="conflicting weights"):
        styledb.merge([a, b])


def test_render_and_info_say_that_the_rates_are_weighted(tmp_path, capsys):
    db = make_db([pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})])
    db["corpus"]["register_weights"] = {"article": 1, "email": 1, "docs": 1}
    styledb.recompute(db)
    assert "register-weighted (article 1, docs 1, email 1)" in styledb.render(db)

    path = tmp_path / "db.json"
    path.write_text(json.dumps(db), encoding="utf-8")
    assert styledb.main(["info", str(path)]) == 0
    assert "register_weights: {'article': 1, 'email': 1, 'docs': 1}" in capsys.readouterr().out


def test_validate_warns_when_an_ai_corpus_document_names_no_generator():
    db = make_db([pattern("punctuation/colon", {"d1": 4})], docs=DOCS[:2], kind="ai")
    db["corpus"]["documents"][0]["generator"] = "GPT-5"
    errors, warnings = styledb.validate(db)
    assert not errors
    assert [w for w in warnings if "no generator" in w and "d2" in w] and not any("d1" in w for w in warnings)


def test_validate_names_the_nearest_verbatim_form_for_a_retyped_quote(tmp_path):
    (tmp_path / "d1.md").write_text("He said it\u2019s **done** \u2014 really. Then nothing.\n", encoding="utf-8")
    p = pattern("punctuation/em-dash", {"d1": 1}, quotes=0,
                evidence=[{"doc": "d1", "quote": "he said it's done - really."},
                          {"doc": "d1", "quote": "never written"}])
    errors, _ = styledb.validate(make_db([p], docs=DOCS[:1]), corpus_dir=str(tmp_path))
    misses = [e for e in errors if "not found verbatim" in e]
    assert len(misses) == 2
    assert "nearest verbatim form: 'He said it\u2019s **done** \u2014 really.'" in misses[0]
    assert "nearest" not in misses[1]


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


def reviewed_db(patterns, **extra):
    db = make_db(patterns, **extra)
    db["review"] = {"status": "reviewed", "date": "2026-08-31", "reviewer": "the author"}
    return db


def test_seal_drops_paths_stamps_the_date_and_keeps_everything_processing_reads():
    db = reviewed_db([pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})])
    styledb.recompute(db)
    before = copy.deepcopy(db["patterns"])
    assert styledb.seal(db, date="2026-08-31") == 5
    assert db["corpus"]["sealed"] == "2026-08-31"
    assert not any("path" in d for d in db["corpus"]["documents"])
    assert all(d["words"] and d["register"] and d["id"] for d in db["corpus"]["documents"])
    assert db["patterns"] == before
    errors, _ = styledb.validate(db)
    assert not errors


def test_seal_is_idempotent():
    db = reviewed_db([pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})])
    styledb.seal(db, date="2026-08-31")
    assert styledb.seal(db, date="2026-09-01") == 0
    assert db["corpus"]["sealed"] == "2026-09-01"


@pytest.mark.parametrize("change,message", [
    ({"review": {"status": "pending"}}, "review round comes first"),
    ({"partial": True}, "merge the parts"),
])
def test_seal_refuses_before_the_review_round_and_on_partials(change, message):
    db = reviewed_db([pattern("punctuation/colon", {"d1": 4})])
    db.update(change)
    with pytest.raises(ValueError, match=message):
        styledb.seal(db)
    assert db["corpus"]["documents"][0]["path"] == "d1.md"


def test_validate_warns_when_corpus_dir_cannot_verify_a_sealed_db(tmp_path):
    p = pattern("punctuation/colon", {"d1": 4}, quotes=1)
    db = reviewed_db([p], docs=DOCS[:1])
    styledb.seal(db, date="2026-08-31")
    errors, warnings = styledb.validate(db, corpus_dir=str(tmp_path))
    assert not errors
    assert [w for w in warnings if "NOT verified" in w and "sealed 2026-08-31" in w]


def test_validate_rejects_a_sealed_db_that_still_carries_paths():
    db = reviewed_db([pattern("punctuation/colon", {"d1": 4})], docs=DOCS[:1])
    db["corpus"]["sealed"] = "2026-08-31"
    errors, _ = styledb.validate(db)
    assert [e for e in errors if "marked sealed" in e and "d1" in e]


def test_merge_seals_the_result_only_when_every_part_is_sealed():
    a = reviewed_db([pattern("punctuation/colon", {"d1": 4, "d2": 1}, quotes=2)], docs=DOCS[:2], partial=True)
    b = reviewed_db([pattern("punctuation/colon", {"d3": 2}, quotes=2)], docs=DOCS[2:3], partial=True)
    a["corpus"]["sealed"] = "2026-08-30"
    mixed = styledb.merge([copy.deepcopy(a), copy.deepcopy(b)])
    assert "sealed" not in mixed["corpus"]
    b["corpus"]["sealed"] = "2026-08-31"
    for doc in b["corpus"]["documents"]:
        doc.pop("path", None)
    for doc in a["corpus"]["documents"]:
        doc.pop("path", None)
    both = styledb.merge([a, b])
    assert both["corpus"]["sealed"] == "2026-08-31"
    assert not styledb.validate(both)[0]


def test_cli_seal_writes_to_output_and_leaves_the_input_alone(tmp_path):
    src = tmp_path / "db.json"
    out = tmp_path / "sealed.json"
    db = reviewed_db([pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})])
    styledb.recompute(db)
    src.write_text(json.dumps(db), encoding="utf-8")
    assert styledb.main(["seal", str(src), "-o", str(out)]) == 0
    assert "path" in json.loads(src.read_text())["corpus"]["documents"][0]
    sealed = json.loads(out.read_text())
    assert "path" not in sealed["corpus"]["documents"][0]
    assert sealed["corpus"]["sealed"]
    assert styledb.main(["seal", str(src)]) == 0
    assert "path" not in json.loads(src.read_text())["corpus"]["documents"][0]


def test_cli_seal_refuses_an_unreviewed_db(tmp_path, capsys):
    path = tmp_path / "db.json"
    path.write_text(json.dumps(make_db([pattern("punctuation/colon", {"d1": 4})], docs=DOCS[:1])),
                    encoding="utf-8")
    assert styledb.main(["seal", str(path)]) == 1
    assert "review round comes first" in capsys.readouterr().out
    assert "path" in json.loads(path.read_text())["corpus"]["documents"][0]


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


def test_dimensions_match_taxonomy():
    import pathlib
    import re
    taxonomy = pathlib.Path(__file__).resolve().parent.parent / "references" / "taxonomy.md"
    headings = re.findall(r"^### ([a-z-]+)\s*$", taxonomy.read_text(encoding="utf-8"), re.M)
    assert headings == styledb.DIMENSIONS


def corpus_db(tmp_path, patterns, text="So I waited: it worked (twice). So did the build.\n"):
    (tmp_path / "d1.md").write_text(text, encoding="utf-8")
    docs = [{"id": "d1", "path": "d1.md", "words": 10, "register": "article"}]
    return make_db(patterns, docs=docs)


def test_validate_recounts_counted_patterns_against_the_corpus(tmp_path):
    # `validate` computes rate, range and tier from documents[].count. Nothing re-derived
    # the counts themselves, so a DB of plausible invented numbers passed every check.
    p = pattern("connectives/so-initial", {"d1": 7}, quotes=1,
                evidence=[{"doc": "d1", "quote": "So I waited"}],
                regex=r"(?:^|(?<=[.!?]\s))So\b")
    errors, _ = styledb.validate(corpus_db(tmp_path, [p]), corpus_dir=str(tmp_path))
    assert [e for e in errors if "records 7 occurrences but the counter finds 2" in e]

    p["documents"][0]["count"] = 2
    assert not styledb.validate(corpus_db(tmp_path, [p]), corpus_dir=str(tmp_path))[0]


def test_recount_skips_what_no_counter_can_reproduce(tmp_path):
    judged = pattern("tone-markers/self-deprecation", {"d1": 4}, measurement="judged",
                     quotes=1, evidence=[{"doc": "d1", "quote": "So I waited"}])
    uncounted = pattern("imagery/gambling", {"d1": 9}, quotes=1,
                        evidence=[{"doc": "d1", "quote": "So I waited"}])
    errors, warnings = styledb.validate(corpus_db(tmp_path, [judged, uncounted]),
                                        corpus_dir=str(tmp_path))
    assert not errors
    assert [w for w in warnings if "counted without regex or stat" in w]


def test_validate_errors_once_per_unreachable_corpus_document(tmp_path):
    # Pointing --corpus-dir one level off used to warn per quote and still exit 0, so a DB
    # of fabricated quotes passed exactly as cleanly as a verified one.
    p = pattern("connectives/so-initial", {"d1": 2}, quotes=1,
                evidence=[{"doc": "d1", "quote": "So I waited"},
                          {"doc": "d1", "quote": "So did the build."}],
                regex=r"(?:^|(?<=[.!?]\s))So\b")
    db = corpus_db(tmp_path, [p])
    errors, _ = styledb.validate(db, corpus_dir=str(tmp_path / "nowhere"))
    assert len(errors) == 1
    assert "cannot open" in errors[0] and "documents[].path" in errors[0]


# --- near-absence -------------------------------------------------------------

BIG = [{"id": "b{}".format(i), "path": "b{}.md".format(i), "words": 2000,
        "register": "article" if i % 2 else "email"} for i in range(12)]


def near_absence(hits_in):
    counts = {d["id"]: (1 if d["id"] in hits_in else 0) for d in BIG}
    return pattern("punctuation/em-dash", counts, kind="absence", quotes=0, stat="em_dash")


def test_a_few_residual_hits_keep_an_absence_an_absence_at_tier_2():
    # Six em dashes in 100k words are the most important do-not-introduce row there is; recorded
    # as a presence they computed to tier 3 and the default setting ignored them.
    db = make_db([near_absence({"b1", "b2"})], docs=BIG)  # 2 hits in 24,000 words: 0.08 per 1k
    styledb.recompute(db)
    p = db["patterns"][0]
    assert p["tier"] == 2 and p["tier_reason"].startswith("near-absent: 2 hit(s) in 2 of 12 documents")
    assert "tier_override 1" in p["tier_reason"]
    errors, warnings = styledb.validate(db)
    assert not errors
    assert [w for w in warnings if "near-absent" in w and "note" in w]
    p["note"] = "both hits are quoted third-party text"
    assert not [w for w in styledb.validate(db)[1] if "near-absent" in w]
    assert "near-absent (2 hit(s) in 2 of 12 documents)" in styledb.render(db)
    # the review round moves it: always remove, or only on hard
    p["tier_override"] = 1
    assert styledb.effective_tier(p) == 1
    p["tier_override"] = 3
    assert styledb.effective_tier(p) == 3


def test_hits_above_the_tolerance_are_still_a_presence():
    db = make_db([near_absence({"b1", "b2", "b3"})], docs=BIG)  # 0.125 per 1k, 3 of 12 documents
    errors, _ = styledb.validate(db)
    assert [e for e in errors if "3 hit(s) in 3 document(s) (0.12 per 1k)" in e and "tolerates fewer than 0.1" in e]
    styledb.recompute(db)
    assert db["patterns"][0]["tier"] == 3
    # an exact zero is still tier 1 over a corpus this size
    db = make_db([near_absence(set())], docs=BIG)
    styledb.recompute(db)
    assert db["patterns"][0]["tier"] == 1


def test_a_near_absence_needs_the_per_1k_unit():
    p = pattern("lists/no-lists", {"b0": 1}, kind="absence", quotes=0, stat="list_items", unit="count",
                documents=[{"id": d["id"], "rate": 1.0 if d["id"] == "b0" else 0.0,
                            "count": 1 if d["id"] == "b0" else 0} for d in BIG])
    errors, _ = styledb.validate(make_db([p], docs=BIG))
    assert [e for e in errors if "tolerates" in e]


# --- validator checks from the field report -----------------------------------

def test_exclude_needs_a_counter_and_a_valid_regex():
    ok = pattern("reveal-frames/verdict-opener", {"d1": 1}, stat="ai_verdict_opener", exclude=r"This is caused")
    own = pattern("connectives/so-initial", {"d1": 1}, regex=r"^So\b", exclude=r"So what")
    bad = pattern("punctuation/colon", {"d1": 1}, regex=":", exclude="(")
    judged = pattern("tone-markers/bluntness", {"d1": 1}, measurement="judged", exclude="x")
    statistic = pattern("sentence-rhythm/median-length", {"d1": 1}, stat="sentence_len_median", unit="words",
                        documents=[{"id": "d1", "rate": 12.0}], exclude="x")
    errors, _ = styledb.validate(make_db([ok, own, bad, judged, statistic]))
    joined = "\n".join(errors)
    assert "verdict-opener" not in joined and "so-initial" not in joined
    assert "punctuation/colon: invalid exclude regex" in joined
    assert "tone-markers/bluntness: exclude subtracts" in joined
    assert "median-length: exclude subtracts" in joined


def test_a_statistic_must_be_filed_under_its_own_unit():
    # A per-1k statistic under `count` holding the per-1k value validated and was wrong.
    wrong = pattern("lists/bullet-density", {"d1": 1}, stat="list_items_per_1k", unit="count",
                    documents=[{"id": "d1", "rate": 4.2}])
    right = pattern("lists/bullet-density", {"d1": 4}, stat="list_items_per_1k", unit="per_1k_words")
    errors, _ = styledb.validate(make_db([wrong]))
    assert [e for e in errors if "'list_items_per_1k' is measured in unit 'per_1k_words', not 'count'" in e]
    assert not styledb.validate(make_db([right]))[0]


def test_documents_entries_carry_the_units_own_field():
    no_count = pattern("punctuation/colon", {"d1": 1}, documents=[{"id": "d1", "rate": 2.0}])
    no_rate = pattern("sentence-rhythm/short-punch", {"d1": 1}, stat="short_sentence_share",
                      unit="share_of_sentences", documents=[{"id": "d1", "count": 3}])
    errors, _ = styledb.validate(make_db([no_count, no_rate]))
    assert [e for e in errors if "punctuation/colon: documents[d1] needs an integer count" in e]
    assert [e for e in errors if "short-punch: documents[d1] needs a numeric rate" in e]


def test_review_fields_are_checked():
    p = pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})
    db = make_db([p])
    db["review"] = {"status": "reviewed"}
    errors, warnings = styledb.validate(db)
    assert [e for e in errors if "review.date is required" in e] and [e for e in errors if "review.reviewer is required" in e]
    assert [w for w in warnings if "carry no review.verdict" in w and "punctuation/colon" in w]
    db["review"] = {"status": "reviewed", "date": "2026-09-02", "reviewer": "the author"}
    db["patterns"][0]["review"] = {"verdict": "WRONG", "note": ""}
    assert [e for e in styledb.validate(db)[0] if "review.verdict 'WRONG' is not one of" in e]
    db["patterns"][0]["review"] = {"verdict": "nuanced", "note": "emails only"}
    errors, warnings = styledb.validate(db)
    assert not errors and not [w for w in warnings if "no review.verdict" in w]


def test_partial_and_pending_vetting_are_said_out_loud():
    p = pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})
    assert [w for w in styledb.validate(make_db([p], partial=True))[1] if "tiers are provisional" in w]
    docs = copy.deepcopy(DOCS)
    docs[0]["vetting"] = "pending"
    assert [w for w in styledb.validate(make_db([p], docs=docs))[1] if "vetting: pending" in w and "d1" in w]


def test_validate_fix_says_what_it_moved(tmp_path, capsys):
    p = pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})
    p["tier"], p["rate"] = 3, 9.9
    path = tmp_path / "db.json"
    path.write_text(json.dumps(make_db([p])), encoding="utf-8")
    assert styledb.main(["validate", str(path), "--fix"]) == 0
    out = capsys.readouterr().out
    assert "tier changed for 1 pattern(s):" in out and "punctuation/colon: 3 -> 1" in out
    assert "rate moved for 1 of 1 pattern(s); largest: punctuation/colon 9.9 -> 2.2" in out


# --- init / count / review ------------------------------------------------------

def write_corpus(root):
    (root / "posts").mkdir()
    (root / "posts" / "one.md").write_text("So I waited: it worked (twice). So did the build.\n", encoding="utf-8")
    (root / "posts" / "two.md").write_text("Plain prose here. Nothing else.\n", encoding="utf-8")
    (root / "mail.txt").write_text("So, thanks. Cheers, Jo\n", encoding="utf-8")


def test_init_builds_the_manifest_with_textstats_word_counts(tmp_path, capsys):
    write_corpus(tmp_path)
    out = tmp_path / "db.json"
    assert styledb.main(["init", str(out), "--corpus-dir", str(tmp_path), "article=posts", "email=mail.txt"]) == 0
    db = json.loads(out.read_text())
    docs = {d["id"]: d for d in db["corpus"]["documents"]}
    assert set(docs) == {"one", "two", "mail"}
    assert docs["one"] == {"id": "one", "path": "posts/one.md", "words": 10, "register": "article",
                           "sole_authored": True, "vetting": "pending"}
    assert docs["mail"]["register"] == "email" and db["corpus"]["total_words"] == 10 + 5 + 4
    assert db["patterns"] == [] and db["review"] == {"status": "pending"} and db["partial"] is False
    printed = capsys.readouterr().out
    assert "article" in printed and "email is a single file" in printed
    assert "article carries 79% of the words" in printed
    assert not styledb.validate(db)[0]
    assert styledb.main(["init", str(out), "--corpus-dir", str(tmp_path), "article=nowhere"]) == 1


def test_init_disambiguates_colliding_file_stems(tmp_path):
    (tmp_path / "a").mkdir(); (tmp_path / "b").mkdir()
    (tmp_path / "a" / "notes.md").write_text("One.\n", encoding="utf-8")
    (tmp_path / "b" / "notes.md").write_text("Two.\n", encoding="utf-8")
    docs = styledb.build_manifest(str(tmp_path), ["note=a", "note=b"])
    assert [d["id"] for d in docs] == ["a-notes", "b-notes"]


def test_count_writes_documents_from_the_corpus_and_hands_judged_rows_to_readers(tmp_path, capsys):
    write_corpus(tmp_path)
    docs = styledb.build_manifest(str(tmp_path), ["article=posts", "email=mail.txt"])
    so = pattern("connectives/so-initial", {"one": 99}, regex=r"(?:^|(?<=[.!?]\s))So\b", quotes=1,
                 evidence=[{"doc": "one", "quote": "So I waited"}])
    share = pattern("sentence-rhythm/short-punch", {"one": 1}, stat="short_sentence_share",
                    unit="share_of_sentences", documents=[{"id": "one", "rate": 0.9}], quotes=1,
                    evidence=[{"doc": "one", "quote": "So I waited"}])
    judged = pattern("tone-markers/bluntness", {"one": 2}, measurement="judged", quotes=1,
                     evidence=[{"doc": "one", "quote": "So I waited"}])
    db = make_db([so, share, judged], docs=docs)
    db["corpus"]["documents"][0]["words"] = 999  # stale: the stripper counts 10
    src, part = tmp_path / "cand.json", tmp_path / "judged.json"
    src.write_text(json.dumps(db), encoding="utf-8")
    assert styledb.main(["count", str(src), "--corpus-dir", str(tmp_path), "--judged", str(part)]) == 0
    printed = capsys.readouterr().out
    assert "counted 2 pattern(s) over 3 document(s)" in printed and "tone-markers/bluntness" in printed
    assert "word counts refreshed for 1 document(s)" in printed and "one" in printed
    counted = json.loads(src.read_text())
    assert counted["corpus"]["documents"][0]["words"] == 10 and counted["corpus"]["total_words"] == 19
    assert "_words_refreshed" not in counted
    by_id = {p["id"]: p for p in counted["patterns"]}
    assert set(by_id) == {"connectives/so-initial", "sentence-rhythm/short-punch"}
    assert by_id["connectives/so-initial"]["documents"] == [
        {"id": "one", "count": 2}, {"id": "two", "count": 0}, {"id": "mail", "count": 1}]
    assert [e["id"] for e in by_id["sentence-rhythm/short-punch"]["documents"]] == ["one", "two", "mail"]
    assert all("rate" in e for e in by_id["sentence-rhythm/short-punch"]["documents"])
    assert by_id["connectives/so-initial"]["rate"] == round(3 / 19 * 1000, 3)  # derived from the real counts
    assert by_id["connectives/so-initial"]["spread"] == 0.667
    # the counted DB verifies by construction, and the skeleton is what the readers fill in
    assert not styledb.validate(counted, corpus_dir=str(tmp_path))[0]
    skeleton = json.loads(part.read_text())
    assert skeleton["partial"] is True and [p["id"] for p in skeleton["patterns"]] == ["tone-markers/bluntness"]
    assert skeleton["patterns"][0]["documents"] == [] and skeleton["patterns"][0]["evidence"]
    skeleton["patterns"][0]["documents"] = [{"id": d["id"], "count": 1} for d in docs]
    merged = styledb.merge([counted, skeleton])
    assert len(merged["patterns"]) == 3 and not styledb.validate(merged, corpus_dir=str(tmp_path))[0]


def test_count_refuses_a_sealed_or_unreachable_corpus(tmp_path, capsys):
    write_corpus(tmp_path)
    docs = styledb.build_manifest(str(tmp_path), ["article=posts"])
    db = make_db([pattern("punctuation/colon", {"one": 1}, regex=":")], docs=docs)
    src = tmp_path / "db.json"
    src.write_text(json.dumps(db), encoding="utf-8")
    assert styledb.main(["count", str(src), "--corpus-dir", str(tmp_path / "nowhere")]) == 1
    assert "cannot open" in capsys.readouterr().out


def test_review_applies_verdicts_weights_and_the_reviewed_stamp(tmp_path, capsys):
    keep = pattern("punctuation/colon", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})
    soften = pattern("connectives/so-initial", {"d1": 4, "d2": 1, "d3": 2, "d4": 2, "d5": 2})
    drop = pattern("imagery/kitchen-metaphors", {"d1": 1}, quotes=1)
    db = make_db([keep, soften, drop])
    styledb.recompute(db)
    src = tmp_path / "db.json"
    src.write_text(json.dumps(db), encoding="utf-8")
    verdicts = tmp_path / "verdicts.json"
    verdicts.write_text(json.dumps({
        "connectives/so-initial": {"verdict": "overstated", "note": "less than that", "tier_override": 2},
        "imagery/kitchen-metaphors": {"verdict": "wrong"}}), encoding="utf-8")
    assert styledb.main(["review", str(src), "--verdicts", str(verdicts), "--weight", "article=1",
                         "--weight", "email=1", "--weight", "docs=1", "--reviewer", "Jo",
                         "--date", "2026-09-02"]) == 0
    printed = capsys.readouterr().out
    assert "imagery/kitchen-metaphors: wrong, removed" in printed
    assert "connectives/so-initial: overstated; tier_override 2" in printed
    assert "1 pattern(s) without a verdict confirmed by default" in printed
    assert "connectives/so-initial: 1 -> 2" in printed  # the override, seen as a tier change
    assert "rate moved for" in printed  # the weighting moved the rates
    out = json.loads(src.read_text())
    assert out["review"] == {"status": "reviewed", "date": "2026-09-02", "reviewer": "Jo"}
    assert [p["id"] for p in out["patterns"]] == ["punctuation/colon", "connectives/so-initial"]
    assert out["patterns"][0]["review"] == {"verdict": "confirmed", "note": ""}
    assert out["patterns"][1]["review"] == {"verdict": "overstated", "note": "less than that"}
    assert out["patterns"][1]["tier_override"] == 2
    assert out["corpus"]["register_weights"] == {"article": 1.0, "email": 1.0, "docs": 1.0}
    assert not styledb.validate(out)[0]
    assert styledb.seal(out) == 5  # a reviewed DB seals


def test_review_refuses_unknown_ids_bad_verdicts_and_partials(tmp_path, capsys):
    db = make_db([pattern("punctuation/colon", {"d1": 4})])
    src = tmp_path / "db.json"
    src.write_text(json.dumps(db), encoding="utf-8")
    verdicts = tmp_path / "v.json"
    verdicts.write_text(json.dumps({"punctuation/nope": {"verdict": "confirmed"}}), encoding="utf-8")
    assert styledb.main(["review", str(src), "--verdicts", str(verdicts)]) == 1
    verdicts.write_text(json.dumps({"punctuation/colon": {"verdict": "meh"}}), encoding="utf-8")
    assert styledb.main(["review", str(src), "--verdicts", str(verdicts)]) == 1
    src.write_text(json.dumps(make_db([], partial=True)), encoding="utf-8")
    assert styledb.main(["review", str(src)]) == 1
    assert "merge the parts first" in capsys.readouterr().out
