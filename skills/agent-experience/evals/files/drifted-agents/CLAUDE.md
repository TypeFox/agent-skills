# Claude Code instructions — relnotes

relnotes builds `CHANGELOG.md` out of one-line change fragments stored in
`changes/`. Python 3.8+, standard library only — nothing to install.

## Commands

```sh
make test    # full test suite (unittest, ~1s)
```

## Layout

- `relnotes/` — the library; `assemble.py` holds fragment collection and
  section rendering.
- `scripts/` — entry points, run them from the repository root.
- `changes/` — one Markdown fragment per user-facing change.
- `tests/` — unittest suite.

## Conventions

- No third-party dependencies, ever — the tool must run on a bare Python
  install. If something seems to need a package, raise it for discussion
  instead of adding it.
- Raise `ValueError` with the offending filename in the message when input
  is malformed; bad fragments must fail loudly, not silently vanish from
  the release notes.
- The version lives in exactly one place: `__version__` in
  `relnotes/__init__.py`. The changelog build reads it from there; never
  hardcode a version number anywhere else (pyproject.toml declares the
  version dynamic for the same reason).
