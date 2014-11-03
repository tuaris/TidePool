import lib.settings as settings
from hashlib import sha256
from Crypto.Hash import SHA256
from sha3 import sha3_256
import ltc_scrypt.ltc_scrypt as ltc_scrypt
import yac_scrypt.yac_scrypt as yac_scrypt
import mrc_scrypt.mrc_scrypt as mrc_scrypt
import thor_scrypt.thor_scrypt as thor_scrypt
import vtc_scrypt.vtc_scrypt as vtc_scrypt
import quark.quark_hash as quark_hash
import max_hash.max_hash as max_hash
import X11.X11_hash as X11_hash
import X13.X13_hash as X13_hash
import X15.X15_hash as X15_hash
import sha3
import skeinhash

def make_header_hash_sha256(header):
	return SHA256.new(SHA256.new(header).digest()).digest()

def make_header_hash_scrypt(header):
	return ltc_scrypt.getPoWHash(header)

def make_header_hash_vtc_scryptjane(header):
	return vtc_scrypt.getPoWHash(header)

def make_header_hash_yac_scryptjane(header, nTime=None):
	return yac_scrypt.getPoWHash(header, nTime)

def make_header_hash_mrc_scryptjane(header, nTime=None):
	return mrc_scrypt.getPoWHash(header, nTime)

def make_header_hash_thor_scryptjane(header, nTime=None):
	return thor_scrypt.getPoWHash(header, nTime)

def make_header_hash_quark(header):
	return quark_hash.getPoWHash(header)

def make_header_hash_X11(header):
	return X11_hash.getPoWHash(header)

def make_header_hash_X13(header):
	return X13_hash.getPoWHash(header)

def make_header_hash_X15(header):
	return X15_hash.getPoWHash(header)

def make_header_hash_skeinhash(header):
	return skeinhash.skeinhash(header)

def make_header_hash_max(header):
	#return max_hash.getPoWHash(header)
	return sha3_256(header).digest()

def make_header_hash_sha3(header):
	s = sha3.SHA3256()
	s.update(header)
	# hash_bin_temp = s.hexdigest()
	# s = sha3.SHA3256()
	# s.update(hash_bin_temp)
	return s.hexdigest()



# MAX Difficulty aka. diff1, found in block.nBits
def get_diff_hex_sha256():
	return 0x00000000ffff0000000000000000000000000000000000000000000000000000

def get_diff_hex_scrypt():
	return 0x0000ffff00000000000000000000000000000000000000000000000000000000

def get_diff_hex_vtc_scryptjane():
	return 0x0000ffff00000000000000000000000000000000000000000000000000000000

def get_diff_hex_yac_scryptjane():
	return 0x0000ffff00000000000000000000000000000000000000000000000000000000

def get_diff_hex_mrc_scryptjane():
	return 0x0000ffff00000000000000000000000000000000000000000000000000000000

def get_diff_hex_thor_scryptjane():
	return 0x0000ffff00000000000000000000000000000000000000000000000000000000

def get_diff_hex_quark():
	return 0x000000ffff000000000000000000000000000000000000000000000000000000

def get_diff_hex_X11():
	return 0x0000ffff00000000000000000000000000000000000000000000000000000000

def get_diff_hex_X13():
	return 0x00000ffff0000000000000000000000000000000000000000000000000000000

def get_diff_hex_X15():
	return 0x00000ffff0000000000000000000000000000000000000000000000000000000

def get_diff_hex_skeinhash():
	return 0x00000000ffff0000000000000000000000000000000000000000000000000000

def get_diff_hex_max():
	return 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00000000

def get_diff_hex_sha3():
	return 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00000000
