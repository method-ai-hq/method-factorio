# Civ 6 economy setup checks, 10 September 2026

The starting save and verifier components work on the installed Mac game.
This is a base-game calibration case. No successful playing Method or scored
benchmark result is claimed.

## Measured checks

| Check | Result |
| --- | --- |
| Starting kit | One population-4 capital, 50 gold, Warrior, Scout, three-charge Builder; no queued or stored production |
| Starting research | Mining, Pottery, Animal Husbandry complete; Writing absent |
| Effective rules | Base game; no community mods; official Aztec pack active |
| Initial save reload | Exact inspected state matched; deliberate live treasury marker was removed by loading |
| Read-only snapshot | About 0.32 seconds per observed read |
| Initial save write | 1.33 seconds including the stable-file check |
| Empty-turn control | 35 completed turns; zero playing actions; goal correctly failed |
| Sum of 35 turn steps | 36.66 seconds; mean 1.047 seconds; observed range 1.037–1.069 seconds |
| Capture and terminal save | 39.20 seconds |
| Full control and separate reload check | 86.16 seconds, including manual load-screen handling and operator delay |
| Live city event fixture | Founding and later removal both emitted the expected city ID and tile |
| Verifier control suite | 28 tests passed |

The terminal control had science 5.2265625, no self-founded new cities, gold
314.4375, net income 7.6015625, and capital food surplus 2. It did not meet the
task. These measurements use one normal graphical game with no recording.
No playing-model call or paid API call was made. Authoring cost is not measured.
These times do not predict a full policy's decision and action cost.

## Evidence files

- `profile.json`: exact local save hash, state hash, task targets, control limits.
- `start-state.json`: read-only state from the actual reloaded save.
- `empty-control.json`: reviewed result, timings, trace hash, terminal-save hash.
- `founding-event.json` and `removal-event.json`: live monitor event results.
- `source-hashes.json`: repository components and the installed MCP sources used.

The binary saves remain in the local game's `Saves/Single` directory. The final
start is `CivTask_Economy_Base_Start_v2.Civ6Save`. Its SHA-256 is
`1be8153bbb8295773be73979cf59426afacacf5627de4c5994082aaf9d9fc659`.
The raw signed control and its private key remain under
`runs/civ6-empty-control-20260910b`. Public hashes identify local evidence;
they do not provide third parties with authentication of private records.

The city fixture used an administratively supplied Settler at (28, 12), then
requested the normal founding operation. The monitor emitted `founded` for
city ID 131073 on that tile. An operator-only deletion of that temporary city
emitted `removed` for the same identity. Both actions were after the empty
control's terminal inspection, outside its trace. The original start was
loaded again afterwards. This fixture is an event test, not task completion.

## Failed setup checks retained

1. Multiple idle MCP servers competed for the single debug connection. Setup
   used one exclusive client. The local server now makes automatic popup
   polling opt-in, so idle desktop instances do not claim the connection.
2. The leader loading screen caused connection timeouts. Escape closed it.
3. A requested Gathering Storm ruleset loaded base rules. The entitlement check
   returned `OwnershipRequired`. The base-game profile records that difference.
4. Four community mods were active in the first generated world. A new world
   was made without them. The old setup saves were not overwritten.
5. The first save-file check used the wrong Mac directory. The save existed in
   the nested `Sid Meier's Civilization VI/Saves/Single` directory.
6. Save matching initially omitted `.Civ6Save`. Those load requests did not
   load the file. Matching was corrected; the treasury-marker test then passed.
7. `SetTech` alone left UI state stale. `SetResearchProgress` updated it. The
   corrected save was given a new name and checked after reload.
8. Several proposed inspection APIs were absent in this build. The final reader
   uses tested per-item production progress methods in InGame and reads exact
   values. It contains no queue repair or other game mutation.
9. The first 35-turn control stopped after three turns. An advisor tutorial
   paused turn advancement. Its signed partial traces and failure record remain
   under `runs/civ6-empty-control-20260910`. Tutorials were disabled, and the
   separate `20260910b` control completed all 35 turns.

Local setup diagnostics remain under `runs/civ6-setup-20260910`. These are setup
failures, not discarded Method trials. No failed result was changed to success.

## Limits

The verifier's positive histories are synthetic control tests. No legal
reference policy has yet achieved the task in the live game. The starting map
has not been certified as feasible or hard, and no multi-map corpus is ready.
A protected playing broker and complete action/ownership tests remain required.
The current verifier therefore never returns a scored `verified_pass`.

See [the operator guide](../../docs/civ6/RUN_ECONOMY_TASK.md) for commands, trust
boundaries, speed limits, and the remaining calibration work.
