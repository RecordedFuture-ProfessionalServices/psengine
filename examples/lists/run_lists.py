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

from psengine.config import Config
from psengine.constants import RF_TOKEN_ENV_VAR
from psengine.entity_lists import EntityListMgr
from psengine.logger import RFLogger

# Name & version of the integration itself
# Below value is set for demo purposes
APP_ID = 'list-sample/1.0.0'

# Name & version of the tool this integrates with (Optional)
# Below value is set for demo purposes
PLATFORM_ID = 'PSE/1.0.0'

# Initializes the logger
LOG = RFLogger().get_logger()


###############################################
# Argument parsing and validation
###############################################


def parse_cmdline_args():
    """Parse arguments from the command line."""
    parser = argparse.ArgumentParser(description='Recorded Future Lists example app')
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
    LOG.info('Recorded Future lists example')

    Config.init(rf_token=args.key, app_id=APP_ID, platform_id=PLATFORM_ID)

    elm = EntityListMgr()

    print('')
    LOG.info("Example how to search for lists with 'Brand' in the name")
    search_results = elm.search(list_name='Brand')

    for returned_list in search_results:
        LOG.info(
            f'List ID: {returned_list.id_}, Name: {returned_list.name}, '
            f'Owner: {returned_list.owner_name}'
        )

    print('')
    LOG.info("Example how to create a new list called 'example-list'")
    example_list = elm.create(list_name='example-list')
    LOG.info(f'ID: {example_list.id_}')
    LOG.info(f'Name: {example_list.name}')
    LOG.info(f'Owner: {example_list.owner_name}')
    LOG.info(f'Created: {example_list.created}')

    print('')
    LOG.info('Example how to fetch the list by ID')
    fetched_list = elm.fetch(search_results[0].id_)
    LOG.info(f'ID: {fetched_list.id_}')
    LOG.info(f'Name: {fetched_list.name}')
    LOG.info(f'Owner: {fetched_list.owner_name}')
    LOG.info(f'Created: {fetched_list.created}')

    print('')
    # Once you have a list, from search_lists(), create_list(), or fetch_list()
    # You can run operations on a list using the list object
    # We will use the example_list from the previous example
    LOG.info('Example how to add an entity by entity ID to the list')
    # Get size and ready status using status()
    list_status = example_list.status()
    LOG.info(f'Size before add: {list_status.size}')
    LOG.info(f'Status before add: {list_status.status}')
    LOG.info('Adding 2 entities to the list')
    example_list.add('ip:8.8.8.8')
    # add(), remove(), bulk_add(), and bulk_remove() remove support name + type or entity ID
    example_list.add(('google.com', 'InternetDomainName'))
    list_status = example_list.status()
    LOG.info(f'Size after add: {list_status.size}')
    LOG.info(f'Status after add: {list_status.status}')
    # Get entities in the list using entities()
    list_entities = example_list.entities()
    entity_info = [
        (entity.entity.name, 'Added: ' + entity.added.strftime('%Y-%m-%d %H:%M:%S'))
        for entity in list_entities
    ]
    LOG.info(f'Entities in the list: {entity_info}')
    # Get further list info using info()
    list_info = example_list.info()
    LOG.info(f'Last updated: {list_info.updated}')
    LOG.info(f'Owner name: {list_info.owner_name}')
    LOG.info(f'Owner ID: {list_info.owner_id}')
    LOG.info(f'Owner enterprise name: {list_info.owner_organisation_details.enterprise_name}')
    LOG.info(f'Owner enterprise ID: {list_info.owner_organisation_details.enterprise_id}')

    print('')
    LOG.info('Example how to remove an entity by entity ID from the list')
    # bulk_add() and bulk_remove() are supported, and take a list of IDs and name+type tuples
    example_list.bulk_remove([('8.8.8.8', 'IpAddress'), 'idn:google.com'])
    # Confirm the size is 0
    list_status = example_list.status()
    LOG.info(f'Size after remove: {list_status.size}')
    LOG.info(f'Status after remove: {list_status.status}')

    LOG.info('Recorded Future lists example completed')


if __name__ == '__main__':
    main()
