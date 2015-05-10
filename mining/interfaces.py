'''This module contains classes used by pool core to interact with the rest of the pool.
   Default implementation do almost nothing, you probably want to override these classes
   and customize references to interface instances in your launcher.
   (see launcher_demo.tac for an example).
''' 
import time
from twisted.internet import reactor, defer
from lib.util import b58encode

import lib.settings as settings
import lib.logger
log = lib.logger.get_logger('interfaces')

import lib.notify_email

import DBInterface
dbi = DBInterface.DBInterface()
dbi.init_main()

class WorkerManagerInterface(object):
	def __init__(self):
		self.worker_log = {}
		self.worker_log.setdefault('authorized', {})
		self.job_log = {}
		self.job_log.setdefault('None', {})
		return

	def authorize(self, worker_name, worker_password):
		# Important NOTE: This is called on EVERY submitted share. So you'll need caching!!!
		return dbi.check_password(worker_name, worker_password)
 
	# Returns a tuple with 
	# 	The difficulty as found the database
	#	True or false stating if custom_diff_enable is set
	# Uppon initial authorization, if the last checkin_time of this user from the database exceeds the threshold (in days), and they are using VARDIFF: 'reset' back to the pool default
	# If the user is not found, we return the default pool difficultly and use vardiff (custom_diff_enable not set)
	def get_user_difficulty(self, worker_name, is_initial_authorization = False, last_checkin_threshold = 0):
		# Initial values
		use_vardiff = True
		difficulty = settings.POOL_TARGET
		is_old = False

		# Gets worker's initial difficulty from database (if there is one)
		try:
			worker_data = dbi.get_user(worker_name)
		except:
			log.warning("An error occured during difficulty lookup for the user '%s'.  Using DIFF=%s VARDIFF=%s" % (worker_name, difficulty, use_vardiff))
			worker_data = {}

		# If there is no information found, then return the defaults
		if len(worker_data) < 6: return (use_vardiff, difficulty)

		log.debug("Found worker: %s" % str(worker_name))
		log.debug("Data: %s" % str(worker_data))
		log.debug("Found difficulty: %s" % str(worker_data['difficulty']))

		# Set the worker's difficulty as long as it's not 0
		if worker_data['difficulty'] != 0:
			difficulty = worker_data['difficulty']

		# Now attempt to lookup to see if we are using VARDIFF for this worker
		try:
			worker_settings = dbi.get_user_settings(worker_data['id'])
		except:
			# If for whatever reason something goes wrong, retur nthe defaults.
			log.warning("VARDIFF state could not be determined for '%s'.  Using VARDIFF=%s" % (worker_name, use_vardiff))

		if not worker_settings is None and worker_settings['custom_diff_enable'] == 1:
			# Enable custom difficulty, turn off VARDIFF
			log.debug("VARDIFF is Disabled")
			use_vardiff = False
		else:
			# Return the user's current difficulty setting
			log.debug("VARDIFF is Enabled")

		# Determines if the data of this worker has not been updated in a while (last_checkin_threshold)
		# Only nessesary during initial authorization
		if is_initial_authorization and use_vardiff:
			log.info("Initial difficulty setup for %s." % worker_name)
			last_checkin_time = time.mktime(worker_data['last_checkin'].timetuple())
			log.debug("Last share accepted on: %s" % str(worker_data['last_checkin']))

			if (Interfaces.timestamper.time() - last_checkin_time) > (last_checkin_threshold * 86400):
				log.info("Worker data is more than %i days old.  Resetting difficulty to pool defualts" % last_checkin_threshold)
				difficulty = settings.POOL_TARGET

		log.info("Difficulty for %s set to %s with VARDIFF=%s" % (worker_name, difficulty, use_vardiff))
		return (use_vardiff, difficulty)

	def register_work(self, worker_name, job_id, difficulty):
		now = Interfaces.timestamper.time()
		work_id = WorkIdGenerator.get_new_id()
		self.job_log.setdefault(worker_name, {})[work_id] = (job_id, difficulty, now)
		return work_id

class WorkIdGenerator(object):
	counter = 1000

	@classmethod
	def get_new_id(cls):
		cls.counter += 1
		if cls.counter % 0xffff == 0:
			cls.counter = 1
		return "%x" % cls.counter

class ShareLimiterInterface(object):
	'''Implement difficulty adjustments here'''

	def submit(self, connection_ref, job_id, current_difficulty, timestamp, worker_name):
		'''connection - weak reference to Protocol instance
		   current_difficulty - difficulty of the connection
		   timestamp - submission time of current share
		   
		   - raise SubmitException for stop processing this request
		   - call mining.set_difficulty on connection to adjust the difficulty'''
		
		new_diff = dbi.get_worker_diff(worker_name)
		session = connection_ref().get_session()
		session['prev_diff'] = session['difficulty']
		session['prev_jobid'] = job_id
		session['difficulty'] = new_diff
		connection_ref().rpc('mining.set_difficulty', [new_diff,], is_notification=True)
		#return dbi.update_worker_diff(worker_name, settings.POOL_TARGET)
		return
 
class ShareManagerInterface(object):
	def __init__(self):
		self.block_height = 0
		self.prev_hash = 0

		# Send out the e-mail saying we are starting.
		notify_email = lib.notify_email.NOTIFY_EMAIL()
		notify_email.notify_start()
		log.debug("Email Notification Sent")

	def on_network_block(self, prevhash, block_height):
		'''Prints when there's new block coming from the network (possibly new round)'''
		self.block_height = block_height
		self.prev_hash = b58encode(int(prevhash, 16))
		pass

	def on_submit_share(self, worker_name, block_header, block_hash, difficulty, timestamp, is_valid, ip, invalid_reason, share_diff):
		log.debug("%s (%s) %s %s" % (block_hash, share_diff, 'valid' if is_valid else 'INVALID', worker_name))
		dbi.queue_share([worker_name, block_header, block_hash, difficulty, timestamp, is_valid, ip, self.block_height, self.prev_hash, invalid_reason, share_diff ])
 
	# The prev_hash, block_height need to be provided since the cached version may have changed to the next block by the time we get to this point
	def on_submit_block(self, is_accepted, worker_name, block_header, block_hash, difficulty, prev_hash, block_height, timestamp, ip, share_diff):
		log.debug("Block %s %s" % (block_hash, 'ACCEPTED' if is_accepted else 'REJECTED'))
		dbi.found_block([worker_name, block_header, block_hash, difficulty, timestamp, is_accepted, ip, block_height, prev_hash, share_diff ])

		# Send out the e-mail saying we found a block.
		if is_accepted:
			notify_email = lib.notify_email.NOTIFY_EMAIL()
			notify_email.notify_found_block(worker_name, block_hash, block_height, timestamp)

class TimestamperInterface(object):
	'''This is the only source for current time in the application.
	Override this for generating unix timestamp in different way.'''
	def time(self):
		return time.time()

class PredictableTimestamperInterface(TimestamperInterface):
	'''Predictable timestamper may be useful for unit testing.'''
	start_time = 1345678900  # Some day in year 2012
	delta = 0

	def time(self):
		self.delta += 1
		return self.start_time + self.delta

class Interfaces(object):
	worker_manager = None
	share_manager = None
	share_limiter = None
	timestamper = None
	template_registry = None

	@classmethod
	def set_worker_manager(cls, manager):
		cls.worker_manager = manager

	@classmethod
	def set_share_manager(cls, manager):
		cls.share_manager = manager

	@classmethod
	def set_share_limiter(cls, limiter):
		cls.share_limiter = limiter

	@classmethod
	def set_timestamper(cls, manager):
		cls.timestamper = manager

	@classmethod
	def set_template_registry(cls, registry):
		dbi.set_bitcoinrpc(registry.bitcoin_rpc)
		cls.template_registry = registry
