"""Handwritten, read-only views over canonical statistics."""

from dataclasses import dataclass
from datetime import timedelta

from . import keys
from .models.common import MetricSeries, Number, TowerAbilities
from .models.reports import RunStatistics

ScalarValue = Number | timedelta | str


@dataclass(frozen=True)
class StatisticsView:
    _statistics: RunStatistics

    def _scalar(self, key: str) -> Number | timedelta | str | None:
        metric = self._statistics.scalar(key)
        return metric.value if metric is not None else None

    def _series(self, key: str) -> MetricSeries | None:
        return self._statistics.get_metric_series(key)


class GeneralView(StatisticsView):
    @property
    def towers_built(self) -> ScalarValue | None:
        return self._scalar(keys.GENERAL_TOWERS_BUILT)

    @property
    def towers_sold(self) -> ScalarValue | None:
        return self._scalar(keys.GENERAL_TOWERS_SOLD)

    @property
    def resources_gained(self) -> ScalarValue | None:
        return self._scalar(keys.GENERAL_RESOURCES_GAINED)

    @property
    def enemies_killed(self) -> ScalarValue | None:
        return self._scalar(keys.GENERAL_ENEMIES_KILLED)

    @property
    def enemies_passed(self) -> ScalarValue | None:
        return self._scalar(keys.GENERAL_ENEMIES_PASSED)

    @property
    def wave_call_time_saved_seconds(self) -> ScalarValue | None:
        return self._scalar(keys.GENERAL_WAVE_CALL_TIME_SAVED_SECONDS)

    @property
    def enemies_buffed(self) -> ScalarValue | None:
        return self._scalar(keys.GENERAL_ENEMIES_BUFFED)

    @property
    def max_miners_built_simultaneously(self) -> ScalarValue | None:
        return self._scalar(keys.GENERAL_MAX_MINERS_BUILT_SIMULTANEOUSLY)

    @property
    def max_towers_built_simultaneously(self) -> ScalarValue | None:
        return self._scalar(keys.GENERAL_MAX_TOWERS_BUILT_SIMULTANEOUSLY)


class EconomyView(StatisticsView):
    @property
    def spent_on_miners(self) -> ScalarValue | None:
        return self._scalar(keys.ECONOMY_SPENT_ON_MINERS)

    @property
    def spent_on_towers(self) -> ScalarValue | None:
        return self._scalar(keys.ECONOMY_SPENT_ON_TOWERS)


class TowersView(StatisticsView):
    @property
    def count(self) -> MetricSeries | None:
        return self._series(keys.TOWER_COUNT)

    @property
    def upgrade_levels(self) -> MetricSeries | None:
        return self._series(keys.TOWER_UPGRADE_LEVELS)

    @property
    def xp_levels(self) -> MetricSeries | None:
        return self._series(keys.TOWER_XP_LEVELS)

    @property
    def mdps(self) -> MetricSeries | None:
        return self._series(keys.TOWER_MDPS)

    @property
    def kills(self) -> MetricSeries | None:
        return self._series(keys.TOWER_KILLS)

    @property
    def damage(self) -> MetricSeries | None:
        return self._series(keys.TOWER_DAMAGE)

    @property
    def money_spent(self) -> MetricSeries | None:
        return self._series(keys.TOWER_MONEY_SPENT)

    @property
    def damage_per_coin(self) -> MetricSeries | None:
        return self._series(keys.TOWER_DAMAGE_PER_COIN)

    @property
    def kills_per_coin(self) -> MetricSeries | None:
        return self._series(keys.TOWER_KILLS_PER_COIN)

    @property
    def sales(self) -> MetricSeries | None:
        return self._series(keys.TOWER_SALES)

    @property
    def abilities(self) -> tuple[TowerAbilities, ...]:
        return self._statistics.tower_abilities

    def tower(self, key: str) -> "TowerView":
        return TowerView(self._statistics, key)


@dataclass(frozen=True)
class EntityView(StatisticsView):
    key: str

    def _value(self, key: str) -> Number | None:
        series = self._series(key)
        if series is None:
            return None
        return next((e.value for e in series.entries if e.entity.key == self.key), None)


class TowerView(EntityView):
    @property
    def count(self) -> Number | None:
        return self._value(keys.TOWER_COUNT)

    @property
    def upgrade_levels(self) -> Number | None:
        return self._value(keys.TOWER_UPGRADE_LEVELS)

    @property
    def xp_levels(self) -> Number | None:
        return self._value(keys.TOWER_XP_LEVELS)

    @property
    def mdps(self) -> Number | None:
        return self._value(keys.TOWER_MDPS)

    @property
    def kills(self) -> Number | None:
        return self._value(keys.TOWER_KILLS)

    @property
    def damage(self) -> Number | None:
        return self._value(keys.TOWER_DAMAGE)

    @property
    def money_spent(self) -> Number | None:
        return self._value(keys.TOWER_MONEY_SPENT)

    @property
    def damage_per_coin(self) -> Number | None:
        return self._value(keys.TOWER_DAMAGE_PER_COIN)

    @property
    def kills_per_coin(self) -> Number | None:
        return self._value(keys.TOWER_KILLS_PER_COIN)

    @property
    def sales(self) -> Number | None:
        return self._value(keys.TOWER_SALES)

    @property
    def abilities(self) -> TowerAbilities | None:
        return next(
            (a for a in self._statistics.tower_abilities if a.tower.key == self.key),
            None,
        )


class ResourcesView(StatisticsView):
    @property
    def gained(self) -> MetricSeries | None:
        return self._series(keys.RESOURCE_GAINED)

    @property
    def miners_built(self) -> MetricSeries | None:
        return self._series(keys.MINER_COUNT)

    @property
    def upgrade_levels(self) -> MetricSeries | None:
        return self._series(keys.MINER_UPGRADE_LEVELS)

    @property
    def money_spent(self) -> MetricSeries | None:
        return self._series(keys.MINER_MONEY_SPENT)

    def resource(self, key: str) -> "ResourceView":
        return ResourceView(self._statistics, key)


class ResourceView(EntityView):
    @property
    def gained(self) -> Number | None:
        return self._value(keys.RESOURCE_GAINED)

    @property
    def miners_built(self) -> Number | None:
        return self._value(keys.MINER_COUNT)

    @property
    def upgrade_levels(self) -> Number | None:
        return self._value(keys.MINER_UPGRADE_LEVELS)

    @property
    def money_spent(self) -> Number | None:
        return self._value(keys.MINER_MONEY_SPENT)


class EnemiesView(StatisticsView):
    @property
    def passed(self) -> MetricSeries | None:
        return self._series(keys.ENEMY_PASSED)

    @property
    def buffs(self) -> MetricSeries | None:
        return self._series(keys.ENEMY_BUFFS)

    @property
    def kills_by_source(self) -> MetricSeries | None:
        return self._series(keys.ENEMY_KILLS_BY_SOURCE)
