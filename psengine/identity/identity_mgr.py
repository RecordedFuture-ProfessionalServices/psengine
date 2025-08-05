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
from contextlib import suppress
from typing import Annotated, Optional, Union

from pydantic import Field, validate_call
from typing_extensions import Doc

from ..constants import DEFAULT_LIMIT
from ..endpoints import (
    EP_IDENTITY_CREDENTIALS_LOOKUP,
    EP_IDENTITY_CREDENTIALS_SEARCH,
    EP_IDENTITY_DETECTIONS,
    EP_IDENTITY_DUMP_SEARCH,
    EP_IDENTITY_HOSTNAME_LOOKUP,
    EP_IDENTITY_INCIDENT_REPORT,
    EP_IDENTITY_IP_LOOKUP,
    EP_IDENTITY_PASSWORD_LOOKUP,
)
from ..helpers import TimeHelpers, connection_exceptions, debug_call
from ..rf_client import RFClient
from .constants import DETECTIONS_PER_PAGE, MAXIMUM_IDENTITIES
from .errors import (
    DetectionsFetchError,
    IdentityLookupError,
    IdentitySearchError,
    IncidentReportFetchError,
)
from .identity import (
    CredentialSearch,
    CredentialsLookupIn,
    CredentialsSearchIn,
    Detections,
    DetectionsIn,
    DumpSearchIn,
    DumpSearchOut,
    HostnameLookupIn,
    IncidentReportIn,
    IncidentReportOut,
    IPLookupIn,
    LeakedIdentity,
    PasswordLookup,
)
from .models.common_models import FilterIn


class IdentityMgr:
    """Manages requests for Recorded Future Identity API."""

    def __init__(
        self,
        rf_token: Annotated[Optional[str], Doc('A Recorded Future API token.')] = None,
    ) -> None:
        """Initializes the `IdentityMgr` object.

        Note:
            The Identity API has some rate limiting that the user needs to take into account.
            See: [Support Article](https://support.recordedfuture.com/hc/en-us/articles/33694346668819-Identity-Lookup-API)
        """
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @validate_call
    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=DetectionsFetchError)
    def fetch_detections(
        self,
        domains: Annotated[
            Union[str, list[str], None], Doc('A domain or a list of domains to filter.')
        ] = None,
        created_gte: Annotated[
            Optional[str],
            Doc(
                'A timestamp to return detections created on or after it (e.g., "7d" or ISO 8601).'
            ),
        ] = None,
        created_lt: Annotated[
            Optional[str], Doc('A timestamp to return detections created before it.')
        ] = None,
        cookies: Annotated[Optional[str], Doc('A filter by cookie type.')] = None,
        detection_type: Annotated[
            Optional[str], Doc('A detection type to filter by ("workforce", "external").')
        ] = None,
        organization_id: Annotated[
            Union[list[str], str, None],
            Doc('Organization ID or a list of IDs for multi-org filtering.'),
        ] = None,
        include_enterprise_level: Annotated[
            Optional[bool], Doc('Whether to include enterprise-level detections.')
        ] = None,
        novel_only: Annotated[
            Optional[bool], Doc('If True, only return novel (previously unseen) detections.')
        ] = None,
        max_results: Annotated[
            Optional[int], Doc('The maximum number of detections returned.')
        ] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DEFAULT_LIMIT),
        detections_per_page: Annotated[
            Optional[int], Doc('The number of detections per page for pagination.')
        ] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DETECTIONS_PER_PAGE),
        offset: Annotated[Optional[str], Doc('An offset token for paginated results.')] = None,
    ) -> Annotated[Detections, Doc('A structured response containing the detection records.')]:
        """Fetch latest detections.

        Endpoint:
            `/identity/detections`

        Example:
            ```python
            from psengine.identity import IdentityMgr

            identity_mgr = IdentityMgr()
            detections = identity_mgr.fetch_detections(created_gte='7d', novel_only=True)
            ```

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            DetectionsFetchError: If connection error occurs.
        """
        data = {
            'organization_id': organization_id,
            'include_enterprise_level': include_enterprise_level,
            'filter': {
                'novel_only': novel_only,
                'domains': domains,
                'detection_type': detection_type,
                'cookies': cookies,
            },
            'limit': min(max_results, detections_per_page),
            'offset': offset,
            'created': {
                'gte': created_gte,
                'lt': created_lt,
            },
        }

        payload = DetectionsIn.model_validate(data).json(exclude_defaults=True, exclude_unset=True)
        self.log.info(f'Fetching detections with the following filters:\n{payload}')

        resp = self.rf_client.request_paged(
            'post',
            url=EP_IDENTITY_DETECTIONS,
            data=payload,
            results_path='detections',
            max_results=max_results or DEFAULT_LIMIT,
        )
        self.log.info(f'Returned {len(resp)} detections')
        return Detections.model_validate({'total': len(resp), 'detections': resp})

    @validate_call
    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=IdentityLookupError)
    def lookup_hostname(
        self,
        hostname: Annotated[str, Doc('The hostname of a compromised machine.')],
        first_downloaded_gte: Annotated[
            Optional[str],
            Doc('First date when these credentials were received and indexed by Recorded Future.'),
        ] = None,
        latest_downloaded_gte: Annotated[
            Optional[str],
            Doc('Latest date when these credentials were received and indexed by Recorded Future.'),
        ] = None,
        exfiltration_date_gte: Annotated[
            Optional[str],
            Doc('Date when the infostealer malware exfiltrated data from the victim device.'),
        ] = None,
        properties: Annotated[Union[str, list[str], None], Doc('Password properties.')] = None,
        breach_name: Annotated[Optional[str], Doc('The name of a breach.')] = None,
        breach_date: Annotated[Optional[str], Doc('The date of a breach.')] = None,
        dump_name: Annotated[Optional[str], Doc('The name of a database dump.')] = None,
        dump_date: Annotated[Optional[str], Doc('The date of a database dump.')] = None,
        username_properties: Annotated[
            Union[str, list[str], None], Doc("Username properties. Only valid value is 'Email'.")
        ] = None,
        authorization_technologies: Annotated[
            Union[str, list[str], None], Doc('Authorization technologies to filter by.')
        ] = None,
        authorization_protocols: Annotated[
            Union[str, list[str], None], Doc('Authorization protocols to filter by.')
        ] = None,
        malware_families: Annotated[
            Union[str, list[str], None], Doc('Known infostealer malware families.')
        ] = None,
        organization_id: Annotated[
            Optional[str], Doc('An organization ID if utilizing a multi-org setup.')
        ] = None,
        max_results: Annotated[
            Optional[int], Doc('The maximum number of credential records returned.')
        ] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DEFAULT_LIMIT),
        identities_per_page: Annotated[
            Optional[int], Doc('The number of credentials per page for pagination.')
        ] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DETECTIONS_PER_PAGE),
        offset: Annotated[Optional[str], Doc('An offset token for paginated results.')] = None,
    ) -> Annotated[list[LeakedIdentity], Doc('A list containing the leaked identity records.')]:
        """Return credentials for a given hostname.

        Endpoint:
            `/identity/hostname/lookup`

        Example:
            ```python
            from psengine.identity import IdentityMgr

            identity_mgr = IdentityMgr()
            properties = ["Letter", "Symbol"]
            creds = identity_mgr.lookup_hostname(hostname="HOSTNAME", properties=properties)
            ```

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            IdentityLookupError: If connection error occurs.
        """
        filter_params = locals()
        for param in [
            'self',
            'hostname',
            'organization_id',
            'max_results',
            'offset',
            'identities_per_page',
        ]:
            filter_params.pop(param)

        filter_body = self._lookup_filter(**filter_params).json()

        data = {
            'hostname': hostname,
            'filter': filter_body,
            'organization_id': organization_id,
            'limit': min(max_results, identities_per_page),
            'offset': offset,
        }

        payload = HostnameLookupIn.model_validate(data).json()
        self.log.info(f'Looking up hostname with filters: {payload}')
        resp = self.rf_client.request_paged(
            'post',
            url=EP_IDENTITY_HOSTNAME_LOOKUP,
            data=payload,
            results_path='identities',
            max_results=max_results or DEFAULT_LIMIT,
        )
        resp = [LeakedIdentity.model_validate(identity) for identity in resp]
        self.log.info(f'Returned {len(resp)} identities')
        return resp

    @validate_call
    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=IdentityLookupError)
    def lookup_password(
        self,
        hash_prefix: Annotated[
            Optional[str], Doc('The prefix of the password hash to be looked up.')
        ] = None,
        algorithm: Annotated[
            Optional[str], Doc('The algorithm used for the password hash.')
        ] = None,
        passwords: Annotated[
            Optional[list[tuple[str, str]]],
            Doc('A list of tuples containing hash prefixes and their respective algorithms.'),
        ] = None,
    ) -> Annotated[list[PasswordLookup], Doc('A list of password lookup results.')]:
        """Lookup passwords to determine if they have been previously exposed.

        Check if either specific password hash prefixes and algorithms, or a list of hash and
        algorithm tuples, have been exposed in the past.

        Endpoint:
            `/identity/password/lookup`

        Example:
            ```python
            from psengine.identity import IdentityMgr

            identity_mgr = IdentityMgr()
            creds = identity_mgr.lookup_password(hash_prefix='8e9a96e', algorithm='sha256')

            passwords = [
                ('995bb852c775d6', 'ntlm'),
                ('8985b89acb97b011913c8b7f57e298d2', 'md5'),
            ]

            creds = identity_mgr.lookup_password(passwords=passwords)
            ```

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            ValueError: If a wrong combination of parameters is given.
            IdentityLookupError: If connection error occurs.
        """
        if passwords and (hash_prefix or algorithm):
            msg = 'Specify only hash_prefix with algorithm, or only passwords'
            self.log.error(msg)
            raise ValueError(msg)

        if not (hash_prefix and algorithm) and not passwords:
            msg = 'hash_prefix must be specified with algorithm'
            self.log.error(msg)
            raise ValueError(msg)

        if hash_prefix and algorithm:
            passwords = [(hash_prefix, algorithm)]

        data = {
            'passwords': [
                {'algorithm': alg.upper(), 'hash_prefix': hash_} for hash_, alg in passwords
            ]
        }

        self.log.info(f'Looking up passwords: {data}')
        resp = self.rf_client.request('post', url=EP_IDENTITY_PASSWORD_LOOKUP, data=data).json()[
            'results'
        ]
        resp = [PasswordLookup.model_validate(v) for v in resp]
        self.log.info(f'Returned {len(resp)} passwords')
        return resp

    @validate_call
    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=IdentityLookupError)
    def lookup_ip(
        self,
        ip: Annotated[Optional[str], Doc('A subject IP address.')] = None,
        range_gte: Annotated[Optional[str], Doc('An IP address lower bound included.')] = None,
        range_gt: Annotated[Optional[str], Doc('An IP address lower bound excluded.')] = None,
        range_lte: Annotated[Optional[str], Doc('An IP address upper bound included.')] = None,
        range_lt: Annotated[Optional[str], Doc('An IP address upper bound excluded.')] = None,
        first_downloaded_gte: Annotated[
            Optional[str],
            Doc('First date when these credentials were received and indexed by Recorded Future.'),
        ] = None,
        latest_downloaded_gte: Annotated[
            Optional[str],
            Doc('Latest date when these credentials were received and indexed by Recorded Future.'),
        ] = None,
        exfiltration_date_gte: Annotated[
            Optional[str],
            Doc('Date when the infostealer malware exfiltrated data from the victim device.'),
        ] = None,
        properties: Annotated[Union[str, list[str], None], Doc('Password properties.')] = None,
        breach_name: Annotated[Optional[str], Doc('The name of a breach.')] = None,
        breach_date: Annotated[Optional[str], Doc('The date of a breach.')] = None,
        dump_name: Annotated[Optional[str], Doc('The name of a database dump.')] = None,
        dump_date: Annotated[Optional[str], Doc('The date of a database dump.')] = None,
        username_properties: Annotated[
            Union[str, list[str], None], Doc("Username properties. Only valid value is 'Email'.")
        ] = None,
        authorization_technologies: Annotated[
            Union[str, list[str], None], Doc('Authorization technologies to filter by.')
        ] = None,
        authorization_protocols: Annotated[
            Union[str, list[str], None], Doc('Authorization protocols to filter by.')
        ] = None,
        malware_families: Annotated[
            Union[str, list[str], None], Doc('Known infostealer malware families.')
        ] = None,
        organization_id: Annotated[
            Optional[str], Doc('An organization ID if utilizing a multi-org setup.')
        ] = None,
        max_results: Annotated[
            Optional[int], Doc('The maximum number of credentials returned.')
        ] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DEFAULT_LIMIT),
        identities_per_page: Annotated[
            Optional[int], Doc('The number of credentials per page for pagination.')
        ] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DETECTIONS_PER_PAGE),
        offset: Annotated[Optional[str], Doc('An offset token for paginated results.')] = None,
    ) -> Annotated[list[LeakedIdentity], Doc('A list containing the leaked identity records.')]:
        """Lookup credentials associated with a specified IP address or an IP range.

        Endpoint:
            `/identity/ip/lookup`

        Example:
            ```python
            from psengine.identity import IdentityMgr

            identity_mgr = IdentityMgr()
            creds = identity_mgr.lookup_ip(ip="8.8.8.8")
            ```

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            IdentityLookupError: If connection error occurs.
        """
        if not (ip or range_gte or range_gt or range_lte or range_lt):
            raise ValueError('Either an IP or a range has to be specified')

        filter_params = locals()
        for param in [
            'self',
            'ip',
            'organization_id',
            'offset',
            'range_gte',
            'range_gt',
            'range_lte',
            'range_lt',
            'max_results',
            'identities_per_page',
        ]:
            filter_params.pop(param)
        filter_body = self._lookup_filter(**filter_params).json()

        ip_range = {
            'gte': range_gte,
            'gt': range_gt,
            'lte': range_lte,
            'lt': range_lt,
        }

        data = {
            'ip': ip,
            'range': ip_range,
            'filter': filter_body,
            'organization_id': organization_id,
            'limit': min(max_results, identities_per_page),
            'offset': offset,
        }
        payload = IPLookupIn.model_validate(data).json(exclude_defaults=True, exclude_unset=True)

        self.log.info(f'Looking up IP(s) with filters: {payload}')
        resp = self.rf_client.request_paged(
            'post',
            url=EP_IDENTITY_IP_LOOKUP,
            data=payload,
            max_results=max_results or DEFAULT_LIMIT,
            results_path='identities',
        )
        resp = [LeakedIdentity.model_validate(identity) for identity in resp]
        self.log.info(f'Returned {len(resp)} identities')
        return resp

    @validate_call
    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=IdentityLookupError)
    def lookup_credentials(
        self,
        subjects: Annotated[
            Union[str, list[str], None], Doc('An email or a list of emails to be queried.')
        ] = None,
        subjects_sha1: Annotated[
            Union[str, list[str], None],
            Doc('A SHA1 hash of a username or email to avoid sending the plain subject.'),
        ] = None,
        subjects_login: Annotated[
            Union[list[dict[str, str]], list[CredentialSearch], None],
            Doc(
                'Username details when login is not an email (also requires authorization domain).'
            ),
        ] = None,
        first_downloaded_gte: Annotated[
            Optional[str],
            Doc('First date when these credentials were received and indexed by Recorded Future.'),
        ] = None,
        latest_downloaded_gte: Annotated[
            Optional[str],
            Doc('Latest date when these credentials were received and indexed by Recorded Future.'),
        ] = None,
        exfiltration_date_gte: Annotated[
            Optional[str],
            Doc('Date when the infostealer malware exfiltrated data from the victim device.'),
        ] = None,
        properties: Annotated[Union[str, list[str], None], Doc('Password properties.')] = None,
        breach_name: Annotated[Optional[str], Doc('The name of a breach.')] = None,
        breach_date: Annotated[Optional[str], Doc('The date of a breach.')] = None,
        dump_name: Annotated[Optional[str], Doc('The name of a database dump.')] = None,
        dump_date: Annotated[Optional[str], Doc('The date of a database dump.')] = None,
        username_properties: Annotated[
            Union[str, list[str], None], Doc("Username properties. Only valid value is 'Email'.")
        ] = None,
        authorization_technologies: Annotated[
            Union[str, list[str], None], Doc('Authorization technologies to filter by.')
        ] = None,
        authorization_protocols: Annotated[
            Union[str, list[str], None], Doc('Authorization protocols to filter by.')
        ] = None,
        malware_families: Annotated[
            Union[str, list[str], None], Doc('Known infostealer malware families.')
        ] = None,
        organization_id: Annotated[
            Optional[str], Doc('An organization ID if utilizing a multi-org setup.')
        ] = None,
        max_results: Annotated[
            Optional[int], Doc('The maximum number of credentials returned.')
        ] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DEFAULT_LIMIT),
        identities_per_page: Annotated[
            Optional[int], Doc('The number of credentials per page for pagination.')
        ] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DETECTIONS_PER_PAGE),
        offset: Annotated[Optional[str], Doc('An offset token for paginated results.')] = None,
    ) -> Annotated[list[LeakedIdentity], Doc('A list containing the leaked identity records.')]:
        """Lookup credential data for a set of subjects.

        The subject can be an email, a SHA1 hash, or a combination of username and domain.
        Different types of subjects can be specified simultaneously, at least one must be present.

        Endpoint:
            `/identity/credentials/lookup`

        Example:
            ```python
            from psengine.identity import IdentityMgr

            identity_mgr = IdentityMgr()
            subjects = ["user@domain.com", "admin@domain.com"]
            creds = identity_mgr.lookup_credentials(subjects=subjects)

            # Or lookup from a search result
            search = identity_mgr.search_credentials(
                domains='norsegods.online',
                domain_types='Email'
            )
            data = identity_mgr.lookup_credentials(subjects_login=search)
            ```

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            IdentityLookupError: If connection error occurs.
        """
        if not (subjects_sha1 or subjects_login or subjects):
            raise ValueError('At least one subject type has to be provided')

        filter_params = locals()
        for param in [
            'self',
            'subjects',
            'subjects_sha1',
            'subjects_login',
            'organization_id',
            'offset',
            'max_results',
            'identities_per_page',
        ]:
            filter_params.pop(param)
        filter_body = self._lookup_filter(**filter_params).json()

        data = {
            'subjects': subjects,
            'subjects_sha1': subjects_sha1,
            'subjects_login': subjects_login,
            'filter': filter_body,
            'organization_id': organization_id,
            'limit': min(max_results, identities_per_page),
            'offset': offset,
        }
        payload = CredentialsLookupIn.model_validate(data).json()
        self.log.info(f'Looking up credentials with filters: {payload}')
        resp = self.rf_client.request_paged(
            'post',
            url=EP_IDENTITY_CREDENTIALS_LOOKUP,
            data=payload,
            max_results=max_results or DEFAULT_LIMIT,
            results_path='identities',
        )
        resp = [LeakedIdentity.model_validate(identity) for identity in resp]
        self.log.info(f'Returned {len(resp)} identities')
        return resp

    @validate_call
    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=IdentitySearchError)
    def search_credentials(
        self,
        domains: Annotated[Union[str, list[str]], Doc('One or more domains to be queried.')],
        domain_types: Annotated[
            Union[str, list[str], None],
            Doc("Domain type filter: 'Email', 'Authorization', or both."),
        ] = None,
        first_downloaded_gte: Annotated[
            Optional[str],
            Doc('First date when these credentials were received and indexed by Recorded Future.'),
        ] = None,
        latest_downloaded_gte: Annotated[
            Optional[str],
            Doc('Latest date when these credentials were received and indexed by Recorded Future.'),
        ] = None,
        exfiltration_date_gte: Annotated[
            Optional[str],
            Doc('Date when the infostealer malware exfiltrated data from the victim device.'),
        ] = None,
        properties: Annotated[Union[str, list[str], None], Doc('Password properties.')] = None,
        breach_name: Annotated[Optional[str], Doc('The name of a breach.')] = None,
        breach_date: Annotated[Optional[str], Doc('The date of a breach.')] = None,
        dump_name: Annotated[Optional[str], Doc('The name of a database dump.')] = None,
        dump_date: Annotated[Optional[str], Doc('The date of a database dump.')] = None,
        username_properties: Annotated[
            Union[str, list[str], None], Doc("Username properties. Only valid value is 'Email'.")
        ] = None,
        authorization_technologies: Annotated[
            Union[str, list[str], None], Doc('Authorization technologies to filter by.')
        ] = None,
        authorization_protocols: Annotated[
            Union[str, list[str], None], Doc('Authorization protocols to filter by.')
        ] = None,
        malware_families: Annotated[
            Union[str, list[str], None], Doc('Known infostealer malware families.')
        ] = None,
        organization_id: Annotated[
            Optional[str], Doc('An organization ID if utilizing a multi-org setup.')
        ] = None,
        max_results: Annotated[
            Optional[int], Doc('The maximum number of credentials returned.')
        ] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DEFAULT_LIMIT),
        identities_per_page: Annotated[
            Optional[int], Doc('The number of credentials per page for pagination.')
        ] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DETECTIONS_PER_PAGE),
        offset: Annotated[Optional[str], Doc('An offset token for paginated results.')] = None,
    ) -> Annotated[list[CredentialSearch], Doc('A list containing the search results.')]:
        """Search credential data for a set of domains.

        Endpoint:
            `/identity/credentials/search`

        Example:
            ```python
            from psengine.identity import IdentityMgr

            identity_mgr = IdentityMgr()
            domains = ["domain.com"]
            creds = identity_mgr.search_credentials(domains=domains)
            ```

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            IdentitySearchError: If connection error occurs.
        """
        filter_params = locals()
        for param in [
            'self',
            'domains',
            'domain_types',
            'organization_id',
            'offset',
            'max_results',
            'identities_per_page',
        ]:
            filter_params.pop(param)

        data = {
            'domains': domains,
            'domain_types': domain_types,
            'filter': self._lookup_filter(**filter_params).json(),
            'organization_id': organization_id,
            'limit': min(max_results, identities_per_page),
            'offset': offset,
        }

        payload = CredentialsSearchIn.model_validate(data).json()
        self.log.info(f'Searching credentials with filters: {payload}')
        resp = self.rf_client.request_paged(
            'post',
            url=EP_IDENTITY_CREDENTIALS_SEARCH,
            data=payload,
            max_results=max_results or DEFAULT_LIMIT,
            results_path='identities',
        )
        resp = [CredentialSearch.model_validate(d) for d in resp]
        self.log.info(f'Returned {len(resp)} credentials')
        return resp

    @validate_call
    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=IdentitySearchError)
    def search_dump(
        self,
        names: Annotated[
            Union[str, list[str]], Doc('The name(s) of a database dump to search for.')
        ],
        max_results: Annotated[
            Optional[int], Doc('Maximum number of dump records to return.')
        ] = Field(le=MAXIMUM_IDENTITIES, default=DEFAULT_LIMIT),
    ) -> Annotated[
        DumpSearchOut,
        Doc('A list containing the dump search results.'),
    ]:
        """Search if a particular database dump is present.

        Endpoint:
            `/identity/metadata/dump/search`

        Example:
            ```python
            from psengine.identity import IdentityMgr

            identity_mgr = IdentityMgr()
            dump_name = "Dump Name"
            dump_info = identity_mgr.search_dump(names=dump_name)
            ```

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            IdentitySearchError: If connection error occurs.
        """
        data = {
            'names': names,
            'limit': max_results,
        }
        payload = DumpSearchIn.model_validate(data).json()
        self.log.info(f'Searching dumps with filters: {payload}')
        resp = self.rf_client.request('post', url=EP_IDENTITY_DUMP_SEARCH, data=payload).json()[
            'dumps'
        ]
        resp = [DumpSearchOut.model_validate(d) for d in resp]
        self.log.info(f'Returned {len(resp)} dump results')
        return resp

    @validate_call
    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=IncidentReportFetchError)
    def fetch_incident_report(
        self,
        source: Annotated[str, Doc('The raw archive name containing malware log data.')],
        include_details: Annotated[
            bool, Doc('Whether to include infected machine details.')
        ] = True,
        organization_id: Annotated[
            Union[list[str], str, None], Doc('The org_id(s) in multi-org setup.')
        ] = None,
        offset: Annotated[Optional[str], Doc('Offset token for paginated results.')] = None,
        max_results: Annotated[
            Optional[int], Doc('Maximum number of credentials to return.')
        ] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DEFAULT_LIMIT),
        identities_per_page: Annotated[
            Optional[int], Doc('Number of credentials per page.')
        ] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DETECTIONS_PER_PAGE),
    ) -> Annotated[
        IncidentReportOut,
        Doc('A detailed incident report from the specified malware source.'),
    ]:
        """Provides an exposure incident report for a single malware log.

        Endpoint:
            `/identity/incident/report`

        Example:
            Fetch incident report from a recent detection:

            ```python
            from psengine.identity import IdentityMgr

            identity_mgr = IdentityMgr()
            detections = identity_mgr.fetch_detections(created_gte='7d', max_results=1)
            recent_detection = detections.detections[0]

            source = recent_detection.dump.source
            report = identity_mgr.fetch_incident_report(source=source, include_details=True)
            ```

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            IncidentReportFetchError: If connection error occurs.
        """
        data = {
            'source': source,
            'include_details': include_details,
            'organization_id': organization_id,
            'limit': min(max_results, identities_per_page),
            'offset': offset,
        }
        payload = IncidentReportIn.model_validate(data).json()
        self.log.info(f'Fetching incident report with filters: {payload}')
        resp = self.rf_client.request_paged(
            'post',
            url=EP_IDENTITY_INCIDENT_REPORT,
            data=payload,
            max_results=max_results or DEFAULT_LIMIT,
            results_path=['credentials', 'details'],
        )

        return IncidentReportOut.model_validate(resp)

    @debug_call
    def _lookup_filter(
        self,
        first_downloaded_gte: Optional[str] = None,
        latest_downloaded_gte: Optional[str] = None,
        exfiltration_date_gte: Optional[str] = None,
        properties: Union[str, list[str], None] = None,
        breach_name: Optional[str] = None,
        breach_date: Optional[str] = None,
        dump_name: Optional[str] = None,
        dump_date: Optional[str] = None,
        username_properties: Union[str, list[str], None] = None,
        authorization_technologies: Union[str, list[str], None] = None,
        authorization_protocols: Union[str, list[str], None] = None,
        malware_families: Union[str, list[str], None] = None,
    ) -> FilterIn:
        """Create a query for filtering identity searches.

        See lookup_hostname(), lookup_ip(), and/or lookup_credentials() for parameter descriptions.

        Raises:
            ValidationError: if any parameter is of incorrect type

        Returns:
            FilterIn: Validated search query
        """
        params = {key: val for key, val in locals().items() if val is not None and key != 'self'}
        query = {'breach_properties': {}, 'dump_properties': {}}

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

        return FilterIn.model_validate(query)

    def _process_arg(self, attr: str, value: Union[int, str, list]) -> tuple[str, Union[str, list]]:
        """Return attribute and value normalized based on type of value."""
        if attr.startswith(('breach_', 'dump_')):
            prop_field = attr.split('_')[0] + '_properties'
            with suppress(ValueError):
                value = TimeHelpers.rel_time_to_date(value)

            filter_key = 'name' if 'name' in attr else 'date'
            return prop_field, {filter_key: value}
        return attr, value
