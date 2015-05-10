import struct
from lib.util import *

import lib.logger
from lib.core.standard import CTransaction
log = lib.logger.get_logger('transaction_txmsg')

# Transaction template for POS type blocks
class CTransactionMessage(CTransaction):
	def __init__(self, Tx_Message):
		super(CTransactionMessage, self).__init__()
		log.info("Adding message support to transaction")
		# Support for Transaction message is version 2
		self.nVersion = 2
		self.strTxComment = Tx_Message

	def deserialize(self, f):
		super(CTransactionMessage, self).deserialize(f)
		self.strTxComment = deser_string(f)

	def serialize(self):
		r = super(CTransactionMessage, self).serialize()
		r += ser_string(self.strTxComment)
		return r