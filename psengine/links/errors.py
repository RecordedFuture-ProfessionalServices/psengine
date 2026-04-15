from ..errors import RecordedFutureError


class LinksError(RecordedFutureError):
    """Base class for all exceptions raised by the Links module.

    This class handles dynamic string formatting for all Links-related
    exceptions, allowing subclasses to easily inject context.
    """

    def __init__(self, message: str = 'A Links error occurred: {}', *args):
        """Initialize and format the exception message.

        Args:
            message (str): The error message or template string.
            *args: Variable length arguments to format the message.
        """
        formatted_message = message.format(*args) if args else message
        super().__init__(formatted_message, *args)


class LinksSearchError(LinksError):
    """Error raised when a Links search request fails."""

    def __init__(self, message: str = 'Links search request failed: {}', *args):
        super().__init__(message, *args)


class LinksMetadataError(LinksError):
    """Error raised when fetching or validating Links metadata fails."""

    def __init__(self, message: str = 'Failed to retrieve Links metadata: {}', *args):
        super().__init__(message, *args)


class LinksValidationError(LinksError):
    """Error raised when pre-flight validation of a Links request fails."""

    def __init__(self, message: str = 'Links request validation failed: {}', *args):
        super().__init__(message, *args)
