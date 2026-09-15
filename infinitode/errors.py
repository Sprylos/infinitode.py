from __future__ import annotations

__all__ = (
    "InfinitodeError",
    "APIError",
    "BadArgument",
    "PlayerNotFound",
    "ParseError",
)


class InfinitodeError(Exception):
    """Base Infinitode Error."""

    pass


class APIError(InfinitodeError):
    """Error directly related to the communication with the API."""

    pass


class BadArgument(InfinitodeError):
    """Error raised when an invalid argument is passed."""

    pass


class PlayerNotFound(BadArgument):
    """Error raised when a player lookup has no exact match."""

    pass


class ParseError(InfinitodeError):
    """Error raised when an HTML response cannot be parsed."""

    pass
