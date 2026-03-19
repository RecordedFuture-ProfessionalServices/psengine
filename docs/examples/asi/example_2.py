from psengine.asi import AttackSurfaceMgr

mgr = AttackSurfaceMgr()

project_id = '10b94298-e411-4d0a-b0ad-bf81b1948f84'
asset_id = 'www.theology.bsu.by'

asset_info = mgr.fetch_asset(
    project_id,
    asset_id,
    additional_fields=[
        'open_tcp_ports',
        'open_udp_ports',
    ],
)
print(f'{asset_info}\n')

ports = []
for ip in asset_info.scanned_ips:
    ports = [str(port.port) for port in ip.open_ports]

print(
    f'{asset_info.name} has open ports: {", ".join(ports)}'
)
