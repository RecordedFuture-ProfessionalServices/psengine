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
from typing import Annotated, Literal, Optional, Union

from pydantic import AfterValidator, Field, validate_call
from typing_extensions import Doc

from psengine.constants import DEFAULT_LIMIT

from ..endpoints import (
    EP_ASI_ASSET,
    EP_ASI_ASSET_EXPOSURES,
    EP_ASI_ASSETS,
    EP_ASI_ASSETS_SEARCH,
    EP_ASI_EXPOSURES,
    EP_ASI_EXPOSURES_BY_SIGNATURE,
    EP_ASI_PROJECTS,
)
from ..helpers import connection_exceptions, debug_call
from .asi import Asset, AssetResponse, AssetWithExposureSearch, ExposureSearchOut
from .client import ASIClient
from .constants import ASSETS_PER_PAGE, MAX_ASI_PAGE_SIZE, AssetType, EnrichmentType, SortByType
from .errors import AttackSurfaceExposureSearchError, FetchProjectsError, SearchAssetsError
from .models import (
    AssetSearchFilterIn,
    AssetSearchRequest,
    ExposureSeverity,
    ProjectListOut,
)

SEVERITY_FILTER = Literal['unknown', 'informational', 'moderate', 'critical']


# Raised a ticket for this, if ASI API adds this check, we will remove it from here.
def _validate_exposure_score_range(v: tuple[int, int]) -> tuple[int, int]:
    if v[0] > v[1]:
        raise ValueError(f'exposure_score start ({v[0]}) must be <= end ({v[1]})')
    return v


_list_or_eq = lambda v: {'in': v} if isinstance(v, list) else {'eq': v}  # noqa: E731
_range = lambda v: {'start': v[0], 'end': v[1]}  # noqa: E731
_eq = lambda v: {'eq': v}  # noqa: E731
_contains = lambda v: {'contains': v}  # noqa: E731

# Maps search_assets() param name -> (filter group, API field name, value transformer)
# Column layout:
#   key: (filter group, API field name, value transformer)
_ASSET_SEARCH_QUERY_MAP: dict[str, tuple[str, str, callable]] = {
    'quick_search': ('quick_search', 'search', lambda v: v),
    'asset_id': ('asset_properties', 'asset_id', _eq),
    'asset_name': ('asset_properties', 'name', _contains),
    'asset_apex_domain': ('asset_properties', 'apex', _list_or_eq),
    'asset_discovered_date': ('asset_properties', 'discovered', _range),
    'asset_type': ('asset_properties', 'type', _eq),
    'custom_tags': ('asset_properties', 'custom_tags', _list_or_eq),
    'is_static_asset': ('asset_properties', 'static_asset', _eq),
    'certificate_issuer': ('certificate_properties', 'certificate_issuer', _list_or_eq),
    'exposure_last_scanned': ('exposure_properties', 'last_scanned_at', _range),
    'exposure_score': ('exposure_properties', 'asset_exposure_score', _range),
    'exposure_severity': ('exposure_properties', 'severity', _list_or_eq),
    'exposure_signature_id': ('exposure_properties', 'signature_id', _list_or_eq),
    'is_responsive': ('technology_properties', 'is_responsive', _eq),
    'open_port_number': ('technology_properties', 'open_port_number', _list_or_eq),
    'open_port_protocol': ('technology_properties', 'open_port_protocol', _list_or_eq),
    'open_port_service': ('technology_properties', 'open_port_service', _list_or_eq),
    'technology_name': ('technology_properties', 'technology_name', _list_or_eq),
}


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
    ) -> Annotated[ProjectListOut, Doc('List of ASI Project models')]:
        params = {}
        if sort_direction:
            params['sort_direction'] = sort_direction

        response = self.asi_client.request('get', EP_ASI_PROJECTS, params=params).json()
        return ProjectListOut.model_validate(
            {'content': response['data'], 'meta': response['meta']}
        )

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=SearchAssetsError)
    def search_assets(
        self,
        project_id: Annotated[str, Doc('The ID of the ASI project to search assets within')],
        quick_search: Annotated[
            Optional[str],
            Doc('Search term to match against asset name, IP addresses, and technology fields'),
        ] = None,
        asset_id: Annotated[
            Optional[str],
            Doc(
                """Filter for the specific asset, which will be either a IP or domain value
                (examples: 192.88.99.2 or www.example.com)."""
            ),
        ] = None,
        asset_name: Annotated[
            Optional[str], Doc("""Filter on the name of the asset(IP address or domain).""")
        ] = None,
        asset_apex_domain: Annotated[
            Optional[Union[str, list[str]]],
            Doc(
                """Filter on the apex domain of the asset (example: example.com).
                Pass a single value or a list."""
            ),
        ] = None,
        asset_discovered_date: Annotated[
            Optional[tuple[Optional[str], Optional[str]]],
            Doc(
                """Filter on the date (Y-m-d) the asset was discovered by Recorded Future ASI.
                This may be different than when the asset was added to the project.
                IPv4 addresses will have a fixed point in the past for their discovery date.
                Use None for an open-ended bound."""
            ),
        ] = None,
        asset_type: Annotated[
            Optional[AssetType],
            Doc(
                """The type of asset, one of: ip, domain and host
                (where domain and host represent the same asset type)."""
            ),
        ] = None,
        custom_tags: Annotated[
            Optional[list[str]],
            Doc('Filter for assets tagged with any of the provided custom tags.'),
        ] = None,
        is_static_asset: Annotated[
            Optional[bool],
            Doc(
                """Filter for assets that are static, meaning they have a consistent IP address or
                domain name over time."""
            ),
        ] = None,
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
                    AfterValidator(_validate_exposure_score_range),
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
        open_port_number: Annotated[
            Optional[Union[int, list[int]]],
            Doc(
                """Filter for assets which have an open port with the provided number (e.g. 80)."""
            ),
        ] = None,
        open_port_service: Annotated[
            Optional[Union[str, list[str]]],
            Doc(
                """Filter for assets which have an open port with the provided service (e.g. http,
                ftp, rdp)."""
            ),
        ] = None,
        open_port_protocol: Annotated[
            Optional[Union[str, list[str]]],
            Doc(
                """Filter for assets which have an open port with the provided protocol (e.g. tcp,
                udp)."""
            ),
        ] = None,
        technology_name: Annotated[
            Optional[Union[str, list[str]]],
            Doc(
                """Filter for the name of a technology found on the asset. Could be directly
                attached to the port (nginx, etc) or a web technology (e.g. 'jQuery',
                'Wordpress'))."""
            ),
        ] = None,
        certificate_issuer: Annotated[
            Optional[Union[str, list[str]]],
            Doc(
                """Filter where the certificate (or in the chain) issuer's common name
                or organization matches the provided value"""
            ),
        ] = None,
        is_responsive: Annotated[
            Optional[bool],
            Doc(
                """Filter for assets that are unresponsive over ICMP and no ports are open.
                This is a boolean filter, so it will return assets that are either responsive
                or not responsive."""
            ),
        ] = None,
        enrichments: Annotated[
            list[EnrichmentType], Doc('List of enrichments to apply to the assets')
        ] = None,
        sort_by: Annotated[list[SortByType], Doc('List of fields to sort the assets by')] = None,
        assets_per_page: Annotated[
            int,
            Field(ge=1, le=MAX_ASI_PAGE_SIZE),
            Doc('Number of assets to fetch per page'),
        ] = ASSETS_PER_PAGE,
        max_results: Annotated[
            Optional[int], Doc('Maximum number of assets to fetch')
        ] = DEFAULT_LIMIT,
    ) -> Annotated[AssetResponse, Doc('Response model for ASI assets search')]:
        """Search for assets within an ASI project.

        Does pagination requests on batches of `assets_per_page` up to `max_results`.

        Endpoint:
            `v2/projects/{project_id}/assets/_search`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            ValueError: If `exposure_score` start is greater than end.
        """
        if sort_by is None:
            sort_by = ['discovered_at']
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

        filter_dict = self._lookup_filter(**filter_params)
        body = {'pagination': {'limit': assets_per_page}}
        if filter_dict:
            body['filter'] = filter_dict

        if enrichments:
            body['enrichments'] = enrichments
        if sort_by:
            body['sort'] = sort_by

        data = AssetSearchRequest.model_validate(body).model_dump(
            by_alias=True, exclude_none=True, mode='json'
        )
        response = self.asi_client.request_paged(
            'post', EP_ASI_ASSETS_SEARCH.format(project_id), data=data, max_results=max_results
        )

        return AssetResponse.model_validate({'content': response['data'], 'meta': response['meta']})

    @debug_call
    def _lookup_filter(
        self,
        quick_search: Optional[str] = None,
        asset_id: Optional[str] = None,
        asset_name: Optional[str] = None,
        asset_apex_domain: Optional[Union[str, list[str]]] = None,
        asset_type: Optional[AssetType] = None,
        asset_discovered_date: Optional[tuple[Optional[str], Optional[str]]] = None,
        custom_tags: Optional[list[str]] = None,
        is_static_asset: Optional[bool] = None,
        open_port_number: Optional[Union[int, list[int]]] = None,
        open_port_service: Optional[Union[str, list[str]]] = None,
        open_port_protocol: Optional[Union[str, list[str]]] = None,
        technology_name: Optional[Union[str, list[str]]] = None,
        certificate_issuer: Optional[Union[str, list[str]]] = None,
        is_responsive: Optional[bool] = None,
        exposure_severity: Optional[Union[ExposureSeverity, list[ExposureSeverity]]] = None,
        exposure_signature_id: Optional[Union[str, list[str]]] = None,
        exposure_score: Optional[
            Annotated[
                tuple[Annotated[int, Field(ge=0, le=100)], Annotated[int, Field(ge=0, le=100)]],
                AfterValidator(_validate_exposure_score_range),
            ]
        ] = None,
        exposure_last_scanned: Optional[tuple[Optional[str], Optional[str]]] = None,
    ) -> AssetSearchFilterIn:
        """Create a query for filtering asset searches."""
        params = {key: val for key, val in locals().items() if val is not None and key != 'self'}
        query = {
            'asset_properties': {},
            'certificate_properties': {},
            'exposure_properties': {},
            'technology_properties': {},
            'quick_search': {},
        }

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

        return AssetSearchFilterIn.model_validate(query).json()

    def _process_arg(self, key: str, value) -> tuple[str, dict]:
        if key not in _ASSET_SEARCH_QUERY_MAP:
            return key, value
        group, field, transform = _ASSET_SEARCH_QUERY_MAP[key]
        return group, {field: transform(value)}

    @debug_call
    @validate_call
    @connection_exceptions(
        ignore_status_code=[], exception_to_raise=AttackSurfaceExposureSearchError
    )
    def search_exposures(
        self,
        project_id: Annotated[str, Doc('The ID of the ASI project to search assets within')],
        filter_cve_id: Annotated[
            Optional[str],
            Doc(
                'Filter for asset or exposure tied to a vulnerability with the provided CVE. Example CVE-2024-6387.'
            ),
        ] = None,
        filter_cvss_score_gte: Annotated[
            Optional[str],
            Doc(
                'Filter for asset or exposure tied to a vulnerability with the provided CVSS score range. Example 7.5. '
            ),
        ] = None,
        filter_cvss_score_lte: Annotated[
            Optional[str],
            Doc(
                'Filter for asset or exposure tied to a vulnerability with the provided CVSS score range. Example 7.5.'
            ),
        ] = None,
        filter_cwe_id: Annotated[
            Optional[str],
            Doc(
                'Filter for asset or exposure tied to a vulnerability associated with the provided CWE. Example CWE-79.'
            ),
        ] = None,
        filter_severity_exact: Annotated[
            Optional[SEVERITY_FILTER],
            Doc('Filter for assets which have an exposure severity matching the provided value.'),
        ] = None,
        filter_severity_min: Annotated[
            Optional[SEVERITY_FILTER],
            Doc(
                'Filter for assets which have an exposure severity matching or higher than the provided value.'
            ),
        ] = None,
        max_results: Annotated[
            Optional[int], Doc('Maximum number of assets to fetch')
        ] = DEFAULT_LIMIT,
    ):
        params = {k: v for k, v in locals().items() if k not in ('self',)}
        data = self.asi_client.request_paged(
            'GET',
            EP_ASI_EXPOSURES.format(project_id),
            params=params,
            max_results=max_results,
        )

        return ExposureSearchOut.model_validate({'content': data['data'], 'meta': data['meta']})

    @debug_call
    @validate_call
    @connection_exceptions(
        ignore_status_code=[], exception_to_raise=AttackSurfaceExposureSearchError
    )
    def fetch_exposures_by_signature(
        self,
        project_id: Annotated[str, Doc('The ID of the ASI project to search assets within')],
        signature_id: Annotated[str, Doc('The ID of the signature to search assets within')],
        max_results: Annotated[
            Optional[int], Doc('Maximum number of assets to fetch')
        ] = DEFAULT_LIMIT,
    ):
        params = {
            k: v for k, v in locals().items() if k not in ('self', 'assets_per_page', 'max_results')
        }
        params['limit'] = max_results
        data = self.asi_client.request_paged(
            'GET',
            EP_ASI_EXPOSURES_BY_SIGNATURE.format(project_id, signature_id),
            params=params,
        )
        return AssetWithExposureSearch.model_validate(data['data'][0])

    def fetch_assets(
        self,
        project_id: Annotated[str, Doc('The ID of the ASI project to search assets within')],
        sort_by: Annotated[
            Literal[
                'discovered_at',
                'added_to_project_at',
                'last_scanned_at',
                'exposure_score',
                'asset_id',
                'apex_domain',
            ],
            Doc('The field to sort by.'),
        ] = 'exposure_score',
        sort_direction: Annotated[
            Literal['asc', 'desc'],
            Doc('The direction to sort by.'),
        ] = 'desc',
        asset_type: Annotated[
            Optional[Literal['domain', 'host', 'ip']],
            Doc('The type of asset, one of: ip, domain, or host.'),
        ] = None,
        custom_tags: Annotated[
            Optional[str],
            Doc('Filter by custom tags placed on your assets.'),
        ] = None,
        custom_tags_strict: Annotated[
            Optional[str],
            Doc(
                'Filter by custom tags placed on your assets. Strict version will return a '
                'validation error if any of the tags have not been defined on your project.'
            ),
        ] = None,
        has_custom_tags: Annotated[
            Optional[bool],
            Doc(
                'Filter for assets that have at least one custom tag applied. Overrides any '
                'other custom tag filtering specified.'
            ),
        ] = None,
        added_to_project_before: Annotated[
            Optional[str],
            Doc('Filter on the date (YYYY-MM-DD) the asset was added to the project.'),
        ] = None,
        added_to_project_after: Annotated[
            Optional[str],
            Doc('Filter on the date (YYYY-MM-DD) the asset was added to the project.'),
        ] = None,
        discovered_before: Annotated[
            Optional[str],
            Doc('Filter on the date (YYYY-MM-DD) the asset was discovered.'),
        ] = None,
        discovered_after: Annotated[
            Optional[str],
            Doc('Filter on the date (YYYY-MM-DD) the asset was discovered.'),
        ] = None,
        apex: Annotated[
            Optional[str],
            Doc('Filter on the apex domain of the assets. Example: example.com.'),
        ] = None,
        referenced_ip: Annotated[
            Optional[str],
            Doc(
                'Filter on an A or CNAME record pointing to the IP address. Use eq or in for '
                'exact IP matching. Use contains with a trailing . for CIDR range matching, '
                'or without for prefix matching.'
            ),
        ] = None,
        referenced_ip_before: Annotated[
            Optional[str],
            Doc(
                'If filtering on a referenced_ip, include additional criteria that the record '
                'existed during a date range. The reference must have started before this date.'
            ),
        ] = None,
        referenced_ip_after: Annotated[
            Optional[str],
            Doc(
                'If filtering on a referenced_ip, include additional criteria that the record '
                'existed during a date range. The reference must have existed after this date.'
            ),
        ] = None,
        has_dns_record_type: Annotated[
            Optional[str],
            Doc('Filter for assets that have this DNS record type, e.g. A, CNAME, MX.'),
        ] = None,
        dns_resolves: Annotated[
            Optional[bool],
            Doc(
                'Filter for assets that in the end resolve to a valid IP currently, either via '
                'an A or CNAME. IP assets are included when filtering for assets that resolve.'
            ),
        ] = None,
        asn: Annotated[
            Optional[int],
            Doc(
                'Filter for assets which either are, or point to, an IP address announced by '
                'the provided ASN.'
            ),
        ] = None,
        cname_reference: Annotated[
            Optional[str],
            Doc(
                'Filter on a domain that is referenced by a CNAME record. Only makes sense for '
                'domain asset types. Treated as a wildcard.'
            ),
        ] = None,
        geo_country_iso: Annotated[
            Optional[str],
            Doc(
                'Filter for assets which either are, or point to, an IP address located in the '
                'provided ISO country code.'
            ),
        ] = None,
        ip_owner: Annotated[
            Optional[str],
            Doc(
                'Filter for assets which either are, or point to, an IP address owned by the '
                'provided organization.'
            ),
        ] = None,
        whois_email: Annotated[
            Optional[str],
            Doc('Filter for assets where the WHOIS email address matches the provided value.'),
        ] = None,
        whois_email_current: Annotated[
            Optional[str],
            Doc(
                'Filter for assets where the WHOIS email address matches the provided value on '
                'the current WHOIS record.'
            ),
        ] = None,
        open_port_number: Annotated[
            Optional[int],
            Doc('Filter for assets which have an open port with the provided number.'),
        ] = None,
        open_port_protocol: Annotated[
            Optional[str],
            Doc('Filter for assets which have an open port on the provided protocol.'),
        ] = None,
        open_port_service: Annotated[
            Optional[str],
            Doc(
                'Filter for assets which have an open port that appears to support the provided '
                'protocol.'
            ),
        ] = None,
        open_port_technology: Annotated[
            Optional[str],
            Doc('Filter for assets which have a specific product listening on an open port.'),
        ] = None,
        technology_name: Annotated[
            Optional[str],
            Doc('Filter for the name of a technology found on the asset.'),
        ] = None,
        web_technology_name: Annotated[
            Optional[str],
            Doc(
                'Filter for the name of a technology specifically associated with web '
                'resources, such as jQuery or Wordpress.'
            ),
        ] = None,
        certificate_issuer: Annotated[
            Optional[str],
            Doc(
                "Filter where the certificate issuer's common name or organization matches the "
                'provided value.'
            ),
        ] = None,
        certificate_expires_before: Annotated[
            Optional[str],
            Doc('Filter where the certificate expiration date is before the provided value.'),
        ] = None,
        certificate_expires_after: Annotated[
            Optional[str],
            Doc('Filter where the certificate expiration date is after the provided value.'),
        ] = None,
        certificate_issued_before: Annotated[
            Optional[str],
            Doc('Filter where the certificate issuance date is before the provided value.'),
        ] = None,
        certificate_issued_after: Annotated[
            Optional[str],
            Doc('Filter where the certificate issuance date is after the provided value.'),
        ] = None,
        certificate_subject: Annotated[
            Optional[str],
            Doc('Filter where certificate subject or organizationName matches the value.'),
        ] = None,
        certificate_subject_alt_name: Annotated[
            Optional[str],
            Doc('Filter where the certificate Subject Alternative Name matches the value.'),
        ] = None,
        certificate_sha256: Annotated[
            Optional[str],
            Doc('Filter where the certificate public key sha256 value matches the value.'),
        ] = None,
        certificate_covers_domain: Annotated[
            Optional[str],
            Doc(
                'Filter where the certificate subject common name or SAN exactly matches or '
                'wildcard-covers the provided value.'
            ),
        ] = None,
        waf_detected: Annotated[
            Optional[bool],
            Doc('Filter for assets where a WAF is detected.'),
        ] = None,
        waf_name: Annotated[
            Optional[str],
            Doc('Filter for assets where a specific WAF is detected.'),
        ] = None,
        is_responsive: Annotated[
            Optional[bool],
            Doc(
                'Filter for assets that are either responsive or not responsive over ICMP and '
                'port scanning.'
            ),
        ] = None,
        exposure_score_gte: Annotated[
            Optional[int],
            Field(ge=0, le=100),
            Doc('Filter for assets with exposure score greater than or equal to this value.'),
        ] = None,
        exposure_score_lte: Annotated[
            Optional[int],
            Field(ge=0, le=100),
            Doc('Filter for assets with exposure score less than or equal to this value.'),
        ] = None,
        exposure_severity: Annotated[
            Optional[Literal['unknown', 'informational', 'moderate', 'critical']],
            Doc(
                'Filter for assets with an exposure severity matching or higher than the '
                'provided value.'
            ),
        ] = None,
        exposure_id: Annotated[
            Optional[str],
            Doc('Filter for assets which have an exposure with the provided ASI Signature ID.'),
        ] = None,
        additional_fields: Annotated[
            Optional[
                list[
                    Literal[
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
                ]
            ],
            Doc(
                'Additional fields to include in the response. May be specified multiple times '
                'or as a comma-separated list in the raw API.'
            ),
        ] = None,
        max_results: Annotated[
            Optional[int], Doc('Maximum number of assets to fetch')
        ] = DEFAULT_LIMIT,
    ):
        params = {k: v for k, v in locals().items() if k not in ('self',)}
        data = self.asi_client.request_paged(
            'GET',
            EP_ASI_ASSETS.format(project_id),
            params=params,
            max_results=max_results,
        )

        return AssetResponse.model_validate({'content': data['data'], 'meta': data['meta']})

    def fetch_asset(
        self,
        project_id: Annotated[str, Doc('The ID of the ASI project to search assets within')],
        asset_id: Annotated[str, Doc('The asset ID to search for.')],
        additional_fields: Annotated[
            Optional[
                list[
                    Literal[
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
                ]
            ],
            Doc(
                'Additional fields to include in the response. May be specified multiple times '
                'or as a comma-separated list in the raw API.'
            ),
        ] = None,
    ):
        params = {k: v for k, v in locals().items() if k not in ('self',)}
        data = self.asi_client.request(
            'GET',
            EP_ASI_ASSET.format(project_id, asset_id),
            params=params,
        ).json()

        return Asset.model_validate(data['data'])

    def fetch_asset_exposures(
        self,
        project_id: Annotated[str, Doc('The ID of the ASI project to search assets within')],
        asset_id: Annotated[str, Doc('The asset ID to search for.')],
    ):
        data = self.asi_client.request(
            'GET',
            EP_ASI_ASSET_EXPOSURES.format(project_id, asset_id),
        ).json()

        return Asset.model_validate(data['data'])
