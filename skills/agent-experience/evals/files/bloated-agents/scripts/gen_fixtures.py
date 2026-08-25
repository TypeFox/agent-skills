"""Regenerate shiftplan/data/holidays.json. Never edit that file by hand."""

import json
from pathlib import Path

# Fixed company holidays as (month, day), expanded over the supported years.
FIXED = [(1, 1), (5, 1), (10, 3), (12, 25), (12, 26)]
YEARS = range(2025, 2028)


def main():
    dates = [f"{y:04d}-{m:02d}-{d:02d}" for y in YEARS for (m, d) in FIXED]
    out = Path(__file__).resolve().parent.parent / "shiftplan" / "data" / "holidays.json"
    out.write_text(
        json.dumps({"generated_by": "scripts/gen_fixtures.py", "holidays": dates}, indent=2)
        + "\n"
    )
    print(f"wrote {out} ({len(dates)} holidays)")


if __name__ == "__main__":
    main()
