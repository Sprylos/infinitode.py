from __future__ import annotations

# std
from typing import (
    Any,
    Dict,
    List,
    Optional,
    overload,
    Union
)

# local
from .score import Score


__all__ = ('Leaderboard',)


class Leaderboard_iterator:
    """Iterator class for a Leaderboard."""
    __slots__ = (
        '_scores',
        '_index'
    )

    def __init__(self, scores: List[Score]) -> None:
        self._scores = scores
        self._index: int = 0

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} scores={len(self._scores)}>'

    def __next__(self) -> Score:
        try:
            score: Score = self._scores[self._index]
        except IndexError:
            raise StopIteration
        self._index += 1
        return score


class Leaderboard:
    """Represents an in-game leaderboard."""
    __slots__ = (
        '_method',
        '_mapname',
        '_mode',
        '_difficulty',
        '_total',
        'raw',
        '_date',
        '_season',
        '_player',

        '_scores',
    )

    def __init__(
        self,
        method: str,
        mapname: str,
        mode: str,
        difficulty: str,
        total: Union[int, str],
        *,
        raw: Dict[str, Any],
        date: Optional[str] = None,
        player: Optional[Score] = None,
        season: Optional[int] = None
    ) -> None:
        self._method = method
        self._mapname = mapname
        self._mode = mode
        self._difficulty = difficulty
        self._total = int(total)
        self.raw = raw
        self._date = date
        self._season = int(season) if season is not None else None
        self._player = player
        self._scores: List[Score] = []

    @classmethod
    def from_payload(
        cls,
        method: str,
        mapname: str,
        mode: str,
        difficulty: str,
        playerid: Optional[str],
        payload: Dict[str, Any],
        *,
        date: Optional[str] = None,
        season: Optional[int] = None
    ) -> Leaderboard:
        '''Builds an instance with the given payload.'''
        player: Dict[str, Any] = payload['player']
        total: int = player['total']
        if playerid is not None and (player['score'] and player['rank'] and total):
            player_score = Score(method, mapname, mode,
                                 difficulty, playerid, **player)
        else:
            player_score = None
        instance = cls(method, mapname, mode, difficulty, total,
                       raw=payload, date=date, player=player_score, season=season)
        for rank, score in enumerate(payload['leaderboards'], start=1):
            instance._append(Score(method, mapname, mode,
                             difficulty, rank=rank, **score))
        return instance

    @property
    def method(self) -> str:
        """The name of the method responsible for creating this leaderboard."""
        return self._method

    @property
    def mapname(self) -> str:
        """The name of the map this leaderboard is from."""
        return self._mapname

    @property
    def mode(self) -> str:
        """The mode of the leaderboard (score/waves)."""
        return self._mode

    @property
    def difficulty(self) -> str:
        """The difficulty of the leaderboard (EASY/NORMAL/ENDLESS_I)"""
        return self._difficulty

    @property
    def total(self) -> int:
        """The total amount of players on this map."""
        return self._total

    @property
    def date(self) -> Optional[str]:
        """The date this leaderboard is from. Only exists when the method is daily_quest_leaderboards."""
        return self._date

    @property
    def season(self) -> Optional[int]:
        """The current season which this leaderboard is from. Only exists when the method is seasonal_leaderboard."""
        return self._season

    @property
    def player(self) -> Optional[Score]:
        """The score of the player. Only exists when a valid playerid was specified."""
        return self._player

    @property
    def is_empty(self) -> bool:
        """Whether there are no scores saved in this leaderboard or there are."""
        return not self._scores

    def format_scores(self) -> str:
        """Default format used in my Advinas Bot. To format the scores yourself, iterate over this object."""
        return '\n'.join([i.format_score() for i in self._scores])

    def print_scores(self) -> None:
        """Prints out the result of format_scores()."""
        print(self.format_scores())

    def get_score(self, attr: str, val: Any) -> Optional[Score]:
        """Returns the score in the leaderboard where the given attribute equals the given value."""
        return next((x for x in self._scores if getattr(x, attr, None) == val), None)

    def _append(self, score: Score) -> None:
        '''Internal append method.'''
        self._scores.append(score)

    # magic methods

    def __repr__(self) -> str:
        attrs = {
            'method': self._method,
            'mapname': self._mapname,
            'mode': self._mode,
            'difficulty': self._difficulty,
            'total': self._total,
            'scores': len(self._scores),
            # Fine to include these 3, when they are not None.
            'date': self._date,
            'season': self._season,
            'player': True if self._player is not None else None
        }
        inner = ' '.join(f'{k}={v}' for k, v in attrs.items() if v is not None)
        return f'<{self.__class__.__name__} {inner}>'

    def __len__(self) -> int:
        return len(self._scores)

    def __contains__(self, item: Any) -> bool:
        return item in self._scores

    @overload
    def __getitem__(self, key: int) -> Score:
        ...

    @overload
    def __getitem__(self, key: slice) -> Leaderboard:
        ...

    def __getitem__(self, key: Any) -> Union[Score, Leaderboard]:
        if isinstance(key, int):
            return self._scores[key]
        elif isinstance(key, slice):
            lb = Leaderboard(
                self._method, self._mapname, self._mode, self._difficulty, self._total,
                raw=self.raw, date=self._date, player=self._player, season=self._season
            )
            lb._scores = self._scores[key]
            return lb
        else:
            raise KeyError('Only int and slice indexes are allowed.')

    def __iter__(self) -> Leaderboard_iterator:
        return Leaderboard_iterator(self._scores)
