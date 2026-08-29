import structure_check as sc

ORIGINAL = """# Title

Intro paragraph with 3 numbers, `readFile()`, and a [link](https://example.com/x).

Second paragraph.

## Steps

1. first
2. second
3. third

```sh
make test
```

> A quoted line.

| a | b |
|---|---|
| 1 | 2 |

## Closing

Final words, 42 of them.
"""


def test_identical_documents_pass():
    errors, warnings = sc.compare(ORIGINAL, ORIGINAL)
    assert errors == [] and warnings == []


def test_reworded_prose_passes():
    rewritten = ORIGINAL.replace("Intro paragraph with 3 numbers", "An intro. It has 3 numbers") \
                        .replace("Final words, 42 of them.", "Forty-two words, 42, and done.")
    errors, warnings = sc.compare(ORIGINAL, rewritten)
    assert errors == [], errors


def test_merged_paragraph_is_a_warning_only():
    rewritten = ORIGINAL.replace("Second paragraph.\n\n", "").replace(
        "https://example.com/x).", "https://example.com/x). Second paragraph.")
    errors, warnings = sc.compare(ORIGINAL, rewritten)
    assert errors == []
    assert any("paragraph count 2 -> 1" in w for w in warnings)


def test_dropped_list_item_and_changed_code_are_errors():
    rewritten = ORIGINAL.replace("3. third\n", "").replace("make test", "make check")
    errors, _ = sc.compare(ORIGINAL, rewritten)
    assert any("list item count 3 -> 2" in e for e in errors)
    assert any("code block text changed" in e for e in errors)


def test_outline_and_block_sequence_changes_are_errors():
    errors, _ = sc.compare(ORIGINAL, ORIGINAL.replace("## Closing", "### Closing"))
    assert any("heading outline changed" in e for e in errors)
    errors, _ = sc.compare(ORIGINAL, ORIGINAL.replace("> A quoted line.\n\n", ""))
    assert any("block sequence changed" in e for e in errors)
    _, warnings = sc.compare(ORIGINAL, ORIGINAL.replace("## Closing", "## Wrap-up"))
    assert any("heading text changed" in w for w in warnings)


def test_quote_link_and_number_invariants():
    rewritten = ORIGINAL.replace("A quoted line.", "A changed quote.") \
                        .replace("https://example.com/x", "https://example.com/y") \
                        .replace("42 of them", "many of them, say 43")
    errors, warnings = sc.compare(ORIGINAL, rewritten)
    joined = "\n".join(errors)
    assert "quoted material changed" in joined
    assert "link dropped or changed: https://example.com/x" in joined
    assert "numbers missing from rewrite: 42" in joined
    assert any("numbers not in original: 43" in w for w in warnings)


def test_inline_code_must_stay_verbatim():
    rewritten = ORIGINAL.replace("`readFile()`", "`readFileSync()`")
    errors, warnings = sc.compare(ORIGINAL, rewritten)
    assert any("inline code missing from rewrite: `readFile()`" in e for e in errors)
    assert any("inline code not in original: `readFileSync()`" in w for w in warnings)
    # Moving the identifier within the sentence is not a violation.
    moved = ORIGINAL.replace("3 numbers, `readFile()`, and", "`readFile()`, 3 numbers, and")
    assert sc.compare(ORIGINAL, moved)[0] == []


def test_cli_exit_code(tmp_path, capsys):
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text(ORIGINAL, encoding="utf-8")
    b.write_text(ORIGINAL.replace("3. third\n", ""), encoding="utf-8")
    assert sc.main([str(a), str(b)]) == 1
    assert "ERROR" in capsys.readouterr().out
    assert sc.main([str(a), str(a), "--json"]) == 0
