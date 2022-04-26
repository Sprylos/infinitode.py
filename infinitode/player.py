from __future__ import annotations

# std
from typing import (
    Dict,
    Optional,
    Union,
    Tuple,
    TYPE_CHECKING
)

# local
from .score import Score
from .errors import MissingSession

if TYPE_CHECKING:
    from .core import Session


__all__ = ('Player',)


class Player:
    """Represents an in-game Player."""
    __slots__ = (
        '_playerid',
        '_nickname',
        '_levels',
        '_level',
        '_xp',
        '_xp_max',
        '_badges',
        '_total_score',
        '_total_rank',
        '_total_top',
        '_replays',
        '_issues',
        '_created_at',

        '__daily_quest',
        '__skill_point'
    )

    def __init__(
        self,
        playerid: str,
        nickname: str,
        *,
        levels: Dict[str, Score],
        level: int,
        xp: int,
        xp_max: int,
        badges: Dict[str, Tuple[str, str]],
        total_score: Union[int, str],
        total_rank: Union[int, str],
        total_top: str,
        replays: int,
        issues: int,
        created_at: str,
    ) -> None:
        self._playerid = playerid
        self._nickname = nickname
        self._levels = levels
        self._level = level
        self._xp = xp
        self._xp_max = xp_max
        self._badges = badges
        self._total_score = int(total_score)
        self._total_rank = int(total_rank)
        self._total_top = total_top
        self._replays = replays
        self._issues = issues
        self._created_at = created_at
        self.__daily_quest: Optional[Score] = None
        self.__skill_point: Optional[Score] = None

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
        return f'https://infinitode.prineside.com/img/avatars/{self._playerid}-128.png'

    def score(self, mapname: str) -> Score:
        """Returns the player's score on the given map."""
        try:
            return self._levels[mapname]
        except KeyError:
            self._levels[mapname] = Score(
                'player', mapname, 'score', 'NORMAL', self._playerid,
                rank=0, score=0, total=0, top='-%')
            return self._levels[mapname]

    async def daily_quest(self, session: Optional[Session] = None) -> Score:
        """Returns the player's current DQ score, and fetches it first if it wasn't already."""
        if self.__daily_quest is None:
            if session is None:
                raise MissingSession(
                    'You need to provide a Session to fetch the daily quest score.')
            self.__daily_quest = (await session.daily_quest_leaderboards(playerid=self._playerid)).player
            assert self.__daily_quest is not None
        return self.__daily_quest

    async def skill_point(self, session: Optional[Session] = None) -> Score:
        """Returns the player's current SP score, and fetches it first if it wasn't already."""
        if self.__skill_point is None:
            if session is None:
                raise MissingSession(
                    'You need to provide a Session to fetch the skill point score.')
            self.__skill_point = (await session.skill_point_leaderboard(playerid=self._playerid)).player
            assert self.__skill_point is not None
        return self.__skill_point

    # magic methods

    def __repr__(self) -> str:
        attrs = {
            'playerid': self._playerid,
            'nickname': self._nickname,
            'total_rank': self._total_rank,
        }
        inner = ' '.join(f'{k}={v}' for k, v in attrs.items())
        return f'<{self.__class__.__name__} {inner}>'
