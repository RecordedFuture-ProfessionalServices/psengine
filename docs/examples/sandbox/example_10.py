from psengine.sandbox import SandboxMgr

SAMPLE_ID = '260501-h4p7laawme'

mgr = SandboxMgr()

# wait_until_ready=True polls until every task resolves
# or `timeout` seconds elapse. Never raises on timeout --
# check `result.complete` instead.
result = mgr.fetch_behavioral_reports(
    SAMPLE_ID, max_workers=10, wait_until_ready=True
)

if result.complete:
    print('No tasks pending.')
else:
    print('Timed out, still pending:', result.not_ready)

for report in result.reports:
    print(f'Task: {report.task_id}')
    print(f'  score={report.analysis.score}')
    print(f'  platform={report.analysis.platform}')

for failure in result.failed:
    print(
        f'Fetch failed for {failure.task_id}: '
        f'{failure.status_code} {failure.message}'
    )
