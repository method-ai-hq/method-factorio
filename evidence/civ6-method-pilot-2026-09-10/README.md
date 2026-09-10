# Civ economy Method pilot, 10 September 2026

The frozen Method passed both comparison runs. Direct Astra also passed both. The Method used 0.5 fewer game turns on average, with more playing time, game requests, and model tokens. This small pilot does not establish a consistent advantage.

The initial Method v1 remained best in development. V2 took more turns; v3 failed the full hold requirement. The search did not produce a revision that beat v1 in its development trial. All versions and results are retained.

## Fresh comparison runs

Each run used a fresh gpt-6-astra Codex process with medium reasoning and ChatGPT authentication. Both arms received the same task, tools, limits, and explicit efficiency goal. The Method arm also received the frozen v1 instruction policy. Each actor used live LLM reasoning during play. There were no outside hints during execution.

| Order | Arm | Task and save checks | Completed turns | Playing seconds | Requests | Input tokens | Cached input | Output tokens |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | direct | Passed | 33 | 292.60 | 120 | 1,284,859 | 1,207,936 | 6,127 |
| 2 | method | Passed | 33 | 308.47 | 136 | 1,816,898 | 1,717,376 | 6,375 |
| 3 | direct | Passed | 33 | 287.28 | 137 | 1,522,933 | 1,444,992 | 5,632 |
| 4 | method | Passed | 32 | 313.51 | 157 | 1,613,564 | 1,531,392 | 6,537 |

| Mean per run | Direct Astra | Frozen Method v1 |
| --- | ---: | ---: |
| Success | 2/2 | 2/2 |
| Completed turns | 33.0 | 32.5 |
| Playing seconds | 289.94 | 310.99 |
| Game requests | 128.5 | 146.5 |
| Input tokens | 1,403,896 | 1,715,231 |
| Output tokens | 5,879.5 | 6,456.0 |

The Method used 1.5% fewer game turns on average. It used 7.3% more playing time, 14.0% more requests, 22.2% more input tokens, and 9.8% more output tokens. These are measured tradeoffs, not proof of a repeatable gain.

Cached input is a subset of input tokens. Reported reasoning tokens are retained in the JSON and are not added to output tokens as a separate cost. Playing time excludes starting-save loading and the independent terminal reload check. Game turns and wall time are separate measures.

## Search and selection

| Version | Task and save checks | Completed turns | Full hold rounds | Playing seconds | Requests |
| --- | --- | ---: | ---: | ---: | ---: |
| v1 | Passed | 31 | 5 | 351.46 | 132 |
| v2 | Passed | 33 | 5 | 366.66 | 128 |
| v3 | Task failed; save matched | 35 | 3 | 342.52 | 165 |

An isolated Astra author wrote each version. Later authors received the previous Method and its actual trial evidence. The first author received only aggregate outcomes from the earlier direct baselines, not a winning action script. The playing actors received no prior trial history beyond the supplied Method.

The fixed selection order was success, fewer completed turns, fewer requests, then playing time. V1 was frozen before the first comparison run. No Method changed during comparison. The old direct baseline results were not substituted for fresh comparison trials.

Search used three author runs (180.28 seconds) and three development games (1060.64 playing seconds). Including the development save checks, these recorded stages took 22.07 minutes. Development games used 425 requests. Authoring and development together used 7,213,526 input tokens, including 6,769,024 cached input tokens, and 25,121 output tokens.

Search costs are separate from frozen execution costs. Earlier setup and direct baselines are excluded. Supervisor time and tokens were not measured separately. No API-key calls were made; subscription dollar cost is unknown, not zero.

## Fixed task and evidence

The start was the original population-4 Roman capital, Warrior, Scout, three-charge Builder, 50 gold, and three initial technologies. The objective stayed fixed: found two cities, grow each to population 3, reach at least 20 science per turn, keep gold balance and net income nonnegative, and keep food surplus nonnegative in all three cities for five complete rounds within 35 completed turns. Each run retained the original 20-minute play and 1,500-request limits, subject to the declared total job stop. No run hit its play-time limit, request limit, or the job stop. V3 reached the 35-turn limit without completing the hold.

All seven signed traces were checked again. All seven terminal save file hashes matched the recorded hashes, and all seven separate reload inspections matched the terminal states. The four comparison prompts were identical apart from the frozen Method. The recorded runner source hashes were identical across those four runs. All 49 unit controls passed. There were no infrastructure failures or replacement trials in this pilot.

Passing runs are marked `calibration_goal_met`; `verified_pass` remains false because the full benchmark release review is pending. The v3 failure is retained as `goal_not_met`, with only three full hold rounds. No result or success condition was changed to improve the report.

This is one map with two comparison trials per arm. It does not show performance on unseen maps, a reliable success-rate difference, or that fixed decision rules could not work equally well. No fixed-rule ablation was run. The extra map cases and combat work remain pending.

## Files

- [Measured results and provenance](results.json)
- [Fixed pilot plan](../../docs/civ6/pilot-20260910/README.md)
- [Job lock](../../docs/civ6/pilot-20260910/lock.json)
- [Selection record](../../docs/civ6/pilot-20260910/frozen.json)
- [Frozen Method v1](../../methods/civ6/pilot-20260910/v1.md)
- [Method v2](../../methods/civ6/pilot-20260910/v2.md) and [change notes](../../methods/civ6/pilot-20260910/v2-changes.md)
- [Method v3](../../methods/civ6/pilot-20260910/v3.md) and [change notes](../../methods/civ6/pilot-20260910/v3-changes.md)

The original saves, signed traces, private signing keys, and full model logs remain local under `runs/civ6-pilot-20260910`. They are not published. The JSON records file and save hashes for each trial.

After all checks, the original four community mod preferences were restored. Civ was left at the main menu. Future calibration runs must use the frozen profile's mod settings again. No new trial was started after the comparison.
