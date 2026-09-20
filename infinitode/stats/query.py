"""Stats-site query parameters, independent of the JSON API's catalogs."""

from dataclasses import dataclass

from ..errors import BadArgument


@dataclass(frozen=True)
class ReplayQuery:
    report_count: int | None = None
    random: bool = False
    game_modes: tuple[str, ...] = ()
    maps: tuple[str, ...] = ()
    builds: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if self.report_count is not None and (
            type(self.report_count) is not int or self.report_count <= 0
        ):
            raise BadArgument("report_count must be a positive integer or None")
        if type(self.random) is not bool:
            raise BadArgument("random must be a boolean")
        for name, kind in (("game_modes", str), ("maps", str), ("builds", int)):
            values = getattr(self, name)
            if not isinstance(values, tuple) or any(
                type(v) is not kind for v in values
            ):
                raise BadArgument(f"{name} must be a tuple of {kind.__name__} values")

    def to_params(self) -> tuple[tuple[str, str], ...]:
        """Serialize PHP array parameters without collapsing repeated keys."""
        params = []
        if self.report_count is not None:
            params.append(("count", str(self.report_count)))
        if self.random:
            params.append(("random", "true"))
        for name, values in (
            ("modes[]", self.game_modes),
            ("maps[]", self.maps),
            ("builds[]", self.builds),
        ):
            params.extend((name, str(value)) for value in values)
        return tuple(params)


@dataclass(frozen=True)
class StatsFilterCatalog:
    game_modes: tuple[str, ...]
    maps: tuple[str, ...]
    builds: tuple[int, ...]
