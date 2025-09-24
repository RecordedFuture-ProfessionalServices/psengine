from psengine.fusion import FusionMgr

mgr = FusionMgr()
head_data = mgr.head_files('/public/risklists/default_ip_risklist.csv')

print(f'File Path: {head_data[0].file_path}')
print(f'File Found: {head_data[0].file_found}')
if head_data[0].file_found:
    print(f'ETag: {head_data[0].etag}')
    print(f'Content Disposition: {head_data[0].content_disposition}')
