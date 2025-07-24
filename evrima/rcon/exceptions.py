class EvrimaRCONError(Exception):
    """Base exception for Evrima RCON errors."""
    pass


class ConnectionFailed(EvrimaRCONError):
    """Raised when connection to the RCON server fails."""
    pass


class CommandFailed(EvrimaRCONError):
    """Raised when an RCON command fails to execute properly."""
    pass
