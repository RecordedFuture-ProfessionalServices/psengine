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


class NoRulesFoundError(RecordedFutureError):
    """Raised when there were no rules returned or an exception occurred during the request."""


class AlertFetchError(RecordedFutureError):
    """Raised when there were no alerts returned or an exception occurred during the request."""


class AlertImageFetchError(RecordedFutureError):
    """Raised when there were no images returned or an exception occurred during the request."""


class AlertUpdateError(RecordedFutureError):
    """Error raised when the update request encounters an exception."""


class AlertSearchError(RecordedFutureError):
    """Error raised when there was an error during the search request."""


class AlertMarkdownError(RecordedFutureError):
    """Error raised when there was an error during markdown conversion."""
