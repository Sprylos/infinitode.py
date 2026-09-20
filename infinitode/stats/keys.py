"""Stable, library-owned metric and issue identifiers (entities remain strings)."""

GENERAL_TOWERS_BUILT = "general.towers_built"
GENERAL_TOWERS_SOLD = "general.towers_sold"
GENERAL_RESOURCES_GAINED = "general.resources_gained"
GENERAL_ENEMIES_KILLED = "general.enemies_killed"
GENERAL_ENEMIES_PASSED = "general.enemies_passed"
GENERAL_WAVE_CALL_TIME_SAVED_SECONDS = "general.wave_call_time_saved_seconds"
GENERAL_ENEMIES_BUFFED = "general.enemies_buffed"
GENERAL_MAX_MINERS_BUILT_SIMULTANEOUSLY = "general.max_miners_built_simultaneously"
GENERAL_MAX_TOWERS_BUILT_SIMULTANEOUSLY = "general.max_towers_built_simultaneously"
ECONOMY_SPENT_ON_MINERS = "economy.spent_on_miners"
ECONOMY_SPENT_ON_TOWERS = "economy.spent_on_towers"
TOWER_COUNT = "tower.count"
TOWER_UPGRADE_LEVELS = "tower.upgrade_levels"
TOWER_XP_LEVELS = "tower.xp_levels"
TOWER_MDPS = "tower.mdps"
TOWER_KILLS = "tower.kills"
TOWER_DAMAGE = "tower.damage"
TOWER_MONEY_SPENT = "tower.money_spent"
TOWER_DAMAGE_PER_COIN = "tower.damage_per_coin"
TOWER_KILLS_PER_COIN = "tower.kills_per_coin"
TOWER_SALES = "tower.sales"
RESOURCE_GAINED = "resource.gained"
MINER_COUNT = "miner.count"
MINER_UPGRADE_LEVELS = "miner.upgrade_levels"
MINER_MONEY_SPENT = "miner.money_spent"
ENEMY_PASSED = "enemy.passed"
ENEMY_BUFFS = "enemy.buffs"
ENEMY_KILLS_BY_SOURCE = "enemy.kills_by_source"
MODIFIER_USAGE = "modifier.usage"
ABILITY_USAGE = "ability.usage"
SCORE_SOURCES = "score.sources"
COINS_SOURCES = "coins.sources"
EXPERIENCE_SOURCES = "experience.sources"
LOOT = "loot"
# A timeline key describes the measurement; its entity identifies the component.
SCORE_CUMULATIVE = "score.cumulative"
COINS_CUMULATIVE = "coins.cumulative"
COINS_RATE = "coins.rate"
EXPERIENCE_CUMULATIVE = "experience.cumulative"
EXPERIENCE_RATE = "experience.rate"
LOOT_CUMULATIVE = "loot.cumulative"
LOOT_RATE = "loot.rate"

UPSTREAM_DIAGNOSTIC = "upstream_diagnostic"
INVALID_NUMBER = "invalid_number"
INVALID_ELAPSED = "invalid_elapsed"
TIMELINE_LENGTH_MISMATCH = "timeline_length_mismatch"
MALFORMED_TIMELINE = "malformed_timeline"

SCALAR_KEYS = frozenset(
    (
        GENERAL_TOWERS_BUILT,
        GENERAL_TOWERS_SOLD,
        GENERAL_RESOURCES_GAINED,
        GENERAL_ENEMIES_KILLED,
        GENERAL_ENEMIES_PASSED,
        GENERAL_WAVE_CALL_TIME_SAVED_SECONDS,
        GENERAL_ENEMIES_BUFFED,
        GENERAL_MAX_MINERS_BUILT_SIMULTANEOUSLY,
        GENERAL_MAX_TOWERS_BUILT_SIMULTANEOUSLY,
        ECONOMY_SPENT_ON_MINERS,
        ECONOMY_SPENT_ON_TOWERS,
    )
)
METRIC_KEYS = frozenset(
    (
        TOWER_COUNT,
        TOWER_UPGRADE_LEVELS,
        TOWER_XP_LEVELS,
        TOWER_MDPS,
        TOWER_KILLS,
        TOWER_DAMAGE,
        TOWER_MONEY_SPENT,
        TOWER_DAMAGE_PER_COIN,
        TOWER_KILLS_PER_COIN,
        TOWER_SALES,
        RESOURCE_GAINED,
        MINER_COUNT,
        MINER_UPGRADE_LEVELS,
        MINER_MONEY_SPENT,
        ENEMY_PASSED,
        ENEMY_BUFFS,
        ENEMY_KILLS_BY_SOURCE,
        MODIFIER_USAGE,
        ABILITY_USAGE,
    )
)
BREAKDOWN_KEYS = frozenset((SCORE_SOURCES, COINS_SOURCES, EXPERIENCE_SOURCES, LOOT))
TIMELINE_KEYS = frozenset(
    (
        SCORE_CUMULATIVE,
        COINS_CUMULATIVE,
        COINS_RATE,
        EXPERIENCE_CUMULATIVE,
        EXPERIENCE_RATE,
        LOOT_CUMULATIVE,
        LOOT_RATE,
    )
)
