from twisted.internet import reactor, defer
import lib.settings as settings

import util
from mining.interfaces import Interfaces

import lib.logger
log = lib.logger.get_logger('block_updater')

class BlockUpdater(object):
	'''
		Polls upstream's getinfo() and detecting new block on the network.
		This will call registry.update_block when new prevhash appear.
		
		This is just failback alternative when something
		with ./coind -blocknotify will go wrong. 
	'''

	def __init__(self, registry, bitcoin_rpc):
		log.debug("Got to Block Updater")
		self.bitcoin_rpc = bitcoin_rpc
		self.registry = registry
		self.clock = None
		self.schedule()

	# Shedules an update to be run later
	def schedule(self):
		when = self._get_next_time()
		log.debug("Next prevhash update in %.03f sec" % when)
		log.debug("Merkle update in next %.03f sec" % \
				  ((self.registry.last_block_update_start_time + settings.MERKLE_REFRESH_INTERVAL)-Interfaces.timestamper.time()))
		self.clock = reactor.callLater(when, self.run)

	# Calculates the next run time
	def _get_next_time(self):
		when = settings.PREVHASH_REFRESH_INTERVAL - (Interfaces.timestamper.time() - self.registry.last_block_update_start_time) % \
			   settings.PREVHASH_REFRESH_INTERVAL
		return when  

	# This is slightly misleading in it's name. It will not always run update.
	# It will instead do the following:
	# 	1) Check if a new block was found on the network
	#	2) Run an update if a new block was found
	#	3) OR, run an update on the transaction refresh interval
	@defer.inlineCallbacks
	def run(self):
		log.info("Polling for new block information.")
		update = False
		prevhash = None

		try:
			# Get the current prevhash from the pool registry if one exists
			if self.registry.last_template:
				log.debug("Loading Prevhash from pool registry.")
				current_prevhash = "%064x" % self.registry.last_template.block.hashPrevBlock
			else:
				log.debug("No Prevhash in pool registry.")
				current_prevhash = None

			# Get the current prevhash from the coin deamon
			log.info("Loading Prevhash from network.")
			prevhash = util.reverse_hash((yield self.bitcoin_rpc.prevhash()))
			log.debug("Got Prevhash: %s" % prevhash)

			# We must have a prevhash
			if prevhash is None:
				log.error("Prevhash is NULL, is coin deamon ready/responding?")
				raise

			# Detects new a block by comparing the new prevhash with the current prevhash
			# If a new block is detected, run an update imidietly.
			# If no new block is detected, update only if it's time to refresh the transactions (merkele refresh)
			if prevhash and prevhash != current_prevhash:
				log.info("New block detected on network! Prevhash: %s" % prevhash)
				update = True
			elif Interfaces.timestamper.time() - self.registry.last_block_update_start_time >= settings.MERKLE_REFRESH_INTERVAL:
				log.info("Performing Merkle tree update. Prevhash: %s" % prevhash)
				update = True

			# Runs a Block/Getwork forced update if needed
			if update:
				self.registry.update_block(True)

		except Exception as e:
			log.warning("Block update failed: %s" % (str(e)))
		finally:
			# Schedule the next update
			self.schedule()