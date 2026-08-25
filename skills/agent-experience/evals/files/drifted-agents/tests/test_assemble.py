import tempfile
import unittest
from pathlib import Path

from relnotes.assemble import collect_entries, render_unreleased


class CollectEntriesTest(unittest.TestCase):
    def _write(self, directory, name, text):
        (Path(directory) / name).write_text(text, encoding="utf-8")

    def test_sorted_by_issue_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "104-later.md", "Second (#104)")
            self._write(tmp, "99-earlier.md", "First (#99)")
            self.assertEqual(collect_entries(tmp), ["First (#99)", "Second (#104)"])

    def test_bad_name_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "notes.txt", "Nope")
            with self.assertRaises(ValueError):
                collect_entries(tmp)

    def test_multiline_fragment_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "12-multi.md", "One\nTwo")
            with self.assertRaises(ValueError):
                collect_entries(tmp)

    def test_empty_fragment_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "13-empty.md", "\n")
            with self.assertRaises(ValueError):
                collect_entries(tmp)


class RenderUnreleasedTest(unittest.TestCase):
    def test_renders_bullets(self):
        section = render_unreleased("0.2.0", ["Fixed a thing (#7)"])
        self.assertIn("## 0.2.0 (unreleased)", section)
        self.assertIn("- Fixed a thing (#7)", section)

    def test_empty_gets_placeholder(self):
        self.assertIn("_No changes yet._", render_unreleased("0.2.0", []))


if __name__ == "__main__":
    unittest.main()
