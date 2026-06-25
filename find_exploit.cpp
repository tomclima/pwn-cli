#include <iostream>
#include <vector>
#include <string>
#include <cstring>

// ============================================================================
// Lightweight SHA-1 Implementation (No external dependencies required)
// ============================================================================
#define SHA1_ROL(value, bits) (((value) << (bits)) | ((value) >> (32 - (bits))))

void sha1_transform(uint32_t state[5], const uint8_t buffer[64]) {
    uint32_t block[80];
    for (int i = 0; i < 16; ++i) {
        block[i] = ((uint32_t)buffer[i * 4] << 24)       |
                   ((uint32_t)buffer[i * 4 + 1] << 16)   |
                   ((uint32_t)buffer[i * 4 + 2] << 8)    |
                   ((uint32_t)buffer[i * 4 + 3]);
    }
    for (int i = 16; i < 80; ++i) {
        block[i] = SHA1_ROL(block[i - 3] ^ block[i - 8] ^ block[i - 14] ^ block[i - 16], 1);
    }

    uint32_t a = state[0], b = state[1], c = state[2], d = state[3], e = state[4];

    for (int i = 0; i < 80; ++i) {
        uint32_t f, k;
        if (i < 20) {
            f = (b & c) | (~b & d); k = 0x5A827999;
        } else if (i < 40) {
            f = b ^ c ^ d; k = 0x6ED9EBA1;
        } else if (i < 60) {
            f = (b & c) | (b & d) | (c & d); k = 0x8F1BBCDC;
        } else {
            f = b ^ c ^ d; k = 0xCA62C1D6;
        }
        uint32_t temp = SHA1_ROL(a, 5) + f + e + k + block[i];
        e = d; d = c; c = SHA1_ROL(b, 30); b = a; a = temp;
    }

    state[0] += a; state[1] += b; state[2] += c; state[3] += d; state[4] += e;
}

// Hashes exactly a 16-byte message and populates a 20-byte digest
void sha1_16bytes(const uint8_t message[16], uint8_t digest[20]) {
    uint32_t state[5] = {0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0};
    uint8_t buffer[64] = {0};
    
    std::memcpy(buffer, message, 16);
    buffer[16] = 0x80; // Padding bit
    
    // Append length in bits (16 bytes = 128 bits -> 0x80) at the end of the 64-byte block
    buffer[63] = 128; 

    sha1_transform(state, buffer);

    for (int i = 0; i < 5; ++i) {
        digest[i * 4]     = (state[i] >> 24) & 0xFF;
        digest[i * 4 + 1] = (state[i] >> 16) & 0xFF;
        digest[i * 4 + 2] = (state[i] >> 8)  & 0xFF;
        digest[i * 4 + 3] = state[i] & 0xFF;
    }
}
// ============================================================================

struct WordData {
    char str[5];
    uint32_t u32_val;
    int ascii_sum;
};

int main() {
    // 1. Precompute all 4-digit strings (0000 - 9999) to bypass hot-loop formatting
    std::vector<WordData> digits(10000);
    for (int i = 0; i < 10000; ++i) {
        snprintf(digits[i].str, sizeof(digits[i].str), "%04d", i);
        digits[i].ascii_sum = digits[i].str[0] + digits[i].str[1] + digits[i].str[2] + digits[i].str[3];
        std::memcpy(&digits[i].u32_val, digits[i].str, 4);
    }

    // Target constants from your code
    const char* GOOG_str = "GOOG";
    uint32_t GOOG_u32;
    std::memcpy(&GOOG_u32, GOOG_str, 4);
    const int GOOG_ASCII = 'G' + 'O' + 'O' + 'G';

    const uint32_t TARGET_X = 0xfef7f3f2;
    const int REQUIRED_ASCII = 986 - GOOG_ASCII;
    const uint32_t REQUIRED_WORD_SUM = TARGET_X - GOOG_u32;

    // The encrypted bytestring from your assembly snippet
    const uint8_t bytestring[3] = {0x51, 0x1a, 0xf8}; 

    std::cout << "[*] Commencing cryptographic payload hunt..." << std::endl;

    for (int i = 0; i < 10000; ++i) {
        const auto& w2 = digits[i];
        
        uint64_t goog_w2_u64;
        char goog_w2_str[8];
        std::memcpy(goog_w2_str, GOOG_str, 4);
        std::memcpy(goog_w2_str + 4, w2.str, 4);
        std::memcpy(&goog_w2_u64, goog_w2_str, 8);
        uint64_t target_w3_w4_u64 = 0x7e71717a707c7c76 ^ goog_w2_u64;

        for (int j = 0; j < 10000; ++j) {
            const auto& w3 = digits[j];

            // Math deducing constraints
            uint32_t needed_w4_u32 = REQUIRED_WORD_SUM - (w2.u32_val + w3.u32_val);
            int needed_w4_ascii = REQUIRED_ASCII - (w2.ascii_sum + w3.ascii_sum);

            char c0 = (needed_w4_u32 & 0xFF);
            char c1 = ((needed_w4_u32 >> 8) & 0xFF);
            char c2 = ((needed_w4_u32 >> 16) & 0xFF);
            char c3 = ((needed_w4_u32 >> 24) & 0xFF);

            // Filter out non-uppercase letters immediately
            if (c0 >= 'A' && c0 <= 'Z' && c1 >= 'A' && c1 <= 'Z' &&
                c2 >= 'A' && c2 <= 'Z' && c3 >= 'A' && c3 <= 'Z') {
                
                if ((c0 + c1 + c2 + c3) == needed_w4_ascii) {
                    char w4_str[5] = {c0, c1, c2, c3, '\0'};

                    if ((GOOG_u32 ^ w2.u32_val ^ w3.u32_val ^ needed_w4_u32) != 0xe0d0d0c) continue;
                    
                    uint64_t check_w3_w4_u64;
                    char w3_w4_str[8];
                    std::memcpy(w3_w4_str, w3.str, 4);
                    std::memcpy(w3_w4_str + 4, w4_str, 4);
                    std::memcpy(&check_w3_w4_u64, w3_w4_str, 8);

                    if (check_w3_w4_u64 != target_w3_w4_u64) continue;

                    // --- STRUCTURAL MATCH FOUND: PROCEED TO SHA-1 CHECK ---
                    uint8_t payload[16];
                    std::memcpy(payload, GOOG_str, 4);
                    std::memcpy(payload + 4, w2.str, 4);
                    std::memcpy(payload + 8, w3.str, 4);
                    std::memcpy(payload + 12, w4_str, 4);

                    uint8_t hash[20];
                    sha1_16bytes(payload, hash);

                    // Check if XOR results in "CTF"
                    if ((bytestring[0] ^ hash[0]) == 'C' &&
                        (bytestring[1] ^ hash[1]) == 'T' &&
                        (bytestring[2] ^ hash[2]) == 'F') {
                        
                        std::cout << "[+] Decryption Successful!" << std::endl;
                        std::cout << "Verified Payload: " 
                                  << std::string((char*)payload, 16) << std::endl;
                        return 0;
                    }
                }
            }
        }
    }

    std::cout << "[-] Mission failure. No matching package payload found." << std::endl;
    return 0;
}   