from app.engine_bridge import get_winnow_fingerprints, compress_text_huffman

doc1 = """#include <iostream>
void sortArray(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}"""

doc2 = """#include <iostream>
void sortArray(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}"""

print("--- TESTING DUAL-STREAM INGESTION (WINNOWING + HUFFMAN) ---")

# 1. Test Stream A (Huffman)
comp_bytes, orig_sz, comp_sz = compress_text_huffman(doc1)
print(f"Stream A (Huffman): {orig_sz} bytes -> {comp_sz} bytes")

# 2. Test Stream B (Winnowing)
fps1 = get_winnow_fingerprints(doc1, k=10, w=4)
fps2 = get_winnow_fingerprints(doc2, k=10, w=4)

print(f"Stream B (Winnowing): Extracted {len(fps1)} fingerprint hashes")

# 3. Test Invariance (Identical docs must produce 100% identical fingerprint hashes)
hashes1 = {fp["hash"] for fp in fps1}
hashes2 = {fp["hash"] for fp in fps2}

shared_hashes = hashes1.intersection(hashes2)
jaccard_similarity = (len(shared_hashes) / len(hashes1.union(hashes2))) * 100.0

print(f"Shared Hashes: {len(shared_hashes)} / {len(hashes1)}")
print(f"Jaccard Hash Similarity: {jaccard_similarity:.1f}%")

assert jaccard_similarity == 100.0, "❌ ERROR: Identical documents did not match 100%!"
print("✅ SUCCESS: Winnowing fingerprinting & Dual-Stream verified!")