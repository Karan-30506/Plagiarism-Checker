#include "include/huffman.hpp"
#include "include/winnowing.hpp"
#include "include/compressed_trie.hpp"
#include "include/binomial_heap.hpp"
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
        std::unordered_map<std::string, uint64_t> doc_total_hashes;

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
                uint64_t count = 0;
                while (iss >> h) {
                    trie.insert(h, doc_id);
                    ++count;
                }
                doc_total_hashes[doc_id] += count;
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
            uint64_t corpus_doc_size = doc_total_hashes.count(doc_id)
                                       ? doc_total_hashes.at(doc_id) : 1;
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

    else {
        std::cerr << "Error: Unknown mode '" << mode << "'\n";
        return 1;
    }

    return 0;
}
