"""Asynchronous client for the public stats HTML endpoints."""

import asyncio
import logging
import re
from urllib.parse import urlencode

import aiohttp

from ..errors import APIError, BadArgument, ParseError
from ._parsers.index import parse_index
from ._parsers.replay import parse_replay
from ._parsers.summary import parse_summary
from .models import AggregateReport, ReplayIndex, ReplayReport
from .query import ReplayQuery

LOG = logging.getLogger(__name__)
BASE_URL = "https://infinitode.prineside.com/stats/"


class StatsClient:
    """Owns sessions it creates; an injected session stays owned by its caller."""

    def __init__(self, session: aiohttp.ClientSession | None = None):
        self._owns_session = session is None
        self._session = session
        self._closed = False

    async def __aenter__(self) -> "StatsClient":
        if self._closed:
            raise APIError("StatsClient is closed")
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    async def close(self) -> None:
        if not self._closed:
            self._closed = True
            if self._owns_session and self._session is not None:
                await self._session.close()

    async def _get(
        self, endpoint: str, params: tuple[tuple[str, str], ...]
    ) -> tuple[str, str]:
        if self._closed:
            raise APIError("StatsClient is closed")
        if self._session is None:
            self._session = aiohttp.ClientSession()
        url = BASE_URL + endpoint
        source_url = url + ("?" + urlencode(params) if params else "")
        LOG.info("Sending stats GET request %s", source_url)
        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                html = await response.text()
        except (aiohttp.ClientError, asyncio.TimeoutError, UnicodeError) as exc:
            raise APIError(f"Unable to retrieve stats report: {source_url}") from exc
        LOG.debug("Stats response from %s: %s", source_url, html)
        return html, source_url

    @staticmethod
    def _query(query: ReplayQuery | None) -> ReplayQuery:
        if query is None:
            return ReplayQuery()
        if not isinstance(query, ReplayQuery):
            raise BadArgument("query must be a ReplayQuery")
        return query

    async def replays(self, query: ReplayQuery | None = None) -> ReplayIndex:
        """Retrieve ordered replay summaries and the site's filter catalog."""
        query = self._query(query)
        html, url = await self._get("index.php", query.to_params())
        return parse_index(html, url, query)

    async def replay(self, replay_id: str) -> ReplayReport:
        """Retrieve a replay, retaining readable data and reporting timeline issues."""
        if (
            not isinstance(replay_id, str)
            or re.fullmatch(r"R-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{6}", replay_id) is None
        ):
            raise BadArgument("Invalid replay identifier")
        html, url = await self._get("replay.php", (("replay", replay_id),))
        report = parse_replay(html, url)
        if report.info.replay_id != replay_id:
            raise ParseError("Server returned a different replay")
        return report

    async def summary(self, query: ReplayQuery | None = None) -> AggregateReport:
        """Retrieve the aggregate statistics for a replay selection."""
        query = self._query(query)
        html, url = await self._get("replays.php", query.to_params())
        return parse_summary(html, url, query)
