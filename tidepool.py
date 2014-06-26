import lib.settings as settings
from twisted.internet import defer

# Run listening when mining service is ready
on_startup = defer.Deferred()

# Load mining service into stratum framework
import mining
from mining.interfaces import Interfaces
from mining.interfaces import WorkerManagerInterface, TimestamperInterface, ShareManagerInterface, ShareLimiterInterface

if settings.VARIABLE_DIFF == True:
	from mining.basic_share_limiter import BasicShareLimiter
	Interfaces.set_share_limiter(BasicShareLimiter())
else:
	from mining.interfaces import ShareLimiterInterface
	Interfaces.set_share_limiter(ShareLimiterInterface())

Interfaces.set_share_manager(ShareManagerInterface())
Interfaces.set_worker_manager(WorkerManagerInterface())
Interfaces.set_timestamper(TimestamperInterface())

mining.setup(on_startup)