from __future__ import annotations

# std
from dataclasses import dataclass
from enum import Enum

# local
from .badge import Badge


__all__ = (
    "PlayerSort",
    "PlayerSortOrder",
    "PlayerSearchEntry",
    "PlayerSearchResult",
)


class PlayerSort(str, Enum):
    """Values supported by the player browser's ``sortType`` parameter."""

    NICKNAME = "nickname"
    PROFILE_XP = "xp"
    SIGN_UP_DATE = "sign_up_date"
    BADGE_SKILLFUL = "profile_badge_skillful"
    BADGE_DAILY_GAME = "profile_badge_daily-game"
    BADGE_KILLED_ENEMIES = "profile_badge_killed-enemies"
    BADGE_SEASON_LEVEL_2 = "profile_badge_season-level-2"
    BADGE_SEASON_LEVEL_3 = "profile_badge_season-level-3"
    BADGE_YOUTUBE_AUTHOR = "profile_badge_youtube-author"
    BADGE_INVITED_PLAYERS = "profile_badge_invited-players"
    BADGE_MINED_RESOURCES = "profile_badge_mined-resources"
    BADGE_SEASON_1 = "profile_badge_season-1"
    BADGE_SEASON_2 = "profile_badge_season-2"
    BADGE_BETA_TESTER_SEASON_2 = "profile_badge_beta-tester-season-2"
    BADGE_BETA_TESTER_SEASON_3 = "profile_badge_beta-tester-season-3"
    BADGE_OF_MERIT = "profile_badge_of-merit"
    BADGE_HIGH_LEVELED = "profile_badge_high-leveled"


class PlayerSortOrder(str, Enum):
    """Values supported by the player browser's ``sortOrder`` parameter."""

    ASC = "ASC"
    DESC = "DESC"


@dataclass(frozen=True)
class PlayerSearchEntry:
    """A player row returned by :meth:`Session.search_players`."""

    playerid: str
    nickname: str
    level: int
    has_avatar: bool
    pinned_badge: Badge | None
    pinned_badge_level: str | None
    sort_value: str | None


@dataclass(frozen=True)
class PlayerSearchResult:
    """A page of player browser results and its search metadata."""

    players: tuple[PlayerSearchEntry, ...]
    total: int
    sort_type: PlayerSort
    sort_order: PlayerSortOrder
    nickname: str | None
