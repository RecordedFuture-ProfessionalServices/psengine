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

import logging
from typing import Optional
from urllib.parse import quote

from pydantic import validate_call

from ..endpoints import CONNECT_API_BASE_URL
from ..helpers import MultiThreadingHelper, connection_exceptions, debug_call
from ..rf_client import RFClient
from .constants import (
    ALLOWED_ENTITIES,
    ENTITY_FIELDS,
    IOC_TO_MODEL,
    MALWARE_FIELDS,
    MESSAGE_404,
    TYPE_MAPPING,
)
from .errors import EnrichmentLookupError
from .lookup import EnrichmentData


class LookupMgr:
    """Enrichment of a single or a group of Entities."""

    def __init__(self, rf_token: str = None):
        """Initializes the LookupMgr object.

        Args:
            rf_token (str, optional): Recorded Future API token. Defaults to None
        """
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @validate_call
    @debug_call
    def lookup(
        self,
        entity: str,
        entity_type: ALLOWED_ENTITIES,
        fields: Optional[list[str]] = None,
    ) -> EnrichmentData:
        """Perform lookup of an entity based on its id or name.
        ``entity`` can contain both a Recorded Future ID or a entity name. See example below.

        The entity_type must always be specified.
        The allowed values are:

            - ``company``,
            - ``Company``,
            - ``company_by_domain``,
            - ``CyberVulnerability``,
            - ``domain``,
            - ``hash``,
            - ``Hash``,
            - ``InternetDomainName``,
            - ``ip``,
            - ``IpAddress``,
            - ``malware``,
            - ``Malware``,
            - ``Organization``,
            - ``url``,
            - ``URL``,
            - ``vulnerability``,

        If ``fields`` parameter is specified, it will be added to the mandatory fields, which
        are:

            - for every entity except malware: ``['entity', 'risk', 'timestamps']``
            - for malware: ``['entity', 'timestamps']``


        Examples:
            Performing a lookup using different ``entity`` type:

                .. code-block:: python
                    :linenos:

                    mgr.lookup('idn:google.com', 'domain')
                    mgr.lookup('google.com', 'domain')
                    mgr.lookup('A_BCDE', 'company')


            Performing a lookup of a ``company_by_domain`` specifying additional fields:

                .. code-block:: python
                    :linenos:

                    mgr.lookup(
                        'recordedfuture.com',
                        entity_type='company_by_domain',
                        fields=['curated']
                    )

        The output is always ``EnrichmentData`` object with a format like below:
        If a 404 is received:

            .. code-block:: python

                {
                    'entity': entity,
                    'entity_type': entity_type,
                    'is_enriched': False,
                    'content': '404 received. Nothing known on this entity',
                }

        If a 200 is received:

            .. code-block:: python

                {
                    'entity': entity,
                    'entity_type': entity_type,
                    'is_enriched': True,
                    'content': the enriched data model
                }

        To write an enriched object to file:

            .. code-block:: python
                :linenos:

                from pathlib import Path
                from json import dump
                from psengine.enrich import LookupMgr

                mgr = LookupMgr()
                OUTPUT_DIR = Path('your' / 'path')
                OUTPUT_DIR.mkdir(exists_ok=True)
                ip = mgr.lookup('1.1.1.1', 'ip')
                (OUTPUT_DIR / f'{ip.entity}.json').write_text(dumps(ip.json(), indent=2))


        Endpoint:
            ``v2/{entity_type}/{entity}``

        Args:
            entity (str): Name or RFID of the entity.
            entity_type (str): Type of the entity.
            fields (List[str], optional): Fields for the entity to enrich.
            EnrichmentData: An object containing the entity details.

        Raises:
            ValidationError If a field does not match the type hint.
            EnrichmentLookupError: if a lookup terminates with a non 200 or 404 return code.
        """
        default_fields = MALWARE_FIELDS if entity_type.lower() == 'malware' else ENTITY_FIELDS
        fields = fields if fields else default_fields
        fields = self._merge_fields(fields, default_fields)

        return self._lookup(entity, entity_type, fields)

    @validate_call
    @debug_call
    def lookup_bulk(
        self,
        entity: list[str],
        entity_type: ALLOWED_ENTITIES,
        fields: list[str] = ENTITY_FIELDS,
        max_workers: Optional[int] = 0,
    ) -> list[EnrichmentData]:
        """Perform lookup of multiple entities based on ids or name.
        ``entity`` can contain both a Recorded Future ID or a entity name.
        The entities must be of the same ``entity_type``. See example below.

        The ``entity_type`` must always be specified.
        The allowed values are:

             - ``company``,
             - ``Company``,
             - ``company_by_domain``,
             - ``CyberVulnerability``,
             - ``domain``,
             - ``hash``,
             - ``Hash``,
             - ``InternetDomainName``,
             - ``ip``,
             - ``IpAddress``,
             - ``malware``,
             - ``Malware``,
             - ``Organization``,
             - ``url``,
             - ``URL``,
             - ``vulnerability``,

        If ``fields`` parameter is specified, it will be added to the mandatory fields, which
        are:

            - for every entity except malware: ``['entity', 'risk', 'timestamps']``
            - for malware: ``['entity', 'timestamps']``

        Examples:
            Multiple IOC types enrichment:

                .. code-block:: python
                     :linenos:

                     data = {
                         'IpAddress': ['1.1.1.1', '2.2.2.2'],
                         'InternetDomainName': [ 'google.com', 'facebook.com']
                     }
                     results = []
                     for entity_type, entities in data.items():
                         results.extend(mgr.lookup_bulk(entities, entity_type)

            To write an enriched object to file:

                .. code-block:: python
                    :linenos:

                    from pathlib import Path
                    from json import dump
                    from psengine.enrich import LookupMgr

                    mgr = LookupMgr()
                    OUTPUT_DIR = Path('your' / 'path')
                    OUTPUT_DIR.mkdir(exists_ok=True)
                    data = mgr.lookup_bulk(['1.1.1.1', '8.8.8.8'], 'ip')
                    for ip in data:
                        (OUTPUT_DIR / f'{ip.entity}.json').write_text(dumps(ip.json(), indent=2))


            The output is always a list of ``EnrichmentData`` object with a format like below:
            If a 404 is received:

                .. code-block:: python

                    {
                        'entity': entity,
                        'entity_type': entity_type,
                        'is_enriched': False,
                        'content': '404 received. Nothing known on this entity',
                    }

            If a 200 is received:

                .. code-block:: python

                    {
                        'entity': entity,
                        'entity_type': entity_type,
                        'is_enriched': True,
                        'content': the enriched data model
                    }

            Multithreaded examples:

                .. code-block:: python

                    mgr.lookup_bulk(['google.com', 'facebook.com'], 'domain', max_workers=10)

        Endpoint:
             ``v2/{entity_type}/{entity}``


        Args:
             entity (List[str]): list of names or RFIDs.
             entity_type (List[str]): Type of the entities.
             fields (List[str], optional): Fields for the entities to enrich.
             max_workers (int, optional): number of workers to multithread requests.

        Returns:
             List[EnrichmentData]: A list of object containing the entity details.

        Raises:
             ValidationError If a field does not match the type hint.
             EnrichmentLookupError: if a lookup terminates with a non 200 or 404 return code.
        """
        default_fields = MALWARE_FIELDS if entity_type.lower() == 'malware' else ENTITY_FIELDS
        fields = fields if fields else default_fields
        fields = self._merge_fields(fields, default_fields)
        if max_workers:
            res = MultiThreadingHelper.multithread_it(
                max_workers,
                self._lookup,
                iterator=entity,
                entity_type=entity_type,
                fields=fields,
            )
        else:
            res = [self._lookup(entity, entity_type, fields) for entity in entity]

        return res

    def _lookup(
        self,
        entity: str,
        entity_type: str,
        fields: list,
    ):
        entity_type = TYPE_MAPPING.get(entity_type, entity_type)

        enriched = self._fetch_data(
            entity=entity,
            entity_type=entity_type,
            fields=fields,
        )
        if not enriched:
            enriched = EnrichmentData(
                entity=entity,
                entity_type=entity_type,
                is_enriched=False,
                content=MESSAGE_404,
            )

        return enriched

    @connection_exceptions(ignore_status_code=[404], exception_to_raise=EnrichmentLookupError)
    @debug_call
    def _fetch_data(self, entity: str, entity_type: str, fields: list) -> EnrichmentData:
        """Perform the actual lookup. If a 404 is returned, return None."""
        encoded_entity = quote(entity, safe='.')
        entity_type = 'company/by_domain' if entity_type == 'company_by_domain' else entity_type

        url = f'{CONNECT_API_BASE_URL}/{entity_type}/{encoded_entity}'

        params = {}
        params['fields'] = ','.join(fields)

        response = self.rf_client.request('get', url, params=params).json()
        return EnrichmentData(
            entity=entity,
            entity_type=entity_type,
            is_enriched=True,
            content=IOC_TO_MODEL[entity_type].model_validate(response['data']),
        )

    def _merge_fields(self, fields: list[str], default_fields: list[str]) -> list[str]:
        return list(set(fields).union(set(default_fields)))
