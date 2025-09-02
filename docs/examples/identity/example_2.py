from psengine.identity import IdentityMgr

mgr = IdentityMgr()

identities = mgr.lookup_credentials('+2@norsegods.online')
for identity in identities:
    for cred in identity.credentials:
        if (details := cred.exposed_secret.details) and details.clear_text_value:
            print(details.clear_text_value.get_secret_value())
