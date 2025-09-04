import os

os.environ["RF_TOKEN"] = ""

from psengine.enrich import LookupMgr

mgr = LookupMgr()
mgr.lookup("8.8.8.8", "ip")
