import unittest
from unittest.mock import patch

from components.diff_viewer import render_diff_viewer


class DiffViewerTests(unittest.TestCase):
    @patch("components.diff_viewer.components.html")
    def test_renders_syntax_highlighted_side_by_side_diff(self, render_html):
        render_diff_viewer(
            "source.py",
            "def calculate(value):\n    return value + 1\n",
            "candidate.py",
            "def calculate(value):\n    return value + 2\n    return value\n",
            {1},
            {1}
        )

        page = render_html.call_args.args[0]
        self.assertIn("source.py", page)
        self.assertIn("candidate.py", page)
        self.assertIn('aria-label="Source document code"', page)
        self.assertIn('aria-label="Matched document code"', page)
        self.assertIn("class='editor-line similar'", page)
        self.assertIn('class="inline-change"', page)
        self.assertIn("class='editor-line added'", page)
        self.assertIn("color-scheme: dark", page)


if __name__ == "__main__":
    unittest.main()
