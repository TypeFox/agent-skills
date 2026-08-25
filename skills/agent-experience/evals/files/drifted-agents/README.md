# relnotes

Assembles the project changelog from per-change fragment files: every
user-facing change adds a one-line Markdown file under `changes/`, and the
unreleased section of `CHANGELOG.md` is rebuilt from those fragments. This
keeps changelog entries merge-conflict-free and reviewable next to the code
they describe.

Python 3.8+, no third-party dependencies.

## Usage

Add a fragment named `<issue>-<slug>.md` (one line, ending with the issue
reference), then rebuild the changelog:

```sh
python3 scripts/gen_changelog.py
```

Run the tests with `make test`.
