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
from typing import Optional, Union

from pydantic import Field, validate_call

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

    def __init__(self, rf_token: str = None):
        """Initializes the IdentityMgr object.


        Note: The identity API has some rate limiting that the user need to take into account.

        Args:
            rf_token (str, optional): Recorded Future API token. Defaults to None
        """
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @validate_call
    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=DetectionsFetchError)
    def fetch_detections(
        self,
        domains: Union[str, list[str], None] = None,
        created_gte: Optional[str] = None,
        created_lt: Optional[str] = None,
        cookies: Optional[str] = None,
        detection_type: Optional[str] = None,
        organization_id: Union[list[str], str, None] = None,
        include_enterprise_level: Optional[bool] = None,
        novel_only: Optional[bool] = None,
        max_results: Optional[int] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DEFAULT_LIMIT),
        detections_per_page: Optional[int] = Field(
            ge=1, le=MAXIMUM_IDENTITIES, default=DETECTIONS_PER_PAGE
        ),
        offset: Optional[str] = None,
    ) -> Detections:
        """Fetch latest detections.

        Example:

            .. code-block:: python
                :linenos:

                from psengine.identity import IdentityMgr

                identity_mgr = IdentityMgr()
                detections = identity_mgr.fetch_detections(created_gte='7d', novel_only=True)

        Endpoint:
            ``/identity/detections``

        Args:
            domains (Union[str, list[str], optional]): Domain or list of domains to filter.
            created_gte (str, optional): Return detections created on or after this timestamp
                ('7d' or ISO 8601).
            created_lt (str, optional): Return detections created before this timestamp.
            detection_type (str, optional): Filter by detection type ('workforce', 'external').
            cookies (str, optional): Filter by cookie type.
            organization_id (Union[str, list[str], optional]): Organization ID(s) for multi-orgs.
            include_enterprise_level (bool, optional): Whether include enterprise-level detections.
            novel_only (bool, optional): If True, only return novel (previously unseen) detections.
            max_results (int, optional): Max number of detections returned (default: DEFAULT_LIMIT).
            detections_per_page (int, optional): Number of detections per page for pagination.
            offset (str, optional): Offset token for paginated results.

        Returns:
            DetectionsOut: A structured response containing the detection records.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            DetectionsFetchError: if connection error occurs.
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
        hostname: str,
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
        organization_id: Optional[str] = None,
        max_results: Optional[int] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DEFAULT_LIMIT),
        identities_per_page: Optional[int] = Field(
            ge=1, le=MAXIMUM_IDENTITIES, default=DETECTIONS_PER_PAGE
        ),
        offset: Optional[str] = None,
    ) -> list[LeakedIdentity]:
        """Return credentials for a given hostname.

        Example:
            .. code-block:: python
                :linenos:

                from psengine.identity import IdentityMgr

                identity_mgr = IdentityMgr()
                properties = ["Letter", "Symbol"]
                creds = identity_mgr.lookup_hostname(hostname="HOSTNAME", properties=properties)

        Endpoint:
            ``/identity/hostname/lookup``

        Args:
            hostname (str): The hostname of a compromised machine.
            first_downloaded_gte (Optional[str]): First date when these credentials were received
                and indexed by Recorded Future.
            latest_downloaded_gte (Optional[str]): Latest date when these credentials were received
                and indexed by Recorded Future. It is not unusual for the same credentials to be
                exposed multiple times, in data from different dumps and/or logs.
            exfiltration_date_gte (Optional[str]): Date when the infostealer malware exfiltrated
                data from the victim device. If Recorded Future has received data indicating that
                the credentials were stolen and exfiltrated repeatedly, then the response will
                contain several exfiltration dates.
            properties (Union[str, list[str]], None]): Password properties.
            breach_name (Optional[str]): The name of a breach.
            breach_date (Optional[str]): The date of a breach.
            dump_name (Optional[str]): The name of a database dump.
            dump_date (Optional[str]): The date of a database dump.
            username_properties (Optional[list[str]]): Only valid value is 'Email'.
            authorization_technologies (Union[str, list[str]], None]): Only include credential with
                these authorization technologies.
            authorization_protocols (Union[str, list[str]], None]): Only include credentials with
                these authorization protocols.
            malware_families (Union[str, list[str]], None]): Known infostealer malware families
                (refer to User Interface for latest list of supported values).
            organization_id (Optional[str]): The org_id if utilizing a multi-org setup.
            max_results (int, optional): Specifies the maximum number of credential records returned
                (default: DEFAULT_LIMIT).
            identities_per_page (int, optional): Number of credentials per page for pagination.
            offset (str, optional): Offset token for paginated results.

        Returns:
            list[LeakedIdentity]: A list containing the leaked identity records.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            IdentityLookupError: if connection error occurs.
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
        hash_prefix: Optional[str] = None,
        algorithm: Optional[str] = None,
        passwords: Optional[list[tuple[str, str]]] = None,
    ) -> list[PasswordLookup]:
        """Lookup passwords to determine if they have been previously exposed.

        Check if either specific password hash prefixes and algorithms, or a list of hash and
        algorithm tuples, have been exposed in the past.

        Example:

            .. code-block:: python
                :linenos:

                from psengine.identity import IdentityMgr

                identity_mgr = IdentityMgr()
                creds = identity_mgr.lookup_password(hash_prefix='8e9a96e', algorithm='sha256')

                passwords = [
                    ('995bb852c775d6', 'ntlm'),
                    ('8985b89acb97b011913c8b7f57e298d2', 'md5'),
                ]

                creds = identity_mgr.lookup_password(passwords=passwords)

        Endpoint:
            ``/identity/password/lookup``

        Args:
            hash_prefix (str, optional): The prefix of the password hash to be looked up.
            algorithm (str, optional): The algorithm used for the password hash.
            passwords (list[tuple[str, str]], optional): A list of tuples containing hash prefixes
                and their respective algorithms.

        Raises:
            ValidationError: if any supplied parameter is of incorrect type.
            ValueError: if a wrong combination of params is given.
            IdentityLookupError: if connection error occurs.

        Returns:
            list[PasswordLookup]: A list of password lookup results.
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
        ip: Optional[str] = None,
        range_gte: Optional[str] = None,
        range_gt: Optional[str] = None,
        range_lte: Optional[str] = None,
        range_lt: Optional[str] = None,
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
        organization_id: Optional[str] = None,
        max_results: Optional[int] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DEFAULT_LIMIT),
        identities_per_page: Optional[int] = Field(
            ge=1, le=MAXIMUM_IDENTITIES, default=DETECTIONS_PER_PAGE
        ),
        offset: Optional[str] = None,
    ) -> list[LeakedIdentity]:
        """Lookup credentials associated with a specified IP address or an IP range.

        Example:

            .. code-block:: python
                :linenos:

                from psengine.identity import IdentityMgr

                identity_mgr = IdentityMgr()
                creds = identity_mgr.lookup_ip(ip="8.8.8.8")

        Endpoint:
            ``/identity/ip/lookup``

        Args:
            ip (str, optional): Subject IP address.
            range_gte (str, optional): IP address lower bound included.
            range_gt (str, optional): IP address lower bound excluded.
            range_lte (str, optional): IP address upper bound included.
            range_lt (str, optional): IP address upper bound excluded.
            first_downloaded_gte (Optional[str]): First date when these credentials were received
                and indexed by Recorded Future.
            latest_downloaded_gte (Optional[str]): Latest date when these credentials were received
                and indexed by Recorded Future. It is not unusual for the same credentials to be
                exposed multiple times, in data from different dumps and/or logs.
            exfiltration_date_gte (Optional[str]): Date when the infostealer malware exfiltrated
                data from the victim device. If Recorded Future has received data indicating that
                the credentials were stolen and exfiltrated repeatedly, then the response will
                contain several exfiltration dates.
            properties (Union[str, list[str]], None]): Password properties.
            breach_name (Optional[str]): The name of a breach.
            breach_date (Optional[str]): The date of a breach.
            dump_name (Optional[str]): The name of a database dump.
            dump_date (Optional[str]): The date of a database dump.
            username_properties (Union[str, list[str]], None]): Only valid value is 'Email'.
            authorization_technologies (Union[str, list[str]], None]): Only include credential with
                these authorization technologies.
            authorization_protocols (Union[str, list[str]], None]): Only include credentials with
                these authorization protocols.
            malware_families (Union[str, list[str]], None]): Known infostealer malware families.
            organization_id (Optional[str]): The org_id if utilizing a multi-org setup.
            max_results (Optional[int]): Specifies the maximum number of credentials returned
                (default: DEFAULT_LIMIT).
            identities_per_page (Optional[int]): Number of credentials per page for pagination.
            offset (Optional[str]): Offset token for paginated results.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            IdentityLookupError: if connection error occurs.

        Returns:
            list[LeakedIdentity]: A list containing the leaked identity records.
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
        subjects: Union[str, list[str], None] = None,
        subjects_sha1: Union[str, list[str], None] = None,
        subjects_login: Union[list[dict[str, str]], list[CredentialSearch], None] = None,
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
        organization_id: Optional[str] = None,
        max_results: Optional[int] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DEFAULT_LIMIT),
        identities_per_page: Optional[int] = Field(
            ge=1, le=MAXIMUM_IDENTITIES, default=DETECTIONS_PER_PAGE
        ),
        offset: Optional[str] = None,
    ) -> list[LeakedIdentity]:
        """Lookup credential data for a set of subjects.

        The subject can be an email, a sha1 or a combination of username/domain. Different types of
        subjects can be specified at the same time but at least one has to be present.

        Example:

             .. code-block:: python
                :linenos:

                from psengine.identity import IdentityMgr

                identity_mgr = IdentityMgr()
                subjects = ["user@domain.com", "admin@domain.com"]
                creds = identity_mgr.lookup_credentials(subjects=subjects)

                # or lookup from a search result
                search = identity_mgr.search_credentials(
                        domains='norsegods.online',
                        domain_types='Email'
                )
                data = identity_mgr.lookup_credentials(subjects_login=search)

        Endpoint:
            ``/identity/credentials/lookup``

        Args:
            subjects (Union[str, list[str]], optional): An email (or list of emails) to be queried.
            subjects_sha1 (Union[str, list[str]], optional): The sha1 hash of a username or email.
                Utilized so that the actual subject being looked up is hashed and not sent to api.
            subjects_login (Optional[list[dict[str, str]]]): Username details when the login is a
                username and not an email address (also requires authorization domain).
            first_downloaded_gte (Optional[str]): The first date when these credentials were
                received and indexed by Recorded Future.
            latest_downloaded_gte (Optional[str]): Latest date when these credentials were received
                and indexed by Recorded Future. It is not unusual for the same credentials to be
                exposed multiple times, in data from different dumps and/or logs.
            exfiltration_date_gte (Optional[str]): Date when the infostealer malware exfiltrated
                data from the victim device. If Recorded Future has received data indicating that
                the credentials were stolen and exfiltrated repeatedly, then the response will
                contain several exfiltration dates.
            properties (Union[str, list[str]], optional): Password properties.
            breach_name (Optional[str]): The name of a breach.
            breach_date (Optional[str]): The date of a breach.
            dump_name (Optional[str]): The name of a database dump.
            dump_date (Optional[str]): The date of a database dump.
            username_properties (Union[str, list[str]], None]): Only valid value is 'Email'.
            authorization_technologies (Union[str, list[str]], None]): Only include credential with
                these authorization technologies.
            authorization_protocols (Union[str, list[str]], None]): Only include credentials with
                these authorization protocols.
            malware_families (Union[str, list[str]], None]): Known infostealer malware families.
            organization_id (Optional[str]): The org_id if utilizing a multi-org setup.
            max_results (int, optional): Specifies the maximum number of credentials returned
                (default: DEFAULT_LIMIT).
            identities_per_page (Optional[int]): Number of credentials per page for pagination.
            offset (Optional[str]): Offset token for paginated results.


        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            IdentityLookupError: if connection error occurs.

        Returns:
            list[LeakedIdentity]: A list containing the leaked identity records.
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
        domains: Union[str, list[str]],
        domain_types: Union[str, list[str], None] = None,
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
        organization_id: Optional[str] = None,
        max_results: Optional[int] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DEFAULT_LIMIT),
        identities_per_page: Optional[int] = Field(
            ge=1, le=MAXIMUM_IDENTITIES, default=DETECTIONS_PER_PAGE
        ),
        offset: Optional[str] = None,
    ) -> list[CredentialSearch]:
        """Search Credential data for a set of domains.

        Example:

             .. code-block:: python
                :linenos:

                from psengine.identity import IdentityMgr

                identity_mgr = IdentityMgr()
                domains = ["domain.com"]
                creds = identity_mgr.search_credentials(domains=domains)

        Endpoint:
            ``/identity/credentials/search``

        Args:
            domains (Union[str, list[str]]): A domain or multiple domains to be queried.
            domain_types (Union[str, list[str]], None]): 'Email', 'Authorization' or both can be
                specified in the array.
            first_downloaded_gte (Optional[str]): The first date when these credentials were
                received and indexed by Recorded Future.
            latest_downloaded_gte (Optional[str]): Latest date when these credentials were received
                and indexed by Recorded Future. It is not unusual for the same credentials to be
                exposed multiple times, in data from different dumps and/or logs.
            exfiltration_date_gte (Optional[str]): Date when the infostealer malware exfiltrated
                data from the victim device. If Recorded Future has received data indicating that
                the credentials were stolen and exfiltrated repeatedly, then the response will
                contain several exfiltration dates.
            properties (Union[str, list[str]], None]): Password properties.
            breach_name (Optional[str]): The name of a breach.
            breach_date (Optional[str]): The date of a breach.
            dump_name (Optional[str]): The name of a database dump.
            dump_date (Optional[str]): The date of a database dump.
            username_properties (Union[str, list[str]], None]): Only valid value is 'Email'.
            authorization_technologies (Union[str, list[str]], None]): Only include credential with
                these authorization technologies.
            authorization_protocols (Union[str, list[str]], None]): Only include credentials with
                these authorization protocols.
            malware_families (Union[str, list[str]], None]): Known infostealer malware families.
            organization_id (Optional[str]): The org_id if utilizing a multi-org setup.
            max_results (int, optional): Specifies the maximum number of credentials returned
                (default: DEFAULT_LIMIT).
            identities_per_page (Optional[int]): Number of credentials per page for pagination.
            offset (Optional[str]): Offset token for paginated results.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            IdentitySearchError: if connection error occurs.

        Returns:
            list[SearchResponseIdentity]: A list containing the search results.
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
        names: Union[str, list[str]],
        max_results: Optional[int] = Field(le=MAXIMUM_IDENTITIES, default=DEFAULT_LIMIT),
    ) -> DumpSearchOut:
        """Search if a particular database dump is present.

        Example:

             .. code-block:: python
                :linenos:

                from psengine.identity import IdentityMgr

                identity_mgr = IdentityMgr()
                dump_name = "Dump Name"
                dump_info = identity_mgr.search_dump(names=dump_name)

        Endpoint:
            ``/identity/metadata/dump/search``

        Args:
            names (Union[str, list[str]]): The name(s) of a database dump.
            max_results (Optional[int]): Specifies the maximum number of dump records returned
                (default: DEFAULT_LIMIT).

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            IdentitySearchError: if connection error occurs.

        Returns:
            DumpSearchOut: A list containing the dump search results.
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
        source: str,
        include_details: bool = True,
        organization_id: Union[list[str], str, None] = None,
        offset: Optional[str] = None,
        max_results: Optional[int] = Field(ge=1, le=MAXIMUM_IDENTITIES, default=DEFAULT_LIMIT),
        identities_per_page: Optional[int] = Field(
            ge=1, le=MAXIMUM_IDENTITIES, default=DETECTIONS_PER_PAGE
        ),
    ) -> IncidentReportOut:
        """Provides an exposure incident report for a single malware log.

        This method requests the `/identity/incident/report` endpoint to fetch detailed reports
        about exposure incidents related to a specific malware log source.

        Endpoint:
            ``/identity/incident/report``

        Example:
            Fetch incident report from a recent detection:

            .. code-block:: python
                :linenos:

                from psengine.identity import IdentityMgr

                # fetch a recent novel detection
                identity_mgr = IdentityMgr()
                detections = identity_mgr.fetch_detections(created_gte='7d', max_results=1)
                recent_detection = detections.detections[0]

                # fetch incident report for a detection using the source field
                source = recent_detection.dump.source
                report = identity_mgr.fetch_incident_report(source=source, include_details=True)

        Args:
            source (str): The raw archive with malware log data.
            include_details (bool): Return the machine details of the infected machine.
            organization_id (Optional[str]): The org_id if utilizing a multi-org setup.
            offset (Optional[str]): Offset token for paginated results.
            max_results (int, optional): Specifies the maximum number of credentials returned
                (default: DEFAULT_LIMIT).
            identities_per_page (Optional[int]): Number of credentials per page for pagination.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            IncidentReportFetchError: if connection error occurs.

        Returns:
            IncidentReportOut: A detailed incident report.
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
            ValidationError if any parameter is of incorrect type

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
