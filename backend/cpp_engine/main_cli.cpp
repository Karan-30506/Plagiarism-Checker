#include "include/huffman.hpp"
#include "include/winnowing.hpp"
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>

int main(int argc, char* argv[]) {
    if (argc < 4) {
        std::cerr << "Usage:\n";
        std::cerr << "  Compress:   " << argv[0] << " compress <input_txt> <output_bin>\n";
        std::cerr << "  Decompress: " << argv[0] << " decompress <input_bin> <output_txt>\n";
        std::cerr << "  Winnow:     " << argv[0] << " winnow <input_txt> <output_hashes_txt> [k] [w]\n";
        return 1;
    }

    std::string mode = argv[1];
    std::string input_path = argv[2];
    std::string output_path = argv[3];

    if (mode == "compress") {
        std::ifstream in(input_path, std::ios::binary);
        if (!in.is_open()) {
            std::cerr << "Error: Cannot open input file " << input_path << "\n";
            return 1;
        }
        std::stringstream buffer;
        buffer << in.rdbuf();
        std::string raw_text = buffer.str();
        in.close();

        HuffmanResult res = HuffmanEngine::compress(raw_text);

        std::ofstream out(output_path, std::ios::binary);
        if (!out.is_open()) {
            std::cerr << "Error: Cannot write output binary " << output_path << "\n";
            return 1;
        }
        out.write(reinterpret_cast<const char*>(res.compressed_data.data()), res.compressed_data.size());
        out.close();

        std::cerr << "[INFO] Compressed " << res.original_size_bytes 
                  << " bytes -> " << res.compressed_size_bytes << " bytes\n";
    } 
    else if (mode == "decompress") {
        std::ifstream in(input_path, std::ios::binary);
        if (!in.is_open()) {
            std::cerr << "Error: Cannot open input binary " << input_path << "\n";
            return 1;
        }
        std::vector<uint8_t> compressed_data((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
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
    else if (mode == "winnow") {
        std::ifstream in(input_path, std::ios::binary);
        if (!in.is_open()) {
            std::cerr << "Error: Cannot open input file " << input_path << "\n";
            return 1;
        }
        std::stringstream buffer;
        buffer << in.rdbuf();
        std::string raw_text = buffer.str();
        in.close();

        int k = (argc >= 5) ? std::stoi(argv[4]) : 10;
        int w = (argc >= 6) ? std::stoi(argv[5]) : 4;

        std::vector<Fingerprint> fps = WinnowingEngine::generate_fingerprints(raw_text, k, w);

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

    return 0;
}