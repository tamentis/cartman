class UsageException(Exception):
    """Base class for any program usage errors/exceptions."""

class InvalidParameter(UsageException):
    """A parameter for the command is invalids (wrong type?)."""


class FatalError(Exception):
    """Unrecoverable error during runtime."""

class UnknownCommand(FatalError):
    """Command is not defined."""

class RequestException(FatalError):
    """A request to Trac failed."""

class LoginError(RequestException):
    """Raise when unable to login."""
