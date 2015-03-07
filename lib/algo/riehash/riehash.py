def isPrime( n ):
	if pow( 2, n-1, n ) == 1:
		return True
	return False

def getPoWHash( hash_int, diff, nNonce ):
	base = 1 << 8
	for i in range(256):
		base = base << 1
		base = base | (hash_int & 1)
		hash_int = hash_int >> 1
	trailingZeros = diff - 1 - 8 - 256
	if trailingZeros < 16 or trailingZeros > 20000:
		return 0
	base = base << trailingZeros

	base += nNonce
	primes = 0

	if (base % 210) != 97:
		return 0

	if not isPrime( base ):
		return 0
	primes = 1

	base += 4
	if isPrime( base ):
		primes+=1

	base += 2
	if isPrime( base ):
		primes+=1

	base += 4
	if isPrime( base ):
		primes+=1

	base += 2
	if isPrime( base ):
		primes+=1

	base += 4
	if isPrime( base ):
		primes+=1

	return primes