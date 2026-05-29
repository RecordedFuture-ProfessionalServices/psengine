from psengine.sandbox import SandboxMgr

mgr = SandboxMgr()

result = mgr.submit_sample(
    kind='url',
    url='https://example.com',
    user_tags=['psengine-docs', 'demo'],
)

print(
    f'Submitted: id={result.id_}, kind={result.kind}, status={result.status}'
)
