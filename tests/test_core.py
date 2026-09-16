import json
from pathlib import Path
import unittest

import aiohttp

import infinitode
from infinitode.core import Session
from infinitode.daily_quest import DailyQuestInfo
from infinitode.errors import APIError, BadArgument, ParseError, PlayerNotFound
from infinitode.player import Player, PlayerSummary


FIXTURES = Path(__file__).parent / "fixtures"
PLAYER_ID = "U-ABCD-EFGH-IJKLMN"


def fixture(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeResponse:
    def __init__(self, *, text="", payload=None, error=None):
        self._text = text
        self._payload = payload
        self._error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    def raise_for_status(self):
        if self._error:
            raise self._error

    async def text(self):
        return self._text

    async def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.get_calls = []
        self.post_calls = []
        self.closed = False

    async def get(self, **kwargs):
        self.get_calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def post(self, url, data=None):
        self.post_calls.append((url, data))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    async def close(self):
        self.closed = True


class ValidationTests(unittest.TestCase):
    def test_valid_and_invalid_player_ids(self):
        Session._kwarg_check(playerid=PLAYER_ID)
        for value in (PLAYER_ID + "junk", "bad", "", 123, None):
            if value is None:
                continue
            with self.subTest(value=value), self.assertRaises(BadArgument):
                Session._kwarg_check(playerid=value)

    def test_supported_leaderboard_values(self):
        for mapname in ("0.1", "0.2", "0.3", "0.4", 5.1):
            Session._kwarg_check(mapname=mapname)
        Session._kwarg_check(mode="score", difficulty="ENDLESS_I")
        for kwargs in (
            {"mapname": "0.5"},
            {"mode": "time"},
            {"difficulty": "HARD"},
        ):
            with self.assertRaises(BadArgument):
                Session._kwarg_check(**kwargs)

    def test_public_constants_are_tuples(self):
        self.assertEqual(infinitode.GAME_API_VERSION, 282)
        self.assertIsInstance(infinitode.SUPPORTED_MAPS, tuple)
        self.assertEqual(infinitode.SUPPORTED_MODES, ("score", "waves"))
        self.assertEqual(
            infinitode.SUPPORTED_DIFFICULTIES, ("EASY", "NORMAL", "ENDLESS_I")
        )


class SessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_player_by_id_uses_params_and_parses_profile(self):
        client = FakeClient([FakeResponse(text=fixture("profile.html"))])
        player = await Session(client).player(playerid=PLAYER_ID)
        self.assertIsInstance(player, Player)
        self.assertEqual(
            (player.playerid, player.nickname, player.level),
            (PLAYER_ID, "Test Player", 42),
        )
        self.assertEqual(player.score("0.1").score, 12345)
        self.assertEqual(
            client.get_calls[0],
            {
                "url": "https://infinitode.prineside.com/xdx/index.php",
                "params": {"url": "profile/view", "id": PLAYER_ID},
            },
        )

    async def test_exact_nickname_uses_encoded_request_params(self):
        client = FakeClient([FakeResponse(text=fixture("profile.html"))])
        await Session(client).player(nickname="A & B/雪")
        self.assertEqual(
            client.get_calls[0]["params"],
            {"url": "profile/view", "nickname": "A & B/雪"},
        )

    async def test_player_requires_exactly_one_valid_lookup(self):
        session = Session(FakeClient([]))
        for args in ({}, {"playerid": PLAYER_ID, "nickname": "Alpha"}):
            with self.subTest(args=args), self.assertRaises(BadArgument):
                await session.player(**args)
        for nickname in ("", "  ", 42):
            with self.subTest(nickname=nickname), self.assertRaises(BadArgument):
                await session.player(nickname=nickname)

    async def test_player_not_found_and_changed_html_are_distinct(self):
        missing = Session(
            FakeClient([FakeResponse(text=fixture("player_not_found.html"))])
        )
        with self.assertRaises(PlayerNotFound):
            await missing.player(nickname="Nobody")
        changed = Session(
            FakeClient([FakeResponse(text="<body><p>changed</p></body>")])
        )
        with self.assertRaises(ParseError):
            await changed.player(nickname="Alpha")

    async def test_search_parses_fields_limits_and_params(self):
        client = FakeClient([FakeResponse(text=fixture("player_search.html"))])
        results = await Session(client).search_players("mAtCh & 雪", limit=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0], PlayerSummary(PLAYER_ID, "Alpha Match", 42, True)
        )
        self.assertEqual(
            client.get_calls[0]["params"],
            {"url": "profile/list", "nickname": "mAtCh & 雪"},
        )

    async def test_search_empty_results_and_beta_route(self):
        client = FakeClient([FakeResponse(text=fixture("player_search_empty.html"))])
        self.assertEqual(await Session(client).search_players("none", beta=True), [])
        self.assertTrue(client.get_calls[0]["url"].startswith("https://beta."))

    async def test_search_validation_and_malformed_html(self):
        session = Session(FakeClient([]))
        for query in ("", " ", 2):
            with self.subTest(query=query), self.assertRaises(BadArgument):
                await session.search_players(query)
        for limit in (0, 101, 1.5, True):
            with self.subTest(limit=limit), self.assertRaises(BadArgument):
                await session.search_players("a", limit=limit)
        malformed = Session(
            FakeClient(
                [FakeResponse(text="<body><label>Players found: 1</label></body>")]
            )
        )
        with self.assertRaises(ParseError):
            await malformed.search_players("a")

    async def test_standard_player_and_runtime_leaderboard_payloads(self):
        payload = json.loads(fixture("leaderboard.json"))
        clients = [
            FakeClient([FakeResponse(payload=payload)]),
            FakeClient([FakeResponse(payload=payload)]),
            FakeClient([FakeResponse(payload=payload)]),
        ]
        score = await Session(clients[0]).leaderboards_rank("0.1", PLAYER_ID)
        board = await Session(clients[1]).leaderboards("0.2", playerid=PLAYER_ID)
        runtime = await Session(clients[2]).runtime_leaderboards("0.3", PLAYER_ID)
        self.assertEqual((score.score, len(board), len(runtime)), (321, 2, 2))
        self.assertEqual(board.player.playerid, PLAYER_ID)

    async def test_daily_quest_date_handling(self):
        payload = json.loads(fixture("leaderboard.json"))
        client = FakeClient([FakeResponse(payload=payload)])
        board = await Session(client).daily_quest_leaderboards("2026-9-5")
        self.assertEqual(board.date, "2026-09-05")
        self.assertEqual(client.post_calls[0][1]["date"], "2026-09-05")
        self.assertEqual(len(client.post_calls), 1)

    async def test_daily_quest_info_parsing_and_derived_properties(self):
        payload = json.loads(fixture("daily_quest_info.json"))
        info = await Session(
            FakeClient([FakeResponse(payload=payload)])
        ).daily_quest_info()
        self.assertIsInstance(info, DailyQuestInfo)
        self.assertEqual(info.date, "2026-09-16")
        self.assertEqual(info.quest_id, 3)
        self.assertIsInstance(info.quest_id, int)
        self.assertEqual(info.end_timestamp, 1789603200)
        self.assertIsInstance(info.end_timestamp, int)
        self.assertEqual(info.data_hash, "7937650143b98f4fddf22bf392b9ea36")
        self.assertEqual(info.mapname, "DQ3")
        self.assertEqual(info.reset_timestamp, info.end_timestamp)
        self.assertIs(infinitode.DailyQuestInfo, DailyQuestInfo)

    async def test_daily_quest_info_rejects_malformed_payloads(self):
        valid_data = json.loads(fixture("daily_quest_info.json"))["data"]
        malformed = (None, [], "bad")
        missing_fields = tuple(
            {key: value for key, value in valid_data.items() if key != missing}
            for missing in valid_data
        )
        invalid_fields = (
            {**valid_data, "date": "2026-9-16"},
            {**valid_data, "daily_quest": "not-an-int"},
            {**valid_data, "end_timestamp": "not-an-int"},
            {**valid_data, "data_hash": 123},
        )
        for data in malformed + missing_fields + invalid_fields:
            with self.subTest(data=data), self.assertRaises(ParseError):
                await Session(
                    FakeClient(
                        [FakeResponse(payload={"status": "success", "data": data})]
                    )
                ).daily_quest_info()

    async def test_daily_quest_info_transport_api_error_and_beta(self):
        payload = json.loads(fixture("daily_quest_info.json"))
        beta_client = FakeClient([FakeResponse(payload=payload)])
        await Session(beta_client).daily_quest_info(beta=True)
        self.assertIn(
            "https://beta.infinitode.prineside.com/", beta_client.post_calls[0][0]
        )
        self.assertIsNone(beta_client.post_calls[0][1])

        with self.assertRaises(APIError):
            await Session(
                FakeClient([aiohttp.ClientConnectionError("offline")])
            ).daily_quest_info()
        with self.assertRaises(APIError):
            await Session(
                FakeClient(
                    [FakeResponse(payload={"status": "error", "message": "nope"})]
                )
            ).daily_quest_info()

    async def test_daily_quest_info_is_not_cached(self):
        first = json.loads(fixture("daily_quest_info.json"))
        second = json.loads(fixture("daily_quest_info.json"))
        second["data"]["daily_quest"] = "4"
        client = FakeClient(
            [FakeResponse(payload=first), FakeResponse(payload=second)]
        )
        session = Session(client)
        self.assertEqual((await session.daily_quest_info()).quest_id, 3)
        self.assertEqual((await session.daily_quest_info()).quest_id, 4)
        self.assertEqual(len(client.post_calls), 2)

    async def test_seasonal_parsing_and_malformed_html(self):
        board = await Session(
            FakeClient([FakeResponse(text=fixture("seasonal.html"))])
        ).seasonal_leaderboard()
        self.assertEqual((board.season, board.total, len(board)), (21, 12345, 2))
        malformed = Session(FakeClient([FakeResponse(text="<body>changed</body>")]))
        with self.assertRaises(ParseError):
            await malformed.seasonal_leaderboard()

    async def test_api_error_for_http_json_and_error_payloads(self):
        request_info = aiohttp.RequestInfo(
            url=aiohttp.client_reqrep.URL("https://example.invalid"),
            method="GET",
            headers={},
            real_url=aiohttp.client_reqrep.URL("https://example.invalid"),
        )
        status_error = aiohttp.ClientResponseError(request_info, (), status=500)
        responses = (
            FakeResponse(error=status_error),
            FakeResponse(payload=ValueError("bad json")),
            FakeResponse(payload={"status": "error", "message": "nope"}),
            aiohttp.ClientConnectionError("offline"),
        )
        for response in responses:
            with self.subTest(response=response), self.assertRaises(APIError):
                await Session(FakeClient([response])).leaderboards("0.4")

        with self.assertRaises(APIError):
            await Session(
                FakeClient([aiohttp.ClientConnectionError("offline")])
            ).search_players("alpha")


if __name__ == "__main__":
    unittest.main()
