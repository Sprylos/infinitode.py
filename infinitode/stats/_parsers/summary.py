"""Aggregate report adapter."""

import re

from ...errors import ParseError
from ..models import AggregateReport, ReportScope
from ..query import ReplayQuery
from .common import Page, info_fields, integer, parse_overview
from .statistics import parse_statistics


def parse_summary(html: str, source_url: str, query: ReplayQuery) -> AggregateReport:
    page = Page(html, source_url)
    if page.heading("Replays info") is None:
        raise ParseError("Response is not an aggregate report")
    fields = info_fields(page, {"Game modes", "Maps", "Count"})
    if not {"Game modes", "Maps", "Count"} <= fields.keys():
        raise ParseError("Missing aggregate scope")
    match = re.fullmatch(r"(?:Top|Random) ([\d,]+) replays", fields["Count"])
    if match is None:
        raise ParseError("Unrecognized aggregate replay count")
    scope = ReportScope(
        query,
        tuple(v.strip() for v in fields["Game modes"].split(",") if v.strip()),
        tuple(v.strip() for v in fields["Maps"].split(",") if v.strip()),
        integer(match[1]),
    )
    overview = parse_overview(page, page.soup.select_one("table.report-summary"))
    statistics = parse_statistics(page)
    return AggregateReport(scope, overview, statistics, page.metadata())
