"""Replay browser and authoritative filter catalog."""

from dataclasses import replace
from urllib.parse import parse_qs, urlsplit

from ...errors import ParseError
from ..models import ReplayIndex, ReplaySummary
from ..query import ReplayQuery, StatsFilterCatalog
from .common import Page, integer, parse_overview


def parse_index(html: str, source_url: str, query: ReplayQuery) -> ReplayIndex:
    page = Page(html, source_url)
    form = page.soup.select_one("form")
    count_input = form.select_one('input[name="count"]') if form is not None else None
    if form is None or count_input is None:
        raise ParseError("Response is not a replay browser")
    for field in form.select("input[name]"):
        if field.get("name") not in {
            "count",
            "random",
            "modes[]",
            "maps[]",
            "builds[]",
        }:
            raise ParseError("Unrecognized stats filter; parser update required")
    count = integer(str(count_input.get("value", "")))
    if query.report_count is None:
        query = replace(query, report_count=count)
    catalog = {}
    for name in ("modes[]", "maps[]", "builds[]"):
        values = tuple(
            str(tag.get("value", ""))
            for tag in form.find_all("input", attrs={"name": name})
        )
        catalog[name] = values
    filters = StatsFilterCatalog(
        catalog["modes[]"],
        catalog["maps[]"],
        tuple(integer(v) for v in catalog["builds[]"]),
    )
    replays = []
    for link in page.soup.find_all("a", href=True):
        url = urlsplit(str(link["href"]))
        if url.path != "replay.php":
            continue
        ids = parse_qs(url.query).get("replay", [])
        fields = link.get_text(" ", strip=True).split(" / ")
        row = link.find_parent("tr")
        if len(ids) != 1 or len(fields) != 3 or row is None:
            raise ParseError("Malformed replay browser entry")
        overview = parse_overview(page, row.select_one("table.report-summary"))
        replays.append(
            ReplaySummary(ids[0], fields[2], fields[0], integer(fields[1]), overview)
        )
    return ReplayIndex(query, filters, tuple(replays), page.metadata())
