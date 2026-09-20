"""Canonical report records and cached access views."""

from dataclasses import dataclass
from datetime import timedelta
from functools import cached_property
from typing import TYPE_CHECKING

from .. import keys
from ..query import ReplayQuery, StatsFilterCatalog
from .common import (
    BreakdownSeries,
    MetricSeries,
    Number,
    ReportMetadata,
    ScalarMetric,
    TowerAbilities,
)

if TYPE_CHECKING:
    from ..views import EconomyView, EnemiesView, GeneralView, ResourcesView, TowersView


@dataclass(frozen=True)
class RunStatistics:
    scalars: tuple[ScalarMetric, ...] = ()
    metric_series: tuple[MetricSeries, ...] = ()
    breakdowns: tuple[BreakdownSeries, ...] = ()
    tower_abilities: tuple[TowerAbilities, ...] = ()

    def scalar(self, key: str) -> ScalarMetric | None:
        if key not in keys.SCALAR_KEYS:
            raise KeyError(key)
        return next((item for item in self.scalars if item.key == key), None)

    def get_metric_series(self, key: str) -> MetricSeries | None:
        if key not in keys.METRIC_KEYS:
            raise KeyError(key)
        return next((item for item in self.metric_series if item.key == key), None)

    def breakdown(self, key: str) -> BreakdownSeries | None:
        if key not in keys.BREAKDOWN_KEYS:
            raise KeyError(key)
        return next((item for item in self.breakdowns if item.key == key), None)

    @cached_property
    def general(self) -> "GeneralView":
        from ..views import GeneralView

        return GeneralView(self)

    @cached_property
    def economy(self) -> "EconomyView":
        from ..views import EconomyView

        return EconomyView(self)

    @cached_property
    def towers(self) -> "TowersView":
        from ..views import TowersView

        return TowersView(self)

    @cached_property
    def resources(self) -> "ResourcesView":
        from ..views import ResourcesView

        return ResourcesView(self)

    @cached_property
    def enemies(self) -> "EnemiesView":
        from ..views import EnemiesView

        return EnemiesView(self)

    @property
    def score_sources(self) -> BreakdownSeries | None:
        return self.breakdown(keys.SCORE_SOURCES)

    @property
    def coin_sources(self) -> BreakdownSeries | None:
        return self.breakdown(keys.COINS_SOURCES)

    @property
    def experience_sources(self) -> BreakdownSeries | None:
        return self.breakdown(keys.EXPERIENCE_SOURCES)

    @property
    def loot(self) -> BreakdownSeries | None:
        return self.breakdown(keys.LOOT)

    @property
    def abilities(self) -> MetricSeries | None:
        return self.get_metric_series(keys.ABILITY_USAGE)

    @property
    def modifiers(self) -> MetricSeries | None:
        return self.get_metric_series(keys.MODIFIER_USAGE)


@dataclass(frozen=True)
class ReportOverview:
    score_sources: BreakdownSeries
    coin_sources: BreakdownSeries
    tower_spending: MetricSeries
    modifiers: MetricSeries
    research_value: Number | None = None
    account_play_time: timedelta | None = None
    duration: timedelta | None = None


@dataclass(frozen=True)
class ReplaySummary:
    replay_id: str
    game_mode: str
    mapname: str
    score: int
    overview: ReportOverview


@dataclass(frozen=True)
class ReplayIndex:
    query: ReplayQuery
    available_filters: StatsFilterCatalog
    replays: tuple[ReplaySummary, ...]
    metadata: ReportMetadata


@dataclass(frozen=True)
class ReplayInfo:
    replay_id: str
    game_mode: str
    mapname: str
    waves: int
    score: int
    os: str | None
    game_build: int | None
    validation: str
    daily_quest: str | None
    xp: int | None


@dataclass(frozen=True)
class ReplayReport:
    info: ReplayInfo
    overview: ReportOverview
    statistics: RunStatistics
    metadata: ReportMetadata


@dataclass(frozen=True)
class ReportScope:
    query: ReplayQuery
    game_modes: tuple[str, ...]
    maps: tuple[str, ...]
    replay_count: int


@dataclass(frozen=True)
class AggregateReport:
    scope: ReportScope
    overview: ReportOverview
    statistics: RunStatistics
    metadata: ReportMetadata
