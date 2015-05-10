'''
    Implements simple interface to a coin daemon's RPC.
'''


import simplejson as json
from twisted.internet import defer

import lib.settings as settings

import time

import lib.logger
log = lib.logger.get_logger('bitcoin_rpc_manager')

from lib.bitcoin_rpc import BitcoinRPC


class BitcoinRPCManager(object):

	def __init__(self):
		log.debug("Got to Bitcoin RPC Manager")
		self.conns = {}
		self.conns[0] = BitcoinRPC(settings.COINDAEMON_TRUSTED_HOST,
								 settings.COINDAEMON_TRUSTED_PORT,
								 settings.COINDAEMON_TRUSTED_USER,
								 settings.COINDAEMON_TRUSTED_PASSWORD)
		self.curr_conn = 0
		for x in range (1, 99):
			if hasattr(settings, 'COINDAEMON_TRUSTED_HOST_' + str(x)) and hasattr(settings, 'COINDAEMON_TRUSTED_PORT_' + str(x)) and hasattr(settings, 'COINDAEMON_TRUSTED_USER_' + str(x)) and hasattr(settings, 'COINDAEMON_TRUSTED_PASSWORD_' + str(x)):
				self.conns[len(self.conns)] = BitcoinRPC(settings.__dict__['COINDAEMON_TRUSTED_HOST_' + str(x)],
									settings.__dict__['COINDAEMON_TRUSTED_PORT_' + str(x)],
									settings.__dict__['COINDAEMON_TRUSTED_USER_' + str(x)],
									settings.__dict__['COINDAEMON_TRUSTED_PASSWORD_' + str(x)])

	def add_connection(self, host, port, user, password):
		# TODO: Some string sanity checks
		self.conns[len(self.conns)] = BitcoinRPC(host, port, user, password)

	def next_connection(self):
		time.sleep(1)
		if len(self.conns) <= 1:
			log.error("Problem with Pool 0 -- NO ALTERNATE POOLS!!!")
			time.sleep(4)
			self.curr_conn = 0
			return
		log.error("Problem with Pool %i Switching to Next!" % (self.curr_conn) )
		self.curr_conn = self.curr_conn + 1
		if self.curr_conn >= len(self.conns):
			self.curr_conn = 0

	@defer.inlineCallbacks
	def check_height(self):
		# Gets the current;y selected connection's hieght while making sure it's alive
		# Switch to the next avialable connection on error
		while True:
			try:
				resp = (yield self.conns[self.curr_conn]._call('getinfo', []))
				break
			except:
				log.error("Check Height -- Pool %i Down!" % (self.curr_conn) )
				self.next_connection()

		# Current connection Height
		curr_height = json.loads(resp)['result']['blocks']
		log.debug("Check Height -- Current Pool %i : %i" % (self.curr_conn,curr_height) )

		# Figures out which connection is the 'heighest' and switches to it.
		# Usefull only with multiple daemons
		for i in self.conns:
			# Ignore current connection
			if i == self.curr_conn:
				continue

			# Load hieght from this connection, skip if error
			try:
				resp = (yield self.conns[i]._call('getinfo', []))
			except:
				log.error("Check Height -- Pool %i Down!" % (i,) )
				continue

			# This connection hieght
			height = json.loads(resp)['result']['blocks']
			log.debug("Check Height -- Pool %i : %i" % (i,height) )

			# Compare, set the activr/current connection to the hieghest
			if height > curr_height:
				self.curr_conn = i

		# We are done here.
		defer.returnValue(True)

	def _call_raw(self, data):
		while True:
			try:
				return self.conns[self.curr_conn]._call_raw(data)
			except:
				self.next_connection()

	def _call(self, method, params):
		while True:
			try:
				return self.conns[self.curr_conn]._call(method,params)
			except:
				self.next_connection()

	def check_submitblock(self):
		while True:
			try:
				return self.conns[self.curr_conn].check_submitblock()
			except:
				self.next_connection()

	def check_getblocktemplate(self, common_format = True):
		while True:
			try:
				return self.conns[self.curr_conn].check_getblocktemplate(common_format)
			except:
				self.next_connection()

	def check_getinfo(self):
		while True:
			try:
				return self.conns[self.curr_conn].check_getinfo()
			except:
				self.next_connection()

	def submitblock(self, block_hex, hash_hex, raw_hex = None, method='submitblock', num_retries=5):
		while True:
			try:
				return self.conns[self.curr_conn].submitblock(block_hex, hash_hex, raw_hex, method, num_retries)
			except:
				self.next_connection()

	def getinfo(self):
		while True:
			try:
				return self.conns[self.curr_conn].getinfo()
			except:
				self.next_connection()

	def getblocktemplate(self, num_retries=5):
		while True:
			try:
				return self.conns[self.curr_conn].getblocktemplate(num_retries)
			except:
				self.next_connection()
 
	def prevhash(self):
		while True:
			try:
				return self.conns[self.curr_conn].prevhash()
			except:
				self.next_connection()

	def validateaddress(self, address):
		while True:
			try:
				return self.conns[self.curr_conn].validateaddress(address)
			except:
				self.next_connection()

	def getdifficulty(self):
		while True:
			try:
				return self.conns[self.curr_conn].getdifficulty()
			except:
				self.next_connection()

	# Some Getters for static values
	def has_getinfo(self):
		return self.conns[self.curr_conn].has_getinfo
	def has_getblocktemplate(self):
		return self.conns[self.curr_conn].has_getblocktemplate
	def blocktemplate_version(self):
		return self.conns[self.curr_conn].blocktemplate_version
	def proof_type(self):
		return self.conns[self.curr_conn].proof_type
