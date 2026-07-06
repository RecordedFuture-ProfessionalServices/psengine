from psengine.sandbox import SandboxMgr

SAMPLE_ID = '260501-h4p7laawme'

mgr = SandboxMgr()
report = mgr.fetch_sample_static_report(SAMPLE_ID)

print(f'Score: {report.analysis.score}')
print(f'Tags:  {report.analysis.tags}')

for f in report.files:
    print(f'  file: {f.filename}')
    print(f'    kind={f.kind}  size={f.filesize}')
    print(f'    sha256={f.sha256}')

for sig in report.signatures:
    print(f'  sig: {sig.name}  score={sig.score}')

for item in report.extracted:
    cfg = item.config
    if cfg and cfg.family:
        print(f'  config: {cfg.family}  c2={cfg.c2}')
