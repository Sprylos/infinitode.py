"""Immutable semantic storage; no HTML or chart configuration is retained."""

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal


@dataclass(frozen=True)
class DisplayValue:
    value: int | Decimal
    display: str


Number = int | Decimal | DisplayValue


@dataclass(frozen=True)
class Entity:
    key: str
    label: str | None = None
    asset_name: str | None = None


@dataclass(frozen=True)
class MetricEntry:
    entity: Entity
    value: Number


@dataclass(frozen=True)
class BreakdownEntry:
    entity: Entity
    value: Number | None
    share: Decimal | None = None
    display_share: Decimal | None = None


@dataclass(frozen=True)
class TimePoint:
    elapsed: timedelta
    value: Number


@dataclass(frozen=True)
class TimeSeries:
    """Ordered observations, with source rates preserved in their supplied units."""

    key: str
    entity: Entity
    points: tuple[TimePoint, ...]


@dataclass(frozen=True)
class MetricSeries:
    key: str
    entries: tuple[MetricEntry, ...]


@dataclass(frozen=True)
class BreakdownSeries:
    key: str
    total: Number | None
    entries: tuple[BreakdownEntry, ...]
    timelines: tuple[TimeSeries, ...] | None = None


@dataclass(frozen=True)
class ScalarMetric:
    key: str
    value: Number | timedelta | str


@dataclass(frozen=True)
class AbilityEntry:
    name: str
    asset_name: str | None
    slot: int | None
    required_level: int | None
    count: int


@dataclass(frozen=True)
class TowerAbilities:
    tower: Entity
    abilities: tuple[AbilityEntry, ...]


@dataclass(frozen=True)
class ReportIssue:
    """A recoverable source problem; sample indexes are zero-based."""

    code: str
    section: str
    message: str
    series_key: str | None = None
    entity_key: str | None = None
    sample_index: int | None = None


@dataclass(frozen=True)
class ReportMetadata:
    source_url: str
    generation_seconds: Decimal | None = None
    issues: tuple[ReportIssue, ...] = ()
