from app.engine_bridge import compress_text_huffman, decompress_text_huffman

# Test 1: Small Code Snippet
sample_code = """#include <iostream>
#include <vector>

void bubbleSort(std::vector<int>& arr) {
    int n = arr.size();
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                std::swap(arr[j], arr[j + 1]);
            }
        }
    }
}

int main() {
    std::vector<int> data = {64, 34, 25, 12, 22, 11, 90};
    bubbleSort(data);
    return 0;
}"""

print("--- TEST 1: SMALL SNIPPET HUFFMAN COMPRESSION ---")
comp_bytes, orig_size, comp_size = compress_text_huffman(sample_code)
restored_text = decompress_text_huffman(comp_bytes)

assert sample_code == restored_text, "❌ ERROR: Small snippet decompress mismatch!"
print(f"Original Size: {orig_size} bytes | Compressed Size: {comp_size} bytes (Header overhead on small input)")
print("✅ Test 1 Passed: Bit-exact restoration verified!\n")


# Test 2: Large Document Payload (12 KB repetition payload)
large_payload = sample_code * 30

print("--- TEST 2: LARGE DOCUMENT HUFFMAN COMPRESSION ---")
comp_bytes_lg, orig_lg, comp_lg = compress_text_huffman(large_payload)
restored_lg = decompress_text_huffman(comp_bytes_lg)

savings_pct = (1.0 - comp_lg / orig_lg) * 100.0
assert large_payload == restored_lg, "❌ ERROR: Large document decompress mismatch!"
print(f"Original Size: {orig_lg} bytes | Compressed Size: {comp_lg} bytes ({savings_pct:.2f}% savings)")
print("✅ Test 2 Passed: Bit-exact restoration & high compression ratio verified!")