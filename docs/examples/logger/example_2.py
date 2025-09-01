from psengine.enrich import LookupMgr
from psengine.logger import RFLogger

log = RFLogger().get_logger()

mgr = LookupMgr()
ip = mgr.lookup('8.8.8.8', 'ip')

log.info(ip)
