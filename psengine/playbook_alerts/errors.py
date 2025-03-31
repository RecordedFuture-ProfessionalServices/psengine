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


class PlaybookAlertError(RecordedFutureError):
    """Error raised when playbook alert fails."""


class PlaybookAlertSearchError(PlaybookAlertError):
    """Error raised when playbook alert search query fails."""


class PlaybookAlertUpdateError(PlaybookAlertError):
    """Error raised when playbook alert update fails."""


class PlaybookAlertFetchError(PlaybookAlertError):
    """Error raised when playbook alert fetch fails."""


class PlaybookAlertRetrieveImageError(PlaybookAlertError):
    """Error raised when playbook alert image fetch fails."""
