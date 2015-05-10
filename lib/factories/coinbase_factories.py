from lib.core.standard import CTransaction
from lib.core.extended import CPosTransaction
from lib.core.extended import CPosTransactionMessage
from lib.core.extended import CTransactionMessage

from lib.core.standard import Coinbase
from lib.core.extended import MasterNodeCoinbase

import lib.logger
log = lib.logger.get_logger('coinbase_factory')

class CoinbaseFactory(object):
	def new_coinbase(self, data):

		# Transaction and data elements required to generate a coinbase
		self.transaction = CTransaction()
		self.data = data

		# Generate the new coinbase from transaction and data
		log.debug("Coinbase Build in Progress...")
		coinbase = self._generate_coinbase()

		# Return coinbase
		log.debug("Coinbase Ready")
		return coinbase

	def _generate_coinbase(self):
		log.debug("Creating a new Coinbase")
		return Coinbase(self.transaction, self.data['height'], self.data['coinbasevalue'], self.data['coinbaseaux']['flags'])

class PoSCoinbaseFactory(CoinbaseFactory):
	def new_coinbase(self, data):

		# Transaction and data elements required to generate a coinbase
		self.transaction = CPosTransaction(data['curtime'])
		self.data = data

		# Generate the new coinbase from transaction and data
		coinbase = self._generate_coinbase()

		# Return coinbase
		return coinbase

class CoinbaseFactoryTxMessage(CoinbaseFactory):
	def __init__(self, TxMessage):
		self.TxMessage = TxMessage

	def new_coinbase(self, data):

		# Transaction and data elements required to generate a coinbase
		self.transaction = CTransactionMessage(self.TxMessage)
		self.data = data

		# Generate the new coinbase from transaction and data
		coinbase = self._generate_coinbase()

		# Return coinbase
		return coinbase

class PoSCoinbaseFactoryTxMessage(CoinbaseFactoryTxMessage):
	def new_coinbase(self, data):
		# Transaction and data elements required to generate a coinbase
		self.transaction = CPosTransactionMessage(self.TxMessage, data['curtime'])
		self.data = data

		# Generate the new coinbase from transaction and data
		coinbase = self._generate_coinbase()

		# Return coinbase
		return coinbase

class MasterNodeCoinbaseFactory(CoinbaseFactory):
	def __init__(self, mn_percentage):
		self.MasternodeDefaultPercentage = mn_percentage

	def new_coinbase(self, data):
		coinbase = super(MasterNodeCoinbaseFactory, self).new_coinbase(data)

		# MasterNode Payment amount
		coinbase.set_masternode_payment(data['payee'], data.get('payee_amount', data['coinbasevalue'] * self.MasternodeDefaultPercentage))

		return coinbase

	def _generate_coinbase(self):
		return MasterNodeCoinbase(self.transaction, self.data['height'], self.data['coinbasevalue'], self.data['coinbaseaux']['flags'])
