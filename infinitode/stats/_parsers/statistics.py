"""Detailed statistics shared by individual and aggregate reports."""

import re
from dataclasses import replace

from ...errors import ParseError
from ..models import (
    AbilityEntry,
    MetricEntry,
    MetricSeries,
    RunStatistics,
    ScalarMetric,
    TowerAbilities,
)
from .common import (
    BREAKDOWNS,
    ECONOMY,
    GENERAL,
    METRICS,
    Page,
    asset,
    entity,
    integer,
    labeled_value,
    number,
    parse_breakdown,
)
from .timelines import parse_timelines


def parse_statistics(page: Page) -> RunStatistics:
    scalars, metrics, breakdowns, abilities = [], [], [], []
    for heading in page.soup.find_all("h2"):
        title = heading.get_text(strip=True)
        if title in BREAKDOWNS:
            key = BREAKDOWNS[title]
            breakdown = parse_breakdown(page, heading.parent, key)
            breakdowns.append(
                replace(
                    breakdown,
                    timelines=parse_timelines(page, heading.parent, key),
                )
            )
        elif title not in {
            "Replay info",
            "Replays info",
            "Top towers",
            "Abilities by tower",
            "Statistics",
            *METRICS,
        }:
            raise ParseError(f"Unrecognized statistical section: {title}")
    abilities_heading = page.heading("Abilities by tower")
    abilities_parent = (
        abilities_heading.parent if abilities_heading is not None else None
    )
    ability_headings = (
        abilities_parent.find_all("h3") if abilities_parent is not None else []
    )
    for heading in ability_headings:
        entries = []
        for bar in page.bars(heading.parent):
            label, value = labeled_value(bar)
            match = re.fullmatch(r"(.+?)(?: \(L(\d+)\))?(?: \((\d+)\))?", label)
            if match is None:
                raise ParseError("Malformed tower ability")
            image = bar.select_one("img")
            entries.append(
                AbilityEntry(
                    match[1],
                    asset(image) if image else None,
                    int(match[3]) if match[3] else None,
                    int(match[2]) if match[2] else None,
                    integer(value),
                )
            )
        abilities.append(
            TowerAbilities(entity(heading.get_text(strip=True)), tuple(entries))
        )
    for heading in page.soup.find_all(["h2", "h3"]):
        if heading in ability_headings:
            continue
        title = heading.get_text(strip=True)
        if title in METRICS:
            metric_entries = []
            for bar in page.bars(heading.parent):
                label, value = labeled_value(bar)
                image = bar.select_one("img")
                metric_entries.append(
                    MetricEntry(
                        entity(label, asset(image) if image else None), number(value)
                    )
                )
            metrics.append(MetricSeries(METRICS[title], tuple(metric_entries)))
        elif title in ("General", "Money spent"):
            for bar in page.bars(heading.parent):
                if title == "General":
                    label_tag = bar.select_one(".horizontal-bar")
                    value_tag = bar.find("span", recursive=False)
                    if label_tag is None or value_tag is None:
                        raise ParseError("Malformed general statistic")
                    label = label_tag.get_text(strip=True)
                    value = value_tag.get_text(strip=True)
                    mapping = GENERAL
                else:
                    label, value = labeled_value(bar)
                    mapping = ECONOMY
                if label not in mapping:
                    raise ParseError(f"Unrecognized scalar metric: {label}")
                scalars.append(ScalarMetric(mapping[label], number(value)))
        elif heading.name == "h3":
            raise ParseError(f"Unrecognized statistical metric: {title}")
    page.audit_bars()
    for collection in (scalars, metrics, breakdowns):
        if len({item.key for item in collection}) != len(collection):
            raise ParseError("Duplicate canonical metric in report")
    return RunStatistics(
        tuple(scalars), tuple(metrics), tuple(breakdowns), tuple(abilities)
    )
