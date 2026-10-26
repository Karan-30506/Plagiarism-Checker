#ifndef KMP_HPP
#define KMP_HPP

/*
 * kmp.hpp  —  Person 3
 * ============================================================
 * Knuth-Morris-Pratt (KMP) String Matcher
 *
 * Provides:
 *   - O(N) LPS (Longest Prefix Suffix / failure function) table construction
 *   - O(N + M) exact pattern matching with all occurrence offsets
 *   - Line-level matching: find which lines in a target text contain a
 *     given pattern string, returning 1-based line offsets
 *   - Multi-pattern batch search for aligning shared lines across two documents
 * ============================================================
 */

#include <string>
#include <vector>
#include <cstdint>

// One match occurrence returned by KMPMatcher::search()
struct KMPMatch {
    size_t byte_offset;  // 0-based byte position in the text where match starts
    int    line_number;  // 1-based line number of the match (-1 if unavailable)
};

// A matched line pair between source and target document
struct LineMatch {
    int    source_line;   // 1-based line number in source document
    int    target_line;   // 1-based line number in target document
    size_t match_length;  // Length of the matching string
    std::string matched_text; // The actual matching content (truncated to 256 chars)
};

class KMPMatcher {
public:
    // Construct a KMP matcher for the given pattern.
    // Precomputes the LPS (failure function) table in O(M).
    explicit KMPMatcher(const std::string& pattern);

    // Search for all occurrences of the pattern in text.
    // Returns a list of KMPMatch with byte offsets and (if newlines provided)
    // 1-based line numbers. O(N + M).
    std::vector<KMPMatch> search(const std::string& text) const;

    // Return the precomputed LPS array (for debugging / inspection).
    const std::vector<int>& lps() const { return lps_; }

    // Pattern accessor
    const std::string& pattern() const { return pattern_; }
    size_t pattern_length() const { return pattern_.size(); }

    // ---------------------------------------------------------------
    // Static helpers — no need to instantiate KMPMatcher per call
    // ---------------------------------------------------------------

    // Compute LPS array for an arbitrary pattern string.
    static std::vector<int> compute_lps(const std::string& pattern);

    // Find all byte positions where pattern occurs in text. O(N + M).
    static std::vector<size_t> find_all(const std::string& text, const std::string& pattern);

    // Given a sorted vector of newline positions (byte offsets of '\n' chars)
    // and a byte offset, return the 1-based line number. O(log N).
    static int byte_to_line(const std::vector<size_t>& newlines, size_t byte_offset);

    // ---------------------------------------------------------------
    // Line-level alignment
    // ---------------------------------------------------------------

    // Given source_text and target_text split into lines, find all pairs of
    // (source_line, target_line) where a non-trivial line from source appears
    // verbatim in target. Lines shorter than min_line_length are skipped.
    //
    // Returns a sorted, deduplicated list of LineMatch records.
    static std::vector<LineMatch> align_lines(
        const std::string& source_text,
        const std::string& target_text,
        size_t             min_line_length = 6
    );

private:
    std::string      pattern_;
    std::vector<int> lps_;
};

#endif // KMP_HPP

