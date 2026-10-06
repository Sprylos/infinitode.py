from __future__ import annotations

# std
import re
import asyncio
import logging
import datetime
from typing import (
    Any,
    Dict,
    Optional,
    Union,
)

# packages
import aiohttp
from bs4 import BeautifulSoup, Comment

# local
from .badge import Badge
from .daily_quest import DailyQuestInfo
from .errors import APIError, BadArgument, ParseError, PlayerNotFound
from .leaderboard import Leaderboard
from .player import Player
from .player_search import (
    PlayerSearchEntry,
    PlayerSearchResult,
    PlayerSort,
    PlayerSortOrder,
)
from .score import Score
from .utils import async_expiring_cache, try_int


__all__ = (
    "Session",
    "GAME_API_VERSION",
    "SUPPORTED_MAPS",
    "SUPPORTED_MODES",
    "SUPPORTED_DIFFICULTIES",
)

LOG = logging.getLogger(__name__)

ID_REGEX = re.compile(r"U-([A-Z0-9]{4}-){2}[A-Z0-9]{6}")
GAME_API_VERSION = 282

# fmt: off
SUPPORTED_MAPS = (
    '0.1', '0.2', '0.3', '0.4',
    '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7', '1.8', '1.b1',
    '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7', '2.8', '2.b1',
    '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7', '3.8', '3.b1',
    '4.1', '4.2', '4.3', '4.4', '4.5', '4.6', '4.7', '4.8', '4.b1',
    '5.1', '5.2', '5.3', '5.4', '5.5', '5.6', '5.7', '5.8', '5.b1', '5.b2',
    '6.1', '6.2', '6.3', '6.4', '6.5', '6.6', 'rumble', 'dev', 'zecred',
    'DQ1', 'DQ3', 'DQ4', 'DQ5', 'DQ7', 'DQ8', 'DQ9', 'DQ10', 'DQ11', 'DQ12',
)
SUPPORTED_MODES = ('score', 'waves')
SUPPORTED_DIFFICULTIES = ('EASY', 'NORMAL', 'ENDLESS_I')
# fmt: on

LEVELS = SUPPORTED_MAPS
MODES = SUPPORTED_MODES
DIFFICULTIES = SUPPORTED_DIFFICULTIES


def base_url(beta: bool = False) -> str:
    return f"https://{'beta.' if beta else ''}infinitode.prineside.com/"


class Session:
    def __init__(self, session: Optional[aiohttp.ClientSession] = None, *, cache_enabled: bool = True) -> None:
        """Set cache_enabled=False when the caller owns caching and refresh policy."""
        self._session = session or aiohttp.ClientSession()
        self.cache_enabled = cache_enabled

    # async enter and exit allow for the fancy "with" statements
    # useful so you don't have to close the session yourself
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self.close()

    async def close(self):
        """Closes the internal ClientSession."""
        await self._session.close()

    @staticmethod
    def _kwarg_check(
        *,
        mapname: Optional[str] = None,
        playerid: Optional[str] = None,
        mode: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> None:
        if mapname is not None and str(mapname) not in LEVELS:
            raise BadArgument(f"Invalid map: {mapname}")
        if playerid is not None and (
            not isinstance(playerid, str) or ID_REGEX.fullmatch(playerid) is None
        ):
            raise BadArgument(f"Invalid playerid: {playerid}")
        if mode is not None and mode not in MODES:
            raise BadArgument(f"Invalid mode (must be one of {MODES}): {mode}")
        if difficulty is not None and difficulty not in DIFFICULTIES:
            raise BadArgument(
                f"Invalid difficulty (must be one of {DIFFICULTIES}): {difficulty}"
            )

    # not being more specific with the payload type
    # so the typechecker stops annoying me
    async def _post(
        self, arg: str, data: Optional[Dict[str, Any]] = None, *, beta: bool = False
    ) -> Dict[str, Any]:
        """Internal post method to communicate with Rainy's API"""
        url = base_url(beta) + (
            f"?m=api&a={arg}&apiv=1&g=com.prineside.tdi2&v={GAME_API_VERSION}"
        )
        LOG.info("Sending POST request %s with data %s", arg, data)
        try:
            async with self._session.post(url, data=data) as r:
                r.raise_for_status()
                try:
                    payload: Dict[str, Any] = await r.json()
                except (ValueError, TypeError) as exc:
                    raise APIError("Invalid JSON response from server") from exc
        except aiohttp.ClientError as exc:
            raise APIError("Something went wrong. Try again later") from exc

        if not isinstance(payload, dict):
            raise APIError("Invalid JSON response from server")
        LOG.debug("Response to POST request %s: %s", arg, payload)

        if payload.get("status") == "success":
            return payload
        raise APIError(
            f'Error response from server: {payload.get("message", "unknown error")}'
        )

    @async_expiring_cache()
    async def leaderboards_rank(
        self,
        mapname: Any,
        playerid: str,
        mode: str = "score",
        difficulty: str = "NORMAL",
        *,
        beta: bool = False,
    ) -> Score:
        """
        Retrieves a Score of the given player.
        A valid playerid needs to be specified.
        """
        self._kwarg_check(
            mapname=mapname, playerid=playerid, mode=mode, difficulty=difficulty
        )
        payload = await self._post(
            "getLeaderboardsRank",
            data={
                "gamemode": "BASIC_LEVELS",
                "difficulty": difficulty,
                "playerid": playerid,
                "mapname": str(mapname),
                "mode": mode,
            },
            beta=beta,
        )
        return Score.from_payload(
            "leaderboards_rank", mapname, mode, difficulty, playerid, payload
        )

    @async_expiring_cache()
    async def leaderboards(
        self,
        mapname: Any,
        playerid: Optional[str] = None,
        mode: str = "score",
        difficulty: str = "NORMAL",
        *,
        beta: bool = False,
    ) -> Leaderboard:
        """
        Retrieves a Leaderboard.
        The leaderboard contains the top 200 scores of the specified map.
        """
        self._kwarg_check(
            mapname=mapname, playerid=playerid, mode=mode, difficulty=difficulty
        )

        payload = await self._post(
            "getLeaderboards",
            data={
                "gamemode": "BASIC_LEVELS",
                "difficulty": difficulty,
                "playerid": playerid,
                "mapname": str(mapname),
                "mode": mode,
            },
            beta=beta,
        )
        lb = Leaderboard.from_payload(
            "leaderboards", mapname, mode, difficulty, playerid, payload
        )

        return lb

    @async_expiring_cache()
    async def runtime_leaderboards(
        self,
        mapname: Any,
        playerid: str,
        mode: str = "score",
        difficulty: str = "NORMAL",
        *,
        beta: bool = False,
    ) -> Leaderboard:
        """
        Retrieves a Runtime Leaderboard (The one displayed top right in-game).
        A valid playerid needs to be specified.
        The leaderboard contains the top 200 scores and one Score for each top% of the specified map.
        """
        self._kwarg_check(
            mapname=mapname, playerid=playerid, mode=mode, difficulty=difficulty
        )
        payload = await self._post(
            "getRuntimeLeaderboards",
            data={
                "gamemode": "BASIC_LEVELS",
                "difficulty": difficulty,
                "playerid": playerid,
                "mapname": str(mapname),
                "mode": mode,
            },
            beta=beta,
        )
        return Leaderboard.from_payload(
            "runtime_leaderboards", mapname, mode, difficulty, playerid, payload
        )

    @async_expiring_cache()
    async def skill_point_leaderboard(
        self, playerid: Optional[str] = None, *, beta: bool = False
    ) -> Leaderboard:
        """
        Retrieves the Skill Point Leaderboard.
        The leaderboard contains the top 3 skill point owners (looking at you, Eupho!).
        """
        if playerid is not None:
            self._kwarg_check(playerid=playerid)

        payload = await self._post(
            "getSkillPointLeaderboard", data={"playerid": playerid}, beta=beta
        )
        lb = Leaderboard.from_payload(
            "skill_point_leaderboard", "SP", "score", "NORMAL", playerid, payload
        )

        return lb

    @async_expiring_cache()
    async def daily_quest_leaderboards(
        self,
        date: Union[datetime.datetime, str, None] = None,
        playerid: Optional[str] = None,
        *,
        beta: bool = False,
        warning: bool = True,
    ) -> Leaderboard:
        """
        Retrieves the Daily Quest Leaderboard for the given date.
        If an invalid or no date is provided, the date will be set to the current date.
        You may disable the invalid date warning by setting the warning param to False.
        The leaderboard contains the top 200 DQ players of the given date.
        """
        if date is None:
            date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        elif isinstance(date, datetime.datetime):
            date = date.strftime("%Y-%m-%d")
        else:
            try:
                date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                if warning is True:
                    LOG.warning(
                        "Invalid date in daily_quest_leaderboards (Use YYYY-MM-DD format): %s",
                        date,
                    )
                date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
            else:
                date = date_obj.strftime("%Y-%m-%d")  # allows for missing leading zeros

        if playerid is not None:
            self._kwarg_check(playerid=playerid)

        payload = await self._post(
            "getDailyQuestLeaderboards",
            data={"date": date, "playerid": playerid},
            beta=beta,
        )
        lb = Leaderboard.from_payload(
            "daily_quest_leaderboards",
            "DQ",
            "score",
            "NORMAL",
            playerid,
            payload,
            date=date,
        )

        return lb

    async def daily_quest_info(self, *, beta: bool = False) -> DailyQuestInfo:
        """Retrieves metadata for the currently active Daily Quest."""
        payload = await self._post("getDailyQuestInfo", beta=beta)

        data = payload.get("data")
        if not isinstance(data, dict):
            raise ParseError("Invalid Daily Quest info response")

        try:
            date = data["date"]
            daily_quest = data["daily_quest"]
            end_timestamp = data["end_timestamp"]
            data_hash = data["data_hash"]
            if (
                not isinstance(date, str)
                or datetime.date.fromisoformat(date).isoformat() != date
            ):
                raise ValueError("invalid date")
            if not isinstance(data_hash, str):
                raise TypeError("invalid data hash")
            if isinstance(daily_quest, bool) or not isinstance(daily_quest, (int, str)):
                raise TypeError("invalid Daily Quest ID")
            if isinstance(end_timestamp, bool) or not isinstance(
                end_timestamp, (int, str)
            ):
                raise TypeError("invalid end timestamp")
            quest_id = int(daily_quest)
            parsed_end_timestamp = int(end_timestamp)
        except (KeyError, TypeError, ValueError) as exc:
            raise ParseError("Invalid Daily Quest info response") from exc

        return DailyQuestInfo(date, quest_id, parsed_end_timestamp, data_hash)

    @async_expiring_cache()
    async def seasonal_leaderboard(self, *, beta: bool = False) -> Leaderboard:
        """
        Retrieves the season Leaderboard.
        The leaderboard contains the top 200 scores in the season.
        This coroutine never takes arguments.
        """
        url = base_url(beta) + "xdx/?url=seasonal_leaderboard"
        LOG.info("Sending GET request to %s", url)

        try:
            r = await self._session.get(url=url)
            r.raise_for_status()
            content = await r.text()
        except aiohttp.ClientError as exc:
            raise APIError("Bad Gateway.") from exc

        seasonal = BeautifulSoup(content, features="lxml")
        try:
            season_label = seasonal.select_one('label[i18n="season_formatted"]')
            count_label = seasonal.select_one('label[i18n="player_count_formatted"]')
            player_labels = seasonal.select('label[color="LIGHT_BLUE:P300"]')
            score_labels = seasonal.select(
                'label[nowrap="true"][text-align="right"]'
            )
            rows = seasonal.select('div[x="90"]')
            if season_label is None or count_label is None:
                raise ValueError("missing seasonal metadata")
            if len(player_labels) != len(rows) or len(score_labels) < len(rows):
                raise ValueError("incomplete seasonal rows")
            season = int(str(season_label["i18nf"]).replace('["', '').replace('"]', ''))
            player_count = int(
                str(count_label["i18nf"])
                .replace('["', '')
                .replace('"]', '')
                .replace(',', '')
            )
            scores = [
                {
                    "playerid": str(player_labels[x]["click"]).split("id=", 1)[1],
                    "nickname": player_labels[x].text,
                    "score": score_labels[x].text.replace(",", ""),
                }
                for x in range(len(rows))
            ]
            return Leaderboard.from_payload(
                "seasonal_leaderboard",
                "season",
                "score",
                "NORMAL",
                None,
                {
                    "status": "success",
                    "player": {"total": player_count},
                    "leaderboards": scores,
                },
                season=season,
            )
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ParseError("Could not parse seasonal leaderboard HTML") from exc

    @async_expiring_cache()
    async def player(
        self,
        playerid: str | None = None,
        nickname: str | None = None,
        *,
        beta: bool = False,
    ) -> Player:
        """
        Retrieves a Player by exact player ID or nickname.

        Nickname matching is case-insensitive. Exactly one lookup value is required.
        """
        if (playerid is None) == (nickname is None):
            raise BadArgument("Specify exactly one of playerid or nickname.")

        url = base_url(beta)
        if nickname is not None:
            if not isinstance(nickname, str) or not nickname.strip():
                raise BadArgument("Nickname must be a non-empty string.")
            params = {"url": "profile/view", "nickname": nickname}
        else:
            self._kwarg_check(playerid=playerid)
            params = {"url": "profile/view", "id": playerid}

        url += "xdx/index.php"
        LOG.info("Sending GET request to %s with params %s", url, params)

        try:
            r = await self._session.get(url=url, params=params)
            r.raise_for_status()
            content = await r.text()
        except aiohttp.ClientError as exc:
            raise APIError("Bad Gateway.") from exc
        not_found = BeautifulSoup(content, features="lxml").select_one("label")
        if (
            not_found is not None
            and not_found.get_text(strip=True) == "Player not found:"
        ):
            raise PlayerNotFound(f"Player not found: {playerid or nickname}")

        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(
                None, self._parse_player, content, beta
            )
        except Exception as exc:
            raise ParseError("Could not parse player profile HTML") from exc

    @async_expiring_cache()
    async def search_players(
        self,
        nickname: str | None = None,
        *,
        sort_type: PlayerSort = PlayerSort.PROFILE_XP,
        sort_order: PlayerSortOrder = PlayerSortOrder.DESC,
        limit: int = 100,
        beta: bool = False,
    ) -> PlayerSearchResult:
        """Searches and sorts players through the public player browser."""
        if nickname is not None and (
            not isinstance(nickname, str) or not nickname.strip()
        ):
            raise BadArgument("Nickname must be a non-empty string or None.")
        if not isinstance(sort_type, PlayerSort):
            raise BadArgument("sort_type must be a PlayerSort member.")
        if not isinstance(sort_order, PlayerSortOrder):
            raise BadArgument("sort_order must be a PlayerSortOrder member.")
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or not 1 <= limit <= 100
        ):
            raise BadArgument("Search limit must be an integer from 1 through 100.")

        url = base_url(beta) + "xdx/index.php"
        params = {
            "url": "profile/list",
            "nickname": nickname or "",
            "sortType": sort_type.value,
            "sortOrder": sort_order.value,
        }
        LOG.info("Sending GET request to %s with params %s", url, params)
        try:
            r = await self._session.get(url=url, params=params)
            r.raise_for_status()
            content = await r.text()
        except aiohttp.ClientError as exc:
            raise APIError("Bad Gateway.") from exc
        loop = asyncio.get_running_loop()
        try:
            players, total = await loop.run_in_executor(
                None, self._parse_player_search, content, sort_type
            )
        except Exception as exc:
            raise ParseError("Could not parse player search HTML") from exc
        return PlayerSearchResult(
            players=tuple(players[:limit]),
            total=total,
            sort_type=sort_type,
            sort_order=sort_order,
            nickname=nickname,
        )

    @staticmethod
    def _parse_player_search(
        content: str, sort_type: PlayerSort
    ) -> tuple[list[PlayerSearchEntry], int]:
        data = BeautifulSoup(content, features="lxml")
        found_label = next(
            (
                label
                for label in data.select("label")
                if label.get_text(strip=True).startswith("Players found:")
            ),
            None,
        )
        if found_label is None:
            raise ValueError("missing player search result count")
        found_count = int(
            found_label.get_text(strip=True).split(":", 1)[1].replace(",", "")
        )
        if found_count < 0:
            raise ValueError("invalid player search result count")

        results: list[PlayerSearchEntry] = []
        for row in data.select('div[width="960"][height="64"]'):
            profile = row.select_one('label[click*="profile/view"][click*="id="]')
            level_badge = row.select_one('div[data^="player-level-badge:"]')
            avatar = row.select_one('img[src*="/avatars/"]')
            if profile is None or level_badge is None or avatar is None:
                raise ValueError("incomplete player search row")
            click = str(profile["click"])
            playerid = click.split("id=", 1)[1].split("&", 1)[0]
            level = int(str(level_badge["data"]).split(":", 1)[1])
            avatar_src = str(avatar["src"])
            nickname = profile.get_text(strip=True)
            if ID_REGEX.fullmatch(playerid) is None or not nickname:
                raise ValueError("invalid player search row")

            pinned_badge = None
            pinned_badge_level = None
            pinned_badge_icon = row.select_one('img[src^="?pb-icon-"]')
            if pinned_badge_icon is not None:
                icon_src = str(pinned_badge_icon["src"])
                icon_name = icon_src[len("?pb-icon-") :]
                if not icon_name:
                    raise ValueError("invalid pinned badge metadata")
                if icon_name.startswith("season-level-") and icon_name.endswith(
                    ("-2", "-3")
                ):
                    pinned_badge_level = icon_name[
                        len("season-level-") :
                    ].rsplit("-", 1)[0]
                else:
                    leveled_badges = (
                        "youtube-author",
                        "high-leveled",
                        "season-1",
                        "season-2",
                    )
                    for badge in leveled_badges:
                        prefix = f"{badge}-"
                        if icon_name.startswith(prefix):
                            pinned_badge_level = icon_name[len(prefix) :]
                            break
                if pinned_badge_level == "":
                    raise ValueError("invalid pinned badge metadata")

                badge_container = pinned_badge_icon.parent
                pinned_badge_overlay = badge_container.select_one(
                    'img[src^="?pb-over-"]'
                )
                icon_color_value = pinned_badge_icon.get("color")
                overlay_src = None
                overlay_color = None
                if pinned_badge_overlay is not None:
                    overlay_src = str(pinned_badge_overlay["src"])[1:]
                    overlay_color_value = pinned_badge_overlay.get("color")
                    if overlay_color_value is not None:
                        overlay_color = str(overlay_color_value)
                pinned_badge = Badge(
                    iconImg=icon_src[1:],
                    iconColor=(
                        str(icon_color_value)
                        if icon_color_value is not None
                        else None
                    ),
                    overlayImg=overlay_src,
                    overlayColor=overlay_color,
                )

            sort_value = None
            if sort_type is not PlayerSort.NICKNAME:
                value_labels = row.select(
                    'label[pad-left="12"][pad-right="12"]'
                )
                if len(value_labels) != 1:
                    raise ValueError("missing player search sort value")
                sort_value = value_labels[0].get_text(strip=True)
                if not sort_value:
                    raise ValueError("invalid player search sort value")
            results.append(
                PlayerSearchEntry(
                    playerid=playerid,
                    nickname=nickname,
                    level=level,
                    has_avatar=not avatar_src.endswith("/guest-64.png"),
                    pinned_badge=pinned_badge,
                    pinned_badge_level=pinned_badge_level,
                    sort_value=sort_value,
                )
            )
        if len(results) != min(found_count, 100):
            raise ValueError("incomplete player search results")
        return results, found_count

    @classmethod
    def _parse_player(cls, content: str, beta: bool) -> Player:
        data = BeautifulSoup(content, features="lxml")

        t: Dict[str, Any] = {}
        t["beta"] = beta
        t["playerid"] = data.select_one("label:not([i18n],[font-min-size])").text  # type: ignore
        t["nickname"] = data.select_one("label:not([i18n])").text  # type: ignore

        cls._parse_totals(data, t)
        cls._parse_level_from_comments(data, t)
        cls._parse_xp_data(data, t)
        cls._parse_levels(data, t)
        cls._parse_badges(data, t)
        cls._parse_misc(data, t)

        return Player(**t)

    @staticmethod
    def _parse_totals(data: BeautifulSoup, t: Dict[str, Any]) -> None:
        totals = data.select_one('div[width="522"][height="140"][align="center"]')
        if totals is None:
            t.update({"total_score": 0, "total_rank": 0, "total_top": 0})
            return

        totals = totals.select("label")
        if len(totals) >= 4:
            t["total_score"] = try_int(totals[1].text.replace(",", ""))
            t["total_rank"] = try_int(totals[2].text.replace(",", ""))
            t["total_top"] = totals[3].text.replace("- Top ", "")
        else:
            t.update({"total_score": 0, "total_rank": 0, "total_top": "0%"})

    @staticmethod
    def _parse_level_from_comments(data: BeautifulSoup, t: Dict[str, Any]) -> None:
        comments = data.findAll(text=lambda text: isinstance(text, Comment))
        for x in comments:
            if "Level:" in x:
                t["level"] = int(x.split(">")[3].split("<")[0])
                break
        else:
            t["level"] = 1

    @staticmethod
    def _parse_xp_data(data: BeautifulSoup, t: Dict[str, Any]) -> None:
        xp_data = data.select_one('div[width="330"][height="64"]')
        xp_data = xp_data.select_one("label").text.split(" / ")  # type: ignore
        t["xp"] = int(xp_data[0])
        t["xp_max"] = int(xp_data[1])
        season_xp_data = data.select_one(
            'div[width="530"][align="center"][height="64"][pad-bottom="10"]'
        )

        if season_xp_data is None:
            t.update({"season_xp": 0, "season_xp_max": 500, "season_level": 1})
            return

        season_xp_borders = season_xp_data.select_one("label").text.split(" / ")  # type: ignore
        t["season_xp"] = int(season_xp_borders[0])
        t["season_xp_max"] = int(season_xp_borders[1])
        season_level_data = season_xp_data.select_one(
            'div[x="466"][width="64"][height="64"]'
        )
        if season_level_data is None:
            t["season_level"] = 1
        else:
            t["season_level"] = int(season_level_data["data"].split(":")[1])  # type: ignore

    @staticmethod
    def _parse_levels(data: BeautifulSoup, t: Dict[str, Any]) -> None:
        t["levels"] = {}

        for x in data.select('div[width="800"][height="40"]')[1:]:
            level_data = x.select("label")
            level = level_data[0].text
            if not x.select_one('label[i18n="not_ranked"]'):
                rank = int(level_data[2].text.replace(",", ""))
                score = int(level_data[1].text.replace(",", ""))
                total = int(level_data[3].text.replace("/ ", "").replace(",", ""))
                top = level_data[-1].text
            else:
                rank, score, total, top = 0, 0, 0, "-%"
            t["levels"][level] = Score(
                "player",
                level,
                "score",
                "NORMAL",
                t["playerid"],
                rank=rank,
                score=score,
                total=total,
                top=top,
                level=t["level"],
                nickname=t["nickname"],
            )

    @staticmethod
    def _parse_badges(data: BeautifulSoup, t: Dict[str, Any]) -> None:
        t["badges"] = {}

        icos = [
            "daily-game",
            "invited-players",
            "killed-enemies",
            "mined-resources",
            "skillful",
            "of-merit",
            "beta-tester-season-2",
            "beta-tester-season-3",
            f"high-leveled-{t['level'] // 10 if t['level'] < 100 else 10}",
        ]
        rars = (
            "not-received",
            "common",
            "rare",
            "very-rare",
            "epic",
            "legendary",
            "supreme",
            "artifact",
        )

        for x in data.select('div[width="80"][height="80"]'):
            rar: str = x.select("img")[0]["src"].split("bg-")[1]  # type: ignore
            if rar in rars:
                ico: str = x.select("img")[1]["src"].split("icon-")[1]  # type: ignore
                if ico in icos + [
                    "youtube-author-" + rar,
                    f"season-level-{rar}-2",
                    f"season-level-{rar}-3",
                ] or ico[:8] in ("season-1", "season-2"):
                    col: str = x.select("img")[-1]["color"]  # type: ignore
                    t["badges"][ico] = (rar, col)

    @staticmethod
    def _parse_misc(data: BeautifulSoup, t: Dict[str, Any]) -> None:
        labels = data.select('table[width="800"][align="center"]')[-1].select("label")
        replays = labels[-3].string.split(" ")  # type: ignore
        t["replays"] = 0 if len(replays) != 4 else int(replays[3])

        issues = labels[-2].string.split(" ")  # type: ignore
        t["issues"] = 0 if len(issues) != 6 else int(issues[0][3:])

        sp = list(labels[-1].string.split("ned ")[1].split(" "))  # type: ignore
        day = sp[0][:-2] if len(sp[0][:2]) == 2 else "0" + sp[0][:2]
        t["created_at"] = datetime.datetime.strptime(
            day + " " + sp[-2] + " " + sp[-1], "%d %B %Y"
        ).strftime("%Y-%m-%d")
