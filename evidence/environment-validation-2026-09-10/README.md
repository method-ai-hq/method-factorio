# Parallel environment test results — 10 September 2026

**Small production works. Full game control is not ready.** All three agent
baselines passed the 20-new-plate task on two matching seeds with the corrected
runner. The fixed script was fast at game speed 20. Advanced tests found a
wrong-target rocket launch and incorrect success reporting for a locked recipe.

These are environment tests. No policy search or fresh-world rocket episode
was run. Native Factorio was used; Docker was not required. Astra used the
Codex ChatGPT subscription. No separate model API calls were made.

## Agent comparison

Same seeds 44341 and 44342, same goal and starting inventory, game speed 1,
FLE fast mode, no starting research or factory, enemies disabled, and a running
game during thinking. Each passed the unchanged independent production check
and a later inspection after loading its terminal save.

| Baseline | Matched runs | Start to verified goal | Complete trial |
| --- | --- | ---: | ---: |
| [A: direct Astra](agent-baselines/README.md) | 2 passed / 2 | 169.8–460.3 s | 189.3–504.1 s |
| [B: fixed Method](agent-baselines/README.md) | 2 passed / 2 | 196.5–226.8 s | 279.1–579.9 s |
| [C: matched FLE connection](fle-connection/README.md) | 2 passed / 2 | 161.9–179.7 s | 216.6–493.1 s |

“Complete” includes startup, model work, report writing, host cleanup, and the
external check. It excludes the later save reload. B also includes Method
connection and model verification steps. Game time and token counts are kept
separately in the [per-run summary](matched-agent-summary.json).

A seed 44342 had five network reconnect errors before gameplay. B seed 44341
and C seed 44341 had long delays after reaching the goal. The records do not
identify the cause of those report delays. Only two matched seeds were run,
with concurrent load on the same Mac and subscription. These data do not
establish a stable ranking or isolate Method overhead.

A and B used the current HTTP controls. C used a Unix socket to the same FLE
actions and full state checks. C did not test the full native FLE interface.
The same playing instruction supplied the goal without a factory recipe.
The Method and fixed success evaluator were not changed.

## Fixed-script speed and control checks

[D: the full brief and measurements](scripted/README.md) cover six production
runs and two batching runs, with no model calls. All eight terminal saves
loaded and matched the recorded game state.

| Requested game speed | HTTP: 20 new plates | Unix: 20 new plates |
| --- | ---: | ---: |
| 1× | 109.29 s | 109.25 s |
| 5× | 22.24 s | 22.51 s |
| 20× | 5.92 s | 5.91 s |

These production times exclude startup and later probes. Startup took
9.58–12.23 seconds. Measured simulation rates were about 60, 300, and 1,200
ticks per second in the small test worlds. The fixed speed-1 evaluator passed
both normal-speed runs. It rejected the four accelerated runs only on its
unchanged speed rule; their separate material checks and save checks passed.

The scripted series recorded 3,036 actions, including 16 deliberate
rejections. Both connections passed 30 checked drill rotations, placement and
pickup checks, rejected-action checks, and recovery after a deliberately lost
craft response. The 1,000-observation HTTP sample had a 33.37 ms median and
39.90 ms p95 response time. This was a short observation test, not a long
large-factory reliability test.

Batches of 1, 10, and 50 kept a state check after every action. Both connections
passed 300 observation actions and 300 furnace placement/pickup actions across
those batch sizes. A craft → denied action → craft batch stopped at the error
without repeating the first craft. Batching gave little local speed gain.
Whether it reduces agent inference or tool-call overhead was not measured.

## Advanced controls

The [advanced brief and all 22 case results](../advanced-control-2026-09-10/README.md)
record successes, setup errors, and failed cases from five native fixture runs.
No model calls were used.

- Powered recipe production, normal research, research prerequisite rejection,
  and basic refinery conversion passed in prepared fixtures.
- A prepared silo launched through FLE and raised a trusted game launch event.
- A request at an empty target position also launched the origin silo. This
  wrong-target mutation failed the rejection test.
- FLE selected a locked recipe and returned success. The game kept production
  locked. This is an error-reporting defect, not a research grant.
- An operator-built mining and transport chain produced 5, 5, and 5 new plates
  in three exact 1,200-tick windows without transfers during measurement.

These passes do not show agent construction of those systems. Recipe choice,
research choice, and rocket launch are still absent from the current A/B/C
playing interface. Trains, circuits, combat, robots, large factories, active
save resume, and a complete rocket route remain unsupported or untested.

## Retained failures and provenance

The first agent runner signalled the whole game process group during cleanup.
A seed 44340 reached 20 plates but lost its final snapshot/save and failed the
full check. An A seed 44341 attempt was stopped during runner repair and is
retained as an interrupted trial. B and C seed 44340 were saved with operator
cleanup; they passed game/save checks but are excluded from complete-time
comparison. New runs with the corrected shutdown used seeds 44341 and 44342.
No failed trial was replaced or counted as a matched success.

The advanced brief preserves setup errors, an incomplete silo fill, and two
incorrect continuous-production layouts. Corrected fixtures used new run
names with unchanged success criteria. Later reporter fixes are identified
in each baseline brief; they did not change the recorded game outcomes.

Factorio 2.0.77, FLE 0.4.8 at
`e2a829d22a635a9a111d21bf5523e09e903ae145`, Method SDK 0.3.0,
Codex CLI 0.153.0, and `gpt-6-astra` were used. The source base was repository
commit `0be55bd`; new and revised test files were frozen by SHA-256 before
execution. Individual records identify those hashes and settings. Raw runs,
model events, native logs, and game saves remain in ignored local `runs/`
folders. Reviewed state, timing, checks, and evidence hashes are published here.

## Next step

Keep native Factorio and the HTTP connection for the next environment stage.
The Unix connection showed no useful production-time gain. Use the measured
20× setting as a candidate for small development trials, then measure a larger
factory and compare state at matching game ticks before choosing full-episode
settings. Model and report delays also need measurement; speeding the simulator
alone will not remove them.

First fix exact rocket targeting and locked-recipe error handling. Then expose
normal recipe and research controls through the restricted interface and run
agent-built continuous production, power, oil, and rocket-route tests. Fast
short trials are established; reasonably fast complete games are not yet
established. See the [remaining test plan](../../docs/environment-validation.md)
and [run commands](../../docs/run-environment-validation.md).
