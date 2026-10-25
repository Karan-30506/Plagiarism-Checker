#include "../include/huffman.hpp"
#include <queue>
#include <stdexcept>
#include <cstring>

// Recursively traverse Huffman Tree to construct character-to-bitcode map
static void build_codes(const std::shared_ptr<HuffmanNode>& node, 
                        const std::string& current_code, 
                        std::map<unsigned char, std::string>& code_map) {
    if (!node) return;

    if (node->is_leaf()) {
        code_map[node->symbol] = current_code.empty() ? "0" : current_code;
        return;
    }

    build_codes(node->left, current_code + "0", code_map);
    build_codes(node->right, current_code + "1", code_map);
}

HuffmanResult HuffmanEngine::compress(const std::string& input_text) {
    HuffmanResult result;
    result.original_size_bytes = input_text.size();

    if (input_text.empty()) {
        result.compressed_size_bytes = 0;
        return result;
    }

    // 1. Calculate frequency of each byte/character (Ordered map for deterministic iteration)
    std::map<unsigned char, uint64_t> freq_map;
    for (unsigned char ch : input_text) {
        freq_map[ch]++;
    }

    // 2. Populate Min-Heap (Priority Queue)
    std::priority_queue<std::shared_ptr<HuffmanNode>, 
                        std::vector<std::shared_ptr<HuffmanNode>>, 
                        HuffmanComparator> min_heap;

    for (const auto& pair : freq_map) {
        min_heap.push(std::make_shared<HuffmanNode>(pair.first, pair.second));
    }

    // 3. Build Huffman Tree by merging 2 lowest frequency nodes
    while (min_heap.size() > 1) {
        auto left = min_heap.top(); min_heap.pop();
        auto right = min_heap.top(); min_heap.pop();

        auto parent = std::make_shared<HuffmanNode>(
            left->frequency + right->frequency, 
            left, 
            right
        );
        min_heap.push(parent);
    }

    auto root = min_heap.top();

    // 4. Generate Prefix Code Lookup Table
    std::map<unsigned char, std::string> code_map;
    build_codes(root, "", code_map);

    // 5. Serialize Header into Binary Buffer
    std::vector<uint8_t>& out = result.compressed_data;

    uint64_t orig_size = result.original_size_bytes;
    out.insert(out.end(), (uint8_t*)&orig_size, (uint8_t*)&orig_size + sizeof(orig_size));

    uint16_t table_size = static_cast<uint16_t>(freq_map.size());
    out.insert(out.end(), (uint8_t*)&table_size, (uint8_t*)&table_size + sizeof(table_size));

    for (const auto& pair : freq_map) {
        out.push_back(pair.first);
        uint32_t f = static_cast<uint32_t>(pair.second);
        out.insert(out.end(), (uint8_t*)&f, (uint8_t*)&f + sizeof(f));
    }

    // 6. Pack Bits into Byte Buffer
    uint8_t current_byte = 0;
    int bit_count = 0;

    for (unsigned char ch : input_text) {
        const std::string& code = code_map[ch];
        for (char bit : code) {
            current_byte <<= 1;
            if (bit == '1') {
                current_byte |= 1;
            }
            bit_count++;

            if (bit_count == 8) {
                out.push_back(current_byte);
                current_byte = 0;
                bit_count = 0;
            }
        }
    }

    // Flush remaining trailing bits
    if (bit_count > 0) {
        current_byte <<= (8 - bit_count);
        out.push_back(current_byte);
    }

    result.compressed_size_bytes = out.size();
    return result;
}

std::string HuffmanEngine::decompress(const std::vector<uint8_t>& compressed_bytes) {
    if (compressed_bytes.empty()) return "";

    size_t offset = 0;

    // 1. Parse Header
    if (compressed_bytes.size() < sizeof(uint64_t) + sizeof(uint16_t)) {
        throw std::invalid_argument("Invalid or corrupted binary header");
    }

    uint64_t original_size;
    std::memcpy(&original_size, compressed_bytes.data() + offset, sizeof(original_size));
    offset += sizeof(original_size);

    uint16_t table_size;
    std::memcpy(&table_size, compressed_bytes.data() + offset, sizeof(table_size));
    offset += sizeof(table_size);

    std::map<unsigned char, uint64_t> freq_map;
    for (uint16_t i = 0; i < table_size; ++i) {
        unsigned char sym = compressed_bytes[offset++];
        uint32_t freq;
        std::memcpy(&freq, compressed_bytes.data() + offset, sizeof(freq));
        offset += sizeof(freq);
        freq_map[sym] = freq;
    }

    if (original_size == 0) return "";

    // 2. Reconstruct Huffman Tree from Frequency Map
    std::priority_queue<std::shared_ptr<HuffmanNode>, 
                        std::vector<std::shared_ptr<HuffmanNode>>, 
                        HuffmanComparator> min_heap;

    for (const auto& pair : freq_map) {
        min_heap.push(std::make_shared<HuffmanNode>(pair.first, pair.second));
    }

    while (min_heap.size() > 1) {
        auto left = min_heap.top(); min_heap.pop();
        auto right = min_heap.top(); min_heap.pop();

        auto parent = std::make_shared<HuffmanNode>(
            left->frequency + right->frequency, 
            left, 
            right
        );
        min_heap.push(parent);
    }

    auto root = min_heap.top();

    // Edge Case: Single unique character text
    if (root->is_leaf()) {
        return std::string(original_size, root->symbol);
    }

    // 3. Traverse Tree using Bitstream
    std::string decoded_text;
    decoded_text.reserve(original_size);

    auto current_node = root;
    for (size_t i = offset; i < compressed_bytes.size(); ++i) {
        uint8_t byte = compressed_bytes[i];
        for (int b = 7; b >= 0; --b) {
            bool bit = (byte >> b) & 1;
            current_node = bit ? current_node->right : current_node->left;

            if (current_node->is_leaf()) {
                decoded_text.push_back(current_node->symbol);
                current_node = root;
                if (decoded_text.size() == original_size) {
                    return decoded_text;
                }
            }
        }
    }

    return decoded_text;
}