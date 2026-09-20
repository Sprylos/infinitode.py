"""Read numeric elapsed-time series without evaluating upstream JavaScript."""

import re
from datetime import timedelta

from bs4 import Tag

from ...errors import ParseError
from .. import keys
from ..models import ReportIssue, TimePoint, TimeSeries
from .common import Page, elapsed, entity, number

TIMELINE_KEYS = {
    keys.SCORE_SOURCES: (keys.SCORE_CUMULATIVE, None),
    keys.COINS_SOURCES: (keys.COINS_CUMULATIVE, keys.COINS_RATE),
    keys.EXPERIENCE_SOURCES: (keys.EXPERIENCE_CUMULATIVE, keys.EXPERIENCE_RATE),
    keys.LOOT: (keys.LOOT_CUMULATIVE, keys.LOOT_RATE),
}


def tokens(array: str) -> list[str]:
    if not array.strip():
        return []
    result = array.split(",")
    # JS permits one trailing comma. Interior holes retain their sample indexes.
    if not result[-1].strip():
        result.pop()
    return [value.strip() for value in result]


def parse_timelines(
    page: Page, container: Tag, section: str
) -> tuple[TimeSeries, ...] | None:
    scripts = container.find_all("script")
    if not scripts:
        return None
    result = []
    for script in scripts:
        source = script.get_text()
        if "series" not in source:
            page.issues.append(
                ReportIssue(keys.MALFORMED_TIMELINE, section, "Missing timeline series")
            )
            continue
        # Preserve explicitly commented data series (e.g. Green papers), while
        # discarding the comment prefix, not executing or interpreting JS code.
        source = re.sub(r"(?m)^\s*//\s?", "", source)
        series_block = re.search(
            r"\bseries\s*:\s*\[(.*?)\]\s*,\s*chart\s*:", source, re.S
        )
        if series_block is None:
            page.issues.append(
                ReportIssue(
                    keys.MALFORMED_TIMELINE, section, "Cannot delimit timeline series"
                )
            )
            continue
        categories = re.search(r"\bcategories\s*:\s*\[([^\]]*)\]", source, re.S)
        coordinates = tokens(categories[1]) if categories else []
        if categories is None:
            page.issues.append(
                ReportIssue(
                    keys.MALFORMED_TIMELINE, section, "Missing elapsed-time coordinates"
                )
            )
        times: list[timedelta | None] = []
        for index, coordinate in enumerate(coordinates):
            try:
                times.append(elapsed(coordinate.strip("\"'")))
            except ParseError:
                times.append(None)
                page.issues.append(
                    ReportIssue(
                        keys.INVALID_ELAPSED,
                        section,
                        "Invalid elapsed-time coordinate",
                        sample_index=index,
                    )
                )
        # Bound each component by the next name, so a damaged component cannot
        # swallow a later component's array and silently change its identity.
        names = list(re.finditer(r"\bname\s*:\s*(['\"])(.*?)\1", series_block[1], re.S))
        if not names and series_block[1].strip():
            page.issues.append(
                ReportIssue(
                    keys.MALFORMED_TIMELINE, section, "Missing timeline component names"
                )
            )
        for position, match in enumerate(names):
            label = match[2]
            cumulative_key, rate_key = TIMELINE_KEYS[section]
            key = rate_key if label.endswith(" (rate)") else cumulative_key
            if key is None:
                raise ParseError(f"Unrecognized rate measurement in {section}")
            item = entity(label.removesuffix(" (rate)"))
            stop = (
                names[position + 1].start()
                if position + 1 < len(names)
                else len(series_block[1])
            )
            component = series_block[1][match.end() : stop]
            data = re.search(r"\bdata\s*:\s*\[([^\]]*)\]", component, re.S)
            if data is None:
                page.issues.append(
                    ReportIssue(
                        keys.MALFORMED_TIMELINE,
                        section,
                        "Missing or malformed component array",
                        key,
                        item.key,
                    )
                )
                result.append(TimeSeries(key, item, ()))
                continue
            values = tokens(data[1])
            if len(values) != len(times):
                page.issues.append(
                    ReportIssue(
                        keys.TIMELINE_LENGTH_MISMATCH,
                        section,
                        f"{len(values)} values for {len(times)} elapsed coordinates",
                        key,
                        item.key,
                    )
                )
            points = []
            for index, token in enumerate(values):
                try:
                    value = number(token)
                except ParseError:
                    page.issues.append(
                        ReportIssue(
                            keys.INVALID_NUMBER,
                            section,
                            "Invalid timeline sample",
                            key,
                            item.key,
                            index,
                        )
                    )
                    continue
                timestamp = times[index] if index < len(times) else None
                if timestamp is not None:
                    points.append(TimePoint(timestamp, value))
            result.append(TimeSeries(key, item, tuple(points)))
    return tuple(result)
