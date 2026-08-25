"""Rebuild the unreleased section of CHANGELOG.md from changes/ fragments.

Run from the repository root: `make changelog` (or
`python3 scripts/build_changelog.py`). Only the section between the
unreleased markers is rewritten; released sections are never touched.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from relnotes.assemble import collect_entries, render_unreleased  # noqa: E402

BEGIN = "<!-- unreleased:begin -->"
END = "<!-- unreleased:end -->"


def read_version():
    text = (ROOT / "relnotes" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__ = "([^"]+)"', text)
    if not match:
        raise SystemExit("could not find __version__ in relnotes/__init__.py")
    return match.group(1)


def main():
    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit(
            "CHANGELOG.md is missing the {} / {} markers".format(BEGIN, END)
        )
    version = read_version()
    section = render_unreleased(version, collect_entries(ROOT / "changes"))
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    changelog.write_text(
        head + BEGIN + "\n" + section + END + tail, encoding="utf-8"
    )
    print("CHANGELOG.md: unreleased section rebuilt for {}".format(version))


if __name__ == "__main__":
    main()
