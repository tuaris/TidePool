import lib.logger
log = lib.logger.get_logger('Factory')

# Factory interface  object
# Allows dynamic creation of basic components using a standard interface

class Factory(object):
	def __init__(self, coinbaser, coinbase_factory, transaction_factory, block_factory):
		# This factory makes objects based on the coinbaser
		self.coinbaser = coinbaser

		# This factory is made up from smaller factories (sub-factories)
		self.coinbase_factory = coinbase_factory
		self.transaction_factory = transaction_factory
		self.block_factory = block_factory

	def new_coinbase(self, data):
		log.debug("Requesting new Coinbase Obejct")
		# Create a new coinbase
		coinbase = self.coinbase_factory.new_coinbase(data)

		log.debug("Completing Coinbase Constructions")
		# Set required paramaters
		coinbase.set_extranonce(self.coinbaser.get_extranonce_type(), self.coinbaser.get_extranonce_placeholder(), self.coinbaser.get_extranonce_size())
		coinbase.set_script_pubkey(self.coinbaser.get_script_pubkey())
		coinbase.set_extra_data(self.coinbaser.get_coinbase_data() + self.coinbaser.get_coinbase_extras())

		# Ready
		log.debug("Coinbase Construction Complete")
		return coinbase

	def new_transaction(self, data = None):
		if data is None:
			# An "empty" transaction
			log.debug("Emtpy Transaction Requested")
			return self.transaction_factory.new_transaction()
		else:
			# A Transaction filled from exiting data
			log.debug("Filling Transaction from provided data")
			return self.transaction_factory.build_transaction(data)

	def new_block(self, data):
		# Not much to do here
		return self.block_factory.new_block(data)