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

from datetime import datetime
from typing import Optional

from pydantic import Field

from ..common_models import RFBaseModel


class FileInfoOut(RFBaseModel):
    type_: str = Field(alias='type')
    name: str
    path: str
    format: Optional[str] = None
    hash: Optional[str] = None
    created: Optional[datetime] = None
    size: Optional[int] = None
    flow: Optional[str] = None
    owner: Optional[str] = None


class DirectoryListOut(RFBaseModel):
    name: str
    path: str
    files: list[FileInfoOut]
    type_: str = Field(alias='type')


class FileGetOut(RFBaseModel):
    path: str
    content: bytes
    exists: bool


class FileDeleteOut(RFBaseModel):
    path: str
    deleted: bool


class FileHeadOut(RFBaseModel):
    path: str
    exists: bool
    content_disposition: Optional[str] = Field(alias='content-disposition', default=None)
    content_length: Optional[int] = Field(alias='Content-Length', default=None)
    content_type: Optional[str] = Field(alias='content-type', default=None)
    etag: Optional[str] = None
    last_modified: Optional[str] = Field(alias='last-modified', default=None)
