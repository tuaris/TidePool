import struct
from lib.util import *

class CMasterNodeVote(object):
	def __init__(self):
		self.blockHeight = 0
		self.scriptPubKey = ""
		self.votes = 0
	def deserialize(self, f):
		self.blockHeight = struct.unpack("<q", f.read(8))[0]
		self.scriptPubKey = deser_string(f)
		self.votes = struct.unpack("<i", f.read(4))[0]
	def serialize(self):
		r = ""
		r += struct.pack("<q", self.blockHeight)
		r += ser_string(self.scriptPubKey)
		r += struct.pack("<i", self.votes)
		return r
	def __repr__(self):
		return "CMasterNodeVote(blockHeight=%d scriptPubKey=%s, votes=%d)" % (self.blockHeight, binascii.hexlify(self.scriptPubKey), self.votes)