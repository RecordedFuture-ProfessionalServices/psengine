import logging

import pytest
import vcr

# Sensitive data to be filtered from headers
FILTER_HEADERS = [('X-RFToken', 'REDACTED_TOKEN'), ('Authorization', 'Bearer REDACTED_TOKEN')]

log = logging.getLogger(__name__)


def scrub_response(response):
    """Scrub sensitive data from the response body."""
    try:
        # If the response is JSON, we can obfuscate specific proprietary fields
        body = response['body']['string'].decode('utf-8')

        # Simple obfuscation: recursively find and replace proprietary looking strings if needed
        # Or just redact the raw JSON string
        body = body.replace('Recorded Future', 'REDACTED_VENDOR')
        # Here we could also redact specific links or IDs if required

        response['body']['string'] = body.encode('utf-8')
    except (UnicodeDecodeError, KeyError, TypeError) as err:
        log.debug(f'Skipping response body obfuscation: {err}')

    # Also strip any set-cookie headers
    if 'Set-Cookie' in response['headers']:
        del response['headers']['Set-Cookie']

    return response


links_vcr = vcr.VCR(
    cassette_library_dir='tests/links/cassettes',
    record_mode='once',
    filter_headers=[h[0] for h in FILTER_HEADERS],
    before_record_response=scrub_response,
    match_on=['method', 'scheme', 'host', 'port', 'path', 'query'],
    decode_compressed_response=True,
)


@pytest.fixture(scope='module')
def vcr_config():
    return {
        'filter_headers': [h[0] for h in FILTER_HEADERS],
        'before_record_response': scrub_response,
        'decode_compressed_response': True,
    }
