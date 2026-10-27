#ifndef HUFFMAN_HPP
#define HUFFMAN_HPP

#include <string>
#include <vector>
#include <map>
#include <cstdint>
#include <memory>
#include <algorithm>

// Node structure for the Min-Heap & Huffman Tree
struct HuffmanNode {
    unsigned char symbol;
    uint64_t frequency;
    unsigned char min_symbol; // tie-breaker for equal frequencies
    std::shared_ptr<HuffmanNode> left;
    std::shared_ptr<HuffmanNode> right;

    HuffmanNode(unsigned char sym, uint64_t freq)
        : symbol(sym), frequency(freq), min_symbol(sym), left(nullptr), right(nullptr) {}

    HuffmanNode(uint64_t freq, std::shared_ptr<HuffmanNode> l, std::shared_ptr<HuffmanNode> r)
        : symbol('\0'), frequency(freq), left(l), right(r) {
        min_symbol = std::min(l->min_symbol, r->min_symbol);
    }

    bool is_leaf() const {
        return left == nullptr && right == nullptr;
    }
};

// Comparator for Priority Queue (Min-Heap) with deterministic tie-breaking
struct HuffmanComparator {
    bool operator()(const std::shared_ptr<HuffmanNode>& a, const std::shared_ptr<HuffmanNode>& b) const {
        if (a->frequency != b->frequency) {
            return a->frequency > b->frequency; // Min-heap by frequency
        }
        return a->min_symbol > b->min_symbol; // Deterministic tie-breaker
    }
};

// Struct holding binary compression metrics
struct HuffmanResult {
    std::vector<uint8_t> compressed_data;
    uint64_t original_size_bytes;
    uint64_t compressed_size_bytes;
};

class HuffmanEngine {
public:
    // Compresses raw text into a self-contained binary payload (header + packed bitstream)
    static HuffmanResult compress(const std::string& input_text);

    // Decompresses binary payload back to exact original string
    static std::string decompress(const std::vector<uint8_t>& compressed_bytes);
};

#endif // HUFFMAN_HPP