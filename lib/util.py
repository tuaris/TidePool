'''Various helper methods. It probably needs some cleanup.'''

import struct
import StringIO
import binascii
import lib.settings as settings
import bitcoin_rpc
import algo.algo_interface as algo_interface
from hashlib import sha256
from algo.sha3 import sha3_256

def deser_string(f):
	nit = struct.unpack("<B", f.read(1))[0]
	if nit == 253:
		nit = struct.unpack("<H", f.read(2))[0]
	elif nit == 254:
		nit = struct.unpack("<I", f.read(4))[0]
	elif nit == 255:
		nit = struct.unpack("<Q", f.read(8))[0]
	return f.read(nit)

def ser_string(s):
	if len(s) < 253:
		return chr(len(s)) + s
	elif len(s) < 0x10000:
		return chr(253) + struct.pack("<H", len(s)) + s
	elif len(s) < 0x100000000L:
		return chr(254) + struct.pack("<I", len(s)) + s
	return chr(255) + struct.pack("<Q", len(s)) + s

def deser_uint256(f):
	r = 0L
	for i in xrange(8):
		t = struct.unpack("<I", f.read(4))[0]
		r += t << (i * 32)
	return r

def ser_uint256(u):
	rs = ""
	for i in xrange(8):
		rs += struct.pack("<I", u & 0xFFFFFFFFL)
		u >>= 32
	return rs

def uint256_from_str(s):
	r = 0L
	t = struct.unpack("<IIIIIIII", s[:32])
	for i in xrange(8):
		r += t[i] << (i * 32)
	return r

def uint256_from_str_be(s):
	r = 0L
	t = struct.unpack(">IIIIIIII", s[:32])
	for i in xrange(8):
		r += t[i] << (i * 32)
	return r

def uint256_from_compact(c):
	nbytes = (c >> 24) & 0xFF
	v = (c & 0xFFFFFFL) << (8 * (nbytes - 3))
	return v

# Added to satisfy riecoin changes, becuase I don't know how this effects existing fuciontion
def uint256_from_compact_alt(c):
	nbytes = (c >> 24) & 0xFF
	if nbytes <= 3:
		v = (c & 0xFFFFFFL) >> (8 * (3 - nbytes))
	else:
		v = (c & 0xFFFFFFL) << (8 * (nbytes - 3))
	return v

def deser_vector(f, c):
	nit = struct.unpack("<B", f.read(1))[0]
	if nit == 253:
		nit = struct.unpack("<H", f.read(2))[0]
	elif nit == 254:
		nit = struct.unpack("<I", f.read(4))[0]
	elif nit == 255:
		nit = struct.unpack("<Q", f.read(8))[0]
	r = []
	for i in xrange(nit):
		t = c()
		t.deserialize(f)
		r.append(t)
	return r

def ser_vector(l):
	r = ""
	if len(l) < 253:
		r = chr(len(l))
	elif len(l) < 0x10000:
		r = chr(253) + struct.pack("<H", len(l))
	elif len(l) < 0x100000000L:
		r = chr(254) + struct.pack("<I", len(l))
	else:
		r = chr(255) + struct.pack("<Q", len(l))
	for i in l:
		r += i.serialize()
	return r

def deser_uint256_vector(f):
	nit = struct.unpack("<B", f.read(1))[0]
	if nit == 253:
		nit = struct.unpack("<H", f.read(2))[0]
	elif nit == 254:
		nit = struct.unpack("<I", f.read(4))[0]
	elif nit == 255:
		nit = struct.unpack("<Q", f.read(8))[0]
	r = []
	for i in xrange(nit):
		t = deser_uint256(f)
		r.append(t)
	return r

def ser_uint256_vector(l):
	r = ""
	if len(l) < 253:
		r = chr(len(l))
	elif len(l) < 0x10000:
		r = chr(253) + struct.pack("<H", len(l))
	elif len(l) < 0x100000000L:
		r = chr(254) + struct.pack("<I", len(l))
	else:
		r = chr(255) + struct.pack("<Q", len(l))
	for i in l:
		r += ser_uint256(i)
	return r

__b58chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
__b58base = len(__b58chars)

def b58decode(v, length):
	""" decode v into a string of len bytes
	"""
	long_value = 0L
	for (i, c) in enumerate(v[::-1]):
		long_value += __b58chars.find(c) * (__b58base**i)

	result = ''
	while long_value >= 256:
		div, mod = divmod(long_value, 256)
		result = chr(mod) + result
		long_value = div
	result = chr(long_value) + result

	nPad = 0
	for c in v:
		if c == __b58chars[0]: nPad += 1
		else: break

	result = chr(0)*nPad + result
	if length is not None and len(result) != length:
		return None

	return result

def b58encode(value):
	""" encode integer 'value' as a base58 string; returns string
	"""
	encoded = ''
	while value >= __b58base:
		div, mod = divmod(value, __b58base)
		encoded = __b58chars[mod] + encoded # add to left
		value = div
	encoded = __b58chars[value] + encoded # most significant remainder
	return encoded

def reverse_hash(h):
	# This only revert byte order, nothing more
	if len(h) != 64:
		raise Exception('hash must have 64 hexa chars')

	return ''.join([ h[56-i:64-i] for i in range(0, 64, 8) ])

def doublesha(b):
	return sha256(sha256(b).digest()).digest()

def bits_to_target(bits):
	return struct.unpack('<L', bits[:3] + b'\0')[0] * 2**(8*(int(bits[3], 16) - 3))

def address_to_pubkeyhash(addr):
	try:
		addr = b58decode(addr, 25)
	except:
		return None

	if addr is None:
		return None

	ver = addr[0]
	cksumA = addr[-4:]

	if settings.COINDAEMON_ALGO == 'keccak':
		cksumB = sha3_256(addr[:-4]).digest()[:4]
	else:
		cksumB = doublesha(addr[:-4])[:4]

	if cksumA != cksumB:
		return None

	return (ver, addr[1:-4])

def ser_uint256_be(u):
	'''ser_uint256 to big endian'''
	rs = ""
	for i in xrange(8):
		rs += struct.pack(">I", u & 0xFFFFFFFFL)
		u >>= 32
	return rs

def deser_uint256_be(f):
	r = 0L
	for i in xrange(8):
		t = struct.unpack(">I", f.read(4))[0]
		r += t << (i * 32)
	return r

def ser_number(n):
	s = bytearray(b'\1')
	while n > 127:
		s[0] += 1
		s.append(n % 256)
		n //= 256
	s.append(n)
	return bytes(s)

def encode_coinbase_nheight(n, min_size = 1):
	# For encoding nHeight into coinbase
	# Little Endian
	# Total size of the returned byte stream is size of n + 1
	s = bytearray(b'\1')

	# Binarry conversion of n
	while n > 127:
		s[0] += 1
		s.append(n % 256)
		n //= 256

	# Add to byte array
	s.append(n)

	# This can never be less that 1 bytes long
	if min_size < 1:
		min_size = 1

	# Satisify Minumim Length
	while len(s) < min_size + 1:
		s.append(0)
		s[0] += 1

	return bytes(s)

def get_hash_hex(header_bin, ntime, nonce):
	# Other algorythm types build upon SHA256
	header_hex = binascii.hexlify(header_bin) #Header in HEX
	hash_bin_sha256 = doublesha(''.join([ header_bin[i*4:i*4+4][::-1] for i in range(0, 20) ])) #Binary Block Hash
	
	# For other algorythm appened to the header_hex
	if settings.COINDAEMON_ALGO == 'scrypt' or settings.COINDAEMON_ALGO == 'scrypt-jane':
		header_hex = header_hex+"000000800000000000000000000000000000000000000000000000000000000000000000000000000000000080020000"
	elif settings.COINDAEMON_ALGO == 'quark':
		header_hex = header_hex+"000000800000000000000000000000000000000000000000000000000000000000000000000000000000000080020000"
	elif settings.COINDAEMON_ALGO == 'max':
		header_hex = header_hex+"000000800000000000000000000000000000000000000000000000000000000000000000000000000000000080020000"
	elif settings.COINDAEMON_ALGO == 'X11':
		header_hex = header_hex+"000000800000000000000000000000000000000000000000000000000000000000000000000000000000000080020000"
	elif settings.COINDAEMON_ALGO == 'X13':
		header_hex = header_hex+"000000800000000000000000000000000000000000000000000000000000000000000000000000000000000080020000"
	elif settings.COINDAEMON_ALGO == 'X15':
		header_hex = header_hex+"000000800000000000000000000000000000000000000000000000000000000000000000000000000000000080020000"
	elif settings.COINDAEMON_ALGO == 'riehash':
		header_hex = header_hex+"00000080000000000000000080030000"
	else: pass

	# 5. Get hash in binary format from header according to algorythm (by Reversing the header)
	if settings.COINDAEMON_ALGO == 'scrypt':
		hash_bin = algo_interface.make_header_hash_scrypt(''.join([ header_bin[i*4:i*4+4][::-1] for i in range(0, 20) ]))
	elif settings.COINDAEMON_ALGO  == 'scrypt-jane':
		if settings.SCRYPTJANE_NAME == 'vtc_scrypt':
			hash_bin = algo_interface.make_header_hash_vtc_scryptjane(''.join([ header_bin[i*4:i*4+4][::-1] for i in range(0, 20) ]))
		elif settings.SCRYPTJANE_NAME == 'mrc_scrypt':
			hash_bin = algo_interface.make_header_hash_mrc_scryptjane(''.join([ header_bin[i*4:i*4+4][::-1] for i in range(0, 20) ]), int(ntime, 16))
		elif settings.SCRYPTJANE_NAME == 'thor_scrypt':
			hash_bin = algo_interface.make_header_hash_thor_scryptjane(''.join([ header_bin[i*4:i*4+4][::-1] for i in range(0, 20) ]), int(ntime, 16))
		else: #yac_scrypt
			hash_bin = algo_interface.make_header_hash_yac_scryptjane(''.join([ header_bin[i*4:i*4+4][::-1] for i in range(0, 20) ]), int(ntime, 16))
	elif settings.COINDAEMON_ALGO == 'quark':
		hash_bin = algo_interface.make_header_hash_quark(''.join([ header_bin[i*4:i*4+4][::-1] for i in range(0, 20) ]))
	elif settings.COINDAEMON_ALGO == 'X11':
		hash_bin = algo_interface.make_header_hash_X11(''.join([ header_bin[i*4:i*4+4][::-1] for i in range(0, 20) ]))
	elif settings.COINDAEMON_ALGO == 'X13':
		hash_bin = algo_interface.make_header_hash_X13(''.join([ header_bin[i*4:i*4+4][::-1] for i in range(0, 20) ]))
	elif settings.COINDAEMON_ALGO == 'X15':
		hash_bin = algo_interface.make_header_hash_X15(''.join([ header_bin[i*4:i*4+4][::-1] for i in range(0, 20) ]))
	elif settings.COINDAEMON_ALGO == 'max':
		hash_bin = algo_interface.make_header_hash_max(''.join([ header_bin[i*4:i*4+4][::-1] for i in range(0, 20) ]))[0:33]
	elif settings.COINDAEMON_ALGO == 'skeinhash':
		hash_bin = algo_interface.make_header_hash_skeinhash(''.join([ header_bin[i*4:i*4+4][::-1] for i in range(0, 20) ]))
	elif settings.COINDAEMON_ALGO == 'keccak':
		hash_bin = algo_interface.make_header_hash_sha3(''.join([ header_bin[i*4:i*4+4][::-1] for i in range(0, 20) ]) + str(int(ntime, 16)))
	else: #SHA256
		hash_bin = hash_bin_sha256

	# The potential block hash in interger value
	hash_int = uint256_from_str(hash_bin)

	# Extra processing of the 'hash_int' variable for reihash
	if settings.COINDAEMON_ALGO == 'riehash':
		# This is kind of an ugly hack: we use hash_int to store the number of primes
		hash_int = algo_interface.make_header_hash_riehash(hash_int, job.target, int(nonce, 16) )

	# The potential block hash in HEX value (in both sha256 and the current coin algorythm)
	hash_hex_from_algo = "%064x" % hash_int
	hash_hex_from_sha256 = hash_bin_sha256[::-1].encode('hex_codec')

	# The block hash that will be checked against the network
	if settings.BLOCK_CHECK_ALGO_HASH:
		check_hash_hex = hash_hex_from_algo
	else:
		check_hash_hex = hash_hex_from_sha256

	# The block hash to be saved in the solutions column in the DB
	if settings.SOLUTION_BLOCK_HASH: 
		solution_hash_hex = hash_hex_from_algo
	else:
		solution_hash_hex = hash_hex_from_sha256

	return {'check_hex' : check_hash_hex, 'int' : hash_int, 'bin' : hash_bin, 'hex' : hash_hex_from_algo, 'header_hex' : header_hex, 'solution_hex' : solution_hash_hex}


def script_to_address(addr):
	d = address_to_pubkeyhash(addr)
	if not d:
		raise ValueError('invalid address')
	(ver, pubkeyhash) = d
	return b'\x76\xa9\x14' + pubkeyhash + b'\x88\xac'

def script_to_pubkey(key):
	if len(key) == 66: key = binascii.unhexlify(key)
	if len(key) != 33: raise Exception('Invalid Address')
	return b'\x21' + key + b'\xac'

def deserialize_header(header):
	nVersion = struct.unpack("<i", header.read(4))[0]
	hashPrevBlock = deser_uint256(header)
	hashMerkleRoot = deser_uint256(header)

	if settings.COINDAEMON_ALGO == 'riehash':
		nBits = struct.unpack("<I", header.read(4))[0]
		nTime = struct.unpack("<II", header.read(8))[0]
		nNonce = struct.unpack("<IIIIIIII", header.read(32))[0]
	else:
		nTime = struct.unpack("<I", header.read(4))[0]
		nBits = struct.unpack("<I", header.read(4))[0]
		nNonce = struct.unpack("<I", header.read(4))[0]

	return nVersion, hashPrevBlock, hashMerkleRoot, nTime, nBits, nNonce

def serialize_header_as_string(nVersion, prevhash_bin, merkle_root_int, ntime_bin, nBits, nonce_bin):
	header  = struct.pack(">i", nVersion)
	header += prevhash_bin
	header += ser_uint256_be(merkle_root_int)

	if settings.COINDAEMON_ALGO == 'riehash':
		header += struct.pack(">I", nBits)
		header += ntime_bin
	else:
		header += ntime_bin
		header += struct.pack(">I", nBits)

	header += nonce_bin

	return header

def serialize_header(nVersion, hashPrevBlock, hashMerkleRoot, nTime, nBits, nNonce):
	# Header structure according to algorythm

	# Common to all algos
	header = []
	header.append(struct.pack("<i", nVersion))
	header.append(ser_uint256(hashPrevBlock))
	header.append(ser_uint256(hashMerkleRoot))

	if settings.COINDAEMON_ALGO == 'riehash':
		header.append(struct.pack("<I", nBits))
		header.append(struct.pack("<Q", nTime))
		header.append(ser_uint256(nNonce))
	else:
		# The reset all use the same structure
		header.append(struct.pack("<I", nTime))
		header.append(struct.pack("<I", nBits))
		header.append(struct.pack("<I", nNonce))

	return header

def make_header_hash(nVersion, hashPrevBlock, hashMerkleRoot, nTime, nBits, nNonce, difficulty = None):
	header = serialize_header(nVersion, hashPrevBlock, hashMerkleRoot, nTime, nBits, nNonce)

	# Genorate's the header hash of a block according to selected algorythm
	if settings.COINDAEMON_ALGO == 'scrypt':
		header_hash = algo_interface.make_header_hash_scrypt(''.join(header))
	elif settings.COINDAEMON_ALGO  == 'scrypt-jane':
		if settings.SCRYPTJANE_NAME == 'vtc_scrypt':
			header_hash = algo_interface.make_header_hash_vtc_scryptjane(''.join(header))
		elif settings.SCRYPTJANE_NAME == 'mrc_scrypt':
			header_hash = algo_interface.make_header_hash_mrc_scryptjane(''.join(header), nTime)
		elif settings.SCRYPTJANE_NAME == 'thor_scrypt':
			header_hash = algo_interface.make_header_hash_thor_scryptjane(''.join(header), nTime)
		else: #yac_scrypt
			header_hash = algo_interface.make_header_hash_yac_scryptjane(''.join(header), nTime)
	elif settings.COINDAEMON_ALGO == 'quark':
		header_hash = algo_interface.make_header_hash_quark(''.join(header))
	elif settings.COINDAEMON_ALGO == 'X11':
		header_hash = algo_interface.make_header_hash_X11(''.join(header))
	elif settings.COINDAEMON_ALGO == 'X13':
		header_hash = algo_interface.make_header_hash_X13(''.join(header))
	elif settings.COINDAEMON_ALGO == 'X15':
		header_hash = algo_interface.make_header_hash_X15(''.join(header))
	elif settings.COINDAEMON_ALGO == 'skeinhash':
		header_hash = algo_interface.make_header_hash_skeinhash(''.join(header))
	elif settings.COINDAEMON_ALGO == 'riehash':
		# Riehash is so diffrent :-)
		header_hash = util.doublesha(''.join([ header[i*4:i*4+4][::-1] for i in range(0, 20) ]))
	elif settings.COINDAEMON_ALGO == 'max':
		header_hash = algo_interface.make_header_hash_max(''.join(header))
	elif settings.COINDAEMON_ALGO == 'keccak':
		header_hash = algo_interface.make_header_hash_sha3(''.join(header) + str(nTime))
	else: #SHA256
		header_hash = algo_interface.make_header_hash_sha256(''.join(header))

	if settings.COINDAEMON_ALGO == 'riehash':
		header_hash = algo_interface.make_header_hash_riehash(uint256_from_str(header_hash), nNonce, difficulty)
	else:
		header_hash = uint256_from_str(header_hash)

	return header_hash

def get_diff_target(difficulty):
	# Get the diff1 in HEX according to selected algorythm
	if settings.COINDAEMON_ALGO == 'scrypt':
		diff1 = algo_interface.get_diff_hex_scrypt()
	elif settings.COINDAEMON_ALGO  == 'scrypt-jane':
		if settings.SCRYPTJANE_NAME == 'vtc_scrypt':
			diff1 = algo_interface.get_diff_hex_vtc_scryptjane()
		elif settings.SCRYPTJANE_NAME == 'mrc_scrypt':
			diff1 = algo_interface.get_diff_hex_mrc_scryptjane()
		elif settings.SCRYPTJANE_NAME == 'thor_scrypt':
			diff1 = algo_interface.get_diff_hex_thor_scryptjane()
		else: #yac_scrypt
			diff1 = algo_interface.get_diff_hex_yac_scryptjane()
	elif settings.COINDAEMON_ALGO == 'quark':
		diff1 = algo_interface.get_diff_hex_quark()
	elif settings.COINDAEMON_ALGO == 'X11':
		diff1 = algo_interface.get_diff_hex_X11()
	elif settings.COINDAEMON_ALGO == 'X13':
		diff1 = algo_interface.get_diff_hex_X13()
	elif settings.COINDAEMON_ALGO == 'X15':
		diff1 = algo_interface.get_diff_hex_X15()
	elif settings.COINDAEMON_ALGO == 'skeinhash':
		diff1 = algo_interface.get_diff_hex_skeinhash()
	elif settings.COINDAEMON_ALGO == 'riehash':
		diff1 = algo_interface.get_diff_hex_riehash(difficulty)
	elif settings.COINDAEMON_ALGO == 'max':
		diff1 = algo_interface.get_diff_hex_max()
	elif settings.COINDAEMON_ALGO == 'keccak':
		diff1 = algo_interface.get_diff_hex_sha3()
	else: #SHA256
		diff1 = algo_interface.get_diff_hex_sha256()

	# Convert diff1 to target
	if settings.COINDAEMON_ALGO == 'riehash':
		# No conversion needed for this algo
		diff = diff1
	else: 
		diff = diff1 / difficulty

	return diff

def get_coinbase_hash(coinbase_bin):
	# Build coinbase based on selected algorythm
	if settings.COINDAEMON_ALGO == 'max':
		coinbase_hash = sha256(coinbase_bin).digest()
	elif settings.COINDAEMON_ALGO == 'keccak':
		coinbase_hash = sha256(coinbase_bin).digest()
	else: #all others
		coinbase_hash = doublesha(coinbase_bin)
	return coinbase_hash

def get_target(nBits):
	if settings.COINDAEMON_ALGO == 'riehash':
		target = settings.POOL_TARGET
	else:
		target = uint256_from_compact(nBits)

	return target

def get_target_rpc(nBits):
	if settings.COINDAEMON_ALGO == 'riehash':
		target = uint256_from_compact_alt(nBits)
	else:
		target = uint256_from_compact(nBits)

	return target

def get_ntime_bin(ntime):
	ntime_bin = binascii.unhexlify(ntime)
	if settings.COINDAEMON_ALGO == 'riehash':
		# Extra work required for this algo
		ntime_bin = (''.join([ ntime_bin[(1-i)*4:(1-i)*4+4] for i in range(0, 2) ]))

	return ntime_bin

def get_nonce_bin(nonce):
	nonce_bin = binascii.unhexlify(nonce)
	if settings.COINDAEMON_ALGO == 'riehash':
		# Extra work required for this algo
		nonce_bin = (''.join([ nonce_bin[(7-i)*4:(7-i)*4+4] for i in range(0, 8) ]))

	return nonce_bin

def check_nonce(nonce):
	# Initial value
	check_result = True
	message = ''

	if settings.COINDAEMON_ALGO == 'riehash':
		if len(nonce) != 64:
			check_result = False
			message = "Incorrect size of nonce. Expected 64 chars"
	else:
		if len(nonce) != 8:
			check_result = False
			message = "Incorrect size of nonce. Expected 8 chars"

	return check_result, message

def check_ntime(ntime):
	# Initial value
	check_result = True
	message = ''

	if settings.COINDAEMON_ALGO == 'riehash':
		if len(ntime) != 16:
			check_result = False
			message = "Incorrect size of ntime. Expected 16 chars"
	else:
		if len(ntime) != 8:
			check_result = False
			message = "Incorrect size of ntime. Expected 8 chars"

	return check_result, message

def check_header_target(header_hash_int, target):
	# Initial value
	check_result = True
	message = ''

	if settings.COINDAEMON_ALGO == 'riehash':
		if header_hash_int < target:
			check_result = False
			message = 'Share does not meet target'
	else:
		if header_hash_int > target:
			check_result = False
			message = 'Share is above target'

	return check_result, message

def check_above_yay_target(header_hash_int, target):
	# Mostly for debugging purposes
	# Valid only for certain alogrythms
	# Just a celebratory message that's being carried over

	# Initial value
	check_result = False
	message = ''

	if settings.COINDAEMON_ALGO == 'riehash':
		check_result = False
		message = 'Not valid for riehash'
	else:
		if header_hash_int <= target:
			check_result = True
			message = 'Yay, share with diff above 100000'

	return check_result, message

def is_block_candidate(header_hash_int, target):
	# Checks if this block hash is a block canidate
	isBlockCandidate = False

	if settings.COINDAEMON_ALGO == 'riehash':
		# For riehash, it's hard coded to 6 (may be adjustable later)
		if header_hash_int == 6:
			isBlockCandidate = True
	else:
		if header_hash_int <= target:
			isBlockCandidate = True

	return isBlockCandidate