from service import MiningService
from subscription import MiningSubscription
from twisted.internet import defer
from twisted.internet.error import ConnectionRefusedError
import time
import simplejson as json
from twisted.internet import reactor
import threading
from mining.work_log_pruner import WorkLogPruner

@defer.inlineCallbacks
def setup(on_startup):
	'''Setup mining service internal environment.
	You should not need to change this. If you
	want to use another Worker manager or Share manager,
	you should set proper reference to Interfaces class
	*before* you call setup() in the launcher script.'''

	import lib.settings as settings

	# Get logging online as soon as possible
	import lib.logger
	log = lib.logger.get_logger('mining')

	from interfaces import Interfaces

	from lib.block_updater import BlockUpdater
	from lib.template_registry import TemplateRegistry
	from lib.bitcoin_rpc_manager import BitcoinRPCManager
	from lib.template_generator import BlockTemplateGenerator
	from lib.coinbaser import Coinbaser
	from lib.factories import ConstructionYard
	from lib.Factory import Factory

	bitcoin_rpc = BitcoinRPCManager()

	# Check coind
	#		 Check we can connect (sleep)
	# Check the results:
	#		 - getblocktemplate is avalible		(Die if not)
	#		 - we are not still downloading the blockchain		(Sleep)
	log.debug("Connecting to upstream blockchain network daemon...")
	upstream_connection_ready = False
	while True:
		try:
			# Check for 'submitblock' RPC function
			# Wait for this to complete
			log.debug("Starting check_submitblock")
			yield bitcoin_rpc.check_submitblock()
			log.debug("Finished check_submitblock")

			# Check for 'getblocktemplate' RPC function
			# Wait for this to complete
			log.debug("Starting check_getblocktemplate")
			yield bitcoin_rpc.check_getblocktemplate()
			log.debug("Completed check_getblocktemplate")

			# Check for 'getinfo' RPC function
			# Wait for this to complete
			log.debug("Starting check_getinfo")
			yield bitcoin_rpc.check_getinfo()
			log.debug("Completed check_getinfo")

			# All is good
			upstream_connection_ready = True
			break
		except ConnectionRefusedError, e:
			# No sense in continuing execution
			log.error("Upstream network daemon refused connection: %s" % (str(e)))
			break
		except Exception, e:
			# Possible race condition
			(critical, waitTime, message) = startup_exception_handler(e)
			if critical:
				# Unrecoverable error prevents us from starting up
				log.error(message)
				break
			else:
				# Wait before trying again
				log.warning(message)
				time.sleep(waitTime)

	if not upstream_connection_ready:
		log.error('Could not connect to upstream network daemon')
		reactor.stop()
		return

	# A sucesfull connection was made to the upstream network daemon
	log.info('Successfully connected to upstream network daemon')

	# Proceed with checking some prerequisite conditions
	prerequisites_satisfied = True

	# We need the 'getinfo' RPC function
	if not bitcoin_rpc.has_getinfo():
		log.error("Upstream network daemon does not support 'getinfo' RPC function.")
		prerequisites_satisfied = False

	# Current version requires the 'getblocktemplate' RPC function as this is how we load block templates
	if not bitcoin_rpc.has_getblocktemplate():
		log.error("Upstream network daemon does not support 'getblocktemplate' RPC function.")
		prerequisites_satisfied = False

	# Check Block Template version
	# Current version needs at least version 1
	# Will throw a valueError eception if 'bitcoin_rpc.blocktemplate_version' is unknown
	try:
		# Upstream network daemon implements version 1 of getblocktemplate
		if bitcoin_rpc.blocktemplate_version() == 2: 
			log.debug("Block Template Version 2") 
		if bitcoin_rpc.blocktemplate_version() >= 1:
			log.debug("Block Template Version 1+")
		else:
			log.error("Block Version mismatch: %s" % bitcoin_rpc.blocktemplate_version())
			raise
	except Exception, e:
		# Can't continue if 'bitcoin_rpc.blocktemplate_version' is unknown or unsupported
		log.error("Could not determine block version: %s." %(str(e)))
		prerequisites_satisfied = False

	# Check Proof Type
	# Make sure the configuration matches the detected proof type
	if bitcoin_rpc.proof_type() == settings.COINDAEMON_Reward:
		log.debug("Upstream network reports %s, Config for %s looks correct" % (bitcoin_rpc.proof_type(), settings.COINDAEMON_Reward))
	else:
		log.error("Wrong Proof Selected, Switch to appropriate PoS/PoW in tidepool.conf!")
		prerequisites_satisfied = False

	# Are we good?
	if not prerequisites_satisfied:
		log.error('Issues have been detected that prevent a sufesfull startup, please review log')
		reactor.stop()
		return

	# All Good!
	log.debug('Begining to load Address and Module Checks.')

	# Start the coinbaser
	log.debug("Starting Coinbaser")
	coinbaser = Coinbaser(bitcoin_rpc, getattr(settings, 'CENTRAL_WALLET'))
	log.debug('Waiting for Coinbaser')
	# Wait for coinbaser to fully initialize
	(yield coinbaser.on_load)
	log.debug('Coinbaser Ready.')

	# Factories
	log.debug("Starting Factory Construction Yard")
	construction_yard = ConstructionYard()
	log.debug("Building Factories")
	main_factory = Factory(coinbaser, 
							construction_yard.build_factory('coinbase'),
							construction_yard.build_factory('transaction'),
							construction_yard.build_factory('block'))

	log.debug("Starting Generator.... Template/Jobs")
	# Job Generator
	job_generator = BlockTemplateGenerator(main_factory)

	# Initialize the Template Registry
	log.info("Initializing Template Registry")
	registry = TemplateRegistry(job_generator,
								bitcoin_rpc,
								getattr(settings, 'INSTANCE_ID'),
								MiningSubscription.on_template,
								Interfaces.share_manager.on_network_block)

	# Template registry is the main interface between Stratum service
	# and pool core logic
	Interfaces.set_template_registry(registry)

	# Set up polling mechanism for detecting new block on the network
	# This is just failsafe solution when -blocknotify
	# mechanism is not working properly	
	BlockUpdater(registry, bitcoin_rpc)

	# Kick off worker pruning thread
	prune_thr = threading.Thread(target=WorkLogPruner, args=(Interfaces.worker_manager.job_log,))
	prune_thr.daemon = True
	prune_thr.start()

	# Ready to Mine!
	log.info("MINING SERVICE IS READY")
	on_startup.callback(True)

def startup_exception_handler(e):
	# Handle upstream network race conditions during startup
	# Returns True or False stating is the exception is critical
	# Also returns a wait time if applicable
	# Thus preventing any further action
	critical = False
	waitTime = 1
	message = None

	# Lets attempt to get some more information
	try:
		error = json.loads(e[2])['error']['message']
	except:
		error = "Invalid JSON"

	# Handle some possible known scenarios that could cause an upstream network race condition
	if error == "Invalid JSON":
		# Invalid JSON returned by server, something is not right.
		message = "RPC error: Invalid JSON. Check Username, Password, and Permissions"
		critical = True
	elif error == "Method not found":
		# This really should not happen but it it does, we must stop
		message = ("Un-handled '%s' exception." % error)
		critical = True
	elif "downloading blocks" in error:
		# The block chain is downloading, not really an error, but prevents us from proceeding
		message = ("Blockchain is downloading... will check back in 30 sec")
		critical = False
		waitTime = 29
	else:
		message = ("Upstream network error during startup: %s" % (str(error)))
		critical = False
		waitTime = 1

	return critical, waitTime, message

