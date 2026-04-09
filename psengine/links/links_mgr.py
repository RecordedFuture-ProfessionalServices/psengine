import logging

from psengine import RFClient
from typing import Annotated, Optional

class LinksMgr:
    """Manager for interacting with the Recorded Future Links API."""

    def __init__(
        self,
        rf_token: Annotated[Optional[str], Doc('Recorded Future API token.')] = None,
    ):
        """Initialize the `LookupMgr` object."""
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

        # Cache variables by "Lazy loading"
        # vars start asNone and will hold 'sets' of valid IDs once fetched
        self._valid_sections: Optional[set[str]] = None
        self._valid_entity_types: Optional[set[str]] = None
        self._valid_events: Optional[set[str]] = None

        # Fetcher/Loader
        def _get_valid_sections() -> set[str]:
            """Lazy load and cache valid section IDs"""
            # If it's already cached, return it instantly
            if self._valid_sections is not None:
                return self._valid_sections

            self.log.debug("Fetching valid sections from "
                           "api.recordedfuture.com/links/metadata/sections")

            # If not cached make the GET request
            response = self.rf_client.request('GET',
                                              'https://api.recordedfuture.com/links/metadata/sections').json()

            # Extract the 'id' in a set for fast lookups
            self._valid_sections = {item['id'] for item in response.get('data', [])}

            return self._valid_sections