import StringIO
import binascii
import struct

import lib.util as util

from lib.core.standard import MerkleTree

import lib.logger
log = lib.logger.get_logger('block_template')

class BlockTemplate(object):
	'''Template is used for generating new jobs for clients.
	Let's iterate extranonce1, extranonce2, ntime and nonce
	to find out valid coin block!'''

	def __init__(self, factory, timestamper, job_id):
		log.debug("Got To Block Template")

		# Component Factory to facilitate creattion of Transaction, Block, and, Coinbase objects
		self.factory = factory

		self.job_id = job_id 
		self.timestamper = timestamper

		self.prevhash_bin = '' # reversed binary form of prevhash
		self.prevhash_hex = ''
		self.timedelta = 0
		self.curtime = 0
		self.target = 0
		self.height = 0

		# Basic Componets
		self.merkletree = None
		self.coinbase = None
		self.block = None

		self.broadcast_args = []

		# List of 4-tuples (extranonce1, extranonce2, ntime, nonce)
		# registers already submitted and checked shares
		# There may be registered also invalid shares inside!
		self.submits = []

	def fill_from_rpc(self, data):
		'''Convert getblocktemplate result into Template instance'''
		log.debug("Filling RPC data")

		# Height
		self.height = data['height']

		# Merkle Tree
		self.hash_merkletree(data['transactions'])

		# Coinbase Transaction
		self.generate_coinbase_tx(data)

		# Block Header
		self.generate_block_header(data)

		# Transactions
		self.stack_transactions(data['transactions'])

		# Time and diffrence
		self.curtime = data['curtime']
		self.timedelta = self.curtime - int(self.timestamper.time()) 

		# Target
		self.target = util.get_target_rpc(self.block.nBits)

		# Reversed prevhash
		self.prevhash_bin = binascii.unhexlify(util.reverse_hash(data['previousblockhash']))
		self.prevhash_hex = "%064x" % self.block.hashPrevBlock

		# Prepare push notification for miners
		self.broadcast_args = self.build_broadcast_args()

	def hash_merkletree(self, transactions):
		txhashes = [None] + [ util.ser_uint256(int(t['hash'], 16)) for t in transactions ]
		self.merkletree = MerkleTree(txhashes)

	def generate_coinbase_tx(self, data):
		log.debug("Generating Coinbase TX")
		self.coinbase = self.factory.new_coinbase(data)
		self.coinbase.set_timestamp(self.timestamper.time())
		self.coinbase.serialize()

	def generate_block_header(self, data):
		log.debug("Generating Block Header")
		self.block = self.factory.new_block(data)

	def stack_transactions(self, transactions):
		# First add the coinbase tx
		self.block.vtx = [ self.coinbase.get_tx(), ]
		# Then add the rest
		for tx in transactions:
			# Get a new Tx and fill in with data
			t = self.factory.new_transaction(StringIO.StringIO(binascii.unhexlify(tx['data'])))
			log.debug("Added TX: %s" % t)
			# Append to tranasctions
			self.block.vtx.append(t)
			log.debug("Total TX: %i" % len(self.block.vtx))

	def register_submit(self, extranonce1, extranonce2, ntime, nonce):
		'''Client submitted some solution. Let's register it to
		prevent double submissions.'''

		t = (extranonce1, extranonce2, ntime, nonce)
		if t not in self.submits:
			self.submits.append(t)
			return True
		return False

	def build_broadcast_args(self):
		'''Build parameters of mining.notify call. All clients
		may receive the same params, because they include
		their unique extranonce1 into the coinbase, so every
		coinbase_hash (and then merkle_root) will be unique as well.'''
		job_id = self.job_id
		prevhash = binascii.hexlify(self.prevhash_bin)
		(coinb1, coinb2) = [ binascii.hexlify(x) for x in self.coinbase.get_serialized() ]
		merkle_branch = [ binascii.hexlify(x) for x in self.merkletree._steps ]
		version = binascii.hexlify(struct.pack(">i", self.block.nVersion))
		nbits = binascii.hexlify(struct.pack(">I", self.block.nBits))
		ntime = binascii.hexlify(struct.pack(">I", self.curtime))
		clean_jobs = True

		return (job_id, prevhash, coinb1, coinb2, merkle_branch, version, nbits, ntime, clean_jobs)

	def serialize_coinbase(self, extranonce1, extranonce2):
		'''Serialize coinbase with given extranonce1 and extranonce2
		in binary form'''
		(part1, part2) = self.coinbase.get_serialized()
		return part1 + extranonce1 + extranonce2 + part2

	def check_ntime(self, ntime, ntime_age):
		'''Check for ntime restrictions.'''
		if ntime < self.curtime:
			return False

		if ntime > (self.timestamper.time() + ntime_age):
			# Be strict on ntime into the near future
			# may be unnecessary
			return False

		return True

	def serialize_header(self, merkle_root_int, ntime_bin, nonce_bin):
		'''Serialize header for calculating block hash'''
		r = util.serialize_header_as_string(self.block.nVersion, self.prevhash_bin, merkle_root_int, ntime_bin, self.block.nBits, nonce_bin)
		return r

	def serialize(self):
		return self.block.serialize()

	def is_valid(self, difficulty):
		return self.block.is_valid(difficulty)

	def finalize(self, merkle_root_int, extranonce1_bin, extranonce2_bin, ntime, nonce):
		'''Take all parameters required to compile block candidate.
		self.is_valid() should return True then...'''

		# Basic Params
		self.block.hashMerkleRoot = merkle_root_int
		self.block.nTime = ntime
		self.block.nNonce = nonce

		# Modify the coibase transaction in the block with new extranonce
		self.coinbase.update_extranonce(extranonce1_bin + extranonce2_bin)
		self.block.vtx[0] = self.coinbase.get_tx()
		log.debug('Final Coinbase Tx => %s' % self.block.vtx[0])
		log.debug('Final Coinbase Tx Serialzed = %s' % binascii.hexlify(self.block.vtx[0].serialize()))

		# Since We changed block parameters, let's reset sha256 cache
		self.sha256 = None
