from psengine.sandbox import SandboxMgr

SAMPLE_ID = '260501-h4p7laawme'

mgr = SandboxMgr()
result = mgr.fetch_behavioral_reports(SAMPLE_ID)

for report in result.reports:
    print(f'Task: {report.task_id}')
    print(f'  score={report.analysis.score}')
    print(f'  platform={report.analysis.platform}')
    print(f'  tags={report.analysis.tags}')

    for proc in report.processes[:5]:
        print(f'  pid={proc.pid}  cmd={proc.cmd}')

    for flow in report.network.flows[:5]:
        print(f'  dst={flow.dst}  domain={flow.domain}')
        print(f'    proto={flow.proto}')

if not result.complete:
    print(f'Still running, retry later: {result.not_ready}')

for failure in result.failed:
    print(
        f'Fetch failed for {failure.task_id}: '
        f'{failure.status_code} {failure.message}'
    )
