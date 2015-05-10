from twisted.internet import reactor, defer
import time
from datetime import datetime
import Queue
import signal
import DB_Mysql
import lib.settings as settings
import lib.logger

log = lib.logger.get_logger('DBInterface')

class DBInterface():
	def __init__(self):
		# Initialize the MySQL database driver and put it in self.DATABASE
		log.debug('DB_Mysql INIT')
		self.DATABASE = DB_Mysql.DB_Mysql()

	def init_main(self):
		self.DATABASE.check_tables()
 
		self.QUEUE = Queue.Queue()
		self.QUEUE_OVERLOADED = False
		self.OVERLOADED_QUEUE_BATCH_SIZE = settings.DB_LOADER_REC_MAX
		self.queueclock = None

		self.usercache = {}
		self.clearusercache()

		self.statsclock = None
		self.nextStatsUpdate = 0

		self.scheduleImport()
		self.scheduleStats()

		self.next_force_import_time = time.time() + settings.DB_LOADER_FORCE_TIME

		self.CURRENT_NUMBEROF_IMPORT_THREADS = 0

		signal.signal(signal.SIGINT, self.signal_handler)

	def signal_handler(self, signal, frame):
		log.warning("SIGINT Detected, shutting down")
		log.info("Flushing shares into database")
		self.do_import(self.DATABASE, True)
		reactor.stop()

	def set_bitcoinrpc(self, bitcoinrpc):
		self.bitcoinrpc = bitcoinrpc

	def clearusercache(self):
		log.debug("DBInterface.clearusercache called")
		self.usercache = {}
		self.usercacheclock = reactor.callLater(settings.DB_USERCACHE_TIME , self.clearusercache)

	def scheduleImport(self):
		log.debug("Scheduling next queue run check %s seconds from now." % settings.DB_LOADER_CHECKTIME)
		self.queueclock = reactor.callLater(settings.DB_LOADER_CHECKTIME , self.run_import_thread)

	def scheduleStats(self):
		self.statsclock = reactor.callLater(settings.DB_STATS_AVG_TIME , self.stats_thread)

	def run_import_thread(self):
		log.debug("Share queue has %d item(s)", self.QUEUE.qsize())

		# Don't incur thread overhead if we're not going to run
		# 1. Queue must not be empty
		# 2. If queue is not empty, then at least one of these two conditions are met
		# 	a. Queue has at least DB_LOADER_REC_MIN number of items
		# 	b. It's time to force an import
		if self.QUEUE.qsize() > 0 and (self.QUEUE.qsize() >= settings.DB_LOADER_REC_MIN or time.time() >= self.next_force_import_time):
			# Import thread will run, next runtime will be scheduled from within the import_thread function
			log.debug("Shares queue: import will run at this time.")
			reactor.callInThread(self.import_thread)
			log.debug("Shares queue: import process has been requested.")
		else:
			# Import thread will not run, we should schedule next runtime
			log.debug("Shares queue: import not nessecary at this time.")
			self.scheduleImport()

	def import_thread(self, onetime = False):
		# Update number of running threads
		self.CURRENT_NUMBEROF_IMPORT_THREADS = self.CURRENT_NUMBEROF_IMPORT_THREADS + 1

		log.info("Shares import thread has started running...")
		# Create a new database connection for use in this thread
		# Since this is called Asyncronosly
		try:
			database = DB_Mysql.DB_Mysql()
		except Exception as e:
			log.error("Import thread failed: %s" % e.args[0])
			return

		# Do the deed
		self.do_import(database, False)
		database.close()

		# Update number of running threads, never drops below 0
		self.CURRENT_NUMBEROF_IMPORT_THREADS = max(self.CURRENT_NUMBEROF_IMPORT_THREADS -1, 0)

		# Schedule next runtime unless this was requested as a single run time
		if not onetime:
			self.scheduleImport()

	# Statistics are no longer handled by the startum service.  Now done by Backoffice.
	def stats_thread(self):
		log.info("Stats thread has started running...")
		# Do the deed
		self.update_stats()

		# Schedule next runtime
		self.scheduleStats()
	
	# Statistics are no longer handled by the startum service.  Now done by Backoffice.
	def update_stats(self):
		if time.time() > self.nextStatsUpdate:
			self.nextStatsUpdate = time.time() + settings.DB_STATS_AVG_TIME
			try:
				log.info("Stats update running")
			except:
				log.error("Stats update failed: %s", e.args[0])

	def do_import(self, dbi, force):
		log.debug("DBInterface.do_import called. force: %s, queue size: %s", 'yes' if force == True else 'no', self.QUEUE.qsize())
		
		# Flush the whole queue on force
		forcesize = 0
		if force == True:
			forcesize = self.QUEUE.qsize()

		# To help us determine how long it takes to import a batch of shares
		start_time = None
		avg_batch_processing_time_seconds = 0
		queue_processing_time_seconds = 0
		total_runs = 0

		# Only run if we have data
		while self.QUEUE.empty() == False and (force == True or self.QUEUE.qsize() >= settings.DB_LOADER_REC_MIN or time.time() >= self.next_force_import_time or forcesize > 0):
			log.debug("Share queue size is %i" % self.QUEUE.qsize())
			self.next_force_import_time = time.time() + settings.DB_LOADER_FORCE_TIME

			# Time this import run has started
			start_time = time.time()

			force = False
			# Put together the data we want to import
			sqldata = []
			datacnt = 0

			if self.QUEUE_OVERLOADED:
				# Increased batch size
				batch_size = self.OVERLOADED_QUEUE_BATCH_SIZE
			else:
				# Normal size batches
				batch_size = settings.DB_LOADER_REC_MAX 

			log.debug("Loading Share Records from queue")
			while self.QUEUE.empty() == False and datacnt < batch_size:
				datacnt += 1
				try:
					data = self.QUEUE.get(timeout=1)
					sqldata.append(data)
					self.QUEUE.task_done()
				except Queue.Empty:
					log.warning("Share Records Queue is empty!")

			log.info("%i share records loaded, %i share records remain in queue." % (datacnt, self.QUEUE.qsize()))
			forcesize -= datacnt

			# try to do the import, if we fail, log the error and put the data back in the queue
			try:
				log.debug("Inserting %i Share Records", datacnt)
				dbi.import_shares(sqldata)
			except Exception as e:
				log.error("Insert Share Records Failed.  Error: %s", e.args[0])
				for k, v in enumerate(sqldata):
					self.QUEUE.put(v)
				break  # Allows us to sleep a little

			# Total time in seconds it took to import a batch of shares in the current run
			batch_processing_time_seconds = max(time.time() - start_time, 0)

			# Lets keep track of how long the whole thing could take
			queue_processing_time_seconds = queue_processing_time_seconds + batch_processing_time_seconds
			# Keep a running average
			total_runs = total_runs + 1
			avg_batch_processing_time_seconds = queue_processing_time_seconds / total_runs
			log.debug("Took %i seconds(s) to import %i shares, AVG: %s." % (batch_processing_time_seconds, datacnt, avg_batch_processing_time_seconds))

			# Lets get an estimate of how long it will take this thread to finsh importing the queue based on it's
			# current size (self.QUEUE.qsize()), the batch size (DB_LOADER_REC_MAX), 
			# and the wait time (DB_LOADER_FORCE_TIME).

			# Lets take a snapshot of the current size of the queue
			current_queue_size = self.QUEUE.qsize()

			# Number of batches that need to be processed
			number_of_batches = (current_queue_size + (batch_size - 1)) // batch_size
			log.debug("Aproximatly %i batche(s) remain." % number_of_batches)

			# Total seconds needed to process all batches
			# 1 batch is done every 'avg_batch_processing_time_seconds' 
			total_time_seconds = (avg_batch_processing_time_seconds * number_of_batches) / max(self.CURRENT_NUMBEROF_IMPORT_THREADS, 1)
			log.debug("Aproximatly %i seconds(s) needed to process entire queue." % total_time_seconds)

			# Remove overload if the queue time is less than 20 minutes
			if self.QUEUE_OVERLOADED and total_time_seconds <= 1200:
				self.QUEUE_OVERLOADED = False

			# Issue a warning if the time is more that 30 minutes
			if total_time_seconds >= 1800:
				log.warning("Large share queue detected (%s items), aproximatly %s hours(s) needed to process entire queue." % (current_queue_size, (total_time_seconds / 60 / 60)))

			# Take some action if it's more than 1 hour, increase the batch size to 15% of the number of batches plus current batch size
			if total_time_seconds >= 3600:
				self.QUEUE_OVERLOADED = True
				self.OVERLOADED_QUEUE_BATCH_SIZE = abs((0.15 * number_of_batches) + batch_size)
				log.warning("Temporaroly increased batch size to: %i" % self.OVERLOADED_QUEUE_BATCH_SIZE)

			# Start another thread if the overload coninues beyond 3 hours estimate
			if (total_time_seconds) >= 10800 and self.CURRENT_NUMBEROF_IMPORT_THREADS < settings.DB_MAX_IMPORT_THREADS:
				# Start anew one time thread (True means it's single use, won't get rescheduled)
				reactor.callInThread(self.import_thread, True)
				log.warning("Spawned new import thread")

		log.debug("Import took %i seconds(s)" % (queue_processing_time_seconds))

	def queue_share(self, data):
		if settings.SAVE_SHARES:
			self.QUEUE.put(data)
		else:
			log.info("Doing somthing else with shares")

	def found_block(self, data):
		try:
			if settings.SAVE_SHARES:
				log.info("Updating Found Block Share Record")
				# We can't Update if the record is not there.
				# Forcable make the database import waiting shares
				self.do_import(self.DATABASE, True)  
				self.DATABASE.found_block(data)
			else:
				log.info("Inserting found block")
				# There is no cncept of 'shares' stored in the database, we insert the information as new

		except Exception as e:
			log.error("Update Found Block Share Record Failed: %s", e.args[0])

	def check_password(self, username, password):
		if username == "":
			log.info("Rejected worker for blank username")
			return False

		# Force username and password to be strings
		username = str(username)
		password = str(password)
		wid = username + ":-:" + password

		if wid in self.usercache:
			return True
		elif not settings.USERS_CHECK_PASSWORD and self.user_exists(username): 
			self.usercache[wid] = 1
			return True
		elif self.DATABASE.check_password(username, password):
			self.usercache[wid] = 1
			return True
		elif settings.USERS_AUTOADD == True:
			self.insert_user(username, password)
			self.usercache[wid] = 1
			return True

		log.info("Authentication for %s failed" % username)
		return False

	def list_users(self):
		return self.DATABASE.list_users()

	def get_user(self, id):
		return self.DATABASE.get_user(id)

	def get_user_settings(self, id):
		return self.DATABASE.get_user_settings(id)

	def user_exists(self, username):
		user = self.DATABASE.get_user(username)
		return user is not None 

	def insert_user(self, username, password):
		return self.DATABASE.insert_user(username, password)

	def delete_user(self, username):
		self.usercache = {}
		return self.DATABASE.delete_user(username)

	def update_user(self, username, password):
		self.usercache = {}
		return self.DATABASE.update_user(username, password)

	def update_worker_diff(self, username, diff):
		return self.DATABASE.update_worker_diff(username, diff)

	def get_worker_diff(self,username):
	  return self.DATABASE.get_worker_diff(username)

	def clear_worker_diff(self):
		return self.DATABASE.clear_worker_diff()

