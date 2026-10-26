#ifndef BINOMIAL_HEAP_HPP
#define BINOMIAL_HEAP_HPP

#include <string>
#include <vector>
#include <cstdint>
#include <memory>

// ---------------------------------------------------------------------------
// Max-Binomial Heap
//
// A forest of binomial trees satisfying the MAX-heap property.
// Used to extract the Top-K highest-similarity candidate documents in
// O(log N) per extraction, where N is the number of candidates.
//
// Each element is a (score, doc_id) pair; the heap orders by score descending.
// ---------------------------------------------------------------------------

struct BinomialNode {
    double      score;      // Jaccard similarity or combined ranking score
    std::string doc_id;     // Document UUID string
    int         degree;     // Number of children (order of this binomial tree)

    std::shared_ptr<BinomialNode> parent;
    std::shared_ptr<BinomialNode> child;   // Leftmost child
    std::shared_ptr<BinomialNode> sibling; // Right sibling

    BinomialNode(double s, const std::string& id)
        : score(s), doc_id(id), degree(0),
          parent(nullptr), child(nullptr), sibling(nullptr) {}
};

struct CandidateMatch {
    std::string doc_id;
    double      similarity_score;
};

class BinomialHeap {
public:
    BinomialHeap();

    // Insert a candidate document with its Jaccard similarity score.
    void insert(double score, const std::string& doc_id);

    // Return (without removing) the max-score candidate. Throws if empty.
    CandidateMatch peek_max() const;

    // Remove and return the max-score candidate. Throws if empty.
    CandidateMatch extract_max();

    // Extract the top-K candidates in descending score order.
    // If K > size(), returns all elements.
    std::vector<CandidateMatch> extract_top_k(int k);

    // Number of elements in the heap.
    size_t size() const;

    // True when the heap has no elements.
    bool empty() const;

private:
    // The heap is stored as a linked list of binomial-tree roots ordered by
    // non-decreasing degree.
    std::shared_ptr<BinomialNode> head_; // Head of root list
    size_t size_;

    // Merge two binomial heaps' root lists into a single degree-sorted list.
    static std::shared_ptr<BinomialNode> merge_root_lists(
        std::shared_ptr<BinomialNode> h1,
        std::shared_ptr<BinomialNode> h2
    );

    // Link two binomial trees of the same degree; makes the smaller-score
    // root a child of the larger-score root (max-heap property).
    static void link_trees(
        std::shared_ptr<BinomialNode> child,
        std::shared_ptr<BinomialNode> parent
    );

    // Consolidate (union) the current root list so degrees are unique.
    void consolidate();

    // Find the root node with the maximum score.
    std::shared_ptr<BinomialNode> find_max_root() const;
};

#endif // BINOMIAL_HEAP_HPP

