from psengine.identity import IdentityMgr


mgr = IdentityMgr()
mgr.lookup_password(hash_prefix='abdcef', algorithm='ntlm')
