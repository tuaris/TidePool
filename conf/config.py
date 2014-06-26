import ConfigLoader
import ConfigParser

'''
Loads values from config file
'''

config_file_parser = ConfigParser.ConfigParser()
config_file_parser.readfp(open(r'' + ConfigLoader.CONFIG_FILE))

# ******************** BASIC SETTINGS ***************
CENTRAL_WALLET = config_file_parser.get('Basic', 'CENTRAL_WALLET')
COINDAEMON_TRUSTED_HOST = config_file_parser.get('Basic', 'COINDAEMON_TRUSTED_HOST')
COINDAEMON_TRUSTED_PORT = config_file_parser.getint('Basic', 'COINDAEMON_TRUSTED_PORT')
COINDAEMON_TRUSTED_USER = config_file_parser.get('Basic', 'COINDAEMON_TRUSTED_USER')
COINDAEMON_TRUSTED_PASSWORD = config_file_parser.get('Basic', 'COINDAEMON_TRUSTED_PASSWORD')
COINDAEMON_ALGO = config_file_parser.get('Basic', 'COINDAEMON_ALGO')
COINDAEMON_Reward = config_file_parser.get('Basic', 'COINDAEMON_Reward')
COINDAEMON_TX_MSG = config_file_parser.getboolean('Basic', 'COINDAEMON_TX_MSG')
SCRYPTJANE_NAME = config_file_parser.get('Basic', 'SCRYPTJANE_NAME')
Tx_Message = config_file_parser.get('Basic', 'Tx_Message')

# ******************** GENERAL SETTINGS ***************
STRATUM_MINING_PROCESS_NAME = config_file_parser.get('General', 'STRATUM_MINING_PROCESS_NAME')
DEBUG = config_file_parser.getboolean('General', 'DEBUG')
LOGDIR = config_file_parser.get('General', 'LOGDIR')
LOGFILE = config_file_parser.get('General', 'LOGFILE')
LOGLEVEL = config_file_parser.get('General', 'LOGLEVEL')
LOG_ROTATION = config_file_parser.getboolean('General', 'LOG_ROTATION')
LOG_SIZE = config_file_parser.getint('General', 'LOG_SIZE')
LOG_RETENTION = config_file_parser.getint('General', 'LOG_RETENTION')

# ******************** SERVICE SETTINGS *********************
THREAD_POOL_SIZE = config_file_parser.getint('Service', 'THREAD_POOL_SIZE')
HOSTNAME = config_file_parser.get('Service', 'HOSTNAME')
LISTEN_SOCKET_TRANSPORT = config_file_parser.getint('Service', 'LISTEN_SOCKET_TRANSPORT')
PASSWORD_SALT = config_file_parser.get('Service', 'PASSWORD_SALT')
ADMIN_PASSWORD = config_file_parser.get('Service', 'ADMIN_PASSWORD')

ENABLE_EXAMPLE_SERVICE = True
LISTEN_HTTP_TRANSPORT = None
LISTEN_HTTPS_TRANSPORT = None
LISTEN_WS_TRANSPORT = None
LISTEN_WSS_TRANSPORT = None
IRC_NICK = None

# ******************** Database  *********************

DATABASE_DRIVER = 'mysql'	# Options: none, sqlite, postgresql or mysql
DATABASE_EXTEND = True		# False = pushpool db layout, True = pushpool + extra columns
DB_SQLITE_FILE = 'pooldb.sqlite'
DB_PGSQL_HOST = 'localhost'
DB_PGSQL_DBNAME = 'pooldb'
DB_PGSQL_USER = 'pooldb'
DB_PGSQL_PASS = '**empty**'
DB_PGSQL_SCHEMA = 'public'

# MySQL
DB_MYSQL_HOST = config_file_parser.get('Database', 'DB_MYSQL_HOST')
DB_MYSQL_DBNAME = config_file_parser.get('Database', 'DB_MYSQL_DBNAME')
DB_MYSQL_USER = config_file_parser.get('Database', 'DB_MYSQL_USER')
DB_MYSQL_PASS = config_file_parser.get('Database', 'DB_MYSQL_PASS')
DB_MYSQL_PORT = config_file_parser.getint('Database', 'DB_MYSQL_PORT')

# ******************** Adv. DB Settings *********************
#  Don't change these unless you know what you are doing
DB_LOADER_CHECKTIME = 15	# How often we check to see if we should run the loader
DB_LOADER_REC_MIN = 10		# Min Records before the bulk loader fires
DB_LOADER_REC_MAX = 50		# Max Records the bulk loader will commit at a time
DB_LOADER_FORCE_TIME = 300      # How often the cache should be flushed into the DB regardless of size.
DB_STATS_AVG_TIME = 300		# When using the DATABASE_EXTEND option, average speed over X sec # Note: this is also how often it updates
DB_USERCACHE_TIME = 600		# How long the usercache is good for before we refresh

# ******************** Adv. Pool Settings *********************
USERS_AUTOADD = True		# Automatically add users to db when they connect.
USERS_CHECK_PASSWORD = False	# Check the workers password? (Many pools don't)
COINBASE_EXTRAS = '/TidePool/'			# Extra Descriptive String to incorporate in solved blocks
ALLOW_NONLOCAL_WALLET = False				# Allow valid, but NON-Local wallet's
INSTANCE_ID = 31		# Used for extranonce and needs to be 0-31
NTIME_AGE = 7200 		# Not a clue what this is for... :P (Sometimes is 1000)

# ******************** Pool Settings *********************
PREVHASH_REFRESH_INTERVAL = config_file_parser.getint('Pool', 'PREVHASH_REFRESH_INTERVAL')
MERKLE_REFRESH_INTERVAL = config_file_parser.getint('Pool', 'MERKLE_REFRESH_INTERVAL')

# ******************** Pool Difficulty Settings *********************
VDIFF_X2_TYPE = False  # powers of 2 e.g. 2,4,8,16,32,64,128,256,512,1024 (BROKEN)
USE_COINDAEMON_DIFF = False   # Set the maximum difficulty to the litecoin difficulty. 
DIFF_UPDATE_FREQUENCY = 86400 # Update the litecoin difficulty once a day for the VARDIFF maximum
ALLOW_EXTERNAL_DIFFICULTY = False 

VDIFF_FLOAT = config_file_parser.getboolean('Pool', 'VDIFF_FLOAT')
POOL_TARGET = config_file_parser.getint('Pool', 'POOL_TARGET')
VARIABLE_DIFF = config_file_parser.getboolean('Pool', 'VARIABLE_DIFF')
VDIFF_MIN_TARGET = config_file_parser.getint('Pool', 'VDIFF_MIN_TARGET')
VDIFF_MAX_TARGET = config_file_parser.getint('Pool', 'VDIFF_MAX_TARGET') 
VDIFF_TARGET_TIME = config_file_parser.getint('Pool', 'VDIFF_TARGET_TIME')
VDIFF_RETARGET_TIME = config_file_parser.getint('Pool', 'VDIFF_RETARGET_TIME')
VDIFF_VARIANCE_PERCENT = config_file_parser.getint('Pool', 'VDIFF_VARIANCE_PERCENT')



#### Advanced Option #####

SOLUTION_BLOCK_HASH = config_file_parser.getboolean('Advanced', 'SOLUTION_BLOCK_HASH')
BLOCK_CHECK_ALGO_HASH = config_file_parser.getboolean('Advanced', 'BLOCK_CHECK_ALGO_HASH')
REJECT_STALE_SHARES = config_file_parser.getboolean('Advanced', 'REJECT_STALE_SHARES')
# ******************** Stats Settings *********************

BASIC_STATS = False		# Enable basic stats page. This has stats for ALL users. (Unessesary)
BASIC_STATS_PORT = None		# Port to listen on

# ******************** Getwork Proxy Settings *********************
# DISABLED
# This enables a copy of slush's getwork proxy for old clients
# It will also auto-redirect new clients to the stratum interface
# so you can point ALL clients to: http://<yourserver>:<GW_PORT>

GW_ENABLE = False		# Enable the Proxy (If enabled you MUST run update_submodules)
GW_PORT = None			# Getwork Proxy Port
GW_DISABLE_MIDSTATE = False	# Disable midstate's (Faster but breaks some clients)
GW_SEND_REAL_TARGET = False	# Propigate >1 difficulty to Clients (breaks some clients)

# ******************** Archival Settings *********************
# Broken
ARCHIVE_SHARES = False		# Use share archiving?
ARCHIVE_DELAY = 86400		# Seconds after finding a share to archive all previous shares
ARCHIVE_MODE = 'file'		# Do we archive to a file (file) , or to a database table (db)

# Archive file options
ARCHIVE_FILE = 'archives/share_archive'	# Name of the archive file ( .csv extension will be appended)
ARCHIVE_FILE_APPEND_TIME = True		# Append the Date/Time to the end of the filename (must be true for bzip2 compress)
ARCHIVE_FILE_COMPRESS = 'none'		# Method to compress file (none,gzip,bzip2)

# ******************** Worker Ban Options *********************
# UNeeded
ENABLE_WORKER_BANNING = False # enable/disable temporary worker banning 
WORKER_CACHE_TIME = 600    # How long the worker stats cache is good before we check and refresh
WORKER_BAN_TIME = 300    # How long we temporarily ban worker
INVALID_SHARES_PERCENT = 50    # Allow average invalid shares vary this % before we ban
 
# ******************** E-Mail Notification Settings *********************
NOTIFY_EMAIL_TO = config_file_parser.get('Email', 'NOTIFY_EMAIL_TO')
NOTIFY_EMAIL_TO_DEADMINER = '' #non used
NOTIFY_EMAIL_FROM = config_file_parser.get('Email', 'NOTIFY_EMAIL_FROM')
NOTIFY_EMAIL_SERVER = config_file_parser.get('Email', 'NOTIFY_EMAIL_SERVER')
NOTIFY_EMAIL_USERNAME = config_file_parser.get('Email', 'NOTIFY_EMAIL_USERNAME')
NOTIFY_EMAIL_PASSWORD = config_file_parser.get('Email', 'NOTIFY_EMAIL_PASSWORD')
NOTIFY_EMAIL_USETLS = config_file_parser.getboolean('Email', 'NOTIFY_EMAIL_USETLS')

#### Memcache ####
# Not Used
MEMCACHE_ENABLE = False
# Memcahce is a option. Enter the settings below
MEMCACHE_HOST = "localhost" # hostname or IP that runs memcached
MEMCACHE_PORT = 11211 # Port
MEMCACHE_TIMEOUT = 900 # Key timeout
MEMCACHE_PREFIX = "stratum_" # Prefix for keys

# ******************** Admin settings *********************

# If ADMIN_PORT is set, you can issue commands to that port to interact with 
# the system for things such as user management. It's a JSON interface following 
# REST principles, so '/users' returns a list of users, '/users/1' or '/users/username'
# returns a single user. POSTs are done to lists (so /users), PUTs are done to 
# items (so /users/1)
ADMIN_PORT = None #Port for JSON admin commands, None to disable


