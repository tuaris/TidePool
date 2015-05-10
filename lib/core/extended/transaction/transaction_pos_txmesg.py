import struct
from lib.util import *

import lib.logger
from lib.core.standard import CTransaction, CTxIn, CTxOut
log = lib.logger.get_logger('transaction_pos_txmsg')

# Transaction template for POS type blocks
class CPosTransactionMessage(CTransaction):
	def __init__(self, Tx_Message, ntime):
		super(CPosTransactionMessage, self).__init__()
		log.info("Adding PoS and message support to transaction")
		# Support for Transaction message is version 2
		self.nVersion = 2
		self.strTxComment = Tx_Message
		# POS blocks have an 'nTime' field
		self.nTime = ntime

	def deserialize(self, f):
		self.nVersion = struct.unpack("<i", f.read(4))[0]
		self.nTime = struct.unpack("<i", f.read(4))[0]
		self.vin = deser_vector(f, CTxIn)
		self.vout = deser_vector(f, CTxOut)
		self.nLockTime = struct.unpack("<I", f.read(4))[0]
		self.sha256 = None
		self.strTxComment = deser_string(f)

	def serialize(self):
		r = ""
		r += struct.pack("<i", self.nVersion)
		r += struct.pack("<i", self.nTime)
		r += ser_vector(self.vin)
		r += ser_vector(self.vout)
		r += struct.pack("<I", self.nLockTime)
		r += ser_string(self.strTxComment)
		return r