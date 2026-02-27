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


import json
import logging
from typing import Optional, Annotated, Literal, Union
from typing_extensions import Doc

from pydantic import validate_call, AfterValidator, Field

from ..helpers import debug_call, connection_exceptions
from .client import ASIClient
from ..endpoints import EP_ASI_PROJECTS, EP_ASI_ASSETS_SEARCH

from .models import (
    AssetResponse,
    Asset,
    AssetSearchFilterIn,
    ExposureSeverity,
    ProjectListResponse,
)
from .errors import FetchProjectsError, SearchAssetsError
from .constants import ASSETS_PER_PAGE


def _validate_score_range(v: tuple[int, int]) -> tuple[int, int]:
    if v[0] > v[1]:
        raise ValueError(f'exposure_score start ({v[0]}) must be <= end ({v[1]})')
    return v


EnrichmentType = Literal[
    'custom_tags',
    'dns_records',
    'whois',
    'ip_metadata',
    'open_tcp_ports',
    'open_udp_ports',
    'web_technologies',
    'certificates',
    'certificate_chain',
    'defenses',
    'exposures',
    'exposure_instance_details',
]

SortByType = Literal[
    'discovered_at',
    'added_to_project_at',
    'last_scanned_at',
    'exposure_score',
    'asset_id',
    'apex_domain',
]


class AttackSurfaceMgr:
    """Manages requests for Recorded Future SecurityTrails (ASI) API."""

    def __init__(self, api_token: str = None):
        """Initializes the `AttackSurfaceMgr` object.

        Args:
            api_token (str, optional): ASI API token.
        """
        self.log = logging.getLogger(__name__)
        self.asi_client = ASIClient(api_token=api_token) if api_token else ASIClient()

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=FetchProjectsError)
    def fetch_projects(
        self,
        sort_direction: Annotated[
            Optional[Literal['asc', 'desc']], Doc('Sort direction for the projects')
        ] = 'asc',
    ) -> Annotated[ProjectListResponse, Doc('List of ASI Project models')]:
        params = {}
        if sort_direction:
            params['sort_direction'] = sort_direction

        response = self.asi_client.request('get', EP_ASI_PROJECTS, params=params).json()
        return ProjectListResponse.model_validate(response)

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=SearchAssetsError)
    def search_assets(
        self,
        project_id: Annotated[str, Doc('The ID of the ASI project to search assets within')],
        exposure_severity: Annotated[
            Optional[Union[ExposureSeverity, list[ExposureSeverity]]],
            Doc("""Filter assets by exposure severity.
            Pass a single value or a list to match any of the provided severities."""),
        ] = None,
        exposure_signature_id: Annotated[
            Optional[Union[str, list[str]]],
            Doc("""Filter assets by ASI Signature ID. Pass a single ID or a list.
            Some signatures align with CVEs, e.g. "cve-2024-6387" or "cve-OpenSSH"."""),
        ] = None,
        exposure_score: Annotated[
            Optional[
                Annotated[
                    tuple[Annotated[int, Field(ge=0, le=100)], Annotated[int, Field(ge=0, le=100)]],
                    AfterValidator(_validate_score_range),
                ]
            ],
            Doc("""Filter assets by exposure score range (0–100). Provide a (min, max) tuple.
            The score indicates potential asset risk based on various factors."""),
        ] = None,
        exposure_last_scanned: Annotated[
            Optional[tuple[Optional[str], Optional[str]]],
            Doc("""Filter assets by the date they were last scanned for exposures.
            Provide a (start, end) tuple of "YYYY-MM-DD" strings.
            Use None for an open-ended bound."""),
        ] = None,
        enrichments: Annotated[
            list[EnrichmentType], Doc('List of enrichments to apply to the assets')
        ] = None,
        sort_by: Annotated[list[SortByType], Doc('List of fields to sort the assets by')] = [
            'discovered_at'
        ],
        assets_per_page: Annotated[
            int,
            Field(ge=1, le=1000),
            Doc('Number of assets to fetch per page'),
        ] = ASSETS_PER_PAGE,
        max_results: Annotated[Optional[int], Doc('Maximum number of assets to fetch')] = 10,
    ) -> Annotated[list[Asset], Doc('Response model for ASI assets search')]:
        """Search for assets within an ASI project.

        Does pagination requests on batches of `assets_per_page` up to `max_results`.

        Endpoint:
            `v2/projects/{project_id}/assets/_search`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            ValueError: If `exposure_score` start is greater than end.
        """
        filter_params = locals()
        for param in [
            'self',
            'project_id',
            'enrichments',
            'sort_by',
            'assets_per_page',
            'max_results',
        ]:
            filter_params.pop(param)

        body = {
            'filter': self._lookup_filter(**filter_params).model_dump(
                by_alias=True, exclude_none=True, mode='json'
            ),
            'pagination': {'limit': assets_per_page},
        }

        if enrichments:
            body['enrichments'] = enrichments
        if sort_by:
            body['sort'] = sort_by

        response = self.asi_client.request_paged(
            'post', EP_ASI_ASSETS_SEARCH.format(project_id), data=body, max_results=max_results
        )
        return [Asset.model_validate(asset) for asset in response]
        # return AssetResponse.model_validate({'data': response, 'meta': {}})

    @debug_call
    def _lookup_filter(
        self,
        exposure_severity: Optional[Union[ExposureSeverity, list[ExposureSeverity]]] = None,
        exposure_signature_id: Optional[Union[str, list[str]]] = None,
        exposure_score: Optional[
            Annotated[
                tuple[Annotated[int, Field(ge=0, le=100)], Annotated[int, Field(ge=0, le=100)]],
                AfterValidator(_validate_score_range),
            ]
        ] = None,
        exposure_last_scanned: Optional[tuple[Optional[str], Optional[str]]] = None,
    ) -> AssetSearchFilterIn:
        """Create a query for filtering asset searches."""
        params = {key: val for key, val in locals().items() if val is not None and key != 'self'}
        query = {'exposure_properties': {}}

        for k, v in params.items():
            key, value = self._process_arg(k, v)
            if isinstance(value, dict):
                query[key].update(value)
            else:
                query[key] = value

        query = {
            key: val
            for key, val in query.items()
            if not ((isinstance(val, (dict, list))) and len(val) == 0)
        }

        return AssetSearchFilterIn.model_validate(query)

    def _process_arg(self, key: str, value) -> tuple[str, dict]:
        if key == 'exposure_severity':
            filt = {'in': value} if isinstance(value, list) else {'eq': value}
            return 'exposure_properties', {'severity': filt}

        if key == 'exposure_signature_id':
            filt = {'in': value} if isinstance(value, list) else {'eq': value}
            return 'exposure_properties', {'signature_id': filt}

        if key == 'exposure_score':
            return 'exposure_properties', {
                'asset_exposure_score': {'start': value[0], 'end': value[1]}
            }

        if key == 'exposure_last_scanned':
            return 'exposure_properties', {'last_scanned_at': {'start': value[0], 'end': value[1]}}

        return key, value

    def post_request_paged(self): ...

    def get_request_paged(self):
        return self.asi_client.request_paged(
            'get',
            'https://api.securitytrails.com/v2/projects/3ce6292b-29be-4199-9024-231818e384a4/assets',
            max_results=300,
            objects_per_page=30,
        )
