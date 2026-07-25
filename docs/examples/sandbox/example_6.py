from psengine.sandbox import SandboxMgr

mgr = SandboxMgr()
mgr.delete_profile('psengine-docs-demo')
created = mgr.create_profile(
    name='psengine-docs-demo',
    tags=['os:windows10-2004-x64', 'locale:en-us'],
    timeout=120,
    network='internet',
    browser='chrome',
)
print(f'Created {created.id_}')
print(f'name={created.name}, timeout={created.timeout}s')

all_profiles = mgr.fetch_profiles()
print(f'\nCompany has {len(all_profiles)} profile(s):')
for p in all_profiles:
    print(f'  {p.id_:40s} {p.name}')

fetched = mgr.fetch_profile(created.id_)
opts = fetched.options
browser = opts.browser if opts else None
print('\nRound-trip:')
print(f'  tags={fetched.tags}')
print(f'  network={fetched.network}')
print(f'  browser={browser}')

update_result = mgr.update_profile(
    profile_id=created.id_,
    name='psengine-docs-demo',
    tags=['os:windows10-2004-x64', 'locale:en-us'],
    timeout=300,
    network='internet',
    browser='firefox',
)
print(f'\nUpdate result: updated={update_result.updated}')

delete_result = mgr.delete_profile(created.id_)
print(f'Delete result: deleted={delete_result.deleted}')
