#ifndef DSU_HPP
#define DSU_HPP

/*
 * dsu.hpp  —  Person 3
 * ============================================================
 * Disjoint Set Union (DSU) — Union-Find with Path Compression
 * and Union by Rank
 *
 * Used to cluster documents into collusion rings:
 *   - Each document is a node identified by an integer ID.
 *   - When two documents exceed a similarity threshold, they are
 *     united into the same component.
 *   - find_set() with path compression gives near-O(1) amortised.
 *   - union_sets() with union by rank keeps tree height O(log N).
 *   - get_components() returns all connected components as groups.
 *   - export_graph() provides node/edge data for PyVis rendering.
 * ============================================================
 */

#include <string>
#include <vector>
#include <unordered_map>
#include <cstdint>

// An edge in the similarity graph (a plagiarism pair)
struct DSUEdge {
    int    node_u;          // Integer node ID
    int    node_v;          // Integer node ID
    double similarity;      // Jaccard / combined similarity score [0, 1]
    std::string doc_id_u;   // Original document UUID string
    std::string doc_id_v;   // Original document UUID string
};

// A node formatted for PyVis export
struct GraphNode {
    int         id;          // Integer node ID
    std::string doc_id;      // Original document UUID string
    std::string label;       // Display label (filename or short UUID)
    int         cluster_id;  // Root representative's integer ID (component colour)
};

// An edge formatted for PyVis export
struct GraphEdge {
    int    source;       // Integer node ID
    int    target;       // Integer node ID
    double weight;       // Similarity score (0.0 – 1.0)
    std::string doc_id_source;
    std::string doc_id_target;
};

class DSU {
public:
    // Initialise with n nodes numbered 0..n-1.
    explicit DSU(int n);

    // -----------------------------------------------------------------------
    // Core DSU operations
    // -----------------------------------------------------------------------

    // Find the representative (root) of the set containing x.
    // Applies iterative path compression so all nodes on the path
    // point directly to the root after the call.
    int find_set(int x);

    // Unite the sets containing x and y using union by rank.
    // Returns true if they were in different sets (a merge occurred).
    bool union_sets(int x, int y);

    // Return true if x and y belong to the same component.
    bool same_set(int x, int y);

    // Number of distinct components currently in the DSU.
    int num_components() const;

    // Total number of nodes.
    int size() const { return static_cast<int>(parent_.size()); }

    // -----------------------------------------------------------------------
    // Graph / collusion analysis
    // -----------------------------------------------------------------------

    // Register a document UUID for node i (for label export).
    void set_label(int i, const std::string& doc_id, const std::string& display_label = "");

    // Add a similarity edge (does NOT automatically union — call union_sets separately).
    void add_edge(int u, int v, double similarity,
                  const std::string& doc_id_u = "",
                  const std::string& doc_id_v = "");

    // Return all connected components as lists of node IDs.
    // Components of size 1 (isolated nodes) are excluded.
    std::vector<std::vector<int>> get_components() const;

    // Export node list formatted for PyVis / JSON serialisation.
    std::vector<GraphNode> export_nodes() const;

    // Export edge list formatted for PyVis / JSON serialisation.
    // Only edges that cross a component boundary are skipped; all intra-
    // component edges are included.
    std::vector<GraphEdge> export_edges() const;

private:
    std::vector<int> parent_;
    std::vector<int> rank_;
    int num_components_;

    // Optional metadata per node
    std::vector<std::string> doc_ids_;     // UUID strings
    std::vector<std::string> labels_;      // Display labels

    // Recorded edges (plagiarism pairs)
    std::vector<DSUEdge> edges_;
};

// ---------------------------------------------------------------------------
// Standalone factory: build a DSU from a list of (doc_id, doc_id, score)
// triples, merging any pair whose score >= threshold.
// Returns the populated DSU and a mapping from doc_id -> integer node index.
// ---------------------------------------------------------------------------
struct DSUBuildResult {
    DSU dsu;
    std::unordered_map<std::string, int> doc_to_node;
};

DSUBuildResult build_dsu_from_pairs(
    const std::vector<std::tuple<std::string, std::string, double>>& pairs,
    double threshold = 0.5
);

#endif // DSU_HPP

