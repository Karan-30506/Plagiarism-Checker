#include "include/huffman.hpp"
#include "include/winnowing.hpp"
#include "include/compressed_trie.hpp"
#include "include/binomial_heap.hpp"
#include "include/suffix_tree.hpp"
#include "include/kmp.hpp"
#include "include/dsu.hpp"
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <algorithm>

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

static std::string read_file(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in.is_open()) {
        std::cerr << "Error: Cannot open file " << path << "\n";
        std::exit(1);
    }
    std::ostringstream buf;
    buf << in.rdbuf();
    return buf.str();
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------
int main(int argc, char* argv[]) {
    if (argc < 4) {
        std::cerr << "Usage:\n";
        std::cerr << "  Compress:   " << argv[0] << " compress <input_txt> <output_bin>\n";
        std::cerr << "  Decompress: " << argv[0] << " decompress <input_bin> <output_txt>\n";
        std::cerr << "  Winnow:     " << argv[0] << " winnow <input_txt> <output_hashes_txt> [k] [w]\n";
        std::cerr << "  Query:      " << argv[0] << " query <query_hashes_txt> <corpus_hashes_dir_listing_txt> <output_json> [top_k]\n";
        std::cerr << "  Diff:       " << argv[0] << " diff <source_txt> <target_txt> <output_json> [min_len]\n";
        std::cerr << "  Collusion:  " << argv[0] << " collusion <pairs_txt> <output_json> [threshold]\n";
        return 1;
    }

    std::string mode       = argv[1];
    std::string input_path = argv[2];
    std::string output_path = argv[3];

    // ------------------------------------------------------------------
    // COMPRESS
    // ------------------------------------------------------------------
    if (mode == "compress") {
        std::string raw_text = read_file(input_path);
        HuffmanResult res = HuffmanEngine::compress(raw_text);

        std::ofstream out(output_path, std::ios::binary);
        if (!out.is_open()) {
            std::cerr << "Error: Cannot write output binary " << output_path << "\n";
            return 1;
        }
        out.write(reinterpret_cast<const char*>(res.compressed_data.data()),
                  res.compressed_data.size());
        out.close();

        std::cerr << "[INFO] Compressed " << res.original_size_bytes
                  << " bytes -> " << res.compressed_size_bytes << " bytes\n";
    }

    // ------------------------------------------------------------------
    // DECOMPRESS
    // ------------------------------------------------------------------
    else if (mode == "decompress") {
        std::ifstream in(input_path, std::ios::binary);
        if (!in.is_open()) {
            std::cerr << "Error: Cannot open input binary " << input_path << "\n";
            return 1;
        }
        std::vector<uint8_t> compressed_data(
            (std::istreambuf_iterator<char>(in)),
            std::istreambuf_iterator<char>()
        );
        in.close();

        std::string decompressed_text = HuffmanEngine::decompress(compressed_data);

        std::ofstream out(output_path, std::ios::binary);
        if (!out.is_open()) {
            std::cerr << "Error: Cannot write output text " << output_path << "\n";
            return 1;
        }
        out.write(decompressed_text.data(), decompressed_text.size());
        out.close();

        std::cerr << "[INFO] Decompressed " << compressed_data.size()
                  << " binary bytes -> " << decompressed_text.size() << " text bytes\n";
    }

    // ------------------------------------------------------------------
    // WINNOW
    // ------------------------------------------------------------------
    else if (mode == "winnow") {
        std::string raw_text = read_file(input_path);

        int k = (argc >= 5) ? std::stoi(argv[4]) : 10;
        int w = (argc >= 6) ? std::stoi(argv[5]) : 4;

        std::vector<Fingerprint> fps =
            WinnowingEngine::generate_fingerprints(raw_text, k, w);

        std::ofstream out(output_path);
        if (!out.is_open()) {
            std::cerr << "Error: Cannot write output hashes " << output_path << "\n";
            return 1;
        }
        for (const auto& fp : fps) {
            out << fp.hash_value << " " << fp.position << "\n";
        }
        out.close();

        std::cerr << "[INFO] Winnowed " << raw_text.size()
                  << " text bytes -> " << fps.size() << " fingerprint hashes\n";
    }

    // ------------------------------------------------------------------
    // QUERY  — Compressed Trie index lookup + Max-Binomial Heap Top-K
    //
    // argv[2]: query_hashes_txt   — one "hash position" per line (from winnow)
    // argv[3]: corpus_index_txt   — corpus fingerprint index file
    //                               format per line: <doc_id> <hash1> <hash2> ...
    // argv[4]: output_json        — ranked Top-K JSON output
    // argv[5]: top_k              — how many results to return (default 10)
    // ------------------------------------------------------------------
    else if (mode == "query") {
        if (argc < 5) {
            std::cerr << "Usage: " << argv[0]
                      << " query <query_hashes_txt> <corpus_index_txt> <output_json> [top_k]\n";
            return 1;
        }
        std::string corpus_index_path = argv[3];
        output_path                   = argv[4];
        int top_k = (argc >= 6) ? std::stoi(argv[5]) : 10;

        // 1. Load query fingerprints
        std::unordered_set<uint64_t> query_hashes;
        {
            std::ifstream qf(input_path);
            if (!qf.is_open()) {
                std::cerr << "Error: Cannot open query hashes file " << input_path << "\n";
                return 1;
            }
            std::string line;
            while (std::getline(qf, line)) {
                if (line.empty()) continue;
                std::istringstream iss(line);
                uint64_t h; uint32_t pos;
                if (iss >> h >> pos) query_hashes.insert(h);
            }
        }

        if (query_hashes.empty()) {
            // Output empty JSON array
            std::ofstream out(output_path);
            out << "[]\n";
            std::cerr << "[INFO] No query hashes — empty result.\n";
            return 0;
        }

        // 2. Build Compressed Trie from corpus index
        //    Corpus index format (one line per doc):
        //      <doc_id> <hash_1> <hash_2> ... <hash_N>
        CompressedTrie trie;
        std::unordered_map<std::string, std::unordered_set<uint64_t>> doc_hash_sets;

        {
            std::ifstream cf(corpus_index_path);
            if (!cf.is_open()) {
                std::cerr << "Error: Cannot open corpus index " << corpus_index_path << "\n";
                return 1;
            }
            std::string line;
            while (std::getline(cf, line)) {
                if (line.empty()) continue;
                std::istringstream iss(line);
                std::string doc_id;
                if (!(iss >> doc_id)) continue;

                uint64_t h;
                while (iss >> h) {
                    trie.insert(h, doc_id);
                    doc_hash_sets[doc_id].insert(h);
                }
            }
        }

        // 3. Trie lookup: count hash hits per corpus document
        std::unordered_map<std::string, uint64_t> hit_counts;
        for (uint64_t qh : query_hashes) {
            std::vector<std::string> matched_docs = trie.lookup(qh);
            for (const std::string& doc_id : matched_docs) {
                hit_counts[doc_id]++;
            }
        }

        if (hit_counts.empty()) {
            std::ofstream out(output_path);
            out << "[]\n";
            std::cerr << "[INFO] No matching documents found.\n";
            return 0;
        }

        // 4. Compute Jaccard similarity: |Q ∩ D| / |Q ∪ D|
        //    |Q ∪ D| = |Q| + |D| - |Q ∩ D|
        BinomialHeap heap;
        uint64_t query_size = static_cast<uint64_t>(query_hashes.size());

        for (const auto& [doc_id, intersection_size] : hit_counts) {
            uint64_t corpus_doc_size = doc_hash_sets.count(doc_id)
                                       ? static_cast<uint64_t>(doc_hash_sets.at(doc_id).size()) : 1;
            uint64_t union_size = query_size + corpus_doc_size - intersection_size;
            double jaccard = union_size > 0
                             ? static_cast<double>(intersection_size) / union_size
                             : 0.0;
            heap.insert(jaccard, doc_id);
        }

        // 5. Extract Top-K via Max-Binomial Heap
        std::vector<CandidateMatch> top_results = heap.extract_top_k(top_k);

        // 6. Write JSON output
        std::ofstream out(output_path);
        if (!out.is_open()) {
            std::cerr << "Error: Cannot write output JSON " << output_path << "\n";
            return 1;
        }
        out << "[\n";
        for (size_t i = 0; i < top_results.size(); ++i) {
            const auto& r = top_results[i];
            out << "  {\"doc_id\": \"" << r.doc_id
                << "\", \"similarity_score\": " << r.similarity_score << "}";
            if (i + 1 < top_results.size()) out << ",";
            out << "\n";
        }
        out << "]\n";
        out.close();

        std::cerr << "[INFO] Query: " << query_hashes.size() << " hashes, "
                  << hit_counts.size() << " candidate docs, "
                  << "Top-" << top_results.size() << " returned.\n";
    }

    // ------------------------------------------------------------------
    // DIFF  — KMP line-level alignment + Suffix Array LCS detection
    //
    // argv[2]: source_txt        — path to source document text file
    // argv[3]: target_txt        — path to target document text file
    // argv[4]: output_json       — diff result JSON
    // argv[5]: min_len           — minimum match length for suffix array (default 10)
    // ------------------------------------------------------------------
    else if (mode == "diff") {
        if (argc < 5) {
            std::cerr << "Usage: " << argv[0]
                      << " diff <source_txt> <target_txt> <output_json> [min_len]\n";
            return 1;
        }
        std::string target_path = argv[3];
        output_path             = argv[4];
        size_t min_len          = (argc >= 6) ? static_cast<size_t>(std::stoi(argv[5])) : 10;

        std::string source_text = read_file(input_path);
        std::string target_text = read_file(target_path);

        // --- KMP: line-level matches ---
        std::vector<LineMatch> line_matches =
            KMPMatcher::align_lines(source_text, target_text, 6);

        // --- Suffix Array: common substrings ---
        SuffixArray sa(source_text, target_text);
        std::vector<CommonSubstring> cs_matches = sa.find_common_substrings(min_len);

        // Collect matched source line numbers (union of both methods)
        std::unordered_set<int> matched_source_lines;
        std::unordered_set<int> matched_target_lines;

        for (const auto& lm : line_matches) {
            matched_source_lines.insert(lm.source_line);
            matched_target_lines.insert(lm.target_line);
        }
        for (const auto& cs : cs_matches) {
            if (cs.line_A > 0) matched_source_lines.insert(cs.line_A);
            if (cs.line_B > 0) matched_target_lines.insert(cs.line_B);
        }

        // Write JSON
        std::ofstream out(output_path);
        if (!out.is_open()) {
            std::cerr << "Error: Cannot write output JSON " << output_path << "\n";
            return 1;
        }

        out << "{\n";
        out << "  \"matched_source_lines\": [";
        bool first = true;
        for (int ln : matched_source_lines) {
            if (!first) out << ", ";
            out << ln; first = false;
        }
        out << "],\n";

        out << "  \"matched_target_lines\": [";
        first = true;
        for (int ln : matched_target_lines) {
            if (!first) out << ", ";
            out << ln; first = false;
        }
        out << "],\n";

        out << "  \"line_matches\": [\n";
        for (size_t i = 0; i < line_matches.size(); ++i) {
            const auto& lm = line_matches[i];
            // Escape backslashes and double-quotes in matched_text
            std::string safe_text = lm.matched_text;
            std::string escaped;
            for (char c : safe_text) {
                if (c == '"')  escaped += "\\\"";
                else if (c == '\\') escaped += "\\\\";
                else escaped += c;
            }
            out << "    {\"source_line\": " << lm.source_line
                << ", \"target_line\": " << lm.target_line
                << ", \"match_length\": " << lm.match_length
                << ", \"text\": \"" << escaped << "\"}";
            if (i + 1 < line_matches.size()) out << ",";
            out << "\n";
        }
        out << "  ],\n";

        out << "  \"common_substrings\": [\n";
        size_t limit = std::min(cs_matches.size(), size_t(50)); // top 50 only
        for (size_t i = 0; i < limit; ++i) {
            const auto& cs = cs_matches[i];
            out << "    {\"pos_in_A\": " << cs.pos_in_A
                << ", \"pos_in_B\": " << cs.pos_in_B
                << ", \"length\": " << cs.length
                << ", \"line_A\": " << cs.line_A
                << ", \"line_B\": " << cs.line_B << "}";
            if (i + 1 < limit) out << ",";
            out << "\n";
        }
        out << "  ]\n";
        out << "}\n";
        out.close();

        std::cerr << "[INFO] Diff: " << line_matches.size() << " line matches, "
                  << cs_matches.size() << " common substrings found.\n";
    }

    // ------------------------------------------------------------------
    // COLLUSION  — DSU clustering from similarity pairs
    //
    // argv[2]: pairs_txt    — one "doc_id_A doc_id_B score\n" per line
    // argv[3]: output_json  — node/edge graph JSON for PyVis
    // argv[4]: threshold    — similarity threshold for merging (default 0.5)
    // ------------------------------------------------------------------
    else if (mode == "collusion") {
        if (argc < 4) {
            std::cerr << "Usage: " << argv[0]
                      << " collusion <pairs_txt> <output_json> [threshold]\n";
            return 1;
        }
        output_path    = argv[3];
        double threshold = (argc >= 5) ? std::stod(argv[4]) : 0.5;

        // Load pairs
        std::vector<std::tuple<std::string, std::string, double>> pairs;
        {
            std::ifstream pf(input_path);
            if (!pf.is_open()) {
                std::cerr << "Error: Cannot open pairs file " << input_path << "\n";
                return 1;
            }
            std::string line;
            while (std::getline(pf, line)) {
                if (line.empty()) continue;
                std::istringstream iss(line);
                std::string da, db;
                double score;
                if (iss >> da >> db >> score) {
                    pairs.emplace_back(da, db, score);
                }
            }
        }

        if (pairs.empty()) {
            std::ofstream out(output_path);
            out << "{\"nodes\": [], \"edges\": []}\n";
            std::cerr << "[INFO] Collusion: no pairs — empty graph.\n";
            return 0;
        }

        // Build DSU
        DSUBuildResult res = build_dsu_from_pairs(pairs, threshold);
        DSU& dsu = res.dsu;

        std::vector<GraphNode> nodes = dsu.export_nodes();
        std::vector<GraphEdge> edges = dsu.export_edges();

        // Write JSON
        std::ofstream out(output_path);
        if (!out.is_open()) {
            std::cerr << "Error: Cannot write output JSON " << output_path << "\n";
            return 1;
        }

        out << "{\n  \"nodes\": [\n";
        for (size_t i = 0; i < nodes.size(); ++i) {
            const auto& n = nodes[i];
            out << "    {\"id\": " << n.id
                << ", \"doc_id\": \"" << n.doc_id << "\""
                << ", \"label\": \"" << n.label << "\""
                << ", \"cluster_id\": " << n.cluster_id << "}";
            if (i + 1 < nodes.size()) out << ",";
            out << "\n";
        }
        out << "  ],\n  \"edges\": [\n";
        for (size_t i = 0; i < edges.size(); ++i) {
            const auto& e = edges[i];
            out << "    {\"source\": " << e.source
                << ", \"target\": " << e.target
                << ", \"weight\": " << e.weight
                << ", \"doc_id_source\": \"" << e.doc_id_source << "\""
                << ", \"doc_id_target\": \"" << e.doc_id_target << "\"}";
            if (i + 1 < edges.size()) out << ",";
            out << "\n";
        }
        out << "  ]\n}\n";
        out.close();

        std::cerr << "[INFO] Collusion: " << nodes.size() << " nodes, "
                  << edges.size() << " edges, "
                  << dsu.num_components() << " components.\n";
    }

    else {
        std::cerr << "Error: Unknown mode '" << mode << "'\n";
        return 1;
    }

    return 0;
}