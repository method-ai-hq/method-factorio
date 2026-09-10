# Advanced game control tests

These fixed script tests found working controls and a wrong-target rocket
launch. They are environment checks. They are not agent trials, Method
comparisons, policy search, or fresh-world wins.

| Case | Latest result | Evidence |
| --- | --- | --- |
| Recipe choice and power | Passed | A solar-powered assembler made iron gears and consumed iron plates. v3: 0.340 seconds. |
| Locked recipe rejection | Failed | FLE selected a locked processing-unit recipe and returned success. The game kept the recipe disabled and reported `RECIPE_NOT_RESEARCHED`. This did not grant research or prove production of a locked item. v3: 0.120 seconds. |
| Normal research | Passed | FLE selected automation. The powered lab consumed 10 red science packs and completed it. v3: 5.221 seconds. |
| Missing research prerequisite | Passed | FLE rejected automation-3. No research was selected or granted. v3: 0.119 seconds. |
| Basic oil recipe | Passed | FLE selected basic oil processing. The refinery consumed 100 crude oil and produced 45 petroleum gas. The operator supplied the input fluid. This does not test pipes, oil extraction, or a complete oil chain. v3: 0.530 seconds. |
| Prepared rocket launch | Passed | Normal FLE item transfers supplied the silo. FLE launch caused one trusted `on_rocket_launched` event. v3: 17.709 seconds, 205 playing calls. This is a prepared fixture launch only. |
| Wrong rocket target | Failed | The call named `(0,1000)`, where no silo existed. FLE launched the ready silo at `(0.5,0.5)` and returned success with a null result. The trusted launch event count became one. v5: 17.077 seconds including preparation. |
| Continuous iron production | Passed | An operator-built drill, belts, inserter, and furnace produced 5, 5, and 5 new plates in three exact 1,200-tick windows after a 600-tick warmup. No transfers occurred during the windows. v5: 3.795 seconds. |

The wrong-target result is a release blocker for unrestricted use of the FLE
launch tool. Its Python client sends `(player_index,x,y)`, but its Lua server
accepts `(x,y)`. The server also searches within 1,000 tiles and does not check
the engine launch return value. The origin launch pass does not establish
safe target handling.

All case times include fixture setup and independent game reads. They exclude
the common game startup and final save. They are single cases, run while other
native games were active. They are not stable latency or throughput estimates.
Requested game speed was 20. E2 used exact tick stops; the other cases used
continuous simulation. No model calls or paid API calls were made.

## Setup and provenance

- Native Factorio 2.0.77; base game only, enemies disabled, seed 44340.
- FLE revision `e2a829d22a635a9a111d21bf5523e09e903ae145`; no FLE changes.
- The operator supplied inventory, machines, prerequisites, terrain, and solar
  power in declared fixtures. Solar power uses normal panels and substations.
- The rocket fixture received 1,000 processing units, 1,000 low-density
  structures, and 1,000 rocket fuel through the character inventory. Repeated
  normal FLE transfers filled the limited silo input slots. The operator added
  one satellite after the rocket became ready.
- Every run saved its criteria and script hash before starting. Each case
  saved and hashed its paused initial game state before playing actions.
- Independent RCON reads checked the game state. The launch check used a
  test-owned game event counter. These are live checks saved as JSON; this
  report does not claim a separate reload check for each intermediate case.
- Administration and measurement stayed in the test process. No unrestricted
  RCON interface was given to a playing agent.

The [summary](summary.json) lists every run and result file. Each run folder
contains its frozen criteria, interface audit, timing, initial and final
states, and action states. Repeated large FLE return objects were removed from
the published action records; checks, errors, timing, and state were retained.
Raw logs and game saves remain in ignored local run folders.

## Failed attempts retained

| Run | Result and reason |
| --- | --- |
| v1 | Six setup errors. The helper expected an RCON response string for commands that returned no text. Raw records say `failed`; the reviewed classification is `setup_error`. No playing action ran. |
| v2 | Four passes; locked-recipe rejection failed. Rocket preparation timed out at 90 seconds because one insertion did not fill all 1,000 requested items. The game input capacity limited the transfer. |
| v3 | Five passes, including prepared rocket launch; locked-recipe rejection and continuous production failed. The continuous fixture inserter pointed the wrong way. |
| v4 | Continuous production still failed. Added position reads showed that the inserter picked up from the furnace side and dropped toward the belt. |
| v5 | The corrected continuous fixture passed. The new wrong-target launch test failed because it launched the other silo. |

No success condition was changed to fit a result. Changes to setup and the
script created new runs; previous runs remain available. Total run times,
including startup and cleanup, were 10.80, 108.24, 37.44, 13.83, and 30.88
seconds for v1 through v5. These runs used different case sets and setup
versions, so their durations are not a speed comparison.

## Control coverage limits

| Family | Adapter result | Current HTTP controls | Agent success in these tests |
| --- | --- | --- | --- |
| Recipe selection | Basic recipe and oil cases passed; locked recipe rejection failed | Not exposed | Not tested |
| Research | Selection, progress, completion, and prerequisite rejection passed | Not exposed | Not tested |
| Power | Solar-powered machine and lab operation passed; construction and faults not tested | Placement exists; complete supply not tested | Not tested |
| Fluids | Basic refinery conversion passed; extraction and pipe transfer not tested | Complete fluid control not tested | Not tested |
| Rocket | Prepared origin launch passed; wrong-target rejection failed | Not exposed | Not tested |
| Automatic item flow | Operator-built drill-to-furnace chain passed | Construction exists; agent-built chain not tested here | Not tested |
| Trains and schedules | No dedicated schedule control in audited agent tool set | Unsupported | Not tested |
| Circuit conditions | No dedicated condition control in audited agent tool set | Unsupported | Not tested |
| Combat and equipment | No dedicated weapon or equipment control in audited agent tool set | Unsupported | Not tested |
| Robots, modules, advanced production, scale, and recovery | Not tested by these probes | Incomplete or not tested | Not tested |

Full base-game control and full rocket-route coverage are not established.
The next release should check exact recipe and rocket targets, reject invalid
actions before changing state, and expose the tested normal research controls.

## Run again

From the project root, use a new run name:

```sh
.venv/bin/python scripts/capability_probe.py --run advanced-new-run
```

For the short continuous-production fixture only:

```sh
.venv/bin/python scripts/capability_probe.py --run continuous-new-run --cases continuous_iron
```

The default native ports are RCON 27205 and UDP 34305. The runner creates a
private run directory and random RCON password, then shuts down its own game.
It does not use Docker or a model service.
