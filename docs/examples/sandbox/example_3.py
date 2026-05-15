from psengine.sandbox import SandboxMgr

mgr = SandboxMgr()

samples = mgr.fetch_samples(subset='owned', max_results=5)
for s in samples:
    print(f'{s.id_:20s} {s.status:12s} {s.kind:6s} submitted={s.submitted.isoformat()}')

if samples:
    detail = mgr.fetch_sample(samples[0].id_)
    print(f'\nFirst sample tasks: {detail.tasks}')
