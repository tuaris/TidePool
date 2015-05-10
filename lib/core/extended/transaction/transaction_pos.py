import struct
from lib.util import *

import lib.logger
from lib.core.standard import CTransaction, CTxIn, CTxOut
log = lib.logger.get_logger('transaction_pos')

# Transaction template for POS type blocks
class CPosTransaction(CTransaction):
	def __init__(self, ntime):
		super(CPosTransaction, self).__init__()
		log.info("Adding PoS support to transaction")
		# POS blocks have an 'nTime' field
		self.nTime = ntime

	def deserialize(self, f):
		self.nVersion = struct.unpack("<i", f.read(4))[0]
		self.nTime = struct.unpack("<i", f.read(4))[0]
		self.vin = deser_vector(f, CTxIn)
		self.vout = deser_vector(f, CTxOut)
		self.nLockTime = struct.unpack("<I", f.read(4))[0]
		self.sha256 = None

	def serialize(self):
		r = ""
		r += struct.pack("<i", self.nVersion)
		r += struct.pack("<i", self.nTime)
		r += ser_vector(self.vin)
		r += ser_vector(self.vout)
		r += struct.pack("<I", self.nLockTime)
		return r