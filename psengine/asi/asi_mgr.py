import json
import logging
from typing import Optional, Annotated, Literal
from typing_extensions import Doc

from pydantic import validate_call

from ..helpers import debug_call, connection_exceptions
from .client import ASIClient
from ..endpoints import EP_ASI_PROJECTS, EP_ASI_ASSETS_SEARCH

from .models import ProjectListResponse, AssetResponse
from .errors import FetchProjectsError
from .constants import ASSETS_PER_PAGE

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
        ] = None,
    ) -> Annotated[ProjectListResponse, Doc('List of ASI Project models')]:
        params = {}
        if sort_direction:
            params['sort_direction'] = sort_direction

        response = self.asi_client.request('get', EP_ASI_PROJECTS, params=params).json()
        return ProjectListResponse.model_validate(response)

    @debug_call
    @validate_call
    # @connection_exceptions(ignore_status_code=[], exception_to_raise=FetchProjectsError)
    def search_assets(
        self,
        project_id: Annotated[str, Doc('The ID of the ASI project to search assets within')],
        enrichments: Annotated[
            list[EnrichmentType], Doc('List of enrichments to apply to the assets')
        ] = None,
        sort_by: Annotated[list[SortByType], Doc('List of fields to sort the assets by')] = None,
        assets_per_page: Annotated[
            int, Doc('Number of assets to fetch per page')
        ] = ASSETS_PER_PAGE,
        max_results: Annotated[Optional[int], Doc('Maximum number of assets to fetch')] = None,
    ) -> Annotated[AssetResponse, Doc('Response model for ASI assets search')]:
        body = {'pagination': {'limit': assets_per_page}}

        response = self.asi_client.request_paged(
            'post', EP_ASI_ASSETS_SEARCH.format(project_id), data=body
        )

        print(json.dumps(response, indent=2))

        return AssetResponse.model_validate(response)

    def post_request_paged(self): ...

    def get_request_paged(self):
        return self.asi_client.request_paged(
            'get',
            'https://api.securitytrails.com/v2/projects/3ce6292b-29be-4199-9024-231818e384a4/assets',
            max_results=300,
            objects_per_page=30,
        )
