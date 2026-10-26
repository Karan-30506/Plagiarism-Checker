/*
 * dsu.cpp  —  Person 3
 * ============================================================
 * Disjoint Set Union implementation with Path Compression
 * and Union by Rank
 * ============================================================
 */

#include "dsu.hpp"

#include <algorithm>
#include <stdexcept>
#include <unordered_set>

// ============================================================
// Constructor
// ============================================================
DSU::DSU(int n)
    : parent_(n), rank_(n, 0), num_components_(n),
      doc_ids_(n), labels_(n)
{
    if (n < 0) throw std::invalid_argument("DSU size must be non-negative.");
    // Every node is its own parent initially
    for (int i = 0; i < n; ++i) parent_[i] = i;
}

// ============================================================
// find_set — iterative path compression
// ============================================================
int DSU::find_set(int x) {
    if (x < 0 || x >= static_cast<int>(parent_.size()))
        throw std::out_of_range("DSU::find_set: node index out of range.");

    // Two-pass path compression: first find root, then point all nodes to root
    int root = x;
    while (parent_[root] != root) root = parent_[root];

    // Path compression: every node on the path now points directly to root
    while (parent_[x] != root) {
        int next    = parent_[x];
        parent_[x]  = root;
        x           = next;
    }
    return root;
}

// ============================================================
// union_sets — union by rank
// ============================================================
bool DSU::union_sets(int x, int y) {
    int rx = find_set(x);
    int ry = find_set(y);

    if (rx == ry) return false; // Already in the same component

    // Attach smaller rank tree under higher rank tree
    if (rank_[rx] < rank_[ry]) std::swap(rx, ry);
    parent_[ry] = rx;
    if (rank_[rx] == rank_[ry]) ++rank_[rx];

    --num_components_;
    return true;
}

// ============================================================
// same_set
// ============================================================
bool DSU::same_set(int x, int y) {
    return find_set(x) == find_set(y);
}

// ============================================================
// num_components
// ============================================================
int DSU::num_components() const {
    return num_components_;
}

// ============================================================
// set_label
// ============================================================
void DSU::set_label(int i, const std::string& doc_id, const std::string& display_label) {
    if (i < 0 || i >= static_cast<int>(doc_ids_.size()))
        throw std::out_of_range("DSU::set_label: node index out of range.");
    doc_ids_[i] = doc_id;
    labels_[i]  = display_label.empty() ? doc_id : display_label;
}

// ============================================================
// add_edge — record similarity relationship (does NOT auto-merge)
// ============================================================
void DSU::add_edge(int u, int v, double similarity,
                   const std::string& doc_id_u,
                   const std::string& doc_id_v)
{
    DSUEdge e;
    e.node_u    = u;
    e.node_v    = v;
    e.similarity = similarity;
    e.doc_id_u  = doc_id_u.empty() ? doc_ids_[u] : doc_id_u;
    e.doc_id_v  = doc_id_v.empty() ? doc_ids_[v] : doc_id_v;
    edges_.push_back(e);
}

// ============================================================
// get_components — returns non-trivial components (size >= 2)
// ============================================================
std::vector<std::vector<int>> DSU::get_components() const {
    const int n = static_cast<int>(parent_.size());

    // We need a mutable copy of parent_ to call find_set(), but find_set is
    // non-const (it mutates parent_ for path compression). We use a local
    // helper lambda that doesn't compress paths.
    auto find_root_const = [&](int x) -> int {
        while (parent_[x] != x) x = parent_[x];
        return x;
    };

    std::unordered_map<int, std::vector<int>> component_map;
    for (int i = 0; i < n; ++i) {
        component_map[find_root_const(i)].push_back(i);
    }

    std::vector<std::vector<int>> result;
    for (auto& [root, members] : component_map) {
        if (members.size() >= 2) {
            std::sort(members.begin(), members.end());
            result.push_back(std::move(members));
        }
    }

    // Sort components by smallest member for deterministic output
    std::sort(result.begin(), result.end(), [](const std::vector<int>& a, const std::vector<int>& b) {
        return a[0] < b[0];
    });

    return result;
}

// ============================================================
// export_nodes — formatted for PyVis / JSON
// ============================================================
std::vector<GraphNode> DSU::export_nodes() const {
    const int n = static_cast<int>(parent_.size());

    // Build a const find-root helper (no path compression)
    auto find_root_const = [&](int x) -> int {
        while (parent_[x] != x) x = parent_[x];
        return x;
    };

    // Determine which nodes are part of a non-trivial component
    std::unordered_map<int, int> root_count;
    for (int i = 0; i < n; ++i) root_count[find_root_const(i)]++;

    // Assign sequential cluster IDs to each root
    std::unordered_map<int, int> root_to_cluster;
    int cluster_counter = 0;
    for (int i = 0; i < n; ++i) {
        int r = find_root_const(i);
        if (root_count[r] >= 2 && root_to_cluster.find(r) == root_to_cluster.end()) {
            root_to_cluster[r] = cluster_counter++;
        }
    }

    std::vector<GraphNode> nodes;
    for (int i = 0; i < n; ++i) {
        int r = find_root_const(i);
        if (root_count[r] < 2) continue; // Skip isolated nodes

        GraphNode gn;
        gn.id         = i;
        gn.doc_id     = doc_ids_[i];
        gn.label      = labels_[i].empty() ? doc_ids_[i] : labels_[i];
        gn.cluster_id = root_to_cluster[r];
        nodes.push_back(gn);
    }

    return nodes;
}

// ============================================================
// export_edges — formatted for PyVis / JSON
// ============================================================
std::vector<GraphEdge> DSU::export_edges() const {
    std::vector<GraphEdge> result;
    result.reserve(edges_.size());

    for (const auto& e : edges_) {
        GraphEdge ge;
        ge.source       = e.node_u;
        ge.target       = e.node_v;
        ge.weight       = e.similarity;
        ge.doc_id_source = e.doc_id_u;
        ge.doc_id_target = e.doc_id_v;
        result.push_back(ge);
    }
    return result;
}

// ============================================================
// Factory: build_dsu_from_pairs
// ============================================================
DSUBuildResult build_dsu_from_pairs(
    const std::vector<std::tuple<std::string, std::string, double>>& pairs,
    double threshold
) {
    // Collect all unique doc IDs and assign integer indices
    std::unordered_map<std::string, int> doc_to_node;
    std::vector<std::string> node_to_doc;

    for (const auto& [da, db, score] : pairs) {
        if (doc_to_node.find(da) == doc_to_node.end()) {
            doc_to_node[da] = static_cast<int>(node_to_doc.size());
            node_to_doc.push_back(da);
        }
        if (doc_to_node.find(db) == doc_to_node.end()) {
            doc_to_node[db] = static_cast<int>(node_to_doc.size());
            node_to_doc.push_back(db);
        }
    }

    const int n = static_cast<int>(node_to_doc.size());
    DSU dsu(n);

    // Assign labels
    for (int i = 0; i < n; ++i) {
        const std::string& doc_id = node_to_doc[i];
        // Use the last 8 hex chars as a short display label
        std::string label = doc_id.size() > 8 ? doc_id.substr(doc_id.size() - 8) : doc_id;
        dsu.set_label(i, doc_id, label);
    }

    // Process pairs: union those that meet threshold, record all edges
    for (const auto& [da, db, score] : pairs) {
        int u = doc_to_node[da];
        int v = doc_to_node[db];
        dsu.add_edge(u, v, score, da, db);
        if (score >= threshold) {
            dsu.union_sets(u, v);
        }
    }

    return DSUBuildResult{std::move(dsu), std::move(doc_to_node)};
}

