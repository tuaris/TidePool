#include <openssl/sha.h>

#include "heavy.h"
#include "uint256.h"
#include "hefty1.h"
#include "sph_keccak.h"
#include "sph_blake.h"
#include "sph_groestl.h"

#define HEAVYCOIN_BLKHDR_SZ 84

/* Combines top 64-bits from each hash into a single hash */
void CombineHashes(uint256& out, uint256 hash1, uint512 hash2, uint512 hash3, uint512 hash4)
{
    uint256 mask = uint256("0x8000000000000000000000000000000000000000000000000000000000000000");
    uint256 hash[4] = { hash1, hash2.trim256(), hash3.trim256(), hash4.trim256() };

    /* Transpose first 64 bits of each hash into out */
    out = 0;
    for (unsigned int i = 0; i < 64; i++) {
        for (unsigned int j = 0; j < 4; j++) {
            out <<= 1;
            if ((hash[j] & mask) != 0)
                out |= 1;
        }
        mask >>= 1;
    }
}

void heavycoin_hashpow(const char* input, char* output)
{
    heavycoin_hash(input, HEAVYCOIN_BLKHDR_SZ, output);
}

void heavycoin_hash(const char* input, int len, char* output)
{
    unsigned char hash1[32];
    HEFTY1((unsigned char *)input, len, hash1);

    /* HEFTY1 is new, so take an extra security measure to eliminate
     * the possiblity of collisions:
     *
     *     Hash(x) = SHA256(x + HEFTY1(x))
     *
     * N.B. '+' is concatenation.
     */
    uint256 hash2;
    SHA256_CTX ctx;
    SHA256_Init(&ctx);
    SHA256_Update(&ctx, input, len);
    SHA256_Update(&ctx, hash1, sizeof(hash1));
    SHA256_Final((unsigned char *)&hash2, &ctx);

    /* Additional security: Do not rely on a single cryptographic hash
     * function.  Instead, combine the outputs of 4 of the most secure
     * cryptographic hash functions-- SHA256, KECCAK512, GROESTL512
     * and BLAKE512.
     */

    uint512 hash3;
    sph_keccak512_context keccakCtx;
    sph_keccak512_init(&keccakCtx);
    sph_keccak512(&keccakCtx, input, len);
    sph_keccak512(&keccakCtx, hash1, sizeof(hash1));
    sph_keccak512_close(&keccakCtx, (void *)&hash3);

    uint512 hash4;
    sph_groestl512_context groestlCtx;
    sph_groestl512_init(&groestlCtx);
    sph_groestl512(&groestlCtx, input, len);
    sph_groestl512(&groestlCtx, hash1, sizeof(hash1));
    sph_groestl512_close(&groestlCtx, (void *)&hash4);

    uint512 hash5;
    sph_blake512_context blakeCtx;
    sph_blake512_init(&blakeCtx);
    sph_blake512(&blakeCtx, input, len);
    sph_blake512(&blakeCtx, (unsigned char *)&hash1, sizeof(hash1));
    sph_blake512_close(&blakeCtx, (void *)&hash5);

    uint256 *final = (uint256 *)output;
    CombineHashes(*final, hash2, hash3, hash4, hash5);
}
