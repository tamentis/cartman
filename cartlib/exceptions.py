class UsageException(Exception):
    """Base class for any program usage errors/exceptions."""
    pass

class UnknownCommand(UsageException):
    """Command is not defined."""
    pass
class InvalidParameter(UsageException):
    """A parameter for the command is invalids (wrong type?)."""
    pass

class FatalError(Exception):
    """Unrecoverable error during runtime."""
    pass
