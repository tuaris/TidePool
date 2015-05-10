import lib.util as util

from lib.core.standard import Coinbase
from lib.core.standard import CTxOut

import lib.logger
log = lib.logger.get_logger('coinbase_masternode')

class MasterNodeCoinbase(Coinbase):

	def __init__(self, _transaction, _height, _value, _flags):
		super(MasterNodeCoinbase, self).__init__(_transaction, _height, _value, _flags)
		log.debug("Adding MasterNode requirements to coinbase")

		# Additional fields for MasterNode type coinbase
		self.payee = None
		self.payee_amount = 0

	def set_masternode_payment(self, _payee, _amount):
		#It's possible that it could be empty.
		if _payee is not None and _payee != '':
			self.payee = util.script_to_address(_payee)
			self.payee_amount = _amount
			# Deduct the payee amount from the block reward
			self.nValue -=  self.payee_amount

	def generate_txout(self):
		super(MasterNodeCoinbase, self).generate_txout()

		# Add the payee if one exists
		if self.payee_amount > 0 and self.payee is not None:
			log.debug("Appending Payee to Outputs")
			tx_out2 = CTxOut()
			tx_out2.nValue = self.payee_amount
			tx_out2.scriptPubKey = self.payee

			self.Transaction.vout.append(tx_out2)