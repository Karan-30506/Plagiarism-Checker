import unittest

from app.engine_bridge import get_winnow_fingerprints, query_trie_top_k
from app.utils import normalize_text


class QuerySimilarityTests(unittest.TestCase):
    def test_duplicate_fingerprints_do_not_reduce_identical_document_score(self):
        repeated_text = "\n".join(
            "int calculate_total(int value) { return value * 2 + 17; }"
            for _ in range(30)
        )
        fingerprints = get_winnow_fingerprints(normalize_text(repeated_text))
        unique_hashes = {fingerprint["hash"] for fingerprint in fingerprints}

        self.assertGreater(len(fingerprints), len(unique_hashes))

        matches = query_trie_top_k(
            query_fingerprints=fingerprints,
            corpus_index={"identical-document": [fp["hash"] for fp in fingerprints]},
            top_k=1
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["doc_id"], "identical-document")
        self.assertAlmostEqual(matches[0]["similarity_score"], 1.0)

    def test_near_identical_document_retains_strong_similarity(self):
        source_text = "\n".join(
            f"int calculate_item_{index}(int value) {{ return value * 2 + {index}; }}"
            for index in range(40)
        )
        candidate_text = source_text.replace(
            "return value * 2 + 20;",
            "return value * 3 + 20;"
        )
        source_fingerprints = get_winnow_fingerprints(normalize_text(source_text))
        candidate_fingerprints = get_winnow_fingerprints(normalize_text(candidate_text))

        matches = query_trie_top_k(
            query_fingerprints=source_fingerprints,
            corpus_index={
                "near-identical-document": [
                    fingerprint["hash"] for fingerprint in candidate_fingerprints
                ]
            },
            top_k=1
        )

        self.assertEqual(len(matches), 1)
        self.assertGreater(matches[0]["similarity_score"], 0.5)


if __name__ == "__main__":
    unittest.main()
