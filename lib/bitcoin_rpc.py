'''
    Implements simple interface to a coin daemon's RPC.
'''

import simplejson as json
import base64
from twisted.internet import defer
from twisted.web import client
import time

import lib.logger
log = lib.logger.get_logger('bitcoin_rpc')

class BitcoinRPC(object):

	def __init__(self, host, port, username, password):
		log.debug("Got to Bitcoin RPC")
		self._lock = defer.DeferredLock()
		self.bitcoin_url = 'http://%s:%d' % (host, port)
		self.credentials = base64.b64encode("%s:%s" % (username, password))
		self.headers = {
			'Content-Type': 'text/json',
			'Authorization': 'Basic %s' % self.credentials,
		}
		client.HTTPClientFactory.noisy = False

		# Not all coins have the "submitblock" RPC call
		self.has_submitblock = False
		# It's possible (in the future) that the 'getinfo' function is no longer named as such
		self.has_getinfo = False
		# The 'getblocktemplate' function is a nessesity
		self.has_getblocktemplate = False

		# This will be auto detected on start up by the 'check_getblocktemplate' function
		self.getblocktemplate_pollformat = None
		# This currently has no effect on mining logic, but may have in the future
		self.blocktemplate_version = None
		# Proof type, currently has no effect on mining logic, but may have in the future
		self.proof_type = None

	def _call_raw(self, data):
		log.debug("RAW POST Dump: %s" % str(data))
		client.Headers
		return client.getPage(
			url=self.bitcoin_url,
			method='POST',
			headers=self.headers,
			postdata=data,
		)

	def _call(self, method, params):
		log.debug("JSON Dump: method: %s | params: %s" % (str(method), str(params)))
		return self._lock.run(self._call_raw, json.dumps({
				'jsonrpc': '2.0',
				'method': method,
				'params': params,
				'id': '1',
			}))

	@defer.inlineCallbacks
	def check_submitblock(self):
		# Detects if the upstream coin daemon supports the 'submitblock' RPC call
		# At the moment this detection does not affect block submission logic.
		# It cuurently only enables or disables an error message.
		try:
			log.info("Checking for 'submitblock' RPC function")
			resp = (yield self._call('submitblock', []))
			# If this worked, then we are done
			self.has_submitblock = True
			log.debug("Sucesfully detected 'submitblock' RPC function.")
		except Exception as e:
			if (str(e) == "404 Not Found"):
				# 404 Error means this function does not exist
				log.debug("No 'submitblock' RPC function was detected.")
				self.has_submitblock = False
			elif (str(e) == "500 Internal Server Error"):
				# The server may return a 500 error which means the function exists
				# It's just that we called it with no paramaters, so it errors out
				log.debug("A 'submitblock' RPC function was detected.")
				self.has_submitblock = True
			else:
				log.debug("An unknown response was recived during 'submitblock' detection: %s" % str(e))
				raise

	@defer.inlineCallbacks
	def check_getblocktemplate(self, common_format = True):
		# Performs 3 checks
		# 1. Check if the 'getblocktemplate' RPC function exists
		# 2. Determine the format of the 'getblocktemplate' function format
		# 3. Determine the block template version as reported by the upstream daemon

		# Some upstream daemons accept '[{}]' and others accept '[]' (ie. peercoin) when polling for a blocktemplate
		# These are the only two known choices. Try the common format first.
		# If it fails, this function will call itself and use the uncommon format.
		# Note: this has no effect when 'getblocktemplate' is called to submit a block when 'submitblock' does not exist.
		if common_format:
			self.getblocktemplate_pollformat = [{}]
		else:
			self.getblocktemplate_pollformat = []

		try:
			# Check number 1 and 2 are done at the same time
			log.info("Checking for 'getblocktemplate' RPC function")
			resp = (yield self._call('getblocktemplate', self.getblocktemplate_pollformat))
			self.has_getblocktemplate = True
			# If there is no error then we are done.
			log.debug("Sucesfully found 'getblocktemplate' RPC function")
			log.info("Detected 'getblocktemplate' poll format as '%s'" % ('[{}]' if common_format else '[]'))

			# Check 3:  Determine the block template version
			result = json.loads(resp)['result']
			self.blocktemplate_version = result['version']
			log.debug("Block version %s detected" % str(self.blocktemplate_version))

		except Exception as e:
			if (str(e) == "500 Internal Server Error"):
				# If 500 error, then 'getblocktemplate' exists, but it was called incorrectly
				self.has_getblocktemplate = True
				if common_format:
					# Lets try 'getblocktemplate' without empty {} (common_format = false)
					yield self.check_getblocktemplate(False)
				else:
					# We already tried with the non-comon format, set it to None and fail
					self.getblocktemplate_pollformat = None
					raise
			elif (str(e) == "404 Not Found"):
				# 404 Error means this function does not exist
				log.error("No 'getblocktemplate' RPC function was found.")
				self.has_getblocktemplate = False
			else:
				log.error("An unknown response was recived during 'getblocktemplate' probe: %s" % str(e))
				raise


	@defer.inlineCallbacks
	def check_getinfo(self):
		# Detects if the upstream coin daemon supports the 'getinfo' RPC call
		# Also determines the upstream coin daemon proof type
		# At the moment this detection does not affect coinbase logic.

		try:
			# Check for 'getwork'
			log.info("Checking for 'getinfo' RPC function")
			resp = (yield self._call('getinfo', []))
			# If this worked, then we are done
			self.has_getinfo = True
			log.debug("Sucesfully detected 'getinfo' RPC function.")

			# Determine the upstream coin daemon proof type
			if 'stake' in resp:
				self.proof_type = 'POS'
				log.debug("Upstream network reports PoS")
			elif 'stake' not in resp:
				self.proof_type = 'POW'
				log.debug("Upstream network reports PoW")
			else:
				# Default to POW
				self.proof_type = 'POW'
				log.warning("Upstream may not be a PoS/PoW network, using PoW anyway.")

		except Exception as e:
			if (str(e) == "404 Not Found"):
				# 404 Error means this function does not exist
				log.debug("No 'getinfo' RPC function was detected.")
				self.has_getinfo = False
			elif (str(e) == "500 Internal Server Error"):
				# The server may return a 500 error which means the function exists
				# It's just that we called it with no paramaters, so it errors out
				log.debug("A 'getinfo' RPC function was detected.")
				self.has_getinfo = True
			else:
				log.error("An unknown response was recived during 'getinfo' detection: %s" % str(e))
				raise

	@defer.inlineCallbacks
	def submitblock(self, block_hex, hash_hex, raw_hex = None, method='submitblock', num_retries=5):
		resp = None
		#Since this is very important, try "num_retries" times. A 500 Internal Server Error could mean random error or that TX messages setting is wrong
		current_attempt = 0
		while True:
			current_attempt += 1
			log.debug("Submitting Block HEX: %s" % [block_hex,])
			# Try submitblock if that fails, go to getblocktemplate
			if method == 'submitblock':
				log.info("Submitting Block with '%s': ATTEMPT #%i" % (method, current_attempt))
				try:
					resp = (yield self._call('submitblock', [block_hex,]))
					break #sucesfull
				except Exception:
					# Submit block failed or is not avialable
					if self.has_submitblock:
						# Only output an error if 'submitblock' was a valid RPC call.
						log.error("Submit Block Failed with submitblock")

					# Fall back to alernative 'old' method
					method = 'getblocktemplate'
					log.info("RPC function 'submitblock' not avialable.  Falling back to '%s'" % method)
				finally:
					log.debug("SUBMITBLOCK RESULT: %s" % str(resp))

			# Try getblocktemplate
			if method == 'getblocktemplate':
				log.info("Submitting Block with '%s': ATTEMPT #%i" % (method, current_attempt))
				try: 
					resp = (yield self._call('getblocktemplate', [{'mode': 'submit', 'data': block_hex}]))
					break #sucesfull
				except Exception as e:
					if current_attempt > num_retries:
						log.error("All block submission methods fail: %s. Try Enabling TX Messages in config.py!" % str(e))
						raise
					else:
						log.warning("Problem Submitting block %s" % str(e))
						log.warning("Retrying %i of %i attempts" % (current_attempt, num_retries))
						continue
				finally:
					log.debug("SUBMITBLOCK RESULT: %s" % str(resp))

		# Either the block was sumbitted or the retires were exhuasted
		if json.loads(resp)['result'] == None:
			# make sure the block was created. 
			defer.returnValue((yield self.blockexists(hash_hex)))
		else:
			defer.returnValue(False)

	@defer.inlineCallbacks
	def getinfo(self):
		 resp = (yield self._call('getinfo', []))
		 defer.returnValue(json.loads(resp)['result'])

	@defer.inlineCallbacks
	def getblocktemplate(self, num_retries=5):
		resp = (yield self._call('getblocktemplate', self.getblocktemplate_pollformat))
		defer.returnValue(json.loads(resp)['result'])

	@defer.inlineCallbacks
	def prevhash(self):
		resp = (yield self._call('getwork', []))
		try:
			defer.returnValue(json.loads(resp)['result']['data'][8:72])
		except Exception as e:
			log.exception("Cannot decode prevhash %s" % str(e))
			raise

	@defer.inlineCallbacks
	def validateaddress(self, address):
		resp = (yield self._call('validateaddress', [address,]))
		defer.returnValue(json.loads(resp)['result'])

	@defer.inlineCallbacks
	def getdifficulty(self):
		resp = (yield self._call('getdifficulty', []))
		defer.returnValue(json.loads(resp)['result'])

	@defer.inlineCallbacks
	def blockexists(self, hash_hex):
		resp = None
		log.debug("Checking Block...%s" % hash_hex)

		#Default is not found
		result = False

		try:
			resp = (yield self._call('getblock', [hash_hex,]))
			if "hash" in json.loads(resp)['result'] and json.loads(resp)['result']['hash'] == hash_hex:
				log.debug("Block Confirmed: %s" % hash_hex)
				result = True
			else:
				log.info("Cannot find block for %s" % hash_hex)
		except Exception as e:
			log.error("Network could not verify block %s. Make sure you have peers connected and have a syncronized block chain. %s" % (hash_hex, str(e)))
		finally:
			log.debug("GETBLOCK RESULT: %s"  % str(resp))

		#Resturn Result
		defer.returnValue(result)
