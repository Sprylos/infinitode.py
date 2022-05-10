from __future__ import annotations

# std
import re
import time
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
import bs4

# local
from .errors import APIError, BadArgument
from .leaderboard import Leaderboard
from .player import Player
from .score import Score


__all__ = ('Session',)

_log = logging.getLogger(__name__)

ID_REGEX = re.compile(r'U-([A-Z0-9]{4}-){2}[A-Z0-9]{6}')
LEVELS = (
    '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7', '1.8', '1.b1',
    '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7', '2.8', '2.b1',
    '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7', '3.8', '3.b1',
    '4.1', '4.2', '4.3', '4.4', '4.5', '4.6', '4.7', '4.8', '4.b1',
    '5.1', '5.2', '5.3', '5.4', '5.5', '5.6', '5.7', '5.8', '5.b1', '5.b2',
    '6.1', '6.2', '6.3', '6.4', 'rumble', 'dev', 'zecred',
    'DQ1', 'DQ3', 'DQ4', 'DQ5', 'DQ7', 'DQ8', 'DQ9', 'DQ10', 'DQ11', 'DQ12',
)


class Session:
    def __init__(self, session: Optional[aiohttp.ClientSession] = None) -> None:
        self._session = session or aiohttp.ClientSession()
        self._cooldown: Dict[str, Any] = {'DailyQuestInfo': 0.0, 'LatestNews': 0.0, 'DailyQuestLeaderboards': {
        }, 'SkillPointLeaderboard': 0.0, 'BasicLevelsTopLeaderboards': {}, 'Leaderboards': {}, 'seasonal': 0.0}
        self._DailyQuestLeaderboards: Dict[str, Leaderboard] = {}
        self._BasicLevelsTopLeaderboards: Dict[str, Leaderboard] = {}
        self._Leaderboards: Dict[str, Leaderboard] = {}
        self._SkillPointLeaderboard: Leaderboard
        self._seasonal: Leaderboard

    # async enter and exit allow for the fancy "with" statements
    # useful so you don't have to close the session yourself
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self.close()

    async def close(self):
        """Closes the internal ClientSession."""
        await self._session.close()

    # Rough parameter checking, "*" makes params keyword only
    @staticmethod
    def _kwarg_check(*, mapname: Optional[str] = None, playerid: Optional[str] = None, mode: Optional[str] = None, difficulty: Optional[str] = None) -> None:
        if mapname is not None and str(mapname) not in LEVELS:
            raise BadArgument('Invalid map: ' + mapname)
        if playerid is not None and not ID_REGEX.match(playerid):
            raise BadArgument('Invalid playerid: ' + playerid)
        if mode is not None and not mode in ('score', 'waves'):
            raise BadArgument(
                "Invalid mode (must be either 'score' or 'waves'): " + mode)
        if difficulty is not None and not difficulty in ('EASY', 'NORMAL', 'ENDLESS_I'):
            raise BadArgument(
                "Invalid difficulty (must be one of 'EASY', 'NORMAL', 'ENDLESS_I': " + difficulty)

    # not being more specific with the payload type
    # so the typechecker stops annoying me
    async def _post(self, arg: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        '''Internal post method to communicate with Rainy's API'''
        url = f'https://infinitode.prineside.com/?m=api&a={arg}&apiv=1&g=com.prineside.tdi2&v=282'
        _log.info('Sending POST request %s with data %s', arg, data)
        async with self._session.post(url, data=data) as r:
            try:
                r.raise_for_status()
            except aiohttp.ClientResponseError:
                raise APIError("Something went wrong. Try again later")

            payload: Dict[str, Any] = await r.json()
            _log.debug('Response to POST request %s: %s', arg, payload)

            if payload['status'] == 'success':
                return payload
            else:
                raise APIError(
                    f'Error response from server: {payload["message"]}')

    # all the mapnames are Any because any python object can be converted to a str
    async def leaderboards_rank(self, mapname: Any, playerid: str, mode: str = 'score', difficulty: str = 'NORMAL') -> Score:
        """
        Retrieves a Score of the given player.
        A valid playerid needs to be specified.
        """
        self._kwarg_check(
            mapname=mapname, playerid=playerid, mode=mode, difficulty=difficulty)
        payload = await self._post('getLeaderboardsRank', data={'gamemode': 'BASIC_LEVELS', 'difficulty': difficulty, 'playerid': playerid, 'mapname': str(mapname), 'mode': mode})
        return Score.from_payload('leaderboards_rank', mapname, mode, difficulty, playerid, payload)

    async def leaderboards(self, mapname: Any, playerid: Optional[str] = None, mode: str = 'score', difficulty: str = 'NORMAL') -> Leaderboard:
        """
        Retrieves a Leaderboard.
        The leaderboard contains the top 200 scores of the specified map.
        """
        self._kwarg_check(
            mapname=mapname, playerid=playerid, mode=mode, difficulty=difficulty)
        key = f'{difficulty}{mode}{mapname}'
        if not playerid and (time.time() < self._cooldown['Leaderboards'].get(key, 0) + 60):
            return self._Leaderboards[key]
        payload = await self._post('getLeaderboards', data={'gamemode': 'BASIC_LEVELS', 'difficulty': difficulty, 'playerid': playerid, 'mapname': str(mapname), 'mode': mode})
        lb = Leaderboard.from_payload(
            'leaderboards', mapname, mode, difficulty, playerid, payload)
        if lb.player is None:
            self._Leaderboards[key] = lb
            self._cooldown['Leaderboards'][key] = time.time()
        return lb

    async def runtime_leaderboards(self, mapname: Any, playerid: str, mode: str = 'score', difficulty: str = 'NORMAL') -> Leaderboard:
        """
        Retrieves a Runtime Leaderboard (The one displayed top right in-game).
        A valid playerid needs to be specified.
        The leaderboard contains the top 200 scores and one Score for each top% of the specified map.
        """
        self._kwarg_check(
            mapname=mapname, playerid=playerid, mode=mode, difficulty=difficulty)
        payload = await self._post('getRuntimeLeaderboards', data={'gamemode': 'BASIC_LEVELS', 'difficulty': difficulty, 'playerid': playerid, 'mapname': str(mapname), 'mode': mode})
        return Leaderboard.from_payload('runtime_leaderboards', mapname, mode, difficulty, playerid, payload)

    async def skill_point_leaderboard(self, playerid: Optional[str] = None) -> Leaderboard:
        """
        Retrieves the Skill Point Leaderboard.
        The leaderboard contains the top 3 skill point owners (looking at you, Eupho!).
        """
        if playerid is not None:
            self._kwarg_check(playerid=playerid)
        elif time.time() < self._cooldown['SkillPointLeaderboard'] + 60:
            return self._SkillPointLeaderboard
        payload = await self._post('getSkillPointLeaderboard', data={'playerid': playerid})
        lb = Leaderboard.from_payload(
            'skill_point_leaderboard', 'SP', 'score', 'NORMAL', playerid, payload)
        if lb.player is None:
            self._SkillPointLeaderboard = lb
            self._cooldown['SkillPointLeaderboard'] = time.time()
        return lb

    async def daily_quest_leaderboards(
        self,
        date: Union[datetime.datetime, str, None] = None,
        playerid: Optional[str] = None,
        warning: bool = True,
    ) -> Leaderboard:
        """
        Retrieves the Daily Quest Leaderboard for the given date.
        If an invalid or no date is provided, the date will be set to the current date.
        You may disable the invalid date warning by setting the warning param to False.
        The leaderboard contains the top 200 DQ players of the given date.
        """
        if date is None:
            date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        elif isinstance(date, datetime.datetime):
            date = date.strftime('%Y-%m-%d')
        else:
            try:
                datetime.datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                if warning == True:
                    _log.warning(
                        'Invalid date in daily_quest_leaderboards (Use YYYY-MM-DD format): %s', date)
                date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        if not playerid and (time.time() < self._cooldown['DailyQuestLeaderboards'].get(date, 0) + 60):
            return self._DailyQuestLeaderboards[date]
        if playerid is not None:
            self._kwarg_check(playerid=playerid)
        payload = await self._post('getDailyQuestLeaderboards', data={'date': date, 'playerid': playerid})
        lb = Leaderboard.from_payload(
            'daily_quest_leaderboards', 'DQ', 'score', 'NORMAL', playerid, payload, date=date)
        if lb.player is None:
            self._DailyQuestLeaderboards[date] = lb
            self._cooldown['DailyQuestLeaderboards'][date] = time.time()
        return lb

    async def seasonal_leaderboard(self) -> Leaderboard:
        """
        Retrieves the season Leaderboard.
        The leaderboard contains the top 100 scores in the season.
        This coroutine never takes arguments.
        """
        if time.time() < self._cooldown['seasonal'] + 60:
            return self._seasonal
        url = 'https://infinitode.prineside.com/xdx/?url=seasonal_leaderboard'
        _log.info('Sending GET request to %s', url)
        r = await self._session.get(url=url)
        try:
            r.raise_for_status()
        except aiohttp.ClientResponseError:
            raise APIError('Bad Gateway.')
        seasonal = bs4.BeautifulSoup(await r.text(), 'lxml')
        season = int(seasonal.select_one('label[i18n="season_formatted"]')['i18nf'].replace('["', '').replace('"]', ''))  # type: ignore # nopep8
        player_count = int(seasonal.select('label[i18n="player_count_formatted"]')[  # type: ignore
            0]['i18nf'].replace('["', '').replace('"]', '').replace(',', ''))  # type: ignore
        lb = Leaderboard.from_payload(
            'seasonal_leaderboard', 'season', 'score', 'NORMAL', None, {
                'status': 'success',
                'player': {'total': player_count},
                'leaderboards': [
                    {
                        'playerid': seasonal.select('label[color="LIGHT_BLUE:P300"]')[x]['click'].split('id=')[1],  # type: ignore # nopep8
                        'nickname': seasonal.select('label[color="LIGHT_BLUE:P300"]')[x].text,  # type: ignore # nopep8
                        'score': seasonal.select('label[nowrap="true"][text-align="right"]')[x].text.replace(',', '')  # type: ignore # nopep8
                    } for x in range(len(seasonal.select('div[x="90"]')))  # type: ignore
                ]
            }, season=season
        )
        self._seasonal = lb
        self._cooldown['seasonal'] = time.time()
        return lb

    async def player(self, playerid: str) -> Player:
        """
        Retrieves the Player.
        A valid playerid needs to be specified.
        """
        self._kwarg_check(playerid=playerid)
        url = f'https://infinitode.prineside.com/xdx/index.php?url=profile/view&id={playerid}'
        _log.info('Sending GET request to %s', url)
        r = await self._session.get(url=url)
        try:
            r.raise_for_status()
        except aiohttp.ClientResponseError:
            raise APIError('Bad Gateway.')
        text = await r.text()
        data = bs4.BeautifulSoup(text, 'lxml')
        t: Dict[str, Any] = {}
        t['playerid'] = playerid
        t['nickname'] = data.select_one('label:not([i18n])').text  # type: ignore # this should never fail # nopep8
        if (totals := data.select_one('div[width="522"][height="128"][pad-top="10"][pad-bottom="10"][align="center"]')) is not None:  # type: ignore # nopep8
            totals = totals.select('label')  # type: ignore # nopep8
            try:
                t['total_score'] = int(totals[1].text.replace(',', ''))
            except (KeyError, ValueError):
                t['total_score'] = 0
            try:
                t['total_rank'] = int(totals[2].text.replace(',', ''))
            except (KeyError, ValueError):
                t['total_rank'] = 0
            try:
                t['total_top'] = totals[3].text.replace('- Top ', '')
            except (KeyError, ValueError):
                t['total_top'] = 0
        else:
            t.update({'total_score': 0, 'total_rank': 0, 'total_top': 0})
        comments = data.findAll(
            text=lambda text: isinstance(text, bs4.Comment))
        for x in comments:
            if 'Level:' in x:
                t['level'] = int(x.split('>')[3].split('<')[0])
                break
        xp_data = data.select_one('div[width="330"][height="64"]').select_one('label').text.split(' / ')  # type: ignore # nopep8
        t['xp'] = int(xp_data[0])
        t['xp_max'] = int(xp_data[1])
        t['levels'] = {}
        for x in data.select('div[width="800"][height="40"]')[1:]:  # type: ignore # nopep8
            level_data = x.select('label')  # type: ignore
            level = level_data[0].text
            if not x.select_one('label[i18n="not_ranked"]'):  # type: ignore # nopep8
                rank = int(level_data[2].text.replace(',', ''))
                score = int(level_data[1].text.replace(',', ''))
                total = int(level_data[3].text.replace(
                    '/ ', '').replace(',', ''))
                top = level_data[-1].text
            else:
                rank, score, total, top = 0, 0, 0, '-%'
            t['levels'][level] = Score(
                'player', level, 'score', 'NORMAL', playerid,
                rank=rank, score=score, total=total, top=top,
                level=t['level'], nickname=t['nickname']
            )
        t['badges'] = {}
        for x in data.select('div[width="80"][height="80"]'):  # type: ignore # nopep8
            rar: str = x.select('img')[0]['src'].split('bg-')[1]  # type: ignore # nopep8
            if rar in ['not-received', 'common', 'rare', 'very-rare', 'epic', 'legendary', 'supreme', 'artifact']:
                ico: str = x.select('img')[1]['src'].split('icon-')[1]  # type: ignore # nopep8
                if ico in ['daily-game', 'invited-players', 'killed-enemies', 'mined-resources', 'of-merit', 'beta-tester-season-2'] or ico[:8] == 'season-1':
                    col: str = x.select('img')[-1]['color']  # type: ignore # nopep8
                    t['badges'][ico] = (rar, col)
        labels = data.select('table[width="800"][align="center"]')[-1].select('label')  # type: ignore # nopep8
        t['replays'] = int(labels[-3].string.split(" ")[3])  # type: ignore
        t['issues'] = int(labels[-2].string.split(" ")[0][3:])  # type: ignore
        sp = list(labels[-1].string.split("ned ")[1].split(" "))  # type: ignore # nopep8
        day = sp[0][:-2] if len(sp[0][:2]) == 2 else "0" + sp[0][:2]
        t['created_at'] = datetime.datetime.strptime(
            day + " " + sp[-2] + " " + sp[-1], "%d %B %Y").strftime('%Y-%m-%d')

        return Player(**t)
