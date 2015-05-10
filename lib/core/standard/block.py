from Crypto.Hash import SHA256
from lib.util import *

class CBlock(object):
	def __init__(self):
		self.nVersion = 1
		self.hashPrevBlock = 0
		self.hashMerkleRoot = 0
		self.nTime = 0
		self.nBits = 0
		self.nNonce = 0
		self.vtx = []
		self.header = None

	# TODO: Move 'deserialize_header' out of the util.py object
	def deserialize(self, f):
		# Note: This function is not used by Tidepool
		self.nVersion, self.hashPrevBlock, self.hashMerkleRoot, self.nTime, self.nBits, self.nNonce = deserialize_header(f)
		# Transactions are not deserialized!
		#self.transaction_factory.new_transaction()
		#self.vtx = deser_vector(f)

	def serialize(self):
		# Header
		r = serialize_header(self.nVersion, self.hashPrevBlock, self.hashMerkleRoot, self.nTime, self.nBits, self.nNonce)
		# Transactions
		r.append(ser_vector(self.vtx))
		return ''.join(r)

	def calc(self, difficulty = None):
		if self.header is None:
			self.header = make_header_hash(self.nVersion, self.hashPrevBlock, self.hashMerkleRoot, self.nTime, self.nBits, self.nNonce, difficulty)
		return self.header

	def is_valid(self, difficulty = None):
		# Calculate the Header Hash
		self.calc(difficulty)

		# Get Target
		target = get_target(self.nBits)

		# Check
		check_result, message = check_header_target(self.header, target)
		if not check_result:
			return False

		hashes = []
		for tx in self.vtx:
			tx.sha256 = None
			if not tx.is_valid():
				return False
			tx.calc_sha256()
			hashes.append(ser_uint256(tx.sha256))

		while len(hashes) > 1:
			newhashes = []
			for i in xrange(0, len(hashes), 2):
				i2 = min(i+1, len(hashes)-1)
				newhashes.append(SHA256.new(SHA256.new(hashes[i] + hashes[i2]).digest()).digest())
			hashes = newhashes

		if uint256_from_str(hashes[0]) != self.hashMerkleRoot:
			return False
		return True

	def __repr__(self):
		return "CBlock(nVersion=%i hashPrevBlock=%064x hashMerkleRoot=%064x nTime=%s nBits=%08x nNonce=%08x vtx=%s)" % (self.nVersion, self.hashPrevBlock, self.hashMerkleRoot, time.ctime(self.nTime), self.nBits, self.nNonce, repr(self.vtx))
