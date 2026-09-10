# First Factorio control test

The same Astra Method produced 20 new iron plates on two fresh maps. Both
results passed the live Method check, the fixed game-data check, and inspection
after loading the terminal save in a separate Factorio server.

| Run | Map seed | New plates | Playing requests | Playing request interval | Game time in that interval |
| --- | --- | --- | --- | --- | --- |
| method-001 | 44340 | 20 | 12 | 153.9 seconds | 153.9 seconds |
| method-002 | 44341 | 20 | 12 | 147.7 seconds | 147.7 seconds |

The request interval starts with the playing agent's first observation and
ends with its final production observation. It excludes setup, the Method
connection check, report writing, and the independent check. Total game time
from host readiness to the final host observation was 330.2 seconds for the
first run and 242.4 seconds for the second. The first includes a failed Method
connection check and its replacement attempt. These are small demonstrations,
not a controlled performance comparison or a reliable success-rate estimate.

## Procedure and setup

Source commit: [`71cae21376589810eb480c22a1b2dbc023440ab6`](https://github.com/method-ai-hq/method-factorio/commit/71cae21376589810eb480c22a1b2dbc023440ab6).
The policy, host, API guide, and fixed check hashes were identical in both runs.
Their hashes and the final save hashes are in [results.json](results.json).

- Method: [iron-plates-v1.method](../../policies/iron-plates-v1.method).
- Model: `gpt-6-astra`, through Codex CLI 0.153.0 signed in with ChatGPT.
- Method SDK: 0.3.0. Python: 3.12.11.
- Factorio: 2.0.77, native macOS ARM64 full installation, base game only.
- FLE: 0.4.8 at `e2a829d22a635a9a111d21bf5523e09e903ae145`.
- Fresh maps, no starting factory, no completed research, enemies disabled.
- Starting inventory: eight iron plates, one wood, one stone furnace, one
  burner mining drill, one pistol, and ten firearm magazines.
- FLE fast mode, game speed 1, game running during model thinking.
- Host limit: 20 minutes and 200 permitted actions. Action limit: 90 seconds.
- Method playing process limit: 12 minutes. Its instructions also limit it
  to 120 requests. No human gameplay actions occurred in either production run.

Astra received the goal and the action guide. It chose the mining and smelting
plan. It kept the eight starting plates in character inventory and left the
20 new plates in furnace output. The procedure was not changed between maps.

FLE uses programmatic actions. Its setup normally changes ore amounts,
research, and daylight. The host restored generated ore amounts, removed
pre-research, and restored the day cycle before recording the start. These
tests do not establish normal keyboard-and-mouse timing. Docker was opened
during setup inspection but was not used to run either game.

## Evidence

- [First run game evidence](method-001-game-evidence.json) and [agent report](method-001-agent-report.md).
- [Second run game evidence](method-002-game-evidence.json) and [agent report](method-002-agent-report.md).
- [Checks, settings, usage, and source hashes](results.json).

The JSON traces contain actual game observations. The game reported 20 iron
plates produced, 20 completed furnace products, and 20 iron plates in furnace
output. A separate server loaded each final save and returned matching
position, inventory, furnace state, research, production, and enemy count.
The agent reports describe its actions; they are not the external evaluator.

Raw logs, Method run records, original maps, and terminal saves remain in the
local ignored `runs/` folders. Game binaries, assets, saves, credentials, and
raw Codex context are not published. The terminal saves preserve the factory
for inspection; they do not yet support resuming the FLE playing process.

Model usage is recorded separately from game time. The first run used 685,231
input tokens, including 524,928 cached input tokens, and 3,977 output tokens
across its failed connection check, replacement check, playing operation, and
final check. The second used 631,417 input tokens, including 563,200 cached
input tokens, and 3,396 output tokens. These are the CLI's reported totals.
The user's subscription was used. There were no separate API calls, credit
purchases, or usage resets. A dollar cost for the subscription usage is unknown.

## Failed setup attempts retained

| Record | Outcome |
| --- | --- |
| integration-001 | Native server startup failed because a required server description was missing. No playing agent ran. |
| integration-002 | The selected HTTP port was occupied. The first save approach also exposed FLE functions that Factorio could not save. No playing agent ran. |
| integration-003 | The attempted paused checkpoint did not produce a save. No playing agent ran. |
| integration-004 | A remaining FLE tick callback called a function removed for saving. The game stopped. No playing agent ran. |
| integration-005 | Movement, crafting, and furnace placement changed the game correctly. Placement response conversion failed. A new observation confirmed the placement before any retry. The attempted save check failed. |
| method-001, first Method attempt | The connection check lacked the tool documentation path and stopped before gameplay. The corrected connection input was used in a new attempt. The Method and map state were unchanged. |

The final host uses Factorio's shutdown save after removing FLE runtime
functions and stopping their tick callbacks. Both final saves loaded correctly.
The basic control probe also rejected reset, raw evaluation, inventory grants,
and research administration through the HTTP interface.

## What remains untested

This establishes observation, movement, mining, placement, transfer into a
furnace, and small production through Method. A separate control probe also
checked hand crafting and actual inventory consumption. It does not establish
continuous automated production, fault recovery, research, electricity, full
game control, a rocket launch, or improvement over a direct agent.

The HTTP interface enforces its action list. The existing Method runtime gives
its agents shell access under the same macOS account. Stronger process
isolation is required before claiming protection against a hostile player.

See [the run guide](../../docs/run-control-test.md) to repeat the test.
