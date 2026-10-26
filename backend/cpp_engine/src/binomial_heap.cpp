#include "../include/binomial_heap.hpp"
#include <stdexcept>
#include <algorithm>

// ---------------------------------------------------------------------------
// Constructor
// ---------------------------------------------------------------------------
BinomialHeap::BinomialHeap() : head_(nullptr), size_(0) {}

// ---------------------------------------------------------------------------
// size / empty
// ---------------------------------------------------------------------------
size_t BinomialHeap::size() const { return size_; }
bool   BinomialHeap::empty() const { return size_ == 0; }

// ---------------------------------------------------------------------------
// link_trees
// Combines two binomial trees of equal degree into one, maintaining MAX-heap.
// The node with the LOWER score becomes the child of the higher-score node.
// ---------------------------------------------------------------------------
void BinomialHeap::link_trees(
    std::shared_ptr<BinomialNode> child_node,
    std::shared_ptr<BinomialNode> parent_node)
{
    child_node->parent  = parent_node;
    child_node->sibling = parent_node->child;
    parent_node->child  = child_node;
    parent_node->degree++;
}

// ---------------------------------------------------------------------------
// merge_root_lists
// Merges two root lists into one sorted by non-decreasing degree.
// Returns the new head of the merged list.
// ---------------------------------------------------------------------------
std::shared_ptr<BinomialNode> BinomialHeap::merge_root_lists(
    std::shared_ptr<BinomialNode> h1,
    std::shared_ptr<BinomialNode> h2)
{
    if (!h1) return h2;
    if (!h2) return h1;

    std::shared_ptr<BinomialNode> head;
    std::shared_ptr<BinomialNode> tail;

    // Pick the smaller-degree root as the initial head
    if (h1->degree <= h2->degree) {
        head = h1;
        h1 = h1->sibling;
    } else {
        head = h2;
        h2 = h2->sibling;
    }
    tail = head;

    while (h1 && h2) {
        if (h1->degree <= h2->degree) {
            tail->sibling = h1;
            h1 = h1->sibling;
        } else {
            tail->sibling = h2;
            h2 = h2->sibling;
        }
        tail = tail->sibling;
    }
    tail->sibling = h1 ? h1 : h2;
    return head;
}

// ---------------------------------------------------------------------------
// consolidate
// Walk the root list and merge trees of the same degree so that each degree
// appears at most once (like carry propagation in binary addition).
// MAX-heap: when two trees of equal degree are linked, the higher-score root
// becomes the parent.
// ---------------------------------------------------------------------------
void BinomialHeap::consolidate() {
    if (!head_) return;

    std::shared_ptr<BinomialNode> prev  = nullptr;
    std::shared_ptr<BinomialNode> curr  = head_;
    std::shared_ptr<BinomialNode> next  = curr->sibling;

    while (next) {
        // Case 1: degrees differ — just advance
        if (curr->degree != next->degree) {
            prev = curr;
            curr = next;
            next = next->sibling;
            continue;
        }

        // Case 2: three equal-degree trees in a row — skip the current pair
        // so we handle it at the next iteration (standard binomial-heap rule)
        if (next->sibling && next->sibling->degree == curr->degree) {
            prev = curr;
            curr = next;
            next = next->sibling;
            continue;
        }

        // Case 3: exactly two trees with equal degree — link them
        if (curr->score >= next->score) {
            // curr becomes the parent; remove next from the root list
            curr->sibling = next->sibling;
            link_trees(next, curr);
            next = curr->sibling;
        } else {
            // next becomes the parent; replace curr in the root list
            if (!prev) {
                head_ = next;
            } else {
                prev->sibling = next;
            }
            link_trees(curr, next);
            curr = next;
            next = curr->sibling;
        }
    }
}

// ---------------------------------------------------------------------------
// insert
// ---------------------------------------------------------------------------
void BinomialHeap::insert(double score, const std::string& doc_id) {
    auto new_node = std::make_shared<BinomialNode>(score, doc_id);

    // A single-node tree is a valid binomial tree of degree 0.
    // Union this singleton heap with the current heap.
    new_node->sibling = head_;
    head_ = new_node;
    size_++;
    consolidate();
}

// ---------------------------------------------------------------------------
// find_max_root
// Linear scan of the root list — O(log N) roots exist.
// ---------------------------------------------------------------------------
std::shared_ptr<BinomialNode> BinomialHeap::find_max_root() const {
    if (!head_) return nullptr;

    std::shared_ptr<BinomialNode> max_node = head_;
    std::shared_ptr<BinomialNode> curr = head_->sibling;

    while (curr) {
        if (curr->score > max_node->score) {
            max_node = curr;
        }
        curr = curr->sibling;
    }
    return max_node;
}

// ---------------------------------------------------------------------------
// peek_max
// ---------------------------------------------------------------------------
CandidateMatch BinomialHeap::peek_max() const {
    if (empty()) {
        throw std::out_of_range("BinomialHeap::peek_max() called on empty heap");
    }
    auto node = find_max_root();
    return {node->doc_id, node->score};
}

// ---------------------------------------------------------------------------
// extract_max
// Removes the root with maximum score, re-inserts its children as a new
// binomial heap (reversing the child list to restore sorted-degree order),
// then consolidates.
// ---------------------------------------------------------------------------
CandidateMatch BinomialHeap::extract_max() {
    if (empty()) {
        throw std::out_of_range("BinomialHeap::extract_max() called on empty heap");
    }

    // 1. Find max root and its predecessor in the root list
    std::shared_ptr<BinomialNode> prev_max = nullptr;
    std::shared_ptr<BinomialNode> max_node = head_;
    std::shared_ptr<BinomialNode> prev     = nullptr;
    std::shared_ptr<BinomialNode> curr     = head_;

    while (curr) {
        if (curr->score > max_node->score) {
            max_node = curr;
            prev_max = prev;
        }
        prev = curr;
        curr = curr->sibling;
    }

    // 2. Remove max_node from the root list
    if (!prev_max) {
        head_ = max_node->sibling;
    } else {
        prev_max->sibling = max_node->sibling;
    }
    max_node->sibling = nullptr;
    size_--;

    // 3. Reverse the child list of max_node to get a valid binomial heap
    //    (children are stored in decreasing-degree order; reversing gives
    //     the standard increasing-degree order needed for merge).
    std::shared_ptr<BinomialNode> child_heap = nullptr;
    std::shared_ptr<BinomialNode> child = max_node->child;

    while (child) {
        std::shared_ptr<BinomialNode> next_child = child->sibling;
        child->sibling = child_heap;
        child->parent  = nullptr;
        child_heap = child;
        child = next_child;
    }

    // 4. Merge child heap back into main root list, then consolidate
    head_ = merge_root_lists(head_, child_heap);
    consolidate();

    return {max_node->doc_id, max_node->score};
}

// ---------------------------------------------------------------------------
// extract_top_k
// ---------------------------------------------------------------------------
std::vector<CandidateMatch> BinomialHeap::extract_top_k(int k) {
    std::vector<CandidateMatch> results;
    int extracted = 0;

    while (!empty() && extracted < k) {
        results.push_back(extract_max());
        ++extracted;
    }
    return results;
}

