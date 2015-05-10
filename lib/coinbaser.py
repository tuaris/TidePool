from twisted.internet import defer

import struct
import lib.util as util
import lib.settings as settings

import lib.logger
log = lib.logger.get_logger('coinbase')

class Coinbaser(object):
	'''This very simple coinbaser uses constant bitcoin address
	for all generated blocks.'''

	def __init__(self, bitcoin_rpc, address):
		log.debug("Got to coinbaser")
		# Fire Callback when the coinbaser is ready
		self.on_load = defer.Deferred()

		self.address = address
		self.pubkey = None

		# Extra Nonce
		self.extranonce_type = '>Q'
		self.extranonce_placeholder = struct.pack(self.extranonce_type, int('f000000ff111111f', 16))
		self.extranonce_size = struct.calcsize(self.extranonce_type)

		# We need to check if pool can use this address
		self.is_valid = False 

		self.bitcoin_rpc = bitcoin_rpc
		self._validate()

	def _validate(self):
		d = self.bitcoin_rpc.validateaddress(self.address)
		d.addCallback(self._address_check)
		d.addErrback(self._failure)

	def _address_check(self, result):
		if result['isvalid'] == True:
			log.debug("Is Valid = %s" % result['isvalid'])

			if 'isscript' in result:
				log.debug("Is Script = %s" % result['isscript'])

			if 'iscompressed' in result:
				log.debug("Is Compressed = %s " % result['iscompressed'])

			if 'account' in result:
				log.debug("Account = %s " % result['account'])

			if 'address' in result:
				self.address = result['address']
				log.debug("Address = %s " % result['address'])

			if 'pubkey' in result:
				self.pubkey = result['pubkey']
				log.debug("PubKey = %s " % result['pubkey'])

			# Local Wallet
			if result['ismine']:
				self.is_valid = True
				log.info("Local wallet address '%s' is valid" % self.address)

				if not self.on_load.called:
					self.on_load.callback(True)

			# Non-Local Wallet
			elif settings.ALLOW_NONLOCAL_WALLET == True :
				self.is_valid = True
				log.warning("!!! Wallet address '%s' is valid BUT it is not local" % self.address)

				if not self.on_load.called:
					 self.on_load.callback(True)

		else:
			self.is_valid = False
			log.exception("Wallet address '%s' is NOT valid!" % self.address)

	def _failure(self, failure):
		log.error("Cannot validate Wallet address '%s'" % self.address)
		raise

	def get_script_pubkey(self):
		self._validate()
		if not self.is_valid:
			# Try again, maybe coind was down?
			self._validate()
			raise Exception("Wallet Address is Wrong")

		if self.pubkey == None:
			return util.script_to_address(self.address)
		else:
			return util.script_to_pubkey(self.pubkey)


	def get_coinbase_data(self):
		return ''

	def get_coinbase_extras(self):
		return getattr(settings, 'COINBASE_EXTRAS')

	def get_extranonce_size(self):
		return self.extranonce_size

	def get_extranonce_type(self):
		return self.extranonce_type

	def get_extranonce_placeholder(self):
		return self.extranonce_placeholder