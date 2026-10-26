#include "../include/compressed_trie.hpp"
#include <algorithm>
#include <sstream>
#include <iomanip>
#include <stdexcept>

// ---------------------------------------------------------------------------
// Helper: Convert uint64_t hash → 16-char lowercase hex string key
// ---------------------------------------------------------------------------
std::string CompressedTrie::hash_to_key(uint64_t hash_value) {
    std::ostringstream oss;
    oss << std::hex << std::setfill('0') << std::setw(16) << hash_value;
    return oss.str();
}

// ---------------------------------------------------------------------------
// Constructor
// ---------------------------------------------------------------------------
CompressedTrie::CompressedTrie()
    : root_(std::make_shared<TrieNode>()), key_count_(0) {}

// ---------------------------------------------------------------------------
// insert
// ---------------------------------------------------------------------------
void CompressedTrie::insert(uint64_t hash_value, const std::string& doc_id) {
    std::string key = hash_to_key(hash_value);
    insert_recursive(root_, key, 0, doc_id);
}

// Core insertion logic — compresses shared prefixes and splits edges as needed.
void CompressedTrie::insert_recursive(
    std::shared_ptr<TrieNode>& node,
    const std::string& key,
    size_t depth,
    const std::string& doc_id)
{
    // All key characters consumed: this node is (or becomes) a terminal.
    if (depth == key.size()) {
        if (!node->is_terminal) {
            node->is_terminal = true;
            key_count_++;
        }
        // Add doc_id if not already recorded
        if (std::find(node->doc_ids.begin(), node->doc_ids.end(), doc_id)
            == node->doc_ids.end()) {
            node->doc_ids.push_back(doc_id);
        }
        return;
    }

    char first_char = key[depth];

    // Check if an outgoing edge starts with first_char
    auto it = node->children.find(first_char);
    if (it == node->children.end()) {
        // No matching edge: create a new leaf node with the remaining key suffix.
        auto child = std::make_shared<TrieNode>(key.substr(depth));
        child->is_terminal = true;
        child->doc_ids.push_back(doc_id);
        node->children[first_char] = child;
        key_count_++;
        return;
    }

    // There IS a matching edge — find how many characters of edge_label match.
    std::shared_ptr<TrieNode>& child = it->second;
    const std::string& label = child->edge_label;

    size_t common = 0;
    size_t remaining_key_len = key.size() - depth;
    size_t label_len = label.size();
    size_t max_common = std::min(remaining_key_len, label_len);

    while (common < max_common && key[depth + common] == label[common]) {
        ++common;
    }

    if (common == label_len) {
        // Edge label fully matched: recurse deeper
        insert_recursive(child, key, depth + common, doc_id);
        return;
    }

    // Partial match: we need to split the edge at position `common`.
    //
    //   BEFORE:  node --[label]--> child
    //   AFTER:   node --[label[0..common)]--> split_node
    //                                              |--- [label[common..]]--> child  (old subtree)
    //                                              |--- [key[depth+common..]]--> new_leaf (if remaining)

    // Create the intermediate split node
    auto split_node = std::make_shared<TrieNode>(label.substr(0, common));

    // Re-attach old child under split node with the remaining label suffix
    child->edge_label = label.substr(common);
    split_node->children[child->edge_label[0]] = child;

    // Replace this edge in the parent
    node->children[first_char] = split_node;

    // Now insert the remaining key into split_node
    size_t new_depth = depth + common;
    if (new_depth == key.size()) {
        // The new key terminates exactly at the split node
        split_node->is_terminal = true;
        split_node->doc_ids.push_back(doc_id);
        key_count_++;
    } else {
        // Create a new leaf for the diverging part of the key
        std::string remaining_suffix = key.substr(new_depth);
        auto new_leaf = std::make_shared<TrieNode>(remaining_suffix);
        new_leaf->is_terminal = true;
        new_leaf->doc_ids.push_back(doc_id);
        split_node->children[remaining_suffix[0]] = new_leaf;
        key_count_++;
    }
}

// ---------------------------------------------------------------------------
// lookup_node  (internal)
// ---------------------------------------------------------------------------
const TrieNode* CompressedTrie::lookup_node(const std::string& key) const {
    const TrieNode* node = root_.get();
    size_t depth = 0;

    while (depth < key.size()) {
        char first_char = key[depth];
        auto it = node->children.find(first_char);
        if (it == node->children.end()) return nullptr;

        const TrieNode* child = it->second.get();
        const std::string& label = child->edge_label;

        // Check that key matches the full edge label
        size_t label_len = label.size();
        for (size_t i = 0; i < label_len; ++i) {
            if (depth + i >= key.size() || key[depth + i] != label[i]) {
                return nullptr; // Mismatch inside edge
            }
        }
        depth += label_len;
        node = child;
    }
    return node->is_terminal ? node : nullptr;
}

// ---------------------------------------------------------------------------
// lookup
// ---------------------------------------------------------------------------
std::vector<std::string> CompressedTrie::lookup(uint64_t hash_value) const {
    std::string key = hash_to_key(hash_value);
    const TrieNode* node = lookup_node(key);
    if (!node) return {};
    return node->doc_ids;
}

// ---------------------------------------------------------------------------
// contains
// ---------------------------------------------------------------------------
bool CompressedTrie::contains(uint64_t hash_value) const {
    std::string key = hash_to_key(hash_value);
    return lookup_node(key) != nullptr;
}

// ---------------------------------------------------------------------------
// remove_document
// ---------------------------------------------------------------------------
void CompressedTrie::remove_doc_dfs(
    std::shared_ptr<TrieNode>& node,
    const std::string& doc_id)
{
    if (!node) return;

    if (node->is_terminal) {
        auto& ids = node->doc_ids;
        ids.erase(std::remove(ids.begin(), ids.end(), doc_id), ids.end());
        if (ids.empty()) {
            node->is_terminal = false;
        }
    }

    for (auto& [ch, child] : node->children) {
        remove_doc_dfs(child, doc_id);
    }
}

void CompressedTrie::remove_document(const std::string& doc_id) {
    remove_doc_dfs(root_, doc_id);
    // Recount keys because some terminal flags were cleared
    key_count_ = count_dfs(root_);
}

size_t CompressedTrie::count_dfs(const std::shared_ptr<TrieNode>& node) const {
    if (!node) return 0;
    size_t count = node->is_terminal ? 1 : 0;
    for (const auto& [ch, child] : node->children) {
        count += count_dfs(child);
    }
    return count;
}

// ---------------------------------------------------------------------------
// size
// ---------------------------------------------------------------------------
size_t CompressedTrie::size() const {
    return key_count_;
}

