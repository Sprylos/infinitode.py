# Infinitode.py

An asynchronous python wrapper for the Infinitode-2 API using `async`-`await` syntax.

## Installing

---

Installing via pip:

```
pip install infinitode.py
```

## Showcase

---

```python
import asyncio
import infinitode


async def main():
    # Creates a session to communicate with Rainy's API.
    # The with statement assures that the underlying session is closed.
    # Alternatively you can can simply call Session.close() once you don't need it anymore.
    async with infinitode.Session() as API:

        # The mapname parameter should be in the form presented in the game (ie 5.1).
        # The mode param (score/waves) defaults to score.
        # The difficulty param (EASY/NORMAL/ENDLESS_I) which defaults to NORMAL can also be specified,
        # however easy leaderboards/scores are always empty.
        # Sometimes a playerid can or must be specified,
        # and the result will have additional info about that players' score.

        # This returns a score of a specific player with the id U-E9BP-FSN9-H6ENMQ on the map 5.1 in normal mode.
        # The parameters mapname and playerid are required, mode and difficulty are optional.
        score_5_1 = await API.leaderboards_rank(mapname='5.1', playerid='U-E9BP-FSN9-H6ENMQ', mode='score', difficulty='NORMAL')

        # This returns a leaderboard of the top 200 wave scores on 5.1 in normal mode.
        # Only the mapname is required.
        # mapname can also be a float
        leaderboard_5_1 = await API.leaderboards(mapname=5.1, playerid=None, mode='waves')

        # The runtime leaderboard is the one displayed in the top right when playing a run.
        # It is similar to leaderboards, however it will also give the top 1-99% each.
        # Mapname and playerid are required.
        runtime_5_1 = await API.runtime_leaderboards(mapname=5.1, playerid='U-E9BP-FSN9-H6ENMQ', difficulty='ENDLESS_I')

        # Top 3 skill point owners, a playerid can be specified for the score of that player.
        sp_leaderboard = await API.skill_point_leaderboard(playerid='U-E9BP-FSN9-H6ENMQ')

        # Top 200 players of todays dailyquest or the one which date is specified.
        # The date should be a str in the YYYY-MM-DD format, or a datetime.datetime object.
        # However the server seems to only save the last 2 or 3 days.
        # Again, a playerid can be specified.
        dq_leaderboard = await API.daily_quest_leaderboards()

        # This returns the top 100 players from the season leaderboard.
        # There is no convenient api response for this call.
        # Instead the data is parsed, which is why this can take a bit.
        # This function never takes parameters.
        season_leaderboard = await API.seasonal_leaderboard()

        # This will return a Player with a lot of attributes.
        # Like the season leaderboard, the data has to be parsed.
        # This function always takes a playerid and nothing else.
        player = await API.player('U-E9BP-FSN9-H6ENMQ')

        # All Leaderboards and Scores have the method, mapname, mode, difficulty attribute:
        print(score_5_1.method, score_5_1.mapname,
              runtime_5_1.mode, runtime_5_1.difficulty)
        # All leaderboards have a total attribute:
        print(leaderboard_5_1.total)

        # They also have an optional player, date and season attribute
        print(dq_leaderboard.date)
        print(season_leaderboard.season)

        # The player attribute will return a Score
        sp_score = sp_leaderboard.player
        assert sp_score is not None  # check if the score exists.

        # Scores also always have a playerid, rank and score attribute:
        print(score_5_1.playerid, score_5_1.rank, score_5_1.score)

        # There is also a variety of optional attributes:
        # has_pfp, level, nickname, pinned_badge, position, top, total, player

        # Every Leaderboard contains a certain amount of scores, with a maxmimum of 300.
        # The best way to retrieve the scores is usually iterating through the leaderboard.
        # for score in leaderboard_5_1:
        #     print(score.nickname)  # do something with score

        # You can also index a single score:
        leaderboard_5_1[35].print_score()
        # or index with a slice to receive a shortened leaderboard:
        print(len(leaderboard_5_1[0:10]))

        # The last main object is a Player, received only be Session.player()
        # Every Player has the same attributes.
        print(
            player.playerid,
            player.nickname,
            player.level,
            player.xp,
            player.xp_max,  # xp required per level
            player.season_level,
            player.season_xp,
            player.season_xp_max,
            player.total_score,
            player.total_rank,
            player.total_top,
            player.replays,
            player.issues,
            player.created_at,  # as str
            player.avatar_link  # even when the person has no pfp
        )

        # Every player also has a .score() method. It will return the players score for the given level.
        player.score('5.1').print_score()

        # You can also get the DQ and SP scores with additional API calls:
        (await player.daily_quest(API)).rank
        (await player.skill_point(API)).rank

# In case you get a runtime error here, ignore it, that's Windows' shit.
asyncio.run(main())
```

## Logging

---

```python
import infinitode
import asyncio
import logging

# setup logger
# INFO will log everytime a request is made
# DEBUG will log the server's response aswell
logging.basicConfig(level=logging.INFO)


async def main():
    async with infinitode.Session() as API:
        await API.leaderboards('6.3')  # just an example

asyncio.run(main())
```
