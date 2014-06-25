# Setup Config
import conf.ConfigLoader as ConfigLoader
ConfigLoader.CONFIG_FILE = '/etc/tidepool/foocoin_pool.conf'
import lib.settings as settings

# Bootstrap Stratum framework and run listening when mining service is ready
from twisted.internet import defer
from twisted.application.service import Application, IProcess
import lib.stratum
application = lib.stratum.setup(defer.Deferred())
IProcess(application).processName = settings.STRATUM_MINING_PROCESS_NAME

# Start the Pool
import tidepool