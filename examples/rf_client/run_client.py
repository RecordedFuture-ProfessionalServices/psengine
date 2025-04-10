##################################### TERMS OF USE ###########################################
# The following code is provided for demonstration purpose only, and should not be used      #
# without independent verification. Recorded Future makes no representations or warranties,  #
# express, implied, statutory, or otherwise, regarding any aspect of this code or of the     #
# information it may retrieve, and provides it both strictly “as-is” and without assuming    #
# responsibility for any information it may retrieve. Recorded Future shall not be liable    #
# for, and you assume all risk of using, the foregoing. By using this code, Customer         #
# represents that it is solely responsible for having all necessary licenses, permissions,   #
# rights, and/or consents to connect to third party APIs, and that it is solely responsible  #
# for having all necessary licenses, permissions, rights, and/or consents to any data        #
# accessed from any third party API.                                                         #
##############################################################################################

import argparse
import os

from requests import ConnectionError, ConnectTimeout, HTTPError, ReadTimeout

from psengine import RFClient
from psengine.config import Config
from psengine.constants import RF_TOKEN_ENV_VAR
from psengine.endpoints import EP_CLASSIC_ALERTS_RULES
from psengine.logger import RFLogger

# Name & version of the integration itself
# Below value is set for demo purposes
APP_ID = 'rf-client-sample/1.0.0'

# Name & version of the tool this integrates with (Optional)
# Below value is set for demo purposes
PLATFORM_ID = 'PSE/1.0.0'


# Initializes the logger
LOG = RFLogger().get_logger()


def parse_cmdline_args():
    """Parse arguments from the command line."""
    parser = argparse.ArgumentParser(description='Recorded Future RF Client example app')
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
    LOG.info('Recorded Future Client usage example')

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

    # RFClient will  automatically use the token set by the GlobalConfigSingleton,
    # but you can also pass it as a parameter RFClient(api_token='your_token)
    rfc = RFClient()

    print('')
    LOG.info('Example GET request with params')
    response = rfc.request(method='get', url=EP_CLASSIC_ALERTS_RULES, params={'limit': 1})
    LOG.info(f' Response Status Code: {response.status_code}')
    LOG.info(f' Response JSON: {response.json()}')

    print('')
    LOG.info('Example POST request with data')
    response = rfc.request(
        method='post',
        url='https://api.recordedfuture.com/threat/actor/search',
        data={'name': 'Fancy', 'limit': 1},
    )
    LOG.info(f' Response Status Code: {response.status_code}')
    LOG.info(f' Response JSON: {response.json()}')

    print('')
    LOG.info('Example paged POST request with data and max_results set to 1565')
    response = rfc.request_paged(
        method='post',
        url='https://api.recordedfuture.com/identity/credentials/search',
        max_results=1565,
        data={
            'domains': ['norsegods.online'],
            'filter': {'first_downloaded_gte': '2024-01-01T23:40:47.034Z'},
            'limit': 100,
        },
        results_path='identities',
        offset_key='offset',
    )
    LOG.info(f' Response number of results: {len(response)}')

    try:
        print('')
        LOG.info('Example request that fails, but is caught')
        # This endpoint is a post and expect a body, we will omit it to cause an error
        response = rfc.request(
            method='post', url='https://api.recordedfuture.com/threat/actor/search'
        )

    except (HTTPError, ConnectionError, ConnectTimeout, ReadTimeout) as err:
        LOG.error(f'HTTP Query failed. {err}', exc_info=False)

    print('')
    LOG.info('Recorded Future Client usage example completed')


if __name__ == '__main__':
    main()
