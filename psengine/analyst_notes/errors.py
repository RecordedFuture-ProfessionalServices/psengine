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


class AnalystNoteError(RecordedFutureError):
    """Error raise when the init of AnalystNote is failing."""


class AnalystNoteLookupError(RecordedFutureError):
    """Error raise when cannot lookup an analyst note."""


class AnalystNoteSearchError(RecordedFutureError):
    """Error raise when cannot search analyst notes."""


class AnalystNoteAttachmentError(RecordedFutureError):
    """Error raise when cannot lookup an analyst note."""


class AnalystNoteDeleteError(RecordedFutureError):
    """Error raise when cannot delete an analyst note."""


class AnalystNotePreviewError(RecordedFutureError):
    """Error raise when cannot post to preview endpoint."""


class AnalystNotePublishError(RecordedFutureError):
    """Error raise when cannot post to publish endpoint."""
