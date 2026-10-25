#ifndef WINNOWING_HPP
#define WINNOWING_HPP

#include <string>
#include <vector>
#include <cstdint>

struct Fingerprint {
    uint64_t hash_value;
    uint32_t position;
};

class WinnowingEngine {
public:
    // Generates winnowed fingerprints using Rabin-Karp rolling hash
    // k: k-gram length (default = 10)
    // w: sliding window size (default = 4)
    static std::vector<Fingerprint> generate_fingerprints(
        const std::string& text, 
        int k = 10, 
        int w = 4
    );

private:
    // Rabin-Karp polynomial rolling hash constants
    static constexpr uint64_t BASE = 31;
    static constexpr uint64_t MOD = 1000000007;

    static uint64_t compute_hash(const std::string& str, int start, int length);
};

#endif // WINNOWING_HPP