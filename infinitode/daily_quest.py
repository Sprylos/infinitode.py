from __future__ import annotations

# std
from dataclasses import dataclass


__all__ = ("DailyQuestInfo",)


@dataclass(frozen=True)
class DailyQuestInfo:
    """Metadata for the currently active Daily Quest."""

    date: str
    quest_id: int
    end_timestamp: int
    data_hash: str

    @property
    def mapname(self) -> str:
        """The map name used by leaderboard APIs for this Daily Quest."""
        return f"DQ{self.quest_id}"

    @property
    def reset_timestamp(self) -> int:
        """The Unix timestamp at which the Daily Quest resets."""
        return self.end_timestamp
