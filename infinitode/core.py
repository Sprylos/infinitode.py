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
from .errors import APIError, BadArgument
from .leaderboard import Leaderboard
from .player import Player
from .score import Score
from .utils import async_expiring_cache, try_int


__all__ = ("Session",)

LOG = logging.getLogger(__name__)

ID_REGEX = re.compile(r"U-([A-Z0-9]{4}-){2}[A-Z0-9]{6}")

# fmt: off
LEVELS = (
    '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7', '1.8', '1.b1',
    '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7', '2.8', '2.b1',
    '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7', '3.8', '3.b1',
    '4.1', '4.2', '4.3', '4.4', '4.5', '4.6', '4.7', '4.8', '4.b1',
    '5.1', '5.2', '5.3', '5.4', '5.5', '5.6', '5.7', '5.8', '5.b1', '5.b2',
    '6.1', '6.2', '6.3', '6.4', '6.5', '6.6', 'rumble', 'dev', 'zecred',
    'DQ1', 'DQ3', 'DQ4', 'DQ5', 'DQ7', 'DQ8', 'DQ9', 'DQ10', 'DQ11', 'DQ12',
)
MODES = ('score', 'waves')
DIFFICULTIES = ('EASY', 'NORMAL', 'ENDLESS_I')
# fmt: on


def base_url(beta: bool = False) -> str:
    return f"https://{'beta.' if beta else ''}infinitode.prineside.com/"


class Session:
    def __init__(self, session: Optional[aiohttp.ClientSession] = None) -> None:
        self.__session = session or aiohttp.ClientSession()

    # async enter and exit allow for the fancy "with" statements
    # useful so you don't have to close the session yourself
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self.close()

    async def close(self):
        """Closes the internal ClientSession."""
        await self.__session.close()

    # Rough parameter checking, "*" makes params keyword only
    @staticmethod
    def __kwarg_check(
        *,
        mapname: Optional[str] = None,
        playerid: Optional[str] = None,
        mode: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> None:
        if mapname is not None and str(mapname) not in LEVELS:
            raise BadArgument("Invalid map: " + mapname)
        if playerid is not None and not ID_REGEX.match(playerid):
            raise BadArgument("Invalid playerid: " + playerid)
        if mode is not None and not mode in MODES:
            raise BadArgument(f"Invalid mode (must be one of {MODES}): " + mode)
        if difficulty is not None and not difficulty in DIFFICULTIES:
            raise BadArgument(
                f"Invalid difficulty (must be one of {DIFFICULTIES}): " + difficulty
            )

    # not being more specific with the payload type
    # so the typechecker stops annoying me
    async def __post(
        self, arg: str, data: Optional[Dict[str, Any]] = None, *, beta: bool = False
    ) -> Dict[str, Any]:
        """Internal post method to communicate with Rainy's API"""
        url = base_url(beta) + f"?m=api&a={arg}&apiv=1&g=com.prineside.tdi2&v=282"
        LOG.info("Sending POST request %s with data %s", arg, data)
        async with self.__session.post(url, data=data) as r:
            try:
                r.raise_for_status()
            except aiohttp.ClientResponseError:
                raise APIError("Something went wrong. Try again later")

            payload: Dict[str, Any] = await r.json()
            LOG.debug("Response to POST request %s: %s", arg, payload)

            if payload["status"] == "success":
                return payload
            else:
                raise APIError(f'Error response from server: {payload["message"]}')

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
        self.__kwarg_check(
            mapname=mapname, playerid=playerid, mode=mode, difficulty=difficulty
        )
        payload = await self.__post(
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
        self.__kwarg_check(
            mapname=mapname, playerid=playerid, mode=mode, difficulty=difficulty
        )

        payload = await self.__post(
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
        self.__kwarg_check(
            mapname=mapname, playerid=playerid, mode=mode, difficulty=difficulty
        )
        payload = await self.__post(
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
            self.__kwarg_check(playerid=playerid)

        payload = await self.__post(
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
                datetime.datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                if warning is True:
                    LOG.warning(
                        "Invalid date in daily_quest_leaderboards (Use YYYY-MM-DD format): %s",
                        date,
                    )
                date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

        if playerid is not None:
            self.__kwarg_check(playerid=playerid)

        payload = await self.__post(
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

    @async_expiring_cache()
    async def seasonal_leaderboard(self, beta: bool = False) -> Leaderboard:
        """
        Retrieves the season Leaderboard.
        The leaderboard contains the top 100 scores in the season.
        This coroutine never takes arguments.
        """
        url = base_url(beta) + "xdx/?url=seasonal_leaderboard"
        LOG.info("Sending GET request to %s", url)

        r = await self.__session.get(url=url)
        try:
            r.raise_for_status()
        except aiohttp.ClientResponseError:
            raise APIError("Bad Gateway.")

        seasonal = BeautifulSoup(await r.text(), features="lxml")

        # fmt: off
        season = int(seasonal.select_one('label[i18n="season_formatted"]')['i18nf'].replace('["', '').replace('"]', ''))  # type: ignore
        player_count = int(seasonal.select('label[i18n="player_count_formatted"]')[
            0]['i18nf'].replace('["', '').replace('"]', '').replace(',', ''))  # type: ignore
        lb = Leaderboard.from_payload(
            'seasonal_leaderboard', 'season', 'score', 'NORMAL', None, {
                'status': 'success',
                'player': {'total': player_count},
                'leaderboards': [
                    {
                        'playerid': seasonal.select('label[color="LIGHT_BLUE:P300"]')[x]['click'].split('id=')[1],  # type: ignore
                        'nickname': seasonal.select('label[color="LIGHT_BLUE:P300"]')[x].text,
                        'score': seasonal.select('label[nowrap="true"][text-align="right"]')[x].text.replace(',', '')
                    } for x in range(len(seasonal.select('div[x="90"]')))
                ]
            }, season=season
        )
        # fmt: on

        return lb

    @async_expiring_cache()
    async def player(self, playerid: str, beta: bool = False) -> Player:
        """
        Retrieves the Player.
        A valid playerid needs to be specified.
        """
        self.__kwarg_check(playerid=playerid)
        url = base_url(beta) + "xdx/index.php?url=profile/view&id=" + playerid
        LOG.info("Sending GET request to %s", url)

        r = await self.__session.get(url=url)
        try:
            r.raise_for_status()
        except aiohttp.ClientResponseError:
            raise APIError("Bad Gateway.")

        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                None, self.__parse_player, await r.text(), playerid, beta
            )
        except Exception as exc:
            raise BadArgument("Invalid playerid: " + playerid) from exc

    @classmethod
    def __parse_player(cls, content: str, playerid: str, beta: bool) -> Player:
        data = BeautifulSoup(content, features="lxml")

        t: Dict[str, Any] = {}
        t["playerid"] = playerid
        t["beta"] = beta
        t["nickname"] = data.select_one("label:not([i18n])").text  # type: ignore

        cls.__parse_totals(data, t)
        cls.__parse_level_from_comments(data, t)
        cls.__parse_xp_data(data, t)
        cls.__parse_levels(data, t)
        cls.__parse_badges(data, t)
        cls.__parse_misc(data, t)

        return Player(**t)

    @staticmethod
    def __parse_totals(data: BeautifulSoup, t: Dict[str, Any]) -> None:
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
    def __parse_level_from_comments(data: BeautifulSoup, t: Dict[str, Any]) -> None:
        comments = data.findAll(text=lambda text: isinstance(text, Comment))
        for x in comments:
            if "Level:" in x:
                t["level"] = int(x.split(">")[3].split("<")[0])
                break
        else:
            t["level"] = 1

    @staticmethod
    def __parse_xp_data(data: BeautifulSoup, t: Dict[str, Any]) -> None:
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
    def __parse_levels(data: BeautifulSoup, t: Dict[str, Any]) -> None:
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
    def __parse_badges(data: BeautifulSoup, t: Dict[str, Any]) -> None:
        t["badges"] = {}

        icos = [
            "daily-game",
            "invited-players",
            "killed-enemies",
            "mined-resources",
            "skillful",
            "of-merit",
            "beta-tester-season-2",
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
    def __parse_misc(data: BeautifulSoup, t: Dict[str, Any]) -> None:
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
