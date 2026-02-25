import logging
from typing import Optional, Union

from pydantic import validate_call

from ..helpers import debug_call
from .client import ASIClient


class ASIMgr:
    """Manages requests for Recorded Future SecurityTrails (ASI)."""

    def __init__(self, api_token: str = None):
        """Initializes the `SandboxMgr` object.

        Args:
            api_token (str, optional): Sandbox API token.
        """
        self.log = logging.getLogger(__name__)
        self.asi_client = ASIClient(api_token=api_token) if api_token else ASIClient()

    def post_request_paged(self): ...

    def get_request_paged(self):
        return self.asi_client.request_paged(
            'get',
            'https://api.securitytrails.com/v2/projects/3ce6292b-29be-4199-9024-231818e384a4/assets',
            max_results=300,
            objects_per_page=30,
        )
