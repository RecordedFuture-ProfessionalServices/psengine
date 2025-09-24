from pathlib import Path

from psengine.fusion import FusionMgr

file_to_upload = Path(__file__).parent / 'file.txt'
file_to_upload.touch(exist_ok=True)
file_to_upload.write_text('example')


mgr = FusionMgr()
post_result = mgr.post_file(
    file_to_upload, '/home/file.txt'
)

print(post_result)
