# Agent instructions — tickbill

tickbill turns time-tracking CSV entries into client invoices. Python 3.8+,
stdlib only — nothing to install.

## Commands

```sh
make test                                 # full test suite (unittest, <1s)
python3 -m unittest tests.test_rounding   # single test module
make demo                                 # run the CLI on sample-data/
```

## Layout

- `tickbill/` — the package: `csvin.py` parses entries, `rounding.py` holds
  the billing-minute arithmetic, `invoice.py` builds invoice lines,
  `cli.py` is the entry point.
- `tests/` — unittest suite.
- `sample-data/` — a small example input for the demo target.

## Conventions

- No third-party dependencies; the tool must run on a bare Python install.
- Malformed input rows raise `ValueError` naming the row number — bad data
  must fail loudly, never be skipped silently.
- All money amounts are computed in `invoice.py`; keep `rounding.py` free
  of currency logic.
