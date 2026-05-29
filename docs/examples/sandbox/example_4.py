import time

from psengine.sandbox import SandboxMgr

TERMINAL = {'reported', 'failed'}
POLL_INTERVAL_SEC = 10
TIMEOUT_SEC = 600

mgr = SandboxMgr()

# TODO - should add sample with file submission instead
submission = mgr.submit_sample(
    kind='url', url='https://example.com'
)
print(
    f'Submitted {submission.id_}, polling until terminal status...'
)

deadline = time.monotonic() + TIMEOUT_SEC
while time.monotonic() < deadline:
    sample = mgr.fetch_sample_analysis_result(
        submission.id_
    )
    print(f'  status={sample.status}')
    if sample.status in TERMINAL:
        break
    time.sleep(POLL_INTERVAL_SEC)
else:
    raise RuntimeError(
        f'Sample {submission.id_} did not reach a terminal status in {TIMEOUT_SEC}s'
    )

summary = mgr.fetch_sample_summary(submission.id_)
print(f'\nScore: {summary.score}')
print(f'Target: {summary.target}')
for task_key, task in summary.tasks.items():
    print(f'  task={task_key}')
