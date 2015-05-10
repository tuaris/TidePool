from Crypto.Hash import SHA256
from lib.util import *

from lib.core.standard import CBlock
import lib.logger

class CPosBlock(CBlock):
	def __init__(self):
		super(CPosBlock, self).__init__()
		# POS Type block have a signature field
		self.signature = b""

	def deserialize(self, f):
		super(CPosBlock, self).deserialize(f)
		self.signature = deser_string(f)

	def serialize(self):
		# Header
		r = serialize_header(self.nVersion, self.hashPrevBlock, self.hashMerkleRoot, self.nTime, self.nBits, self.nNonce)
		# Transactions
		r.append(ser_vector(self.vtx))
		# Singnature
		r.append(ser_string(self.signature))
		return ''.join(r)