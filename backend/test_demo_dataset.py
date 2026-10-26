import unittest
from pathlib import Path
from types import SimpleNamespace
import uuid

from app.engine_bridge import get_winnow_fingerprints, query_trie_top_k, run_collusion_engine
from app.routes.reports import (
    _calculate_fingerprint_similarity_pairs,
    _deduplicate_similarity_pairs,
)
from app.utils import normalize_text


class DemoDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        demo_dir = Path(__file__).resolve().parents[1] / "test_files"
        prefixes = ("observatory_", "garden_", "archive_", "independent_")
        cls.files = sorted(
            path
            for path in demo_dir.iterdir()
            if path.is_file() and path.name.startswith(prefixes)
        )
        cls.fingerprints = {
            path.name: get_winnow_fingerprints(
                normalize_text(path.read_text(encoding="utf-8"))
            )
            for path in cls.files
        }
        cls.document_ids = {
            path.name: uuid.uuid5(uuid.NAMESPACE_URL, path.name)
            for path in cls.files
        }
        documents = [
            SimpleNamespace(
                id=cls.document_ids[path.name],
                fingerprints=cls.fingerprints[path.name],
            )
            for path in cls.files
        ]
        scores = _calculate_fingerprint_similarity_pairs(
            documents,
            set(cls.document_ids.values()),
        )
        cls.report_pairs = _deduplicate_similarity_pairs([
            (str(source_id), str(matched_id), score)
            for (source_id, matched_id), score in scores.items()
        ])
        cls.anchor_scores = {}
        for prefix, extension in (
            ("observatory", "py"),
            ("garden", "c"),
            ("archive", "js"),
        ):
            anchor = f"{prefix}_00_anchor.{extension}"
            corpus = {
                name: [fingerprint["hash"] for fingerprint in fingerprints]
                for name, fingerprints in cls.fingerprints.items()
                if name != anchor
            }
            matches = query_trie_top_k(
                cls.fingerprints[anchor],
                corpus,
                top_k=len(corpus),
            )
            cls.anchor_scores[anchor] = {
                match["doc_id"]: match["similarity_score"]
                for match in matches
            }

    def test_sample_count_and_similarity_bands(self):
        self.assertEqual(len(self.files), 18)
        expected_bands = {
            "90": (0.90, 1.0),
            "80": (0.80, 0.90),
            "50": (0.50, 0.60),
            "40": (0.40, 0.50),
        }
        for prefix, extension in (
            ("observatory", "py"),
            ("garden", "c"),
            ("archive", "js"),
        ):
            anchor = f"{prefix}_00_anchor.{extension}"
            for tier, (minimum, maximum) in expected_bands.items():
                candidate = f"{prefix}_{tier}.{extension}"
                score = self.anchor_scores[anchor][candidate]
                with self.subTest(anchor=anchor, candidate=candidate):
                    self.assertGreaterEqual(score, minimum)
                    self.assertLess(score, maximum)

    def test_groups_and_negative_controls_are_separated(self):
        for anchor, scores in self.anchor_scores.items():
            prefix = anchor.split("_", maxsplit=1)[0]
            for other, score in scores.items():
                if other.startswith("independent_"):
                    self.assertEqual(score, 0.0, f"{anchor} matched {other}")
                elif not other.startswith(prefix + "_"):
                    self.assertLess(score, 0.20, f"{anchor} cross-matched {other}")

    def test_negative_controls_do_not_match_any_positive_sample(self):
        positive_samples = [
            path for path in self.files if not path.name.startswith("independent_")
        ]
        controls = {
            path.name: [item["hash"] for item in self.fingerprints[path.name]]
            for path in self.files
            if path.name.startswith("independent_")
        }
        for source in positive_samples:
            matches = query_trie_top_k(
                self.fingerprints[source.name],
                controls,
                top_k=len(controls),
            )
            with self.subTest(source=source.name):
                self.assertEqual(matches, [])

    def test_dsu_components_change_with_similarity_threshold(self):
        expected_component_sizes = {
            0.00: [2, 15],
            0.20: [5, 5, 5],
            0.40: [5, 5, 5],
            0.50: [4, 4, 4],
            0.60: [3, 3, 3],
            0.80: [3, 3, 3],
            0.90: [2, 2, 2],
        }
        expected_edge_counts = {
            0.00: 66,
            0.20: 30,
            0.40: 27,
            0.50: 16,
            0.60: 9,
            0.80: 9,
            0.90: 3,
        }
        for threshold, expected_sizes in expected_component_sizes.items():
            eligible_pairs = [
                pair for pair in self.report_pairs if pair[2] >= threshold
            ]
            graph = run_collusion_engine(eligible_pairs, threshold=threshold)
            actual_sizes = {}
            for node in graph["nodes"]:
                actual_sizes.setdefault(node["cluster_id"], 0)
                actual_sizes[node["cluster_id"]] += 1
            with self.subTest(threshold=threshold):
                self.assertEqual(sorted(actual_sizes.values()), expected_sizes)
                self.assertEqual(len(graph["edges"]), expected_edge_counts[threshold])

    def test_graph_rebuild_scores_match_corpus_wide_jaccard(self):
        source_id, shared_id, unrelated_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        documents = [
            SimpleNamespace(
                id=source_id,
                fingerprints=[{"hash": value} for value in (1, 2, 3, 4)]
            ),
            SimpleNamespace(
                id=shared_id,
                fingerprints=[{"hash": value} for value in (1, 2, 3, 5)]
            ),
            SimpleNamespace(
                id=unrelated_id,
                fingerprints=[{"hash": value} for value in (8, 9)]
            )
        ]

        scores = _calculate_fingerprint_similarity_pairs(documents, {source_id})

        self.assertAlmostEqual(scores[(source_id, shared_id)], 3 / 5)
        self.assertNotIn((source_id, unrelated_id), scores)

    def test_graph_edges_are_undirected_and_not_duplicated(self):
        deduplicated = _deduplicate_similarity_pairs([
            ("doc-a", "doc-b", 0.75),
            ("doc-b", "doc-a", 0.75),
            ("doc-a", "doc-c", 0.60),
        ])

        self.assertEqual(
            {frozenset((source, matched)): score for source, matched, score in deduplicated},
            {
                frozenset(("doc-a", "doc-b")): 0.75,
                frozenset(("doc-a", "doc-c")): 0.60,
            },
        )


if __name__ == "__main__":
    unittest.main()
