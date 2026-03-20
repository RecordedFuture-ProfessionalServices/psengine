from psengine.asi import AttackSurfaceMgr

mgr = AttackSurfaceMgr()

project_id = '10b94298-e411-4d0a-b0ad-bf81b1948f84'
signature = 'CVE-2022-2551'

data = mgr.fetch_exposures_by_signature(
    project_id, signature
)

for asset in data.asset_exposures:
    asset_id = asset.asset_id
    details = asset.details
    print(f'{asset_id} is affected at {details["target"]}')
