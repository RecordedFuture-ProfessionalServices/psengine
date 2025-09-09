from psengine.config import Config, get_config
from psengine.enrich import LookupMgr

Config.init(https_proxy='https://localhost:8080', client_ssl_verify=False)
mgr = LookupMgr()

data = mgr.lookup('8.8.8.8', 'ip')
print(data)
