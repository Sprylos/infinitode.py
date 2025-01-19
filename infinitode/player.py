from __future__ import annotations

# std
from typing import Any, Dict, Optional, Union, Tuple, TYPE_CHECKING

# local
from .score import Score
from .errors import InfinitodeError
from .utils import MISSING

if TYPE_CHECKING:
    from .core import Session


__all__ = ("Player",)


AVATAR_URL = "https://storage.prineside.com/files/i2{}/avatars/{}-128.png"


class Player:
    """Represents an in-game Player."""

    __slots__ = (
        "_badges",
        "_beta",
        "_created_at",
        "_daily_quest",
        "_issues",
        "_level",
        "_levels",
        "_nickname",
        "_playerid",
        "_replays",
        "_season_level",
        "_season_xp",
        "_season_xp_max",
        "_skill_point",
        "_total_rank",
        "_total_score",
        "_total_top",
        "_created_at",
        "_xp",
        "_xp_max",
    )

    def __init__(
        self,
        beta: bool,
        playerid: str,
        nickname: str,
        *,
        levels: Dict[str, Score],
        level: int,
        xp: int,
        xp_max: int,
        season_level: int,
        season_xp: int,
        season_xp_max: int,
        badges: Dict[str, Tuple[str, str]],
        total_score: Union[int, str],
        total_rank: Union[int, str],
        total_top: str,
        replays: int,
        issues: int,
        created_at: str,
    ) -> None:
        self._beta = beta
        self._playerid = playerid
        self._nickname = nickname
        self._levels = levels
        self._level = level
        self._xp = xp
        self._xp_max = xp_max
        self._season_level = season_level
        self._season_xp = season_xp
        self._season_xp_max = season_xp_max
        self._badges = badges
        self._total_score = int(total_score)
        self._total_rank = int(total_rank)
        self._total_top = total_top
        self._replays = replays
        self._issues = issues
        self._created_at = created_at
        self._daily_quest: Optional[Score] = MISSING
        self._skill_point: Optional[Score] = MISSING

    @property
    def playerid(self) -> str:
        """The player's playerid."""
        return self._playerid

    @property
    def nickname(self) -> str:
        """The player's nickname."""
        return self._nickname

    @property
    def level(self) -> int:
        """The player's XP level."""
        return self._level

    @property
    def xp(self) -> int:
        """The player's XP in the current level."""
        return self._xp

    @property
    def xp_max(self) -> int:
        """The XP required for the player to level up."""
        return self._xp_max

    @property
    def season_level(self) -> int:
        """The player's season XP level."""
        return self._season_level

    @property
    def season_xp(self) -> int:
        """The player's XP in the current season level."""
        return self._season_xp

    @property
    def season_xp_max(self) -> int:
        """The season XP required for the player to level up."""
        return self._season_xp_max

    @property
    def badges(self) -> Dict[str, Tuple[str, str]]:
        """
        The player's badges as a dict in the form:
            type: (rarity, colour)
        """
        return self._badges

    @property
    def total_score(self) -> int:
        """The player's total (seasonal) score."""
        return self._total_score

    @property
    def total_rank(self) -> int:
        """The player's total (seasonal) rank (placement in the leaderboard)."""
        return self._total_rank

    @property
    def total_top(self) -> str:
        """The player's total (seasonal) top % (as str)."""
        return self._total_top

    @property
    def replays(self) -> int:
        """The player's amount of verified replays."""
        return self._replays

    @property
    def issues(self) -> int:
        """The player's amount of replays that failed verification."""
        return self._issues

    @property
    def created_at(self) -> str:
        """The player's creation date as a str in the format: '%Y-%m-%d'."""
        return self._created_at

    @property
    def avatar_link(self):
        """The link to the player's avatar. Invalid URL if the user doesn't have a pfp."""
        return AVATAR_URL.format("beta" if self._beta else "", self._playerid)

    @property
    def daily_quest(self):
        """Returns the player's daily quest score, or raises InfinitodeError if it wasn't fetched yet."""
        if self._daily_quest is MISSING:
            raise InfinitodeError(
                "This score has not been fetched yet. Use ~.fetch_daily_quest first."
            )
        else:
            return self._daily_quest

    @property
    def skill_point(self):
        """Returns the player's daily quest score, or raises InfinitodeError if it wasn't fetched yet."""
        if self._skill_point is MISSING:
            raise InfinitodeError(
                "This score has not been fetched yet. Use ~.fetch_skill_point first."
            )
        else:
            return self._skill_point

    def score(self, mapname: str) -> Score:
        """Returns the player's score on the given map."""
        try:
            return self._levels[mapname]
        except KeyError:
            self._levels[mapname] = Score(
                "player",
                mapname,
                "score",
                "NORMAL",
                self._playerid,
                rank=0,
                score=0,
                total=0,
                top="-%",
            )
            return self._levels[mapname]

    async def fetch_daily_quest(
        self, session: Optional[Session] = None
    ) -> Optional[Score]:
        """
        Fetches the player's Daily Quest score if it wasn't fetched already.
        Returns None if the player is not ranked.
        """
        if self._daily_quest:
            return self._daily_quest

        if session is None:
            if self._daily_quest is None:
                return

            # daily_quest is MISSING
            raise InfinitodeError(
                "You need to provide a Session to fetch the daily quest score."
            )

        lb = await session.daily_quest_leaderboards(
            playerid=self._playerid, beta=self._beta
        )
        self._daily_quest = lb.player

        return self._daily_quest

    async def fetch_skill_point(
        self, session: Optional[Session] = None
    ) -> Optional[Score]:
        """
        Fetches the player's Skill Point score if it wasn't fetched already.
        Returns None if the player is not ranked.
        """
        if self._skill_point:
            return self._skill_point

        if session is None:
            if self._skill_point is None:
                return

            # skill_point is MISSING
            raise InfinitodeError(
                "You need to provide a Session to fetch the skill point score."
            )

        lb = await session.skill_point_leaderboard(
            playerid=self._playerid, beta=self._beta
        )
        self._skill_point = lb.player

        return self._skill_point

    # magic methods

    def __repr__(self) -> str:
        attrs: dict[str, Any] = {
            "playerid": self._playerid,
            "nickname": self._nickname,
            "total_rank": self._total_rank,
        }
        inner = " ".join(f"{k}={v}" for k, v in attrs.items())
        return f"<{self.__class__.__name__} {inner}>"
