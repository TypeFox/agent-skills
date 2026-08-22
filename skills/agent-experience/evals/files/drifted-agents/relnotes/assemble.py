"""Collect change fragments and render the unreleased changelog section."""

import re
from pathlib import Path

FRAGMENT_PATTERN = re.compile(r"^(?P<num>\d+)-[a-z0-9-]+\.md$")


def collect_entries(changes_dir):
    """Return fragment lines from changes_dir, lowest issue number first.

    Each fragment is a single-line Markdown file named NNN-slug.md. Files
    not matching that pattern are rejected so typos don't silently vanish
    from the release notes.
    """
    entries = []
    for path in sorted(Path(changes_dir).iterdir()):
        match = FRAGMENT_PATTERN.match(path.name)
        if not match:
            raise ValueError(
                f"unrecognized fragment name: {path.name} (expected NNN-slug.md)"
            )
        text = path.read_text(encoding="utf-8").strip()
        if not text or "\n" in text:
            raise ValueError(f"fragment must be a single non-empty line: {path.name}")
        entries.append((int(match.group("num")), text))
    entries.sort(key=lambda pair: pair[0])
    return [text for _, text in entries]


def render_unreleased(version, entries):
    """Render the "## <version> (unreleased)" section from fragment lines."""
    lines = ["## {} (unreleased)".format(version), ""]
    if entries:
        lines.extend("- {}".format(entry) for entry in entries)
    else:
        lines.append("_No changes yet._")
    return "\n".join(lines) + "\n"
