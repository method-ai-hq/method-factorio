# Direct-agent and Method environment tests

Date: 10 September 2026. This tests the small production task, not policy search,
full control, continuous factory production, or rocket launch.

**Both baselines passed on both matched seeds.** Each run produced 20 new iron
plates, left them in furnace output, passed the unchanged external check, and
passed a separate saved-game check. No human selected a gameplay action.

## Matched results

All times are wall-clock seconds. Complete time includes game startup, agent work,
report writing, final checks, save, and shutdown. The separate save reload takes
place after this interval. Model calls and game simulation can overlap.

| Baseline | Seed | Start to verified goal | Complete trial | Requests | Action errors | Live and save checks |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| A: direct Astra | 44341 | 169.77 | 189.32 | 12 | 0 | Passed |
| A: direct Astra | 44342 | 460.33 | 504.12 | 12 | 0 | Passed |
| B: Method | 44341 | 196.46 | 579.87 | 14 | 0 | Passed |
| B: Method | 44342 | 226.79 | 279.13 | 14 | 0 | Passed |

A used one persistent Codex process. B used the unchanged
`policies/iron-plates-v1.method`: one playing operation, a connection check before
play, and a separate verification operation. A received the same playing
instructions and game guide. Its final response was plain text; B used the
existing Method output contract. Each B run made 12 playing requests, one
connection observation, and one final verification observation.

The direct run on seed 44342 recorded five Codex network reconnection errors.
Its first game request arrived 257.93 seconds after the game was ready. The
Method run on seed 44341 reached the goal early, then took much longer to finish
its report. Its playing operation took 513.74 seconds in total. That operation
has no recorded Codex transport error; the cause of its long delay is unknown.
These delays remain in the results.

The median complete time was 346.72 seconds for A and 429.50 seconds for B.
With only two runs per baseline, unequal delays, and shared machine load, this
is not a reliable estimate of Method overhead. One run per baseline met the
five-minute full-trial target. All four passed correctness for this small task.
We have not established reliable five-minute iteration.

## Method phases and usage

Phase times below use the recorded prompt and result file times. They include
tool execution and report writing; they are not pure model inference time.

| Method seed | Connection check | Playing operation, including report | Verification |
| --- | ---: | ---: | ---: |
| 44341 | 24.37 s | 513.74 s | 22.96 s |
| 44342 | 26.34 s | 215.47 s | 18.59 s |

| Baseline | Seed | Input tokens | Cached input tokens | Output tokens |
| --- | ---: | ---: | ---: | ---: |
| A | 44341 | 452,472 | 419,584 | 2,388 |
| A | 44342 | 663,016 | 641,280 | 2,807 |
| B | 44341 | 601,402 | 467,712 | 3,396 |
| B | 44342 | 728,681 | 629,120 | 3,758 |

Token counts come from actual Codex `turn.completed` events. Cached tokens are
part of the input count. B totals include all three Codex operations. Each
run's JSON has phase-level usage, including any extra fields supplied by Codex.
The runs used the owner's ChatGPT subscription. Separate API spending was zero;
per-run subscription cost is unknown. No credit reset or purchase was used.

## Preserved setup records

Three earlier records are separate from the matched comparison:

| Run | Result | Reason |
| --- | --- | --- |
| `parallel-20260910-ab-a-44340` | Infrastructure failure | Live state reached 20 plates. A runner bug stopped the game before the host saved the final state. No final save exists, so this is not a full pass. |
| `parallel-20260910-ab-b-44340` | Goal and saved-game checks passed; timing excluded | The controller finished. The supervisor then stopped the host alone to avoid the same save bug. The manual stop invalidates complete-time comparison. |
| `parallel-20260910-ab-a-44341` | Infrastructure interruption | The supervisor stopped this partly completed run to replace the faulty runner. Its clean save has zero new plates. The saved state matches the final state. |

The bug was in process shutdown. The runner sent a termination signal to the
host's whole process group, including Factorio. The corrected runner signals
only the host first. The host then records state and saves the game before it
stops Factorio. The game rules, playing policy, action guide, and evaluator did
not change. The original runner bytes remain in the local run records with the
same hash as the failed pilot.

## Conditions and files

- Base Factorio 2.0.77 and the pinned FLE revision in each run's settings.
- Fresh maps, no starting factory or research, enemies disabled.
- Initial inventory: eight iron plates, one wood, one stone furnace, one burner
  mining drill, one pistol, and ten firearm magazines.
- FLE fast mode enabled; game speed 1; simulation continues during model work.
- Host limit: 900 seconds and 200 requests. Playing limit: 720 seconds and 120
  requests. The batch had a 35-minute total wall-clock limit; corrected runs had
  a 22-minute sublimit. No further runs were started after the matched pair.
- Model: `gpt-6-astra`, through Codex with the same user configuration for A and B.
- Separate game servers. A and B lanes ran in parallel with other environment
  tests on the same Mac. Later seeds began as each lane became free. These are
  not measurements under isolated machine load.
- The action API excluded game administration. Codex still had same-account shell
  access. Strong process isolation is not established.

[summary.json](summary.json) lists every recorded attempt. Each run JSON contains
initial and final game state, settings, source hashes, token counts, action timing,
external check results, and saved-game check results when available. Raw model
prompts, transcripts, server logs, and game saves stay in ignored `runs/` folders.

[measured-runner.py](measured-runner.py) is the exact corrected runner used for
these four measured runs. After the games finished, the production runner gained
a small report guard for error responses with `state: null`. A synthetic failed
action confirmed that this case produces no false goal and retains unknown
usage. This report-only correction did not require another game run.

Run another bounded comparison with:

```sh
.venv/bin/python scripts/compare_agent_baselines.py --batch NEW-UNIQUE-NAME --seeds 44341 44342 --minutes 22
```

This command uses separate ports for A and B and refuses existing run names. Read
`docs/run-control-test.md` for the required local game, FLE, Method, and Codex setup.
