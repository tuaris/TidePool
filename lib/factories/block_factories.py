from lib.core.standard import CBlock
from lib.core.extended import CPosBlock
from lib.core.extended import CMasterNodeBlock

import lib.logger
log = lib.logger.get_logger('block_factories')

class BlockFactory(object):
	def new_block(self, data):
		# Obtain a new blank block
		block = self._generate_block()

		# Basic Setup
		log.debug("Block Build in Progress...")
		block.nVersion = data['version']
		block.hashPrevBlock = int(data['previousblockhash'], 16)
		block.nBits = int(data['bits'], 16)
		block.hashMerkleRoot = 0
		block.nTime = 0
		block.nNonce = 0

		# Ready
		log.debug("Block Ready")
		return block

	def _generate_block(self):
		log.info("Creating a new Block")
		return CBlock()

class PoSBlockFactory(BlockFactory):
	def _generate_block(self):
		log.info("Creating a new PoS Block")
		return CPosBlock()

class MasterNodeBlockFactory(BlockFactory):
	def new_block(self, data):
		block = super(PoSBlockFactory).new_block(data)

		# Add in Masternode Extras
		block.set_votes(data['votes'])
		block.set_masternode_payments = data['masternode_payments']

	def _generate_block(self):
		log.info("Creating a new Master Node Block")
		return CMasterNodeBlock()