# Infinitode.py

An asynchronous Python wrapper for the Infinitode-2 API using `async`-`await` syntax.

---

## Installation

Install the library via pip:

```bash
pip install infinitode.py
```

---

## Showcase

### Setting Up a Session

Create a session to communicate with Rainy's API. Use the `with` statement to ensure the session closes properly.
Alternatively you can can simply call `Session.close()` once you don't need it anymore.

```python
import asyncio
import infinitode

async def main():
    async with infinitode.Session() as API:
        # Your API calls go here
        pass

asyncio.run(main())
```

---

### Fetching Leaderboard Data

Parameters:
- `mapname`: The map identifier (e.g., "5.1" or "4.b1" or "zecred").
- `playerid` (sometimes optional): The player's unique identifier.
- `mode` (optional): One of `'score'`, `'waves'`. Defaults to `'score'`.
- `difficulty` (optional): One of `'EASY'`, `'NORMAL'`, `'ENDLESS_I'`. Defaults to `'NORMAL'`.

The immutable `infinitode.SUPPORTED_MAPS`, `infinitode.SUPPORTED_MODES`, and
`infinitode.SUPPORTED_DIFFICULTIES` tuples contain the values accepted by the
current library. `infinitode.GAME_API_VERSION` exposes the game API version used
for JSON API calls.

#### Player Score on a Specific Map

Retrieve the score of a specific player on a particular map.

```python
score_5_1 = await API.leaderboards_rank(
    mapname="5.1",
    playerid="U-E9BP-FSN9-H6ENMQ",
    mode="score",
    difficulty="NORMAL"
)
```

#### Top 200 Leaderboard on a Specific Map

Retrieve the leaderboard of the top 200 wave scores on 5.1.

```python
leaderboard_5_1 = await API.leaderboards(
    mapname=5.1,
    mode="waves"
)
```

#### Runtime Leaderboard

Fetch the leaderboard displayed during gameplay. This provides additional percentile information.

```python
runtime_5_1 = await API.runtime_leaderboards(
    mapname=5.1,
    playerid="U-E9BP-FSN9-H6ENMQ",
    difficulty="ENDLESS_I"
)
```

---

#### Skill Point Leaderboard

Get the top 3 skill point owners. Optionally specify a `playerid`.

```python
sp_leaderboard = await API.skill_point_leaderboard(
    playerid="U-E9BP-FSN9-H6ENMQ"
)
```


#### Daily Quest Leaderboard

Retrieve the top 200 players of today's daily quest or a specified date.

- `date`: `YYYY-MM-DD` (string) or `datetime.datetime`.

```python
dq_leaderboard = await API.daily_quest_leaderboards("2024-12-05")
```

Retrieve metadata for the currently active Daily Quest. The reset timestamp is
also available as `reset_timestamp`, and `mapname` is derived from `quest_id`.

```python
dq = await API.daily_quest_info()
print(dq.date, dq.quest_id, dq.mapname)
print(dq.end_timestamp, dq.reset_timestamp, dq.data_hash)
```

---

### Working with Leaderboards

A leaderboard is a sequence of scores with additional utility functions.

#### Access Score and Leaderboard Attributes

Leaderboards always have these attributes:
- `mapname`, `mode`, `difficulty`, `total`

And optionally these:
- `date`, `season`, `player` (will return a score object)

Scores always have these attributes:
- `playerid`, `rank`, `score`, `mapname`, `mode`, `difficulty` 

And optionally these:
- `has_pfp`, `level`, `nickname`, `pinned_badge`, `position`, `top`, `total`, `player` (will return a Player object if fetched beforehand)

#### Example for printing attributes, scores, and leaderboards

```python
for score in leaderboard_5_1:
    print(score.nickname)
    score.print_score()  # Helper method

leaderboard_5_1.print_scores()
```

#### Slice a Leaderboard

Retrieve a subset of the leaderboard:

```python
top_1 = leaderboard_5_1[0]
top_10 = leaderboard_5_1[0:10]
print(len(top_10))
```

---

### Player Information

#### Fetch Player Data

Retrieve detailed player information.

```python
player = await API.player(playerid="U-E9BP-FSN9-H6ENMQ")
# Or look up a case-insensitive, exact nickname:
player = await API.player(nickname="EuphoRowan")
```

Attributes include:
- `playerid`, `nickname`, `level`, `xp`, `season_level`, `total_score`, and many more.

#### Get Player Scores

Use the `score` method to access specific map scores.

```python
player.score(5.1).print_score()
```

#### Fetch Daily Quest and Skill Point Scores

Use additional API calls to retrieve daily quest and skill point scores:

```python
await player.fetch_daily_quest(API)
await player.fetch_skill_point(API)

print(player.daily_quest.rank, player.skill_point.score)
```

An invalid argument raises `infinitode.errors.BadArgument`, and an exact lookup
with no matching player raises its `PlayerNotFound` subclass. HTTP and JSON API
failures raise `APIError`; unexpected changes to parsed HTML raise `ParseError`.

---

### Experimental features

`Session.search_players()` performs an unauthenticated, case-insensitive
substring search of player nicknames:

```python
players = await API.search_players("eupho", limit=20)
for result in players:
    print(result.playerid, result.nickname, result.level, result.has_avatar)
```

Each `PlayerSummary` contains only the verified `playerid`, `nickname`, `level`,
and `has_avatar` fields. The upstream page returns at most 100 results and does
not offer pagination. This feature parses an HTML page rather than a stable JSON
API, so upstream markup changes may cause `ParseError` until the parser is
updated.

---

### Beta Scores

Almost all API calls support an additional `beta` boolean parameter. This will make a request to the beta servers instead. No guarantees for it working.

```python
leaderboard_5_1 = await API.leaderboards(mapname=5.1, mode='waves', beta=True)
```


### Logging

Set up logging to monitor requests and responses. 

- `INFO`: Logs every request.
- `DEBUG`: Logs server responses.

```python
import infinitode
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    async with infinitode.Session() as API:
        await API.leaderboards("6.3")

asyncio.run(main())
```

---

### Notes

- Some data (e.g., seasonal leaderboard, players) require additional parsing and will take longer to process.
- Do not abuse this API wrapper for any kind of malicious action.
