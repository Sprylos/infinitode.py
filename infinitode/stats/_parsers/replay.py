"""Individual replay report adapter."""

from ...errors import ParseError
from ..models import ReplayInfo, ReplayReport
from .common import Page, info_fields, integer, parse_overview
from .statistics import parse_statistics


def parse_replay(html: str, source_url: str) -> ReplayReport:
    page = Page(html, source_url)
    if page.heading("Replay info") is None:
        raise ParseError("Response is not a replay report")
    fields = info_fields(
        page,
        {
            "ID",
            "Game mode",
            "Map name",
            "Waves",
            "Score",
            "OS",
            "Game build",
            "Validation",
            "DQ",
            "XP",
        },
    )
    if (
        not {"ID", "Game mode", "Map name", "Waves", "Score", "Validation"}
        <= fields.keys()
    ):
        raise ParseError("Missing essential replay information")
    if not fields["ID"]:
        raise ParseError("Missing replay identifier")
    info = ReplayInfo(
        fields["ID"],
        fields["Game mode"],
        fields["Map name"],
        integer(fields["Waves"]),
        integer(fields["Score"]),
        fields.get("OS") or None,
        integer(fields["Game build"]) if fields.get("Game build") else None,
        fields["Validation"],
        fields.get("DQ") or None,
        integer(fields["XP"]) if fields.get("XP") else None,
    )
    overview = parse_overview(page, page.soup.select_one("table.report-summary"))
    statistics = parse_statistics(page)
    return ReplayReport(info, overview, statistics, page.metadata())
