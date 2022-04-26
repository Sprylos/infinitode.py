from __future__ import annotations

__all__ = (
    'InfinitodeError',
    'APIError',
    'BadArgument',
    'MissingSession',
)


class InfinitodeError(Exception):
    '''Base Infinitode Error.'''
    pass


class APIError(InfinitodeError):
    '''Error directly related to the communication with the API.'''
    pass


class BadArgument(InfinitodeError):
    '''Error raised when an invalid argument is passed.'''
    pass


class MissingSession(InfinitodeError):
    '''Error raised when a session is required but not given.'''
