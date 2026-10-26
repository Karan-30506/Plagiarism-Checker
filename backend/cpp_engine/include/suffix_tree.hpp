#ifndef SUFFIX_TREE_HPP
#define SUFFIX_TREE_HPP

/*
 * suffix_tree.hpp  —  Person 3
 * ============================================================
 * Generalized Suffix Array + Kasai's LCP Array
 *
 * Implements a joint suffix array over two concatenated documents
 * (separated by unique sentinel characters) allowing:
 *   - O(N log N) suffix array construction via std::sort
 *   - O(N) LCP array construction via Kasai's algorithm
 *   - O(1) LCP range-minimum queries via a sparse table
 *   - O(N) Longest Common Substring (LCS) detection across documents
 *
 * Usage:
 *   SuffixArray sa(text_A, text_B);
 *   auto matches = sa.find_common_substrings(min_length);
 * ============================================================
 */

#include <string>
#include <vector>
#include <cstdint>

// Represents a common substring found between the two documents.
struct CommonSubstring {
    size_t pos_in_A;   // 0-based byte offset in text_A
    size_t pos_in_B;   // 0-based byte offset in text_B
    size_t length;     // Length of the matched substring
    int    line_A;     // 1-based line number in text_A (-1 if unavailable)
    int    line_B;     // 1-based line number in text_B (-1 if unavailable)
};

class SuffixArray {
public:
    // Construct joint suffix array over text_A and text_B.
    // Sentinels '$' (0x01) and '#' (0x02) are appended internally.
    SuffixArray(const std::string& text_A, const std::string& text_B);

    // Find all common substrings of length >= min_length between the two texts.
    // Returns a list of CommonSubstring records sorted by length descending.
    std::vector<CommonSubstring> find_common_substrings(size_t min_length = 10) const;

    // Return the LCS (single longest) between the two texts.
    CommonSubstring longest_common_substring() const;

    // Byte offset -> 1-based line number in text_A or text_B.
    int byte_to_line_A(size_t byte_offset) const;
    int byte_to_line_B(size_t byte_offset) const;

    size_t size_A() const { return len_A_; }
    size_t size_B() const { return len_B_; }

private:
    std::string text_A_;
    std::string text_B_;
    std::string joint_;   // text_A + sentinel_A + text_B + sentinel_B

    size_t len_A_;        // length of text_A (not including sentinel)
    size_t len_B_;        // length of text_B (not including sentinel)

    std::vector<int> sa_;    // Suffix Array  (indices into joint_)
    std::vector<int> rank_;  // Rank array (inverse SA)
    std::vector<int> lcp_;   // LCP array (Kasai)

    // Sparse table for O(1) range-minimum queries on lcp_
    std::vector<std::vector<int>> sparse_table_;
    std::vector<int> log2_table_;

    // Pre-computed newline positions for line number lookup
    std::vector<size_t> newlines_A_;
    std::vector<size_t> newlines_B_;

    // Build suffix array via O(N log N) prefix-doubling
    void build_suffix_array();

    // Build LCP array using Kasai's O(N) algorithm
    void build_lcp_array();

    // Build sparse table for O(1) RMQ on lcp_
    void build_sparse_table();

    // Range minimum query: minimum value in lcp_[l..r] (inclusive)
    int rmq(int l, int r) const;

    // LCP between suffix at sa_[i] and sa_[j]
    int lcp_query(int i, int j) const;

    // Return true if suffix at position p belongs to text_A
    bool is_from_A(int p) const;

    // Return true if suffix at position p belongs to text_B
    bool is_from_B(int p) const;

    // Build newline lookup tables
    void build_newline_tables();
};

#endif // SUFFIX_TREE_HPP

