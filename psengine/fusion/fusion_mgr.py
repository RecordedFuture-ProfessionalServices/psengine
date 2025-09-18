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
from datetime import datetime
from typing import Annotated, Optional, Union
from urllib.parse import quote

from pydantic import Field, validate_call
from typing_extensions import Doc

from psengine.common_models import RFBaseModel
from psengine.endpoints import EP_FUSION_DIR_V3, EP_FUSION_FILES_V3

from ..helpers import debug_call
from ..helpers.helpers import connection_exceptions
from ..rf_client import RFClient
from .errors import (
    FusionGetFileError,
    FusionListDirError,
)


class FusionFile(RFBaseModel):
    file_path: str
    file_content: bytes
    file_found: bool


class File(RFBaseModel):
    type_: str = Field(alias='type')
    name: str
    path: str
    format: Optional[str] = None
    hash: Optional[str] = None
    created: Optional[datetime] = None
    size: Optional[int] = None
    flow: Optional[str] = None
    owner: Optional[str] = None


class FusionDirectory(RFBaseModel):
    name: str
    path: str
    files: list[File]
    type_: str = Field(alias='type')


class FusionMgr:
    """Manages requests for Recorded Future Fusion files."""

    def __init__(self, rf_token: str = None):
        """Initializes the `FusionMgr` object.

        Args:
            rf_token (str, optional): Recorded Future API token.
        """
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=FusionGetFileError)
    def get_files(
        self, file_paths: Annotated[Union[str, list[str]], Doc('One or more paths to fetch')]
    ) -> Annotated[list[FusionFile], Doc('A FusionFile object with name and content of the file')]:
        """Get one or more files.

        Endpoint:
            `/fusion/v3/files/`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            FusionGetFileError: If API error occurs.
        """
        returned_files = []
        file_paths = file_paths if isinstance(file_paths, list) else [file_paths]
        file_paths = [f'/{p}' if not p.startswith('/') else p for p in file_paths]

        for file in file_paths:
            data = self._get_files(file)
            if data:
                returned_files.append(
                    FusionFile.model_validate(
                        {'file_path': file, 'file_content': data.content, 'file_found': True}
                    )
                )
            else:
                returned_files.append(
                    FusionFile.model_validate(
                        {'file_path': file, 'file_content': '', 'file_found': False}
                    )
                )

        return returned_files

    @connection_exceptions(ignore_status_code=[404], exception_to_raise=FusionGetFileError)
    def _get_files(self, file):
        return self.rf_client.request('get', EP_FUSION_FILES_V3 + quote(file, safe='.'))

    # @debug_call
    # @validate_call
    # @connection_exceptions(ignore_status_code=[], exception_to_raise=FusionPostFileError)
    # def post_files(
    #     self,
    #     published: Annotated[Optional[str], Doc('Notes published after a date.')] = None,
    # ) -> Annotated[list[AnalystNote], Doc('A list of deduplicated AnalystNote objects.')]:
    #     """Get file.
    #
    #     Endpoint:
    #         `/fusion/v3/files/`
    #
    #     Raises:
    #         ValidationError: If any supplied parameter is of incorrect type.
    #         FusionPostFileError: If API error occurs.
    #     """
    #
    # @debug_call
    # @validate_call
    # @connection_exceptions(ignore_status_code=[], exception_to_raise=FusionDeleteFileError)
    # def delete_files(
    #     self,
    #     published: Annotated[Optional[str], Doc('Notes published after a date.')] = None,
    # ) -> Annotated[list[AnalystNote], Doc('A list of deduplicated AnalystNote objects.')]:
    #     """Get file.
    #
    #     Endpoint:
    #         `/fusion/v3/files/`
    #
    #     Raises:
    #         ValidationError: If any supplied parameter is of incorrect type.
    #         FusionDeleteFileError: If API error occurs.
    #     """
    #
    # @debug_call
    # @validate_call
    # @connection_exceptions(ignore_status_code=[], exception_to_raise=FusionHeadFileError)
    # def head_files(
    #     self,
    #     published: Annotated[Optional[str], Doc('Notes published after a date.')] = None,
    # ) -> Annotated[list[AnalystNote], Doc('A list of deduplicated AnalystNote objects.')]:
    #     """Get file.
    #
    #     Endpoint:
    #         `/fusion/v3/files/`
    #
    #     Raises:
    #         ValidationError: If any supplied parameter is of incorrect type.
    #         FusionHeadFileError: If API error occurs.
    #     """
    #

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=FusionListDirError)
    def list_dir(
        self, file_path: Annotated[str, Doc('Directory to list')]
    ) -> Annotated[FusionDirectory, Doc('The tree structure.')]:
        """Get directory, subdirectory and file informations of a path.

        Endpoint:
            `/fusion/v3/files/directory`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            FusionListDirError: If API error occurs.
        """
        data = self.rf_client.request('get', EP_FUSION_DIR_V3 + quote(file_path, safe='.')).json()
        return FusionDirectory.model_validate(data)
