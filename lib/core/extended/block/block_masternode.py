from Crypto.Hash import SHA256
import StringIO
import binascii
from lib.util import *

from lib.core.standard import CBlock
from lib.core.extended.other import CMasterNodeVote

class CMasterNodeBlock(CBlock):
	def __init__(self):
		super(CMasterNodeBlock, self).__init__()
		# MN Voting Type blocks
		self.vmn = []
		self.masternode_payments = False

	def deserialize(self, f):
		super(CMasterNodeBlock, self).deserialize(f)

		if self.masternode_payments: 
			self.vmn = deser_vector(f, CMasterNodeVote)

	def serialize(self):
		r = super(CMasterNodeBlock, self).serialize()

		if self.masternode_payments: 
			r.join(ser_vector(self.vmn))

		return ''.join(r)

	def set_votes(self, votes):
		# Add in Masternode Extras
		for vote in data['votes']:
			v = CMasterNodeVote()
			v.deserialize(StringIO.StringIO(binascii.unhexlify(vote)))
			self.vmn.append(v)

	def set_masternode_payments(self, isEnabled):
		self.masternode_payments = isEnabled