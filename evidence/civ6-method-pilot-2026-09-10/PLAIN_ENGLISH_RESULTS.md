# Civilization VI: seven-game results

We replayed **the same small Civilization VI scenario seven times**. Three games tested strategy revisions. Four new games compared direct Astra with Astra given the selected strategy.

**Correction: we did not use the Method CLI.** The strategies were Markdown instructions added to Astra's prompt. These results compare direct Astra with Astra given extra strategy instructions. They do not test the Method v3 system. Earlier reports called these instructions “Methods”; that label was misleading.

## What each game required

Every game started from the same save. We controlled Rome. We started with one city at population 4, a Warrior, a Scout, a Builder with three charges, and 50 gold. Mining, Pottery, and Animal Husbandry were already researched. There were no rival civilizations, city-states, barbarians, or tribal villages.

Astra had to:

1. Found two more cities and grow each to population 3 or more.
2. Reach at least 20 science per turn.
3. Keep the gold balance and gold income at zero or above.
4. Keep the food surplus at zero or above in all three cities.
5. Keep the original capital and hold all the conditions for five complete rounds.

The limit was 35 completed game turns, 20 minutes of play, and 1,500 game requests per game. The whole job also had a fixed stop time. No game reached a time or request limit. The third strategy reached the turn limit before it completed the five-round hold.

The game used Online speed, with quick movement and combat. Each game used a fresh Astra process (`gpt-6-astra`, medium reasoning), the same restricted game tools, and ChatGPT authentication. Astra made decisions during play in both groups.

## What we did

An Astra author wrote strategy v1. A fresh Astra player tested it. An author then used the result to write v2, which another fresh player tested. We repeated this once more for v3. We kept all three versions and their results.

| Strategy | Result | Completed game turns | Full hold rounds |
| --- | --- | ---: | ---: |
| v1 | Met the task conditions | 31 | 5 |
| v2 | Met the task conditions | 33 | 5 |
| v3 | Did not meet the task conditions | 35 | 3 |

We selected v1 because it was the best of these three trials. Neither revision improved on it. We then kept v1 unchanged for the comparison.

We ran four fresh games in this order: direct Astra, Astra with v1, direct Astra, Astra with v1. Both groups received the same task, tools, limits, and instruction to finish efficiently. Only the v1 group received the saved strategy instructions.

## Comparison results

| Run | Player instructions | Result | Game turns | Playing seconds | Game requests |
| ---: | --- | --- | ---: | ---: | ---: |
| 1 | Direct Astra | Met the task conditions | 33 | 292.60 | 120 |
| 2 | Astra with v1 | Met the task conditions | 33 | 308.47 | 136 |
| 3 | Direct Astra | Met the task conditions | 33 | 287.28 | 137 |
| 4 | Astra with v1 | Met the task conditions | 32 | 313.51 | 157 |

| Average per comparison game | Direct Astra | Astra with v1 |
| --- | ---: | ---: |
| Successful games | 2 of 2 | 2 of 2 |
| Game turns | 33.0 | 32.5 |
| Playing seconds | 289.94 | 310.99 |
| Game requests | 128.5 | 146.5 |
| Input tokens | 1,403,896 | 1,715,231 |
| Output tokens | 5,879.5 | 6,456.0 |

The saved strategy reduced the average game-turn count by half a turn. It took about 21 more seconds per game, used 14% more game requests, and used 22% more input tokens. This is a tradeoff. It is not a clear overall improvement.

Playing time excludes loading the starting save and checking the final save by loading it again. Input token counts include cached input. They are not counts of unique words or a dollar cost.

## Search cost and checks

Writing the three strategies took about three minutes of model execution. The three development games took about 17.7 minutes of play. Those stages, including the development save checks, took about 22.1 minutes. They used 425 game requests, 7,213,526 input tokens, and 25,121 output tokens. These search costs are separate from the four comparison games.

Earlier setup work and earlier baseline games are excluded from these costs. Supervisor time and tokens were not measured separately. No API-key calls were made. The subscription dollar cost is unknown.

We checked all seven recorded game traces. We also loaded each final save again and checked that its state matched the recorded final state. All 49 unit checks passed. No game was replaced because of an infrastructure failure.

These are calibration results. The passing records say `calibration_goal_met`; formal benchmark approval remains pending (`verified_pass` is false).

## What this shows

Direct Astra could complete this task. Extra strategy instructions did not improve the measured success rate. With only two comparison games per group on one map, we cannot claim a consistent advantage or performance on new maps.

We have a working Civ task, game controls, saved trials, and task checks. **We do not yet have a Civ comparison that runs candidates through the Method CLI.** That requires real Method v3 candidates, execution through `method3 validate` and `method3 run`, and new comparison games. No new games were run for this report.

The [detailed results](README.md) and [recorded measurements](results.json) retain the original trial identifiers. Their historical `method` labels refer to the strategy-prompt group in this seven-game pilot.
