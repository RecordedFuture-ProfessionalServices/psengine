from psengine.sandbox import SandboxMgr

SAMPLE_ID = '260501-h4p7laawme'

mgr = SandboxMgr()
reports = mgr.fetch_behavioral_reports(SAMPLE_ID)

if not reports:
    print('No behavioral tasks for this sample.')
    raise SystemExit(0)

for report in reports:
    print(f'Task: {report.task_id}')
    print(f'  score={report.analysis.score}')
    print(f'  platform={report.analysis.platform}')
    print(f'  tags={report.analysis.tags}')

    for proc in report.processes[:5]:
        print(f'  pid={proc.pid}  cmd={proc.cmd}')

    for flow in report.network.flows[:5]:
        print(f'  dst={flow.dst}  domain={flow.domain}')
        print(f'    proto={flow.proto}')
