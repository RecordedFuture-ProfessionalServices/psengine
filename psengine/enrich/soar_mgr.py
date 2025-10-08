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
from itertools import chain
from typing import Annotated, Optional

from pydantic import validate_call
from typing_extensions import Doc

from ..endpoints import EP_SOAR_ENRICHMENT
from ..helpers import MultiThreadingHelper, connection_exceptions, debug_call
from ..rf_client import RFClient
from .constants import SOAR_POST_ROWS
from .errors import EnrichmentSoarError
from .soar import SOAREnrichedEntity, SOAREnrichIn, SOAREnrichOut


class SoarMgr:
    """Perform SOAR enrichment of entities."""

    def __init__(
        self,
        rf_token: Annotated[Optional[str], Doc('Recorded Future API token.')] = None,
    ):
        """Initialize the `SoarMgr` object."""
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @validate_call
    @debug_call
    def soar(
        self,
        ip: Annotated[Optional[list[str]], Doc('List of IP addresses to enrich.')] = None,
        domain: Annotated[Optional[list[str]], Doc('List of domains to enrich.')] = None,
        hash_: Annotated[Optional[list[str]], Doc('List of file hashes to enrich.')] = None,
        vulnerability: Annotated[
            Optional[list[str]], Doc('List of vulnerabilities to enrich.')
        ] = None,
        url: Annotated[Optional[list[str]], Doc('List of URLs to enrich.')] = None,
        companybydomain: Annotated[
            Optional[list[str]], Doc('List of company domains to enrich.')
        ] = None,
        max_workers: Annotated[
            Optional[int], Doc('Number of workers to multithread requests.')
        ] = 0,
    ) -> Annotated[list[SOAREnrichOut], Doc('A list of enriched data for the provided IOCs.')]:
        """Enrich multiple types of IOCs via the SOAR API.

        This method supports batch processing of IOC types including IPs, domains, hashes,
        vulnerabilities, URLs, and company domains. Uses multithreading if `max_workers` > 0.

        Endpoint:
            `soar/v3/enrichment`

        Example:
            Simple bulk enrichment:
            ```python
            from psengine.enrich import SoarMgr

            mgr = SoarMgr()
            ips = mgr.soar(ip=['1.1.1.1'])
            ```

            With multithreading:
            ```python
            from psengine.enrich import SoarMgr

            mgr = SoarMgr()
            ips = mgr.soar(ip=['1.1.1.1'], max_workers=10)
            ```

            Save enriched results to file:
            ```python
            from pathlib import Path
            from json import dumps
            from psengine.enrich import SoarMgr

            mgr = SoarMgr()

            OUTPUT_DIR = Path('your' / 'path')
            OUTPUT_DIR.mkdir(exist_ok=True)
            data = mgr.soar(ip=['1.1.1.1', '8.8.8.8'])
            for ip in data:
                (OUTPUT_DIR / f'{ip.entity}.json').write_text(dumps(ip.json(), indent=2))
            ```

        Raises:
            ValueError: If no parameters are provided or all provided lists are empty.
            ValidationError: if any supplied parameter is of incorrect type.
            EnrichmentSoarError: If an HTTP or JSON decoding error occurs during enrichment.
        """
        iocs = {
            'ip': ip,
            'domain': domain,
            'hash': hash_,
            'vulnerability': vulnerability,
            'url': url,
            'companybydomain': companybydomain,
        }
        iocs = {k: v for k, v in iocs.items() if v}
        if not iocs:
            raise ValueError('At least one parameter must be used')

        results = []
        if max_workers:
            results.append(
                chain.from_iterable(
                    MultiThreadingHelper.multithread_it(
                        max_workers,
                        self._fetch_data,
                        iterator=self._batched_cross_entity(iocs, SOAR_POST_ROWS),
                    )
                )
            )
        else:
            results = [
                self._fetch_data(batched_iocs)
                for batched_iocs in self._batched_cross_entity(iocs, SOAR_POST_ROWS)
            ]

        return list(chain.from_iterable(results))

    def _batched_cross_entity(self, iocs, batch_size):
        """Batches the SOAR data in dict of maximum SOAR_POST_ROWS elements in total.
        It always return a list of SoarRequest compatible object as dict.
        """
        batches = []
        current_batch = {k: [] for k in iocs}
        current_count = 0

        for k, vals in iocs.items():
            for v in vals:
                if current_count >= batch_size:
                    batches.append({k: v for k, v in current_batch.items() if v})
                    current_batch = {k: [] for k in iocs}
                    current_count = 0

                current_batch[k].append(v)
                current_count += 1

        batches.append({k: v for k, v in current_batch.items() if v})
        return batches

    @connection_exceptions(ignore_status_code=[], exception_to_raise=EnrichmentSoarError)
    @debug_call
    def _fetch_data(self, data: dict) -> list[SOAREnrichOut]:
        """Perform soar post request and raises EnrichementSoarError if something goes wrong."""
        data = SOAREnrichIn.model_validate(data)
        res = self.rf_client.request('post', EP_SOAR_ENRICHMENT, data=data.json()).json()['data'][
            'results'
        ]
        result = []

        for d in res:
            content = SOAREnrichedEntity.model_validate(d)
            entity = content.entity.name
            result.append(SOAREnrichOut(entity=entity, is_enriched=True, content=content))

        return result
