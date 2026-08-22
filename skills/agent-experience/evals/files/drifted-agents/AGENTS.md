# Agent instructions — relnotes

relnotes assembles `CHANGELOG.md` from one-line change fragments in
`changes/`. Python 3.8+, stdlib only — there is nothing to install.

## Commands

```sh
make test                                  # full test suite (unittest, ~1s)
python3 -m unittest tests.test_assemble    # single test module
```

## Layout

- `relnotes/` — the library: `assemble.py` holds fragment collection and
  section rendering; keep it free of side effects beyond reading files.
- `scripts/` — entry points, meant to be run from the repository root.
- `changes/` — one Markdown fragment per user-facing change.
- `tests/` — unittest suite.

## Conventions

- No third-party dependencies, ever — the tool must run on a bare Python
  install. If something seems to need a package, raise it for discussion
  instead of adding it.
- Tests never read or write the repository's real `changes/` directory —
  build fragments in a temporary directory instead (see the helpers in
  `tests/test_assemble.py`).
- Raise `ValueError` with the offending filename in the message when input
  is malformed; bad fragments must fail loudly, not silently vanish from
  the release notes.

## Releasing

The release procedure is documented in `docs/RELEASING.md`.
