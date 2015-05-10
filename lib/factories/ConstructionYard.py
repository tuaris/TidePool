import coinbase_factories
import transaction_factories
import block_factories

# The ConstructionYard allows us to build the sub-factories for the Main Factory 'a la carte'
class ConstructionYard(object):
	def __init__(self):
		self.coinbase_factory = ''
		self.block_factory = ''
		self.transaction_factory = ''

		# Automaticly figure out what type of factories to create
		self._architect()

	def build_factory(self, type):
		if type == 'coinbase':
			return self.build_coinbase_factory()
		elif type == 'transaction':
			return self.build_transaction_factory()
		elif type == 'block':
			return self.build_block_factory()
		else:
			raise Exception("Can't build factory of type '%s'" % (type))

	def build_coinbase_factory(self):
		return self.coinbase_factory

	def build_transaction_factory(self):
		return self.transaction_factory

	def build_block_factory(self):
		return self.block_factory

	def _architect(self):
		import lib.settings as settings
		# Which type of factories should be used based on settings.
		if getattr(settings, 'COINDAEMON_Reward') == 'POW' and getattr(settings, 'COINDAEMON_TX_MSG') == False:
			# Basic
			if getattr(settings, 'MASTERNODE_PAYMENTS') == True:
				self.coinbase_factory =  coinbase_factories.MasterNodeCoinbaseFactory(getattr(settings, 'MASTERNODE_PERCENT'))
			else:
				self.coinbase_factory =  coinbase_factories.CoinbaseFactory()

			self.transaction_factory =  transaction_factories.TransactionFactory()
			self.block_factory =  block_factories.BlockFactory()
		elif getattr(settings, 'COINDAEMON_Reward') == 'POW' and getattr(settings, 'COINDAEMON_TX_MSG') == True:
			# Basic with Messaging
			self.coinbase_factory =  coinbase_factories.CoinbaseFactoryTxMessage(getattr(settings, 'Tx_Message'))
			self.transaction_factory =  transaction_factories.TransactionMessageFactory()
			self.block_factory =  block_factories.BlockFactory()
		elif getattr(settings, 'COINDAEMON_Reward') == 'POS' and getattr(settings, 'COINDAEMON_TX_MSG') == False:
			# PoS Block, no Messaging
			self.coinbase_factory =  coinbase_factories.PoSCoinbaseFactory()
			self.transaction_factory =  transaction_factories.PoSTransactionFactory()
			self.block_factory =  block_factories.PoSBlockFactory()
		elif getattr(settings, 'COINDAEMON_Reward') == 'POS' and getattr(settings, 'COINDAEMON_TX_MSG') == True:
			# PoS Block, with Messaging
			self.coinbase_factory =  coinbase_factories.PoSCoinbaseFactoryTxMessage(getattr(settings, 'Tx_Message'))
			self.transaction_factory =  transaction_factories.PoSTransactionMessageFactory()
			self.block_factory =  block_factories.PoSBlockFactory()

