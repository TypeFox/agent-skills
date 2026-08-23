"""Unit tests for check_docs.py.

Run from this directory (or point pytest at this file from anywhere):

    pytest test_check_docs.py

pytest is the only test dependency; the script under test stays stdlib-only.
The suite builds throwaway repos in tmp_path and asserts on finding levels
and cited tokens rather than message prose, so wording tweaks don't break it.
Several tests pin the matcher's deliberate skips (placeholders, build dirs,
unanchored segments) — those document design intent, not accidents.
"""

import textwrap

import pytest

import check_docs as cd


def write(root, relpath, text=""):
    p = root / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(text))
    return p


def run_checker(root, doc):
    checker = cd.Checker(root)
    checker.check_file(doc)
    return checker


def errors(checker):
    return [f for f in checker.findings if f.level == "error"]


def warnings(checker):
    return [f for f in checker.findings if f.level == "warning"]


def cited(findings):
    return [f.cited for f in findings]


# --- parse_frontmatter ---

class TestParseFrontmatter:
    def test_no_frontmatter(self):
        assert cd.parse_frontmatter(["# Title", "text"]) == (None, 0)

    def test_empty_input(self):
        assert cd.parse_frontmatter([]) == (None, 0)

    def test_unterminated_block_treated_as_absent(self):
        assert cd.parse_frontmatter(["---", "key: value"]) == (None, 0)

    def test_scalar_value_and_line_numbers(self):
        data, end = cd.parse_frontmatter(["---", "status: accepted", "---"])
        assert data == {"status": (["accepted"], 2)}
        assert end == 3

    def test_empty_scalar_gives_empty_list(self):
        data, _ = cd.parse_frontmatter(["---", "status:", "---"])
        assert data["status"][0] == []

    def test_inline_list(self):
        data, _ = cd.parse_frontmatter(
            ["---", "depends-on: [plan-a, 'plan-b']", "---"])
        assert data["depends-on"][0] == ["plan-a", "plan-b"]

    def test_dash_list_appends_to_preceding_key(self):
        data, _ = cd.parse_frontmatter(
            ["---", "depends-on:", "  - plan-a", "  - plan-b", "---"])
        assert data["depends-on"][0] == ["plan-a", "plan-b"]

    def test_comments_and_blank_lines_ignored(self):
        data, _ = cd.parse_frontmatter(
            ["---", "# a comment", "", "status: accepted  # trailing", "---"])
        assert data["status"][0] == ["accepted"]

    def test_quoted_scalars_stripped(self):
        data, _ = cd.parse_frontmatter(["---", 'title: "Hello"', "---"])
        assert data["title"][0] == ["Hello"]


# --- looks_like_path ---

class TestLooksLikePath:
    @pytest.mark.parametrize("token", [
        "docs/guide.md",
        "scripts/check_docs.py",
        "./run.sh",
        "src/utils/",           # trailing slash asserts a directory
        "config/Makefile",      # known filename after a slash
    ])
    def test_accepted(self, token):
        assert cd.looks_like_path(token)

    @pytest.mark.parametrize("token", [
        "Makefile",             # bare filename: generic prose, not a location
        "CLAUDE.md",
        "https://example.com/a.md",
        "/absolute/path.md",
        "docs/<name>.md",       # placeholder
        "docs/$VAR/x.md",
        "a b/c.md",             # space
        "../up.md",             # parent traversal
        "-v",
        "#anchor",
        "src/image.png",        # extension not in the known-ext allowlist
        "",
    ])
    def test_rejected(self, token):
        assert not cd.looks_like_path(token)


# --- path_exists / first_segment_anchored ---

class TestPathResolution:
    def test_resolves_relative_to_root_or_doc_dir(self, tmp_path):
        write(tmp_path, "docs/guide.md")
        assert cd.path_exists("docs/guide.md", tmp_path, tmp_path / "sub")
        assert cd.path_exists("guide.md", tmp_path, tmp_path / "docs")
        assert not cd.path_exists("gone.md", tmp_path, tmp_path / "docs")

    def test_anchor_and_trailing_slash_stripped(self, tmp_path):
        write(tmp_path, "docs/guide.md")
        assert cd.path_exists("docs/guide.md#section", tmp_path, tmp_path)
        assert cd.path_exists("docs/", tmp_path, tmp_path)

    def test_first_segment_must_be_real_directory(self, tmp_path):
        (tmp_path / "docs").mkdir()
        assert cd.first_segment_anchored("docs/x.md", tmp_path, tmp_path)
        assert not cd.first_segment_anchored("application/json", tmp_path, tmp_path)

    def test_build_dirs_never_anchor(self, tmp_path):
        (tmp_path / "dist").mkdir()
        assert not cd.first_segment_anchored("dist/app.js", tmp_path, tmp_path)

    def test_explicit_dot_slash_always_anchors(self, tmp_path):
        assert cd.first_segment_anchored("./anything", tmp_path, tmp_path)


# --- resolve_adr ---

class TestResolveAdr:
    @pytest.fixture
    def adr_dir(self, tmp_path):
        write(tmp_path, "docs/adr/0002-use-postgres.md")
        write(tmp_path, "docs/adr/0010-drop-cache.md")
        return tmp_path / "docs" / "adr"

    @pytest.mark.parametrize("token", [
        "0002-use-postgres.md",  # full filename
        "0002-use-postgres",     # stem
        "ADR-2",                 # canonical reference
        "adr2",                  # sloppy variants still resolve
        "2",
        "0002",
    ])
    def test_resolves(self, adr_dir, token):
        resolved = cd.resolve_adr(adr_dir, token)
        assert resolved is not None and resolved.stem == "0002-use-postgres"

    @pytest.mark.parametrize("token", ["ADR-3", "nonexistent", "ADR-10x"])
    def test_unresolvable(self, adr_dir, token):
        assert cd.resolve_adr(adr_dir, token) is None


# --- task-runner manifest loaders ---

class TestLoaders:
    def test_scripts_union_across_candidates(self, tmp_path):
        write(tmp_path, "package.json", '{"scripts": {"build": "x"}}')
        write(tmp_path, "sub/package.json", '{"scripts": {"test": "y"}}')
        scripts = cd.load_scripts([tmp_path, tmp_path / "sub"])
        assert set(scripts) == {"build", "test"}

    def test_scripts_none_without_manifest_but_empty_on_bad_json(self, tmp_path):
        assert cd.load_scripts([tmp_path]) is None
        write(tmp_path, "package.json", "not json{")
        assert cd.load_scripts([tmp_path]) is None

    def test_make_targets(self, tmp_path):
        write(tmp_path, "Makefile", """\
            .PHONY: build test
            build: deps
            \tgo build
            test lint:
            \tgo test
            %.o: %.c
            VAR := value
            """)
        targets = cd.load_make_targets([tmp_path])
        assert targets == {"build", "test", "lint"}

    def test_make_none_without_makefile(self, tmp_path):
        assert cd.load_make_targets([tmp_path]) is None

    def test_just_recipes(self, tmp_path):
        write(tmp_path, "justfile", """\
            set export := true
            version := "1.0"
            default:
            \techo hi
            @quiet-recipe:
            \techo shh
            build target="all": default
            \techo {{target}}
            """)
        recipes = cd.load_just_recipes([tmp_path])
        # recipes with default-valued params count; := settings do not
        assert recipes == {"default", "quiet-recipe", "build"}

    def test_just_none_without_justfile(self, tmp_path):
        assert cd.load_just_recipes([tmp_path]) is None


# --- inline backtick path references ---

class TestInlinePathChecks:
    def test_missing_path_is_error(self, tmp_path):
        (tmp_path / "scripts").mkdir()
        doc = write(tmp_path, "AGENTS.md", "Run `scripts/gone.py` first.")
        checker = run_checker(tmp_path, doc)
        assert cited(errors(checker)) == ["scripts/gone.py"]

    def test_existing_path_is_clean(self, tmp_path):
        write(tmp_path, "scripts/run.py")
        doc = write(tmp_path, "AGENTS.md", "Run `scripts/run.py` first.")
        checker = run_checker(tmp_path, doc)
        assert not checker.findings and checker.checked == 1

    def test_md_reference_checked_even_without_anchored_segment(self, tmp_path):
        # .md cross-links are unambiguous even when their first segment
        # doesn't exist — that's exactly the broken-link case.
        doc = write(tmp_path, "AGENTS.md", "See `guides/setup.md`.")
        checker = run_checker(tmp_path, doc)
        assert cited(errors(checker)) == ["guides/setup.md"]

    def test_unanchored_non_md_token_skipped(self, tmp_path):
        # `application/json`-style tokens: first segment is no directory here,
        # so the matcher must stay silent.
        doc = write(tmp_path, "AGENTS.md", "Send `application/json` bodies.")
        checker = run_checker(tmp_path, doc)
        assert not checker.findings and checker.checked == 0

    def test_build_dir_paths_skipped(self, tmp_path):
        (tmp_path / "dist").mkdir()
        doc = write(tmp_path, "AGENTS.md", "Ship `dist/bundle.js` only.")
        checker = run_checker(tmp_path, doc)
        assert not checker.findings

    def test_bare_filename_not_checked(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md", "Add a `Makefile` if you like.")
        checker = run_checker(tmp_path, doc)
        assert not checker.findings and checker.checked == 0

    def test_doc_relative_paths_resolve(self, tmp_path):
        write(tmp_path, "docs/setup/install.md")
        doc = write(tmp_path, "docs/guide.md", "See `setup/install.md`.")
        checker = run_checker(tmp_path, doc)
        assert not errors(checker)


# --- markdown links ---

class TestMarkdownLinks:
    def test_dead_link_is_error(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md", "[setup](docs/setup.md)")
        checker = run_checker(tmp_path, doc)
        assert cited(errors(checker)) == ["docs/setup.md"]

    def test_live_link_with_anchor_is_clean(self, tmp_path):
        write(tmp_path, "docs/setup.md")
        doc = write(tmp_path, "AGENTS.md", "[setup](docs/setup.md#install)")
        checker = run_checker(tmp_path, doc)
        assert not checker.findings and checker.checked == 1

    @pytest.mark.parametrize("target", [
        "https://example.com/x.md", "mailto:a@b.c",
        "/absolute/path.md", "docs/<placeholder>.md",
    ])
    def test_external_and_placeholder_targets_skipped(self, tmp_path, target):
        doc = write(tmp_path, "AGENTS.md", f"[link]({target})")
        checker = run_checker(tmp_path, doc)
        assert not checker.findings


# --- intra-document references (anchor links, prose pointers) ---

class TestAnchorLinks:
    def test_dead_anchor_is_error(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md", "# Setup\n\n[jump](#deploy)\n")
        checker = run_checker(tmp_path, doc)
        assert cited(errors(checker)) == ["#deploy"]

    def test_anchor_resolves_against_slugged_heading(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md",
                    "## Running Tests — CI & Local\n\n"
                    "[how](#running-tests--ci--local)\n")
        checker = run_checker(tmp_path, doc)
        assert not checker.findings and checker.checked == 1

    def test_duplicate_heading_suffix_accepted(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md",
                    "# Setup\n\ntext\n\n# Setup\n\n[second](#setup-1)\n")
        checker = run_checker(tmp_path, doc)
        assert not errors(checker)

    def test_heading_inside_code_fence_is_no_anchor(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md", """\
            ```bash
            # deploy
            ```
            [jump](#deploy)
            """)
        checker = run_checker(tmp_path, doc)
        assert cited(errors(checker)) == ["#deploy"]

    def test_setext_heading_and_html_id_are_anchors(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md", """\
            Deploy steps
            ============
            <a name="rollback"></a>
            [a](#deploy-steps) [b](#rollback)
            """)
        checker = run_checker(tmp_path, doc)
        assert not errors(checker)

    def test_placeholder_anchor_skipped(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md", "[tpl](#<section>)")
        checker = run_checker(tmp_path, doc)
        assert not checker.findings


class TestProsePointers:
    def test_dead_pointer_in_fence_comment_is_error(self, tmp_path):
        # The observed failure mode: a commands block promising an "open
        # question below" in a doc that contains no such thing.
        doc = write(tmp_path, "AGENTS.md", """\
            ```sh
            ruff check .   # assumes ruff on PATH, see open question below
            ```
            Nothing else here.
            """)
        checker = run_checker(tmp_path, doc)
        errs = errors(checker)
        assert len(errs) == 1 and "see open question below" in errs[0].cited

    def test_pointer_satisfied_across_inflection(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md", """\
            Run lint (see open question below).

            ## Open questions
            - is ruff pinned?
            """)
        checker = run_checker(tmp_path, doc)
        assert not checker.findings and checker.checked == 1

    def test_form_only_phrase_not_judged(self, tmp_path):
        # "the notes below" names a form, not a subject — nothing checkable.
        doc = write(tmp_path, "AGENTS.md", "Careful (see the notes below).\n")
        checker = run_checker(tmp_path, doc)
        assert not checker.findings and checker.checked == 0

    def test_above_direction_checked(self, tmp_path):
        # The pointer's own line is not part of the region it may point at.
        doc = write(tmp_path, "AGENTS.md", """\
            ## Deployment
            Ship it.

            Roll back as described, see deployment steps above.
            Also see migration steps above.
            """)
        checker = run_checker(tmp_path, doc)
        errs = errors(checker)
        assert len(errs) == 1 and "migration" in errs[0].cited


# --- fenced shell blocks ---

class TestShellFences:
    def test_unknown_executable_is_warning_only(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md", """\
            ```bash
            no-such-cmd-abcxyz --flag
            ```
            """)
        checker = run_checker(tmp_path, doc)
        assert not errors(checker)
        assert cited(warnings(checker)) == ["no-such-cmd-abcxyz"]

    def test_builtins_and_comments_not_which_checked(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md", """\
            ```bash
            # no-such-cmd-abcxyz would warn outside a comment
            cd somewhere
            export FOO=1
            ```
            """)
        checker = run_checker(tmp_path, doc)
        assert not checker.findings

    def test_placeholder_commands_skipped(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md", """\
            ```bash
            npm run <script-name>
            ```
            """)
        checker = run_checker(tmp_path, doc)
        assert not checker.findings

    def test_continuation_lines_not_reparsed(self, tmp_path):
        # Only the first physical line of a `\`-continued command is judged;
        # continuation args must not be misread as fresh commands.
        doc = write(tmp_path, "AGENTS.md", """\
            ```bash
            echo one \\
              no-such-cmd-abcxyz
            ```
            """)
        checker = run_checker(tmp_path, doc)
        assert not checker.findings

    def test_non_shell_fences_ignored(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md", """\
            ```python
            npm run missing
            ```
            """)
        checker = run_checker(tmp_path, doc)
        assert not checker.findings

    def test_dollar_prompt_prefix_stripped(self, tmp_path):
        write(tmp_path, "package.json", '{"scripts": {"build": "x"}}')
        doc = write(tmp_path, "AGENTS.md", """\
            ```sh
            $ npm run build
            ```
            """)
        checker = run_checker(tmp_path, doc)
        assert not errors(checker)

    def test_interpreter_script_argument_checked(self, tmp_path):
        (tmp_path / "scripts").mkdir()
        doc = write(tmp_path, "AGENTS.md", """\
            ```bash
            python3 scripts/gone.py --flag
            ```
            """)
        checker = run_checker(tmp_path, doc)
        assert "scripts/gone.py" in cited(errors(checker))

    def test_dot_slash_invocation_checked(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md", """\
            ```bash
            ./bootstrap.sh
            ```
            """)
        checker = run_checker(tmp_path, doc)
        assert "./bootstrap.sh" in cited(errors(checker))

    def test_compound_commands_split_and_env_prefix_dropped(self, tmp_path):
        write(tmp_path, "package.json", '{"scripts": {"build": "x"}}')
        doc = write(tmp_path, "AGENTS.md", """\
            ```bash
            cd pkg && NODE_ENV=production npm run deploy
            ```
            """)
        checker = run_checker(tmp_path, doc)
        assert "npm run deploy" in cited(errors(checker))


# --- task-runner invocations (inline code is enough to trigger them) ---

class TestRunnerChecks:
    def test_missing_npm_script_with_suggestion(self, tmp_path):
        write(tmp_path, "package.json", '{"scripts": {"build": "x"}}')
        doc = write(tmp_path, "AGENTS.md", "Run `npm run bild`.")
        checker = run_checker(tmp_path, doc)
        errs = errors(checker)
        assert cited(errs) == ["npm run bild"]
        assert "build" in errs[0].problem  # difflib suggestion surfaced

    def test_npm_test_resolves_to_test_script(self, tmp_path):
        write(tmp_path, "package.json", '{"scripts": {"build": "x"}}')
        doc = write(tmp_path, "AGENTS.md", "Run `npm test` before pushing.")
        checker = run_checker(tmp_path, doc)
        assert cited(errors(checker)) == ["npm test"]

    def test_yarn_and_pnpm_share_the_npm_check(self, tmp_path):
        write(tmp_path, "package.json", '{"scripts": {"build": "x"}}')
        doc = write(tmp_path, "AGENTS.md",
                    "Use `yarn run gone` or `pnpm run gone`.")
        checker = run_checker(tmp_path, doc)
        assert len(errors(checker)) == 2

    def test_npm_without_manifest_is_warning(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md", "Run `npm run build`.")
        checker = run_checker(tmp_path, doc)
        assert not errors(checker) and len(warnings(checker)) == 1

    def test_make_target_checked(self, tmp_path):
        write(tmp_path, "Makefile", "build:\n\ttrue\n")
        doc = write(tmp_path, "AGENTS.md", "Run `make build` then `make deploy`.")
        checker = run_checker(tmp_path, doc)
        assert cited(errors(checker)) == ["make deploy"]

    def test_make_without_makefile_is_warning(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md", "Run `make build` first.")
        checker = run_checker(tmp_path, doc)
        assert not errors(checker) and cited(warnings(checker)) == ["make build"]

    def test_make_flags_and_var_assignments_skipped(self, tmp_path):
        write(tmp_path, "Makefile", "build:\n\ttrue\n")
        doc = write(tmp_path, "AGENTS.md", "Run `make -j4 VERBOSE=1 build`.")
        checker = run_checker(tmp_path, doc)
        assert not checker.findings

    def test_just_recipe_checked(self, tmp_path):
        write(tmp_path, "justfile", "default:\n\techo hi\n")
        doc = write(tmp_path, "AGENTS.md", "Run `just deploy` to ship.")
        checker = run_checker(tmp_path, doc)
        assert cited(errors(checker)) == ["just deploy"]


# --- exec-plan frontmatter graph ---

class TestExecPlanGraph:
    def test_dead_edge_is_error_live_edge_is_clean(self, tmp_path):
        write(tmp_path, "docs/exec-plans/plan-b.md", "---\nstatus: done\n---\n")
        doc = write(tmp_path, "docs/exec-plans/plan-a.md", """\
            ---
            depends-on: [plan-b, plan-c]
            ---
            """)
        checker = run_checker(tmp_path, doc)
        assert cited(errors(checker)) == ["depends-on: plan-c"]

    def test_filename_and_stem_both_accepted(self, tmp_path):
        write(tmp_path, "docs/exec-plans/plan-b.md")
        doc = write(tmp_path, "docs/exec-plans/plan-a.md", """\
            ---
            discovered-from: [plan-b.md]
            ---
            """)
        checker = run_checker(tmp_path, doc)
        assert not checker.findings

    def test_relates_to_edge_checked(self, tmp_path):
        write(tmp_path, "docs/exec-plans/plan-b.md")
        doc = write(tmp_path, "docs/exec-plans/plan-a.md", """\
            ---
            relates-to: [plan-b, plan-gone]
            ---
            """)
        checker = run_checker(tmp_path, doc)
        assert cited(errors(checker)) == ["relates-to: plan-gone"]

    def test_edges_resolve_across_active_completed_folders(self, tmp_path):
        # The lifecycle scenario: an active plan depending on completed ones.
        write(tmp_path, "docs/exec-plans/completed/plan-done.md")
        doc = write(tmp_path, "docs/exec-plans/active/plan-next.md", """\
            ---
            depends-on: [plan-done]
            discovered-from: plan-gone
            ---
            """)
        checker = run_checker(tmp_path, doc)
        assert cited(errors(checker)) == ["discovered-from: plan-gone"]

    def test_placeholder_edges_skipped(self, tmp_path):
        doc = write(tmp_path, "docs/exec-plans/plan-a.md", """\
            ---
            depends-on: [<plan-id>]
            ---
            """)
        checker = run_checker(tmp_path, doc)
        assert not checker.findings


# --- ADR frontmatter lifecycle ---

class TestAdrLifecycle:
    def adr(self, tmp_path, frontmatter):
        return write(tmp_path, "docs/adr/0001-decision.md",
                     f"---\n{frontmatter}\n---\n")

    def test_superseded_without_edge_is_error(self, tmp_path):
        doc = self.adr(tmp_path, "status: superseded")
        checker = run_checker(tmp_path, doc)
        assert cited(errors(checker)) == ["status: superseded"]

    def test_edge_without_superseded_status_is_error(self, tmp_path):
        write(tmp_path, "docs/adr/0002-next.md")
        doc = self.adr(tmp_path, "status: accepted\nsuperseded-by: 0002-next")
        checker = run_checker(tmp_path, doc)
        assert cited(errors(checker)) == ["superseded-by: 0002-next"]

    def test_dead_superseded_by_target_is_error(self, tmp_path):
        doc = self.adr(tmp_path, "status: superseded\nsuperseded-by: ADR-9")
        checker = run_checker(tmp_path, doc)
        assert "superseded-by: ADR-9" in cited(errors(checker))

    def test_consistent_supersession_is_clean(self, tmp_path):
        write(tmp_path, "docs/adr/0002-next.md")
        doc = self.adr(tmp_path, "status: superseded\nsuperseded-by: ADR-2")
        checker = run_checker(tmp_path, doc)
        assert not checker.findings

    def test_nonstandard_status_is_warning(self, tmp_path):
        doc = self.adr(tmp_path, "status: rejected")
        checker = run_checker(tmp_path, doc)
        assert not errors(checker)
        assert cited(warnings(checker)) == ["status: rejected"]


# --- ADR references in root instruction files ---

class TestAdrRefsInRootDocs:
    @pytest.fixture
    def repo(self, tmp_path):
        write(tmp_path, "docs/adr/0001-a.md", "---\nstatus: accepted\n---\n")
        write(tmp_path, "docs/adr/0002-b.md",
              "---\nstatus: superseded\nsuperseded-by: 0003-c\n---\n")
        write(tmp_path, "docs/adr/0003-c.md", "---\nstatus: proposed\n---\n")
        return tmp_path

    def test_statuses_gate_citations(self, repo):
        doc = write(repo, "AGENTS.md",
                    "Follow ADR-1 and ADR-2; ADR-3 and ADR-9 too.")
        checker = run_checker(repo, doc)
        assert cited(errors(checker)) == ["ADR-2", "ADR-9"]
        assert cited(warnings(checker)) == ["ADR-3"]

    def test_only_root_instruction_files_are_gated(self, repo):
        doc = write(repo, "docs/guide.md", "Historical context: ADR-2.")
        checker = run_checker(repo, doc)
        assert not checker.findings

    def test_no_adr_dir_means_no_check(self, tmp_path):
        doc = write(tmp_path, "AGENTS.md", "We should write ADR-1 someday.")
        checker = run_checker(tmp_path, doc)
        assert not checker.findings


# --- frontmatter is excluded from body scanning ---

class TestFrontmatterBodyBoundary:
    def test_body_checks_start_after_frontmatter(self, tmp_path):
        doc = write(tmp_path, "docs/guide.md", """\
            ---
            related: docs/gone.md
            ---
            See [real](guide.md).
            """)
        checker = run_checker(tmp_path, doc)
        # the frontmatter value is not a body reference; the self-link resolves
        assert not checker.findings and checker.checked == 1


# --- doc discovery ---

class TestDiscoverDocs:
    def test_finds_agent_docs_and_skips_build_dirs(self, tmp_path):
        for rel in ("AGENTS.md", "packages/core/CLAUDE.md", "docs/guide.md",
                    ".github/copilot-instructions.md", ".claude/rules/style.md",
                    "node_modules/dep/AGENTS.md", "README.md"):
            write(tmp_path, rel)
        found = {str(p.relative_to(tmp_path)) for p in cd.discover_docs(tmp_path)}
        assert found == {"AGENTS.md", "packages/core/CLAUDE.md", "docs/guide.md",
                         ".github/copilot-instructions.md",
                         ".claude/rules/style.md"}

    def test_exclude_globs_filter_by_relative_path(self, tmp_path):
        write(tmp_path, "AGENTS.md")
        write(tmp_path, "fixtures/broken/AGENTS.md")
        write(tmp_path, "docs/guide.md")
        found = {str(p.relative_to(tmp_path))
                 for p in cd.discover_docs(tmp_path, excludes=["fixtures/*"])}
        assert found == {"AGENTS.md", "docs/guide.md"}

    def test_gitignored_docs_are_skipped(self, tmp_path):
        if not cd.shutil.which("git"):
            pytest.skip("git not available")
        import subprocess
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
        write(tmp_path, ".gitignore", "scratch/\n")
        write(tmp_path, "AGENTS.md")
        write(tmp_path, "scratch/CLAUDE.md")
        found = {str(p.relative_to(tmp_path)) for p in cd.discover_docs(tmp_path)}
        assert found == {"AGENTS.md"}

    def test_no_git_repo_keeps_all_docs(self, tmp_path):
        # tmp_path is outside any work tree; check-ignore fails → no filtering
        write(tmp_path, "AGENTS.md")
        assert cd.git_ignored(tmp_path, list(tmp_path.glob("*.md"))) == set()

    def test_build_dir_name_above_root_does_not_hide_docs(self, tmp_path):
        # The repo itself sits under a directory named like a build dir (a /tmp
        # checkout, ~/build/repo, ...). Only the path below root may be
        # filtered, or every doc vanishes and the check reports a clean run.
        root = tmp_path / "build" / "repo"
        write(root, "AGENTS.md")
        write(root, "dist/AGENTS.md")  # below root: still skipped
        found = {str(p.relative_to(root)) for p in cd.discover_docs(root)}
        assert found == {"AGENTS.md"}

    def test_root_ignored_by_enclosing_repo_keeps_docs(self, tmp_path):
        # root is not its own work tree but sits inside one that ignores it.
        # git walks up and calls every path ignored; trusting that would
        # discard the whole doc set and report "no agent docs found".
        if not cd.shutil.which("git"):
            pytest.skip("git not available")
        import subprocess
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
        write(tmp_path, ".gitignore", "workspace/\n")
        root = tmp_path / "workspace" / "project"
        write(root, "AGENTS.md")
        write(root, "CLAUDE.md")
        assert cd.git_ignored(root, cd.candidate_docs(root)) == set()
        found = {str(p.relative_to(root)) for p in cd.discover_docs(root)}
        assert found == {"AGENTS.md", "CLAUDE.md"}


# --- CLI entry point ---

class TestMain:
    def run_main(self, monkeypatch, argv):
        monkeypatch.setattr(cd.sys, "argv", ["check_docs.py"] + argv)
        return cd.main()

    def test_clean_repo_exits_zero(self, tmp_path, monkeypatch, capsys):
        write(tmp_path, "docs/setup.md")
        write(tmp_path, "AGENTS.md", "[setup](docs/setup.md)")
        assert self.run_main(monkeypatch, [str(tmp_path)]) == 0
        assert "Result: OK" in capsys.readouterr().out

    def test_errors_exit_one(self, tmp_path, monkeypatch, capsys):
        write(tmp_path, "AGENTS.md", "[setup](docs/setup.md)")
        assert self.run_main(monkeypatch, [str(tmp_path)]) == 1
        assert "Result: FAIL" in capsys.readouterr().out

    def test_warnings_pass_unless_strict(self, tmp_path, monkeypatch, capsys):
        write(tmp_path, "AGENTS.md", "Run `npm run build`.")  # no package.json
        assert self.run_main(monkeypatch, [str(tmp_path)]) == 0
        assert self.run_main(monkeypatch, ["--strict", str(tmp_path)]) == 1
        capsys.readouterr()

    def test_explicit_file_arguments(self, tmp_path, monkeypatch, capsys):
        doc = write(tmp_path, "notes.md", "[gone](missing.md)")
        assert self.run_main(monkeypatch, [str(doc)]) == 1
        capsys.readouterr()

    def test_exclude_flag_skips_broken_fixture(self, tmp_path, monkeypatch,
                                               capsys):
        write(tmp_path, "AGENTS.md")
        write(tmp_path, "fixtures/AGENTS.md", "[gone](missing.md)")
        argv = ["--exclude", "fixtures/*", str(tmp_path)]
        assert self.run_main(monkeypatch, argv) == 0
        capsys.readouterr()

    def test_nonexistent_file_argument_exits_two(self, tmp_path, monkeypatch,
                                                 capsys):
        assert self.run_main(monkeypatch, [str(tmp_path / "nope.md")]) == 2
        capsys.readouterr()

    def test_repo_without_docs_exits_zero(self, tmp_path, monkeypatch, capsys):
        assert self.run_main(monkeypatch, [str(tmp_path)]) == 0
        assert "nothing to check" in capsys.readouterr().out

    def test_all_docs_gitignored_is_an_error(self, tmp_path, monkeypatch,
                                             capsys):
        # Invisible filtering removed every doc. Exiting 0 would report success
        # for a repo the check cannot read — the whole point of a gate.
        if not cd.shutil.which("git"):
            pytest.skip("git not available")
        import subprocess
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
        write(tmp_path, ".gitignore", "*.md\n")
        write(tmp_path, "AGENTS.md")
        write(tmp_path, "docs/guide.md")
        assert self.run_main(monkeypatch, [str(tmp_path)]) == 1
        out = capsys.readouterr().out
        assert "discarded as gitignored" in out
        assert "Result: FAIL" in out

    def test_all_docs_excluded_warns_but_passes_unless_strict(
            self, tmp_path, monkeypatch, capsys):
        # The user's own --exclude matched everything: deliberate, so a warning
        # rather than a failure, promoted to an error under --strict.
        write(tmp_path, "AGENTS.md")
        write(tmp_path, "docs/guide.md")
        argv = ["--exclude", "*", str(tmp_path)]
        assert self.run_main(monkeypatch, argv) == 0
        assert "all matched --exclude" in capsys.readouterr().out
        assert self.run_main(monkeypatch, ["--strict"] + argv) == 1
        capsys.readouterr()
