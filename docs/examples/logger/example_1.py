import logging

from psengine.enrich import LookupMgr

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

mgr = LookupMgr()
ip = mgr.lookup("8.8.8.8", "ip")

log.info(ip)
