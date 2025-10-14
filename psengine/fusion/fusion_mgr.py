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
from pathlib import Path
from typing import Annotated, Union
from urllib.parse import quote

from pydantic import validate_call
from typing_extensions import Doc

from ..endpoints import EP_FUSION_DIR_V3, EP_FUSION_FILES_V3
from ..helpers import debug_call
from ..helpers.helpers import connection_exceptions
from ..rf_client import RFClient
from .errors import (
    FusionDeleteFileError,
    FusionGetFileError,
    FusionHeadFileError,
    FusionListDirError,
    FusionPostFileError,
)
from .models import DirectoryListOut, FileDeleteOut, FileGetOut, FileHeadOut, FileInfoOut


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
    ) -> Annotated[list[FileGetOut], Doc('A FusionFile object with name and content of the file')]:
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
            data = self._get_file(file)
            if data:
                returned_files.append(
                    FileGetOut.model_validate(
                        {'path': file, 'content': data.content, 'exists': True}
                    )
                )
            else:
                returned_files.append(
                    FileGetOut.model_validate({'path': file, 'content': '', 'exists': False})
                )

        return returned_files

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=FusionPostFileError)
    def post_file(
        self,
        file_path: Annotated[Path, Doc('Path of the local file')],
        fusion_path: Annotated[str, Doc('Path of the fusion file')],
    ) -> Annotated[list[FileInfoOut], Doc('Info of the file that have been posted')]:
        """Post a file.

        Endpoint:
            `/fusion/v3/files/`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            FusionPostFileError: If API error occurs or the input file cannot be read.
        """
        if not file_path.exists():
            raise FusionPostFileError(f'The file {file_path} does not exist')

        data = file_path.read_bytes()

        headers = 'application/octet-stream'
        returned_data = self.rf_client.request(
            'post',
            EP_FUSION_FILES_V3 + quote(fusion_path, safe='.'),
            data=data,
            content_type_header=headers,
        ).json()

        return FileInfoOut.model_validate(returned_data)

    @debug_call
    @validate_call
    def delete_files(
        self, file_paths: Annotated[Union[str, list[str]], Doc('One or more paths to delete')]
    ) -> Annotated[list[FileDeleteOut], Doc('A list of deleted files.')]:
        """Delete one or more files.

        Endpoint:
            `/fusion/v3/files/`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            FusionDeleteFileError: If API error occurs.
        """
        returned_files = []
        file_paths = file_paths if isinstance(file_paths, list) else [file_paths]
        file_paths = [f'/{p}' if not p.startswith('/') else p for p in file_paths]

        for file in file_paths:
            data = self._delete_file(file)
            returned_files.append(
                FileDeleteOut.model_validate({'path': file, 'deleted': bool(data)})
            )

        return returned_files

    @debug_call
    @validate_call
    def head_files(
        self, file_paths: Annotated[Union[str, list[str]], Doc('One or more paths to check')]
    ) -> Annotated[list[FileHeadOut], Doc('List of headers info for the requested files.')]:
        """Head of one or more files.

        Endpoint:
            `/fusion/v3/files/`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            FusionHeadFileError: If API error occurs.
        """
        returned_files = []
        file_paths = file_paths if isinstance(file_paths, list) else [file_paths]
        file_paths = [f'/{p}' if not p.startswith('/') else p for p in file_paths]

        for file in file_paths:
            data = self._head_file(file)
            if data:
                returned_files.append(
                    FileHeadOut.model_validate({'path': file, 'exists': True, **data.headers})
                )
            else:
                returned_files.append(FileHeadOut.model_validate({'path': file, 'exists': False}))

        return returned_files

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=FusionListDirError)
    def list_dir(
        self, file_path: Annotated[str, Doc('Directory to list')]
    ) -> Annotated[DirectoryListOut, Doc('The tree structure.')]:
        """Get directory, subdirectory and file information of a path.

        Endpoint:
            `/fusion/v3/files/directory`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            FusionListDirError: If API error occurs.
        """
        data = self.rf_client.request('get', EP_FUSION_DIR_V3 + quote(file_path, safe='.')).json()
        return DirectoryListOut.model_validate(data)

    @connection_exceptions(ignore_status_code=[404], exception_to_raise=FusionHeadFileError)
    def _head_file(self, file):
        return self.rf_client.request('head', EP_FUSION_FILES_V3 + quote(file, safe='.'))

    @connection_exceptions(ignore_status_code=[404], exception_to_raise=FusionDeleteFileError)
    def _delete_file(self, file):
        return self.rf_client.request('delete', EP_FUSION_FILES_V3 + quote(file, safe='.'))

    @connection_exceptions(ignore_status_code=[404], exception_to_raise=FusionGetFileError)
    def _get_file(self, file):
        return self.rf_client.request('get', EP_FUSION_FILES_V3 + quote(file, safe='.'))
