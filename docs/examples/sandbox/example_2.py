from psengine.sandbox import SandboxMgr

mgr = SandboxMgr()

# TODO - review search parameters and results
results = mgr.search(family='emotet', max_results=5)

for sample in results:
    print(f'{sample.id_:20s} {sample.status:12s} {sample.kind:6s} {sample.sha256 or sample.url}')
