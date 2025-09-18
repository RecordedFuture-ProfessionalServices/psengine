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

from ..errors import RecordedFutureError


class FusionGetFileError(RecordedFutureError):
    """Error raise when the get file operation fails."""


class FusionHeadFileError(RecordedFutureError):
    """Error raise when the head file operation fails."""


class FusionPostFileError(RecordedFutureError):
    """Error raise when the post file operation fails."""


class FusionDeleteFileError(RecordedFutureError):
    """Error raise when the delete file operation fails."""


class FusionListDirError(RecordedFutureError):
    """Error raise when the list dir operation fails."""
