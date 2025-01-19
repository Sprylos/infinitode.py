from __future__ import annotations

# std
import time
import asyncio
from typing import Any, Callable, Coroutine, Dict, Tuple, TypeVar, ParamSpec

T = TypeVar("T")
P = ParamSpec("P")


__all__ = ("MISSING", "async_expiring_cache", "try_int")


def try_int(string: str, /, *, default: int = 0) -> int:
    try:
        return int(string)
    except ValueError:
        return default


def async_expiring_cache(seconds: int = 60) -> Any:
    """Decorator to cache coroutines return value for the given amount of seconds.
    
    It is not perfect because 
    """

    def decorator(func: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, asyncio.Task[T]]:
        cache: Dict[Tuple[Any, ...], Tuple[asyncio.Task[T], float]] = {}

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> asyncio.Task[T]:
            key: Tuple[Any, ...] = (*args, *kwargs.items())  # key consists of the function arguments
            if key in cache:
                value, timestamp = cache[key]
                if time.time() < timestamp + seconds:
                    return value
   
            coro = func(*args, **kwargs)
            value = asyncio.ensure_future(coro)
            cache[key] = (value, time.time())
            return value

        return wrapper

    return decorator


class _MissingSentinel:
    # taken from discord.py, see:
    # https://github.com/Rapptz/discord.py/blob/a14b43f2fda863ed6555374eb872bf014bdd1adf/discord/utils.py#L96

    def __eq__(self, other: Any):
        return False

    def __bool__(self):
        return False

    def __hash__(self):
        return 0

    def __repr__(self):
        return "..."


MISSING: Any = _MissingSentinel()
