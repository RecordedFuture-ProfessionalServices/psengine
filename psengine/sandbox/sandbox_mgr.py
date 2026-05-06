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
from typing import Annotated, Literal, cast

from pydantic import Field, validate_call
from typing_extensions import Doc

from ..endpoints import (
    EP_SANDBOX_SAMPLES_SUMMARY,
    EP_SANDBOX_SEARCH,
    EP_SANDBOX_USERS,
    EP_SANDBOX_USERS_APIKEYS,
    EP_SANDBOX_USERS_APIKEYS_NAME,
    EP_SANDBOX_USERS_ID,
    SANDBOX_BASE_URLS,
)
from ..helpers import debug_call
from .client import SandboxClient
from .constants import DEFAULT_PAGE_LIMIT
from .sandbox import SampleSummary, SearchIn, SearchResult

SandboxChoice = Literal['eu', 'usa', 'apj', 'public', 'private']


def validate_sandbox_choice(sandbox_choice: str) -> SandboxChoice:
    """Validate the sandbox selection and return a typed value."""
    if sandbox_choice not in SANDBOX_BASE_URLS:
        raise ValueError(
            f'Invalid sandbox choice: {sandbox_choice}. Must be one of {list(SANDBOX_BASE_URLS.keys())}'
        )
    return cast(SandboxChoice, sandbox_choice)


class SandboxMgr:
    """Manages requests for Recorded Future sandbox."""

    def __init__(
        self,
        api_token: Annotated[
            str | None,
            Doc('The Sandbox API token. Defaults to SANDBOX_TOKEN environment variable.'),
        ] = None,
        sandbox_choice: Annotated[
            SandboxChoice,
            Doc('Sandbox environment to use. Options: eu (default), usa, apj, public, private.'),
        ] = 'eu',
    ):
        """Initializes the `SandboxMgr` object."""
        self.log = logging.getLogger(__name__)
        self.base_url = SANDBOX_BASE_URLS[validate_sandbox_choice(sandbox_choice)]
        self.sb_client = SandboxClient(api_token=api_token) if api_token else SandboxClient()

    @debug_call
    @validate_call
    def sample_summary(self, sample_id: str) -> SampleSummary:
        endpoint = EP_SANDBOX_SAMPLES_SUMMARY.format(base_url=self.base_url, sample_id=sample_id)
        data = self.sb_client.request(
            'get',
            endpoint,
        )
        return SampleSummary.model_validate(data.json())

    def search(
        self,
        file_hash: list[str] | str | None = None,
        family: list[str] | str | None = None,
        tag: list[str] | str | None = None,
        botnet: list[str] | str | None = None,
        platform: list[str] | str | None = None,
        extracted_c2_data: list[str] | str | None = None,
        wallet: list[str] | str | None = None,
        analysis_time: list[str] | str | None = None,
        query: str | None = None,
        max_results: int | None = DEFAULT_PAGE_LIMIT,
    ):
        # TODO: write about the id constraints
        params = {p: v for p, v in locals().items() if p not in ('self', 'query', 'max_results')}
        params = SearchIn.model_validate(params).to_query_out()

        if query:
            params.query += query

        endpoint = EP_SANDBOX_SEARCH.format(base_url=self.base_url)
        data = self.sb_client.request_paged(
            'get', endpoint, params=params.model_dump(), max_samples=max_results
        )
        return [SearchResult.model_validate(e) for e in data]

    @debug_call
    @validate_call
    def fetch_all_users(
        self,
    ) -> Annotated[list[dict], Doc('List of company users.')]:
        """Fetch and return company users from `GET /users`."""
        endpoint = EP_SANDBOX_USERS.format(base_url=self.base_url)
        print(f'fetch_all_users [GET]: {endpoint}')
        response = self.sb_client.request('get', endpoint)
        payload = response.json()

        return payload

    @debug_call
    @validate_call
    def create_user(
        self,
    ) -> Annotated[str, Doc('POST /users endpoint URL.')]:
        """Return and print the URL for creating a user (POST /users)."""
        endpoint = EP_SANDBOX_USERS.format(base_url=self.base_url)
        print(f'create_user [POST]: {endpoint}')
        return endpoint

    @debug_call
    @validate_call
    def fetch_user(
        self,
        user_id: Annotated[str, Field(min_length=1), Doc('Sandbox user identifier.')],
    ) -> Annotated[str, Doc('Resolved endpoint URL for fetching or deleting a user.')]:
        """Return and print the URL for getting a user (GET /users/{userID})."""
        endpoint = EP_SANDBOX_USERS_ID.format(base_url=self.base_url, user_id=user_id)
        print(f'fetch_user [GET]: {endpoint}')
        return endpoint

    @debug_call
    @validate_call
    def delete_user(
        self,
        user_id: Annotated[
            str,
            Field(min_length=1),
            Doc('User ID, username, or email supported by the endpoint.'),
        ],
    ) -> Annotated[str, Doc('DELETE /users/{userID} endpoint URL.')]:
        """Return and print the URL for deleting a user (DELETE /users/{userID})."""
        endpoint = EP_SANDBOX_USERS_ID.format(base_url=self.base_url, user_id=user_id)
        print(f'delete_user [DELETE]: {endpoint}')
        return endpoint

    @debug_call
    @validate_call
    def fetch_user_apikeys(
        self,
        user_id: Annotated[str, Field(min_length=1), Doc('Sandbox user identifier.')],
    ) -> Annotated[str, Doc('Resolved endpoint URL for listing or creating user API keys.')]:
        """Return and print the URL for listing user API keys (GET /users/{userID}/apikeys)."""
        endpoint = EP_SANDBOX_USERS_APIKEYS.format(base_url=self.base_url, user_id=user_id)
        print(f'fetch_user_apikeys [GET]: {endpoint}')
        return endpoint

    @debug_call
    @validate_call
    def create_user_apikey(
        self,
        user_id: Annotated[str, Field(min_length=1), Doc('Sandbox user identifier.')],
    ) -> Annotated[str, Doc('Resolved endpoint URL for listing or creating user API keys.')]:
        """Return and print the URL for creating a user API key (POST /users/{userID}/apikeys)."""
        endpoint = EP_SANDBOX_USERS_APIKEYS.format(base_url=self.base_url, user_id=user_id)
        print(f'create_user_apikey [POST]: {endpoint}')
        return endpoint

    @debug_call
    @validate_call
    def delete_user_apikey(
        self,
        user_id: Annotated[str, Field(min_length=1), Doc('Sandbox user identifier.')],
        name: Annotated[str, Field(min_length=1), Doc('API key name.')],
    ) -> Annotated[str, Doc('Resolved endpoint URL for deleting a specific user API key.')]:
        """Return and print the URL for deleting a user API key (DELETE /users/{userID}/apikeys/{name})."""
        endpoint = EP_SANDBOX_USERS_APIKEYS_NAME.format(
            base_url=self.base_url, user_id=user_id, name=name
        )
        print(f'delete_user_apikey [DELETE]: {endpoint}')
        return endpoint

    def submit_sample(): ...

    def fetch_sample(): ...

    def fetch_my_sample(): ...

    def download_sample(): ...

    def sample_overview(): ...

    def delete_sample(): ...
