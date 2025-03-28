"""##################################### TERMS OF USE ###########################################
# The following code is provided for demonstration purpose only, and should not be used      #
# without independent verification. makes no representations or warranties,  #
# express, implied, statutory, or otherwise, regarding any aspect of this code or of the     #
# information it may retrieve, and provides it both strictly “as-is” and without assuming    #
# responsibility for any information it may retrieve. shall not be liable    #
# for, and you assume all risk of using, the foregoing. By using this code, Customer         #
# represents that it is solely responsible for having all necessary licenses, permissions,   #
# rights, and/or consents to connect to third party APIs, and that it is solely responsible  #
# for having all necessary licenses, permissions, rights, and/or consents to any data        #
# accessed from any third party API.                                                         #.
##############################################################################################
"""

import argparse
import os

from requests import ConnectionError, ConnectTimeout, HTTPError, ReadTimeout

from psengine import BaseHTTPClient
from psengine.config import Config, get_config
from psengine.constants import RF_TOKEN_ENV_VAR
from psengine.endpoints import EP_ALERT_RULE
from psengine.logger import RFLogger

# Name & version of the integration itself
# Below value is set for demo purposes
APP_ID = 'base-client-sample/1.0.0'

# Name & version of the tool this integrates with (Optional)
# Below value is set for demo purposes
PLATFORM_ID = 'PSE/1.0.0'

# Initializes the logger
LOG = RFLogger().get_logger()


def parse_cmdline_args():
    """Parse arguments from the command line."""
    LOG.info('Parsing command line arguments')
    parser = argparse.ArgumentParser(description='Base HTTP Client example app')
    parser.add_argument(
        '-k',
        '--key',
        help='Recorded Future API key',
        default=os.environ.get(RF_TOKEN_ENV_VAR),
    )
    parser.add_argument(
        '--log-level',
        help='Logging level',
        dest='log_level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    )

    return parser.parse_args()


def main():
    args = parse_cmdline_args()
    LOG.setLevel(args.log_level)
    LOG.info('Base HTTP Client usage example')

    Config.init(rf_token=args.key, app_id=APP_ID, platform_id=PLATFORM_ID)
    # Example how to run this with a proxy
    # Config.init(
    #     rf_token=args.key,
    #     app_id=APP_ID,
    #     platform_id=PLATFORM_ID,
    #     http_proxy='http://localhost:8080',
    #     https_proxy='https://localhost:8080',
    #     client_ssl_verify=False,
    # )

    config = get_config()

    bc = BaseHTTPClient()

    print('')
    LOG.info('Example GET request with headers and params')
    response = bc.call(
        method='get',
        url=EP_ALERT_RULE,
        headers={'X-RFToken': config.rf_token.get_secret_value()},
        params={'limit': 1},
    )
    LOG.info(f' Response Status Code: {response.status_code}')
    LOG.info(f' Response JSON: {response.json()}')

    print('')
    LOG.info('Example POST request with JSON body')
    response = bc.call(method='post', url='https://httpbin.org/post', data={'key': 'value'})
    LOG.info(f' Response Status Code: {response.status_code}')

    print('')
    LOG.info('Example PUT request with JSON body')
    response = bc.call(method='put', url='https://httpbin.org/put', data={'key': 'value'})
    LOG.info(f' Response Status Code: {response.status_code}')

    print('')
    LOG.info('Example DELETE request')
    response = bc.call(method='delete', url='https://httpbin.org/delete')
    LOG.info(f' Response Status Code: {response.status_code}')

    print('')
    LOG.info('Example HEAD request to check Fusion File date')
    response = bc.call(
        method='head',
        url='https://api.recordedfuture.com/v2/fusion/files',
        params={'path': '/public/hunt/threatactor/risklists/ta_domain_risklist.csv'},
        headers={'X-RFToken': config.rf_token.get_secret_value()},
    )
    LOG.info(f' Response Status Code: {response.status_code}')
    LOG.info(f' Date in response headers: {response.headers.get("date")}')

    try:
        print('')
        LOG.info('Example request that fails, but is caught')
        # The RF API Key was not provided, this will cause a 401 Unauthorized
        response = bc.call(method='post', url='https://api.recordedfuture.com/threat/actor/search')

    except (HTTPError, ConnectionError, ConnectTimeout, ReadTimeout) as err:
        LOG.error(f'HTTP Query failed. {err}', exc_info=False)

    print('')
    LOG.info('Base HTTP Client usage example completed')


if __name__ == '__main__':
    main()
