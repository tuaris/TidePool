import struct
import binascii
from Crypto.Hash import SHA256

from lib.util import *

class COutPoint(object):
	def __init__(self):
		self.hash = 0
		self.n = 0
	def deserialize(self, f):
		self.hash = deser_uint256(f)
		self.n = struct.unpack("<I", f.read(4))[0]
	def serialize(self):
		r = ""
		r += ser_uint256(self.hash)
		r += struct.pack("<I", self.n)
		return r
	def __repr__(self):
		return "COutPoint(hash=%064x n=%i)" % (self.hash, self.n)

class CTxIn(object):
	def __init__(self):
		self.prevout = COutPoint()
		self.scriptSig = ""
		self.nSequence = 0
	def deserialize(self, f):
		self.prevout = COutPoint()
		self.prevout.deserialize(f)
		self.scriptSig = deser_string(f)
		self.nSequence = struct.unpack("<I", f.read(4))[0]
	def serialize(self):
		r = ""
		r += self.prevout.serialize()
		r += ser_string(self.scriptSig)
		r += struct.pack("<I", self.nSequence)
		return r
	def __repr__(self):
		return "CTxIn(prevout=%s scriptSig=%s nSequence=%i)" % (repr(self.prevout), binascii.hexlify(self.scriptSig), self.nSequence)

class CTxOut(object):
	def __init__(self):
		self.nValue = 0
		self.scriptPubKey = ""
	def deserialize(self, f):
		self.nValue = struct.unpack("<q", f.read(8))[0]
		self.scriptPubKey = deser_string(f)
	def serialize(self):
		r = ""
		r += struct.pack("<q", self.nValue)
		r += ser_string(self.scriptPubKey)
		return r
	def __repr__(self):
		return "CTxOut(nValue=%i.%08i scriptPubKey=%s)" % (self.nValue // 100000000, self.nValue % 100000000, binascii.hexlify(self.scriptPubKey))

class CTransaction(object):
	def __init__(self):
		#Basics
		self.nVersion = 1
		self.vin = []
		self.vout = []
		self.nLockTime = 0
		self.sha256 = None

	def deserialize(self, f):
		self.nVersion = struct.unpack("<i", f.read(4))[0]
		self.vin = deser_vector(f, CTxIn)
		self.vout = deser_vector(f, CTxOut)
		self.nLockTime = struct.unpack("<I", f.read(4))[0]
		self.sha256 = None

	def serialize(self):
		r = ""
		r += struct.pack("<i", self.nVersion)
		r += ser_vector(self.vin)
		r += ser_vector(self.vout)
		r += struct.pack("<I", self.nLockTime)
		return r
 
	def calc_sha256(self):
		if self.sha256 is None:
			self.sha256 = uint256_from_str(SHA256.new(SHA256.new(self.serialize()).digest()).digest())
		return self.sha256
	
	def is_valid(self):
		self.calc_sha256()
		for tout in self.vout:
			if tout.nValue < 0 or tout.nValue > 21000000L * 100000000L:
				return False
		return True
	def __repr__(self):
		return "CTransaction(nVersion=%i vin=%s vout=%s nLockTime=%i)" % (self.nVersion, repr(self.vin), repr(self.vout), self.nLockTime)
