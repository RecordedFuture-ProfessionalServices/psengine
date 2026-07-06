from psengine.sandbox import SandboxMgr
from psengine.sandbox.errors import (
    SampleReportNotAvailableError,
)

SAMPLE_ID = '260501-h4p7laawme'

mgr = SandboxMgr()

try:
    report = mgr.fetch_sample_overview_report(
        SAMPLE_ID
    )
except SampleReportNotAvailableError as exc:
    print(f'{SAMPLE_ID}: analysis not complete.')
    print('Retry once the sample is reported.')
    raise SystemExit(1) from exc

print(f'Score:  {report.analysis.score}')
print(f'Family: {report.analysis.family}')
print(f'Tags:   {report.analysis.tags}')

for cfg in report.extracted:
    if cfg.config:
        fam = cfg.config.family
        c2 = cfg.config.c2
        print(f'  config: {fam}  c2={c2}')

for target in report.targets:
    print(f'\nTarget: {target.target}')
    print(f'  score={target.score}')
    if target.iocs:
        print(f'  domains={target.iocs.domains}')
        print(f'  ips={target.iocs.ips}')

for task_id, task in report.tasks.items():
    print(f'  {task_id}  {task.kind}  {task.status}')
    print(f'    score={task.score}')
