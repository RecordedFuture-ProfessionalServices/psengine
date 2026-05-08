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
from typing import Annotated, Optional
from urllib.parse import quote

from pydantic import validate_call
from typing_extensions import Doc

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

    def __init__(
        self,
        rf_token: Annotated[Optional[str], Doc('Recorded Future API token.')] = None,
    ):
        """Initialize the `LookupMgr` object."""
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @validate_call
    @debug_call
    def lookup(
        self,
        entity: Annotated[str, Doc('Name or Recorded Future ID of the entity.')],
        entity_type: Annotated[ALLOWED_ENTITIES, Doc('Type of the entity to enrich.')],
        fields: Annotated[
            Optional[list[str]], Doc('Optional additional fields for enrichment.')
        ] = None,
    ) -> Annotated[EnrichmentData, Doc('An object containing the enriched entity details.')]:
        """Perform lookup of an entity based on its ID or name.

        The `entity` can be either a Recorded Future ID or a readable entity name.
        The `entity_type` must always be specified. Allowed values include:

        - `company`
        - `Company`
        - `company_by_domain`
        - `CyberVulnerability`
        - `domain`
        - `hash`
        - `Hash`
        - `InternetDomainName`
        - `ip`
        - `IpAddress`
        - `malware`
        - `Malware`
        - `Organization`
        - `organization`
        - `url`
        - `URL`
        - `vulnerability`

        If `fields` are specified, they are added to the mandatory fields:

        - All entities except malware: `['entity', 'risk', 'timestamps']`
        - For malware: `['entity', 'timestamps']`

        Endpoint:
            `v2/{entity_type}/{entity}`

        Example:
            ```python
            from psengine.enrich import LookupMgr

            mgr = LookupMgr()
            enriched_dom = mgr.lookup('idn:google.com', 'domain')
            enriched_dom2 = mgr.lookup('google.com', 'domain')
            enriched_company_via_id = mgr.lookup('A_BCDE', 'company')
            ```

            Lookup with additional fields:
            ```python
            from psengine.enrich import LookupMgr

            mgr = LookupMgr()
            enriched_dom = mgr.lookup('idn:google.com', 'domain')
            company_by_domain = mgr.lookup(
                'recordedfuture.com',
                entity_type='company_by_domain',
                fields=['curated']
            )
            ```
            To save to file:
            ```python
            from pathlib import Path
            from json import dumps

            OUTPUT_DIR = Path('your' / 'path')
            OUTPUT_DIR.mkdir(exist_ok=True)
            ip = mgr.lookup('1.1.1.1', 'ip')
            (OUTPUT_DIR / f'{ip.entity}.json').write_text(dumps(ip.json(), indent=2))
            ```

        If a 404 is received:
        ```python
        {
            'entity': entity,
            'entity_type': entity_type,
            'is_enriched': False,
            'content': '404 received. Nothing known on this entity',
        }
        ```

        If a 200 is received:
        ```python
        {
            'entity': entity,
            'entity_type': entity_type,
            'is_enriched': True,
            'content': the enriched data model
        }
        ```
        Raises:
            ValidationError: if any supplied parameter is of incorrect type.
            EnrichmentLookupError: If the lookup fails with a non-200 or non-404 status.
        """
        default_fields = MALWARE_FIELDS if entity_type.lower() == 'malware' else ENTITY_FIELDS
        fields = fields or default_fields
        fields = self._merge_fields(fields, default_fields)

        return self._lookup(entity, entity_type, fields)

    @validate_call
    @debug_call
    def lookup_bulk(
        self,
        entity: Annotated[list[str], Doc('List of entity names or Recorded Future IDs.')],
        entity_type: Annotated[ALLOWED_ENTITIES, Doc('Type of the entities to enrich.')],
        fields: Annotated[
            list[str], Doc('Optional additional fields for enrichment.')
        ] = ENTITY_FIELDS,
        max_workers: Annotated[
            Optional[int], Doc('Number of workers to multithread requests.')
        ] = 0,
    ) -> Annotated[
        list[EnrichmentData], Doc('A list of objects containing the enriched entity details.')
    ]:
        """Perform lookup of multiple entities based on IDs or names.

        The `entity` list can contain Recorded Future IDs or plain entity names.
        All entities must be of the same `entity_type`.

        Allowed `entity_type` values include:

        - `company`
        - `Company`
        - `company_by_domain`
        - `CyberVulnerability`
        - `domain`
        - `hash`
        - `Hash`
        - `InternetDomainName`
        - `ip`
        - `IpAddress`
        - `malware`
        - `Malware`
        - `Organization`
        - `organization`
        - `url`
        - `URL`
        - `vulnerability`

        If `fields` are specified, they are added to the mandatory fields:

        - All entities except malware: `['entity', 'risk', 'timestamps']`
        - For malware: `['entity', 'timestamps']`

        Endpoint:
            `v2/{entity_type}/{entity}`

        Example:
            ```python
            from psengine.enrich import LookupMgr

            mgr = LookupMgr()
            data = {
                'IpAddress': ['1.1.1.1', '2.2.2.2'],
                'InternetDomainName': ['google.com', 'facebook.com']
            }
            results = []
            for entity_type, entities in data.items():
                results.extend(mgr.lookup_bulk(entities, entity_type))
            ```

            To save the results:
            ```python
            from pathlib import Path
            from json import dumps

            OUTPUT_DIR = Path('your' / 'path')
            OUTPUT_DIR.mkdir(exist_ok=True)
            results = mgr.lookup_bulk(['1.1.1.1', '8.8.8.8'], 'ip')
            for entity in results:
                (OUTPUT_DIR / f'{entity.entity}.json').write_text(dumps(entity.json(), indent=2))
            ```

            With multithreading:
            ```python
            from psengine.enrich import LookupMgr

            mgr = LookupMgr()
            domains = mgr.lookup_bulk(['google.com', 'facebook.com'], 'domain', max_workers=10)
            ```

        If a 404 is received:
        ```python
        {
            'entity': entity,
            'entity_type': entity_type,
            'is_enriched': False,
            'content': '404 received. Nothing known on this entity',
        }
        ```

        If a 200 is received:
        ```python
        {
            'entity': entity,
            'entity_type': entity_type,
            'is_enriched': True,
            'content': the enriched data model
        }
        ```

        Raises:
            ValidationError: if any supplied parameter is of incorrect type.
            EnrichmentLookupError: If a lookup terminates with a non-200 or 404 return code.
        """
        default_fields = MALWARE_FIELDS if entity_type.lower() == 'malware' else ENTITY_FIELDS
        fields = fields or default_fields
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
        entity_type = TYPE_MAPPING.get(entity_type.lower(), entity_type.lower())

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
