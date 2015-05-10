import binascii
import lib.util as util

from transaction import CTxIn, CTxOut

import lib.logger
log = lib.logger.get_logger('coinbase')

# Basic Coinbase with single input and single output
class Coinbase(object):
	'''Construct special transaction used for coinbase tx.
	It also implements quick serialization using pre-cached
	scriptSig template.'''

	def __init__(self, _transaction, _height, _value, _flags):
		log.debug("Initializing Coinbase Transaction: %s init called" % type(self))

		# Empty Transaction object
		self.Transaction = _transaction

		# Coinbase basic static paramaters
		self.nHeight = _height
		self.nValue = _value
		self.Flags = _flags

		# Additional Dynamic Paramaters
		self.ScriptPubkey = ''
		self.Timestamp = 0
		self.ExData = ''

		# Initialize Extranonce items ans empty
		self.extranonce_type = ''
		self.extranonce_placeholder = ''
		self.extranonce_size = 0

		self._scriptSig_template = ''

		# Cache the serialized coinbase tx
		self.serialized = ''

	def set_extranonce(self, extranonce_type, extranonce_placeholder, extranonce_size):
		# 'extranonce_size' should be automaticly calculated from 'extranonce_type' and 'extranonce_placeholder'
		if len(extranonce_placeholder) != extranonce_size:
			raise Exception("Extranonce placeholder don't match expected length!")

		self.extranonce_type = extranonce_type
		self.extranonce_placeholder = extranonce_placeholder
		self.extranonce_size = extranonce_size

		log.debug("Extranonce Placeholder: %s" % binascii.hexlify(self.extranonce_placeholder))
		log.debug("Extranonce Type: %s" % extranonce_type)
		log.debug("Extranonce Size: %i" % extranonce_size)

	def set_script_pubkey(self, script_pubkey):
		log.debug("Script Pubkey: %s" % binascii.hexlify(script_pubkey))
		self.ScriptPubkey = script_pubkey

	def set_timestamp(self, timestamp):
		log.debug("Timestamp: %i" % timestamp)
		self.Timestamp = int(timestamp)

	def set_extra_data(self, additional_data):
		log.debug("Additional Data: %s" % additional_data)
		self.ExData = additional_data

	def generate_txin(self):
		log.info("Generating TXin")
		if self.extranonce_placeholder == '':
			raise Exception("Extranonce not setup")

		# Script Sig Template
		self._scriptSig_template = (util.encode_coinbase_nheight(self.nHeight) + binascii.unhexlify(self.Flags) + util.ser_number(self.Timestamp) + chr(self.extranonce_size), util.ser_string(self.ExData))

		# Reset vin
		self.Transaction.vin = []

		# Reward
		tx_in = CTxIn()
		tx_in.prevout.hash = 0L
		tx_in.prevout.n = 2**32-1
		tx_in.scriptSig = self._scriptSig_template[0] + self.extranonce_placeholder + self._scriptSig_template[1]
		self.Transaction.vin.append(tx_in)

	def generate_txout(self):
		log.info("Generating TXout")
		# Reset vout
		self.Transaction.vout = []
		# Single Output
		tx_out = CTxOut()
		tx_out.nValue = self.nValue
		tx_out.scriptPubKey = self.ScriptPubkey
		self.Transaction.vout.append(tx_out)

	def update_extranonce(self, extranonce):
		if len(extranonce) != self.extranonce_size:
			raise Exception("Incorrect extranonce size")

		(part1, part2) = self._scriptSig_template
		self.Transaction.vin[0].scriptSig = part1 + extranonce + part2

	def get_tx(self):
		return self.Transaction

	def serialize(self):
		if self.serialized == '':
			log.info("Generating Coinbase TX")
			# Generate tx_in and tx_out first
			self.generate_txin()
			self.generate_txout()

			log.info("Serializing Coinbase TX")
			serialized_tx = self.Transaction.serialize()
			log.debug("Serialized Tx: %s" % binascii.hexlify(serialized_tx))

			# Cache the result
			self.serialized = serialized_tx.split(self.extranonce_placeholder)

		log.debug("Serialized Tx: PART1: %s | PART2: %s" % (binascii.hexlify(self.serialized[0]), binascii.hexlify(self.serialized[0])))

		# Two parts of serialized coinbase, just put part1 + extranonce + part2 to have final serialized tx
		return self.serialized

	def get_serialized(self):
		return self.serialized