import io
import os
from urllib.parse import quote

import requests

from psengine import RFClient

outfile = io.BytesIO()
outfile.write(b"{'a': 10, 'b': 20}")
outfile.seek(0)

filename = 'moise_example.json'
path = f'/home/moise/{filename}'


# print('Example with requests')
# response = requests.request(
#     'post',
#     f'https://api.recordedfuture.com/v2/fusion/files/?path={quote(path, safe="")}',
#     files={filename: outfile},
#     headers={'X-RFToken': os.getenv('RF_TOKEN')},
# )
# print(response.status_code)

print('Example with psengine')
client = RFClient()
response = client.request(
    'post',
    f'https://api.recordedfuture.com/v2/fusion/files/?path={quote(path, safe="")}',
    files={filename: outfile},
)
print(response.status_code)
