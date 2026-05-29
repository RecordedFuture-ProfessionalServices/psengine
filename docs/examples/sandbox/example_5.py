from psengine.sandbox import SandboxMgr

mgr = SandboxMgr()

submission = mgr.submit_sample(
    kind='url',
    url='https://example.com',
    user_tags=['psengine-docs', 'delete-me'],
)
print(
    f'Submitted {submission.id_} (status={submission.status})'
)

result = mgr.delete_sample(submission.id_)
print(f'Delete result: deleted={result.deleted}')
