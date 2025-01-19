from __future__ import annotations

# std
from typing import Any, Dict, Optional, Union, TYPE_CHECKING

# local
from .errors import InfinitodeError
from .badge import Badge

if TYPE_CHECKING:
    from .core import Session
    from .player import Player

__all__ = ("Score",)


class Score:
    """Represents a single in-game Score."""

    __slots__ = (
        "_method",
        "_mapname",
        "_mode",
        "_difficulty",
        "_playerid",
        "_rank",
        "_score",
        "raw",
        "_has_pfp",
        "_level",
        "_nickname",
        "_pinned_badge",
        "_position",
        "_top",
        "_total",
        "_player",
    )

    def __init__(
        self,
        method: str,
        mapname: str,
        mode: str,
        difficulty: str,
        playerid: str,
        rank: Union[int, str],
        score: Union[int, str],
        *,
        hasPfp: Optional[bool] = None,
        level: Optional[int] = None,
        nickname: Optional[str] = None,
        pinnedBadge: Optional[Dict[str, str]] = None,
        position: Optional[int] = None,
        top: Optional[str] = None,
        total: Optional[Union[str, int]] = None,
        player: Optional[Player] = None,
    ) -> None:
        self._method = method
        self._mapname = mapname
        self._mode = mode
        self._difficulty = difficulty
        self._playerid = playerid
        self._rank = int(rank)
        self._score = int(score)
        self._has_pfp = hasPfp
        self._level = level
        self._nickname = nickname
        self._pinned_badge: Optional[Badge] = (
            Badge(**pinnedBadge) if pinnedBadge is not None else None
        )  # nopep8
        self._position: Optional[int] = (
            int(position) if position is not None else None
        )  # nopep8
        self._top = top
        # apparently some payloads provide total, but i think it is pointless as a property
        # so i will keep it as a private attribute just in case it will ever be needed
        self._total: Optional[int] = int(total) if total is not None else None
        self._player = player

    @classmethod
    def from_payload(
        cls,
        # a standalone score payload is only received from the leaderboards rank call
        method: str,
        mapname: str,
        mode: str,
        difficulty: str,
        playerid: str,
        payload: Dict[str, Any],
    ) -> Score:
        """'Builds an instance with the given payload."""
        score: Dict[str, Any] = payload["player"]
        return cls(method, mapname, mode, difficulty, playerid, **score)

    @property
    def method(self) -> str:
        """The name of the method responsible for creating this Score."""
        return self._method

    @property
    def mapname(self) -> str:
        """The name of the map this score is from."""
        return self._mapname

    @property
    def mode(self) -> str:
        """The mode of this score (score/waves)."""
        return self._mode

    @property
    def difficulty(self) -> str:
        """The difficulty of this score (EASY/NORMAL/ENDLESS_I)"""
        return self._difficulty

    @property
    def playerid(self) -> str:
        """The playerid of the player."""
        return self._playerid

    @property
    def rank(self) -> int:
        """The rank (position) of this score."""
        return self._rank

    @property
    def score(self) -> int:
        """The score (points) of this score."""
        return self._score

    @property
    def has_pfp(self) -> Optional[bool]:
        """Whether the player has a pfp or not. Only sometimes available."""
        return self._has_pfp

    @property
    def level(self) -> Optional[int]:
        """The XP level of the player. Only sometimes available."""
        return self._level

    @property
    def nickname(self) -> Optional[str]:
        """The nickname of the player. Only sometimes available."""
        return self._nickname

    @property
    def pinned_badge(self) -> Optional[Badge]:
        """The pinned badge of the player. Only sometimes available."""
        return self._pinned_badge

    @property
    def position(self) -> Optional[int]:
        """Similar to ~.rank, but coming from the server. Only sometimes available and unreliable beyond top 200."""
        return self._position

    @property
    def top(self) -> Optional[str]:
        """The top % of this score (as str)."""
        return self._top

    @property
    def player(self) -> Optional[Player]:
        """The player object of this score. This has to be fetched first using the ~.fetch_player coro."""
        return self._player

    async def fetch_player(self, session: Session) -> Player:
        """Fetch the player using a given session (This is an API call)."""
        if self._player is None:
            self._player = await session.player(self._playerid)
        return self._player

    def format_score(self):
        """Formats the score the way i use it in my Advinas bot."""
        if self._nickname is None:
            raise InfinitodeError(
                "The score is not valid for formatting (There is no nickname attached to this score)."
            )

        return "#{:<5} {:<22} {:>0,}".format(
            self._rank,
            self._nickname if len(self._nickname) < 21 else f"{self._nickname[:19]}...",
            self._score,
        )

    def print_score(self):
        """Prints out the result of format_score()."""
        print(self.format_score())

    # magic methods

    def __repr__(self) -> str:
        attrs: dict[str, Any] = {
            "method": self._method,
            "mapname": self._mapname,
            "mode": self._mode,
            "difficulty": self._difficulty,
            "playerid": self._playerid,
            "rank": self._rank,
            "score": self._score,
            # only include the "important" attributes.
            # 'has_pfp': self._has_pfp,
            # 'level': self._level,
            # 'nickname': self._nickname,
            # 'pinned_badge': self._pinned_badge,
            # 'position': self._position,
            # 'top': self._top,
            # 'total': self._total,
            # 'player': True if self._player is not None else None
        }
        inner = " ".join(f"{k}={v}" for k, v in attrs.items())
        return f"<{self.__class__.__name__} {inner}>"
