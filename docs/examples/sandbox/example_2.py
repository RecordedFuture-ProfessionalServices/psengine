from psengine.sandbox import SandboxMgr

mgr = SandboxMgr()

results = mgr.search_samples(
    family=['emotet', 'cobaltstrike', 'asyncrat'],
    max_results=5,
)

for sample in results:
    print(
        f'{sample.id_:20s} {sample.status:12s} {sample.kind:6s} {sample.sha256 or sample.url}'
    )
