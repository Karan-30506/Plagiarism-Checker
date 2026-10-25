#include "../include/winnowing.hpp"
#include <algorithm>
#include <cctype>

uint64_t WinnowingEngine::compute_hash(const std::string& str, int start, int length) {
    uint64_t hash = 0;
    for (int i = 0; i < length; ++i) {
        hash = (hash * BASE + static_cast<unsigned char>(str[start + i])) % MOD;
    }
    return hash;
}

std::vector<Fingerprint> WinnowingEngine::generate_fingerprints(
    const std::string& text, 
    int k, 
    int w
) {
    std::vector<Fingerprint> fingerprints;
    int n = static_cast<int>(text.length());

    if (n < k) return fingerprints; // Text shorter than k-gram length

    // 1. Compute rolling hashes for all k-grams
    int num_grams = n - k + 1;
    std::vector<uint64_t> hashes(num_grams);

    // Compute power base (BASE^(k-1) % MOD) for rolling subtraction
    uint64_t base_pow = 1;
    for (int i = 0; i < k - 1; ++i) {
        base_pow = (base_pow * BASE) % MOD;
    }

    // First k-gram hash
    hashes[0] = compute_hash(text, 0, k);

    // Rolling hash calculation for subsequent k-grams
    for (int i = 1; i < num_grams; ++i) {
        uint64_t prev_char = static_cast<unsigned char>(text[i - 1]);
        uint64_t next_char = static_cast<unsigned char>(text[i + k - 1]);

        // Remove leading character contribution
        uint64_t term = (prev_char * base_pow) % MOD;
        uint64_t hash = (hashes[i - 1] + MOD - term) % MOD;

        // Shift left and add trailing character
        hash = (hash * BASE + next_char) % MOD;
        hashes[i] = hash;
    }

    if (num_grams < w) {
        // Text yields fewer hashes than window size: pick absolute minimum
        auto min_it = std::min_element(hashes.begin(), hashes.end());
        uint32_t pos = static_cast<uint32_t>(std::distance(hashes.begin(), min_it));
        fingerprints.push_back({*min_it, pos});
        return fingerprints;
    }

    // 2. Winnowing algorithm: Slide window of size w
    int min_idx = -1;

    for (int i = 0; i <= num_grams - w; ++i) {
        int current_min = i;
        for (int j = 1; j < w; ++j) {
            // Pick minimum hash; break ties by picking the rightmost minimum
            if (hashes[i + j] <= hashes[current_min]) {
                current_min = i + j;
            }
        }

        // Only add fingerprint if minimum changed to avoid duplicate adjacent hashes
        if (current_min != min_idx) {
            min_idx = current_min;
            fingerprints.push_back({hashes[min_idx], static_cast<uint32_t>(min_idx)});
        }
    }

    return fingerprints;
}