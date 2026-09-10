# Civ work left after the short pilot

The owner requested that work finish within less than one hour, then asked
for final cleanup within about five to ten minutes. The short pilot is
complete. This handoff preserves the wider goal; it does not certify that
the wider goal is complete or authorize a new experiment window.

## Completion audit

| Required work | Current evidence and status |
| --- | --- |
| Restricted economy player API and isolated Astra actors | Implemented and used in the checked baseline and pilot runs. Basic context isolation probes passed. Full benchmark release review remains pending. |
| Fixed economy target and original starting kit | One frozen profile exists: `profiles/economy-nearby-food-1.json`. The original save has checked legal completions. |
| Three economy map families | Incomplete. Only the first profile is frozen. A second map candidate was created, but its intended planning tradeoff and feasibility are not certified. The third case is absent. |
| Two direct baselines per economy map | The first map has two checked original baselines. Four baselines on the other two maps remain. Later same-map pilot comparisons do not replace those missing cases. |
| Combat starting state and ordinary AI opponent | Design and setup drafts exist. No calibrated combat start or legal completion witness exists. |
| Combat acquisition, retention, hold, and save verifier | Python logic and synthetic controls exist. The live capture event fixture, broker connection, complete protected snapshot, and terminal checks remain. |
| Direct combat baselines | Not run. |
| Short same-map Method search and comparison | Complete. Three versions were tested; v1 was frozen. Both comparison arms passed 2/2 runs. See the published report. |
| Runtime LLM contribution compared with fixed rules | Not tested. Live Astra execution is present, but no fixed-rule ablation was run. |

## Preserved draft work

`civ6_cases.py` provides operator commands for new worlds, map inspection,
kit preparation, and profile freezing. New-game, map-read, and preparation
paths were used for map seed 6100920. The save is named
`CivTask_Economy_Campus_6100920_Start_v1`. Its name does not establish that
it meets the proposed Campus tradeoff. It was not used in a scored trial.
The map dump remains local in `runs/civ6-map-design-20260910`.

`civ6_new_game.lua` adds optional map/game seeds and a two-player setup flag.
The new economy seed path ran successfully. The combat flag is unvalidated.

The three `civ6_combat_*` Lua drafts are not connected to the broker. Before
using them, validate all city and unit setup entries before any mutation,
record the AI kit and war state, connect the protected role snapshot, and
check actual combat transfer events. Complete normal player actions needed
for combat, including city health observations and the keep-city choice.
Do not treat synthetic verifier traces as live feasibility evidence.

## Resume conditions

Do not restart the completed pilot or extend its 21:04:30 UTC stop on
10 September 2026. The next experiment needs a new owner-set time allowance.
Use the same declared rules unless the owner adopts a new profile. Preserve
all existing successes, failures, invalid traces, and source versions.

At handoff, all seven pilot actor processes were confirmed exited. The four
original community mod preferences were restored, and Civ was left at the
main menu. A future trial must restore the calibration mod settings before
loading and checking its frozen start. Do not connect a second operator
while the broker owns the FireTuner connection.

The first next experiment step is to finish and freeze the two remaining
map cases, obtain legal completion evidence, and run their missing baselines.
The combat work then needs live fixture checks and calibrated cases before
its baseline panel. Any new Method comparison should retain the fixed task,
record search costs separately, and test the frozen Method on unseen cases
before making a general performance claim.

See [the pilot report](../../evidence/civ6-method-pilot-2026-09-10/README.md)
and [the baseline plan](BASELINE_PLAN.md) for measured results and limits.
