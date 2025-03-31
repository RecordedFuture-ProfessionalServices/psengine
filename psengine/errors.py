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


class RecordedFutureError(Exception):
    """Base class for exceptions in PSEngine."""

    def __init__(
        self,
        message='An error occurred. Raise exceptions with a message argument to see additional information',  # noqa: E501
        *args,
    ):
        super().__init__(message, *args)
        self.message = message

    def __str__(self):
        return self.message


class ReadFileError(RecordedFutureError):
    """Error raised when PSEngine classes cannot read from file."""

    def __init__(self, message='Error reading from file', *args):
        super().__init__(message.format(*args), *args)


class WriteFileError(RecordedFutureError):
    """Error raised when PSEngine classes cannot write to file."""

    def __init__(self, message='Error writing to file', *args):
        super().__init__(message.format(*args), *args)
