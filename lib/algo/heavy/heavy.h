#ifndef __HEAVY_H__
#define __HEAVY_H__

#ifdef __cplusplus
extern "C" {
#endif

void heavycoin_hash(const char* input, int len, char* output);
void heavycoin_hashpow(const char* input, char* output);

#ifdef __cplusplus
}
#endif

#endif // __HEAVY_H__
