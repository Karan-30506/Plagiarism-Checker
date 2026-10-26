#ifndef COMPRESSED_TRIE_HPP
#define COMPRESSED_TRIE_HPP

#include <string>
#include <vector>
#include <unordered_map>
#include <cstdint>
#include <memory>

// ---------------------------------------------------------------------------
// Compressed Radix Trie  (Radix Tree / Patricia Trie)
//
// Stores winnowing fingerprint hashes (as hex-string keys) mapped to the
// document IDs that own them.  Each edge carries an explicit label string
// so that shared prefixes are compressed into a single node, giving
// O(L) lookup and insert where L is the key length.
// ---------------------------------------------------------------------------

struct TrieNode {
    // Children keyed by the FIRST character of each outgoing edge label.
    std::unordered_map<char, std::shared_ptr<TrieNode>> children;

    // The compressed edge label leading INTO this node from its parent.
    std::string edge_label;

    // Document IDs that have a fingerprint whose key terminates at this node.
    std::vector<std::string> doc_ids;

    // True when at least one document fingerprint ends exactly here.
    bool is_terminal = false;

    TrieNode() = default;
    explicit TrieNode(const std::string& label) : edge_label(label) {}
};

class CompressedTrie {
public:
    CompressedTrie();

    // Insert a 64-bit hash associated with a document ID.
    // The hash is converted to a 16-character hex string as the key.
    void insert(uint64_t hash_value, const std::string& doc_id);

    // Return all document IDs whose fingerprint set contains this hash.
    // O(L) where L = 16 (fixed hex-string length).
    std::vector<std::string> lookup(uint64_t hash_value) const;

    // Return true if the trie contains any entry for this hash.
    bool contains(uint64_t hash_value) const;

    // Remove all entries belonging to doc_id.
    void remove_document(const std::string& doc_id);

    // Total number of distinct hash keys stored in the trie.
    size_t size() const;

private:
    std::shared_ptr<TrieNode> root_;
    size_t key_count_ = 0;

    // Convert a 64-bit hash to a fixed 16-char lowercase hex string.
    static std::string hash_to_key(uint64_t hash_value);

    // Internal recursive insert helper.
    void insert_recursive(
        std::shared_ptr<TrieNode>& node,
        const std::string& key,
        size_t depth,
        const std::string& doc_id
    );

    // Internal recursive lookup helper. Returns pointer to terminal node or nullptr.
    const TrieNode* lookup_node(const std::string& key) const;

    // Internal DFS used by remove_document.
    void remove_doc_dfs(
        std::shared_ptr<TrieNode>& node,
        const std::string& doc_id
    );

    // Recalculate key_count_ via DFS (used after removals).
    size_t count_dfs(const std::shared_ptr<TrieNode>& node) const;
};

#endif // COMPRESSED_TRIE_HPP

