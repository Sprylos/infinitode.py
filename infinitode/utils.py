from __future__ import annotations

# std
from typing import Any

__all__ = ('MISSING',)


class _MissingSentinel:
    # taken from discord.py, see:
    # https://github.com/Rapptz/discord.py/blob/a14b43f2fda863ed6555374eb872bf014bdd1adf/discord/utils.py#L96

    def __eq__(self, other):
        return False

    def __bool__(self):
        return False

    def __hash__(self):
        return 0

    def __repr__(self):
        return '...'


MISSING: Any = _MissingSentinel()
