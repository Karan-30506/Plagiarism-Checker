/*
 * suffix_tree.cpp  —  Person 3
 * ============================================================
 * Generalized Suffix Array + Kasai's LCP Array implementation
 * ============================================================
 */

#include "suffix_tree.hpp"

#include <algorithm>
#include <cassert>
#include <cstring>
#include <limits>
#include <numeric>
#include <stdexcept>

// Unique sentinels that must not appear in user text.
static constexpr char SENTINEL_A = '\x01'; // terminates text_A in joint string
static constexpr char SENTINEL_B = '\x02'; // terminates text_B in joint string

// ============================================================
// Constructor
// ============================================================
SuffixArray::SuffixArray(const std::string& text_A, const std::string& text_B)
    : text_A_(text_A), text_B_(text_B),
      len_A_(text_A.size()), len_B_(text_B.size())
{
    // Build joint string: A + sentinel_A + B + sentinel_B
    joint_.reserve(len_A_ + 1 + len_B_ + 1);
    joint_ += text_A_;
    joint_ += SENTINEL_A;
    joint_ += text_B_;
    joint_ += SENTINEL_B;

    build_suffix_array();
    build_lcp_array();
    build_sparse_table();
    build_newline_tables();
}

// ============================================================
// Suffix Array Construction  (O(N log N) prefix-doubling / sort)
// ============================================================
void SuffixArray::build_suffix_array() {
    const int n = static_cast<int>(joint_.size());
    sa_.resize(n);
    rank_.resize(n);
    std::vector<int> tmp(n);

    // Initial ranks from character values
    std::iota(sa_.begin(), sa_.end(), 0);
    for (int i = 0; i < n; ++i) rank_[i] = static_cast<unsigned char>(joint_[i]);

    for (int gap = 1; gap < n; gap <<= 1) {
        // Comparator using current rank and rank at offset gap
        auto cmp = [&](int a, int b) {
            if (rank_[a] != rank_[b]) return rank_[a] < rank_[b];
            int ra = (a + gap < n) ? rank_[a + gap] : -1;
            int rb = (b + gap < n) ? rank_[b + gap] : -1;
            return ra < rb;
        };
        std::sort(sa_.begin(), sa_.end(), cmp);

        // Re-assign ranks
        tmp[sa_[0]] = 0;
        for (int i = 1; i < n; ++i) {
            tmp[sa_[i]] = tmp[sa_[i - 1]] + (cmp(sa_[i - 1], sa_[i]) ? 1 : 0);
        }
        rank_ = tmp;
        if (rank_[sa_[n - 1]] == n - 1) break; // All ranks unique — done
    }
}

// ============================================================
// LCP Array via Kasai's O(N) algorithm
// ============================================================
void SuffixArray::build_lcp_array() {
    const int n = static_cast<int>(joint_.size());
    lcp_.assign(n, 0);

    // Build inverse SA (rank_)
    std::vector<int> inv(n);
    for (int i = 0; i < n; ++i) inv[sa_[i]] = i;

    int h = 0;
    for (int i = 0; i < n; ++i) {
        if (inv[i] > 0) {
            int j = sa_[inv[i] - 1];
            while (i + h < n && j + h < n && joint_[i + h] == joint_[j + h]) ++h;
            lcp_[inv[i]] = h;
            if (h > 0) --h;
        }
    }
}

// ============================================================
// Sparse Table for O(1) RMQ on lcp_
// ============================================================
void SuffixArray::build_sparse_table() {
    const int n = static_cast<int>(lcp_.size());
    if (n == 0) return;

    int LOG = 1;
    while ((1 << LOG) <= n) ++LOG;

    log2_table_.resize(n + 1, 0);
    for (int i = 2; i <= n; ++i)
        log2_table_[i] = log2_table_[i / 2] + 1;

    sparse_table_.assign(LOG, std::vector<int>(n, 0));
    sparse_table_[0] = lcp_;

    for (int j = 1; j < LOG; ++j) {
        for (int i = 0; i + (1 << j) <= n; ++i) {
            sparse_table_[j][i] = std::min(sparse_table_[j - 1][i],
                                            sparse_table_[j - 1][i + (1 << (j - 1))]);
        }
    }
}

int SuffixArray::rmq(int l, int r) const {
    if (l > r) std::swap(l, r);
    ++l; // lcp_[l..r] means lcp between SA[l-1] and SA[r]
    if (l > r) return 0;
    int k = log2_table_[r - l + 1];
    return std::min(sparse_table_[k][l], sparse_table_[k][r - (1 << k) + 1]);
}

int SuffixArray::lcp_query(int i, int j) const {
    if (i == j) return static_cast<int>(joint_.size()) - sa_[i];
    return rmq(i, j);
}

// ============================================================
// Helpers: which document does a suffix position belong to?
// ============================================================
bool SuffixArray::is_from_A(int p) const {
    return p < static_cast<int>(len_A_);
}

bool SuffixArray::is_from_B(int p) const {
    return p > static_cast<int>(len_A_) && p < static_cast<int>(len_A_ + 1 + len_B_);
}

// ============================================================
// Newline tables for line-number lookup
// ============================================================
void SuffixArray::build_newline_tables() {
    newlines_A_.clear();
    for (size_t i = 0; i < text_A_.size(); ++i)
        if (text_A_[i] == '\n') newlines_A_.push_back(i);

    newlines_B_.clear();
    for (size_t i = 0; i < text_B_.size(); ++i)
        if (text_B_[i] == '\n') newlines_B_.push_back(i);
}

int SuffixArray::byte_to_line_A(size_t byte_offset) const {
    if (byte_offset >= len_A_) return -1;
    // Count newlines strictly before byte_offset
    auto it = std::lower_bound(newlines_A_.begin(), newlines_A_.end(), byte_offset);
    return static_cast<int>(it - newlines_A_.begin()) + 1;
}

int SuffixArray::byte_to_line_B(size_t byte_offset) const {
    if (byte_offset >= len_B_) return -1;
    auto it = std::lower_bound(newlines_B_.begin(), newlines_B_.end(), byte_offset);
    return static_cast<int>(it - newlines_B_.begin()) + 1;
}

// ============================================================
// Find all common substrings of length >= min_length
// ============================================================
std::vector<CommonSubstring> SuffixArray::find_common_substrings(size_t min_length) const {
    const int n = static_cast<int>(sa_.size());
    std::vector<CommonSubstring> results;

    // Sweep adjacent SA entries; whenever lcp_ >= min_length and the two
    // suffixes come from different documents, record a match.
    for (int i = 1; i < n; ++i) {
        int lcp_val = lcp_[i];
        if (static_cast<size_t>(lcp_val) < min_length) continue;

        int pa = sa_[i - 1];
        int pb = sa_[i];

        bool a_from_A = is_from_A(pa);
        bool b_from_B = is_from_B(pb);
        bool a_from_B = is_from_B(pa);
        bool b_from_A = is_from_A(pb);

        // Exactly one suffix must come from A and the other from B
        bool valid = (a_from_A && b_from_B) || (a_from_B && b_from_A);
        if (!valid) continue;

        // Normalise: offset_A is the byte position within text_A,
        //            offset_B is the byte position within text_B.
        size_t offset_A, offset_B;
        if (a_from_A) {
            offset_A = static_cast<size_t>(pa);
            offset_B = static_cast<size_t>(pb) - len_A_ - 1; // skip sentinel_A byte
        } else {
            offset_A = static_cast<size_t>(pb);
            offset_B = static_cast<size_t>(pa) - len_A_ - 1;
        }

        // Clamp length to stay within both texts (avoid crossing sentinels)
        size_t clamped_len = static_cast<size_t>(lcp_val);
        clamped_len = std::min(clamped_len, len_A_ - offset_A);
        clamped_len = std::min(clamped_len, len_B_ - offset_B);

        if (clamped_len < min_length) continue;

        CommonSubstring cs;
        cs.pos_in_A  = offset_A;
        cs.pos_in_B  = offset_B;
        cs.length    = clamped_len;
        cs.line_A    = byte_to_line_A(offset_A);
        cs.line_B    = byte_to_line_B(offset_B);
        results.push_back(cs);
    }

    // Sort by length descending
    std::sort(results.begin(), results.end(), [](const CommonSubstring& x, const CommonSubstring& y) {
        return x.length > y.length;
    });

    return results;
}

// ============================================================
// Longest Common Substring (the single LCS)
// ============================================================
CommonSubstring SuffixArray::longest_common_substring() const {
    const int n = static_cast<int>(sa_.size());
    CommonSubstring best{};
    best.length = 0;

    for (int i = 1; i < n; ++i) {
        int lcp_val = lcp_[i];
        if (lcp_val <= 0) continue;

        int pa = sa_[i - 1];
        int pb = sa_[i];

        bool a_from_A = is_from_A(pa);
        bool b_from_B = is_from_B(pb);
        bool a_from_B = is_from_B(pa);
        bool b_from_A = is_from_A(pb);

        bool valid = (a_from_A && b_from_B) || (a_from_B && b_from_A);
        if (!valid) continue;

        size_t offset_A, offset_B;
        if (a_from_A) {
            offset_A = static_cast<size_t>(pa);
            offset_B = static_cast<size_t>(pb) - len_A_ - 1;
        } else {
            offset_A = static_cast<size_t>(pb);
            offset_B = static_cast<size_t>(pa) - len_A_ - 1;
        }

        size_t clamped = static_cast<size_t>(lcp_val);
        clamped = std::min(clamped, len_A_ - offset_A);
        clamped = std::min(clamped, len_B_ - offset_B);

        if (clamped > best.length) {
            best.pos_in_A = offset_A;
            best.pos_in_B = offset_B;
            best.length   = clamped;
            best.line_A   = byte_to_line_A(offset_A);
            best.line_B   = byte_to_line_B(offset_B);
        }
    }

    return best;
}
