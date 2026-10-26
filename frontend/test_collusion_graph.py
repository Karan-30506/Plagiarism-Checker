import unittest
from unittest.mock import patch

from components.collusion_graph import render_collusion_graph


class CollusionGraphTests(unittest.TestCase):
    @patch("components.collusion_graph.components.html")
    def test_renders_similarity_edges_in_mocha_network(self, render_html):
        render_collusion_graph(
            [
                {"id": 0, "doc_id": "doc-a", "label": "alpha.py", "cluster_id": 0},
                {"id": 1, "doc_id": "doc-b", "label": "beta.py", "cluster_id": 0}
            ],
            [{"source": 0, "target": 1, "weight": 0.75}]
        )

        page = render_html.call_args.args[0]
        self.assertIn("#1e1e2e", page)
        self.assertIn("alpha.py", page)
        self.assertIn("beta.py", page)
        self.assertIn("Similarity: 75.0%", page)
        self.assertIn("<script>", page)


if __name__ == "__main__":
    unittest.main()
