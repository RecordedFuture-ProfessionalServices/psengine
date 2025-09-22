from psengine.identity import IdentityMgr

identity_mgr = IdentityMgr()

password_lookup = identity_mgr.lookup_password(
    hash_prefix='8e9a96e', algorithm='sha256'
)
print(password_lookup[0].exposure_status)
