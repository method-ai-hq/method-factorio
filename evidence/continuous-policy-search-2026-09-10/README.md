# Continuous Method v3 policy search

The search stopped at the existing 18:20:26 UTC limit. It created **16 new Method versions** from game feedback and completed **57 attempts: 52 passes and five failures**. Every trial closed before the search stop. The job used 78 of 120 trial slots and 29 of 32 frozen policy slots. No limit was extended.

The paired development recheck found a material and action reduction, but **no speed gain**:

| Method | Passes | Mean full time | Actions | Loaded coal |
| --- | ---: | ---: | ---: | ---: |
| Starting Method p10 | 3/3 | 9.82 s | 13 | 130 |
| Candidate p20 | 3/3 | 10.11 s | 10 | 9 |

[Method p20](../../policies/continuous-v3/p20-fuel-reserve-check/p20-fuel-reserve-check.method) uses returned state, points the route toward the player, moves only within placement reach, and verifies fuel inserts. It keeps one coal beyond the measured use in each machine. It was selected for this paired recheck from the earlier three-map panels. The six paired trials were declared before execution. The higher p20 time does not support a speed improvement. See the [paired records](paired-recheck.json).

[Method p27](../../policies/continuous-v3/p27-serial-verified-production/p27-serial-verified-production.method) also checks actual startup production and uses an exact internal Method check. It passed all three development maps with 12 actions and nine loaded coal. This is an alternative with stronger internal evidence; it was not in the paired recheck.

## What changed from feedback

- p12 removed redundant observations and rotation: 10 actions instead of 13.
- p13 failed because its batch request had the wrong shape. p14 returned to separate fuel actions.
- p15 showed that drill placement needs a player within 10 tiles. p16 reduced movement but caused downstream reach errors. p17 pointed the route toward the player and avoided those errors on the three maps. p18 repaired a distance error without rebuilding the route.
- p19 used observed fuel consumption and passed with six loaded coal. p20 added one reserve coal per machine and checked each insert, for nine total.
- p21 checked actual route geometry and returned a boolean construction result. An offline negative test confirmed that its internal check rejects failed construction. Its first invalid Method draft was saved before repair.
- p22 corrected the batch envelope and checked each response. p23 and p24 batched placements and checked the resulting geometry. They passed, but did not establish a speed gain.
- p25 checked for one new plate before handoff. It needed five observations. p26 delayed the first check and used two observations. p27 combined that check with the simpler serial construction path.

Every [new Method folder](../../policies/continuous-v3/README.md) contains its parent, hypothesis, input trials, source, validation result, and hash record. No frozen version was edited after its tests. The complete version table includes failed candidates:

| Method | Passes | Mean ranked time | Actions | Loaded coal |
| --- | ---: | ---: | ---: | ---: |
| [p10-direction-retry](../../policies/search-v3/bundles/p10-direction-retry/p10-direction-retry.method) | 4/4 | 9.64 s | 13–13 | 130 |
| [p12-state-reuse](../../policies/continuous-v3/p12-state-reuse/p12-state-reuse.method) | 3/3 | 8.86 s | 10–10 | 130 |
| [p13-late-fuel-batch](../../policies/continuous-v3/p13-late-fuel-batch/p13-late-fuel-batch.method) | 0/3 | 330.00 s | 40–40 | 0 |
| [p14-late-fuel-serial](../../policies/continuous-v3/p14-late-fuel-serial/p14-late-fuel-serial.method) | 3/3 | 8.60 s | 10–10 | 130 |
| [p15-place-before-move](../../policies/continuous-v3/p15-place-before-move/p15-place-before-move.method) | 3/3 | 8.59 s | 12–12 | 130 |
| [p16-move-to-reach](../../policies/continuous-v3/p16-move-to-reach/p16-move-to-reach.method) | 3/3 | 8.66 s | 10–22 | 130 |
| [p17-face-player](../../policies/continuous-v3/p17-face-player/p17-face-player.method) | 3/3 | 8.70 s | 10–10 | 130 |
| [p18-local-reach-repair](../../policies/continuous-v3/p18-local-reach-repair/p18-local-reach-repair.method) | 3/3 | 10.15 s | 10–12 | 130 |
| [p19-observed-fuel](../../policies/continuous-v3/p19-observed-fuel/p19-observed-fuel.method) | 3/3 | 8.51 s | 10–10 | 6 |
| [p20-fuel-reserve-check](../../policies/continuous-v3/p20-fuel-reserve-check/p20-fuel-reserve-check.method) | 6/6 | 9.27 s | 10–10 | 9 |
| [p21-checked-handoff](../../policies/continuous-v3/p21-checked-handoff/p21-checked-handoff.method) | 3/4 | 88.99 s | 10–10 | 9 |
| [p22-correct-batch-envelope](../../policies/continuous-v3/p22-correct-batch-envelope/p22-correct-batch-envelope.method) | 3/3 | 8.68 s | 10–10 | 9 |
| [p23-batch-route-pair](../../policies/continuous-v3/p23-batch-route-pair/p23-batch-route-pair.method) | 3/3 | 8.70 s | 10–10 | 9 |
| [p24-batch-full-route](../../policies/continuous-v3/p24-batch-full-route/p24-batch-full-route.method) | 3/3 | 9.40 s | 10–10 | 9 |
| [p25-observe-startup-production](../../policies/continuous-v3/p25-observe-startup-production/p25-observe-startup-production.method) | 3/3 | 10.59 s | 15–15 | 9 |
| [p26-delayed-production-check](../../policies/continuous-v3/p26-delayed-production-check/p26-delayed-production-check.method) | 3/3 | 9.43 s | 12–12 | 9 |
| [p27-serial-verified-production](../../policies/continuous-v3/p27-serial-verified-production/p27-serial-verified-production.method) | 3/3 | 9.26 s | 12–12 | 9 |

Every failure receives 330 seconds in the fixed ranking. This exploration table contains different trial counts and is not a matched speed comparison. The first p10 runtime setup failure is kept separately from its policy executions. The p21 missing-save failure stays in its row, including the penalty.

## Fixed task and evidence

The search used the unchanged, validated version 2 source at `b25d4303cbe7e29a4c21fbab3e8a237fbe97e341`. All original frozen file hashes still match. A separate execution folder let this work use the tested source without changing the current workspace scheduler. The validator, kit, maps, game settings, limits, and ranking did not change.

The supplied-kit task requires a connected drill, belt, inserter, and furnace. After 600 warmup ticks, each of three exact 1,200-tick windows must produce five new plates and mine five new ore. Policy actions stop during those windows. Every passing trial has a matching independent terminal-save check.

Each trial used one headless world, game speed 20, and running game time during policy execution. There was no video. A separate Factorio task was observed during part of this search and may have affected wall time. No process from that task was changed. These are small supplied-kit tests, not rocket launches or a general success-rate estimate.

Only the three existing development maps were used. The earlier final comparison remains unchanged. These new Methods have no unseen-map final result.

## Failures and recovery

The first p10 attempt stopped before policy execution because the source copy lacked the runtime Git metadata. Its save check passed. Connecting the unchanged pinned runtime fixed the launch; one linked replacement passed. Frozen source hashes still matched.

One p21 test lost its game process to SIGKILL before the terminal save was written. The sender is unknown. The live production windows passed, but the attempt remains a failure because its save evidence is missing. New trials paused for diagnosis. One linked diagnostic replacement passed. The original records were not replaced, and no validator source changed. See the [failure](save-failure.json) and [replacement link](replacement.json).

The three p13 game failures and one rejected p21 Method draft also remain saved. An [offline negative check](internal-check-negative.json) showed that the repaired p21 internal Method check fails when game actions fail. This check used a local test endpoint and no Factorio launch.

## Cost, records, and stop

These code Methods made **zero execution-time model requests**. Known additional API execution cost is **$0**. Subscription authoring cost is unknown. No credits were redeemed and no weights were trained.

Full action/state traces, Method execution records, errors, measurements, and available terminal saves remain in the local job folder. The first setup failure had no Method execution record because the revision check stopped it first. The p21 SIGKILL attempt has no terminal save; that omission is explicit in its failed result.

The [verification record](verification.json) confirms all policy hashes, Method validation, unchanged validator hashes, matching saves for all passes, and no remaining process owned by this continuation. The [stop record](stop.json) preserves the original limits. There is no deployment target in this repository.

[Complete attempt data](summary.json). [Exact original commands](attempts.md). [Original validator freeze](benchmark-freeze.json). [Runtime repair](repair.json).

The saved commands have expired deadlines. Repeating these tests requires a separately authorized execution allowance and a validated source freeze; the commands do not extend this job.
