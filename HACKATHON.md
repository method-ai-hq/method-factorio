# Hackathon scope

## Repository

This repository starts on 10 September 2026. It contains the new Factorio experiment. It does not include the private Method application repository or its history.

## Contribution record

| Component | Origin | Current status |
| --- | --- | --- |
| Goals, plan, design, and experiment rules | Created for this hackathon | Written; implementation settings remain open. |
| Factorio game | Existing third-party product | Not included. |
| Factorio Learning Environment | Existing third-party project | Installed locally at a fixed revision for the small test. Its code is not copied into this repository. |
| Method SDK and existing runtime | Existing Method work | Installed SDK 0.3.0 provides local authoring, execution, and checks. |
| Game adapter integration | New work here | Native macOS host, restricted HTTP and Unix connections, batched actions, separate server ports, limits, timing records, and terminal game saves. |
| Additional Method execution support | Existing SDK used | SDK 0.3.0 runs the agent operation and a separate check. No new SDK execution type was needed for the small test. |
| Policy improvement and evaluation | New work partly implemented | Fixed small-production check and saved-game inspection work. Policy improvement and scored rocket evaluation are not implemented. |
| Playing Methods and trial results | Created during this event | The same Method produced 20 new iron plates on two fresh maps. Both live game and saved-game checks passed. |

Update this table as work completes. For each result, identify the code commit, policy version, run settings, and evidence.

The first integration uses Factorio 2.0.77, FLE 0.4.8 at
`e2a829d22a635a9a111d21bf5523e09e903ae145`, Method SDK 0.3.0, and
`gpt-6-astra` through the user's Codex subscription. It uses FLE fast mode
with game speed 1 and a running simulation during model thinking. The action
interface rejects raw code and administrative commands. The existing Method
runtime still has local shell access; stronger process isolation is not claimed.

See [run instructions](docs/run-control-test.md) for setup and limits. The
small test establishes basic control and production, not complete control,
normal keyboard-and-mouse timing, a rocket launch, or improved performance.
The [reviewed results](evidence/control-test-2026-09-10/README.md) identify the
source commit, policy hashes, map settings, measured outcomes, model usage,
and failed setup attempts.

The first parallel [environment results](evidence/environment-validation-2026-09-10/README.md)
cover direct-agent, Method, matched FLE connection, and fixed-script tests.
The fixed script produced 20 plates in about 109, 22, and 6 seconds at game
speeds 1, 5, and 20. This does not establish full-game speed. All six scripted
production runs passed material checks and separate save reload checks.

The [advanced fixtures](evidence/advanced-control-2026-09-10/README.md) passed
selected recipe, research, oil, continuous-production, and prepared-launch
checks. They also found locked-recipe error handling and wrong-target launch
defects. These were operator-prepared fixtures, not agent-built factories or
fresh-world rocket wins. Failed setup and trial records remain saved.

The [test plan](docs/environment-validation.md) lists the remaining coverage.
The current work remains environment validation; policy search has not started.

The [policy-search goal prompt](docs/policy-search-goal.md) now specifies the next
60-minute search through the Method v3 CLI, with up to eight game worlds and four
Astra workers. It requires a new automatic-production evaluator, actual gameplay
recordings for every attempt, and separate development and final maps. This is a
written launch procedure. The new evaluator, recorder, and search are not claimed
as implemented or measured by publishing the prompt.

## Demo rules

The demo must identify features, code, and results created during the event. Explain dependencies as prior work. Do not present Factorio, FLE, or existing Method features as new inventions.

Show measured gameplay. Label replay, speed changes, partial runs, and human help. If the rocket goal is not reached, report that directly. Passing intermediate checks is not a completed game.

## Public release

Release our original source, Methods, documentation, and reviewed evidence under the repository license. Include exact dependency instructions when implementation exists. Do not copy game binaries, unlicensed assets, private application code, account files, credentials, or unrestricted local run logs.

The hackathon requires a public repository and a team of at most four people. These notes are based on the rules supplied by the project owner. They are not an organizer approval or a claim of eligibility beyond those rules.

## Method v3 setup attempt, 10 September 2026

The one-hour policy-search job stopped during setup. All 12 allowed setup
episodes were used. Six concurrent graphical clients failed to join within
60 seconds, so negative live evaluator checks remained incomplete. No policy
trial was scored. No winner, final comparison, or policy improvement is claimed.

New code adds a restricted supplied-kit host, exact game-tick evaluator,
separate save inspection, native game recording, a trial runner, and local
evidence indexing. These form an unapproved benchmark draft. The old evaluator
is unchanged. The public Method v3 runtime is prior work; its pinned CLI and
real model backend passed integration checks. Thirteen new Method documents
(11 candidates and 2 baselines) passed validation and remain untested in scored
play. The initial Method was frozen before gameplay feedback.

One operator reference produced 5 new plates and 5 new ore in each of three
fixed windows. Its native PNG footage and independent save reload passed. This
is a setup result, not a policy win. JPEG capture was added to reduce storage
but did not pass a live check before the stop. The known setup API estimate is
$0.00657; Codex authoring cost is unknown. See the
[reviewed setup report](evidence/policy-search-v3-2026-09-10/README.md).

## Headless optimization support

After the setup stop, the owner removed screen recording from optimization.
The host and trial runner now support a separate headless evidence contract.
Two simultaneous operator-reference worlds started in about 3.4 seconds each,
passed all three production windows, and passed separate save reload checks.
No graphical client or model call was used. These are code repair checks,
not scored policy results. See the [headless check report](evidence/headless-control-2026-09-10/README.md).

The scheduler now starts native graphics one client at a time, checks the tested
concurrency limit, preserves pending work, and permits one serial replacement
only when the fixed run settings authorize it. Eleven control tests passed.
Recorded demonstrations can link to an original headless trial; they remain
new executions with separate results. Higher headless capacity and full policy
integration remain unverified.

## Completed headless comparison, 10 September 2026

The new job completed a matched comparison at two-world capacity. It used
18 setup episodes, then 15 development trials and four final trials under
benchmark version 2. Two earlier version 1 attempts remain separate: one
passed, and a scheduler storage fault stopped the other. The full panel was
rerun after two live repair checks. The old job remains unchanged.

The direct agent passed two of three development maps. The frozen initial
Method and all three candidate Methods passed all three maps. The fixed
ranking selected the existing immutable `p10-direction-retry` Method. No
policy was rewritten after feedback. The initial and selected Methods each
passed both unseen final maps. Mean full final time was 51.78 seconds for
the initial Method and 9.06 seconds for the selected Method. This small sample
supports a measured time difference under the declared supplied-kit rules.
It does not establish a rocket launch or a general success rate.

New integration work binds game tools to the assigned endpoint, checks full
runtime evidence and request limits, records exact commands and source hashes,
and tolerates temporary files removed during game shutdown. The scored code
is commit `b25d4303cbe7e29a4c21fbab3e8a237fbe97e341`. A later offline test found
a separate failure-status/process-exit race. Its repair passed all 40 offline
tests. No game or API call ran after that repair, so the new scheduler code
has no live-scoring approval.

The known API estimate is $2.497554 for 161 requests. Usage is known for
160 responses. One interrupted request, cache-write charges, and subscription
authoring cost remain unknown. The selected Method used no execution-time
model calls. No credits were redeemed or weights trained. No screen recording
was made. Full local traces and terminal saves remain saved; all terminal-save
checks passed, including a later check for the interrupted attempt.

See the [reviewed report](evidence/headless-policy-search-2026-09-10/README.md)
for Methods, exact commands, measurements, limitations, and source versions.
Later recorded demonstrations require a separate attempt and time allowance.

## Civ 6 experiment design

A separate [Civ 6 design](docs/civ6/EXPERIMENT.md) now specifies two competing
Method design groups, fixed paired hill-climbing gates, and held-out final
games. Its [validator contract](docs/civ6/VALIDATOR.md) specifies trusted game
evidence, independent save inspection, access boundaries, and negative tests.
The execution-lock template is blocked pending tested components and operator
budgets. This is design work; no Civ 6 policy search, live game validator, or
fair direct agent-versus-agent match is claimed. The installed upstream MCP
and Civilization VI are prior work. Factorio's experiment is unchanged.

## Short Civ 6 task options

The owner selected continuous single-player search as the direction. The new
[task options](docs/civ6/SHORT_TASK_OPTIONS.md) compare economic expansion, city
capture, industry, and recovery tasks. They propose a three-city research
economy, an exact state-and-history verifier, and calibration for a 5–10 minute
trial target. This is design work. No task difficulty, runtime, live verifier,
or Civ policy improvement has been measured. The earlier full-game competition
proposal is retained as history.

## Continuous feedback search, 10 September 2026

A continuation created 16 new Method v3 versions from actual development
results and completed 57 attempts: 52 passed and five failed. All trials
closed before the existing 18:20:26 UTC search stop. The full job used 78 of
120 trial slots and 29 of 32 frozen policy slots. No limit or validator changed.
The executed validator source remained commit
`b25d4303cbe7e29a4c21fbab3e8a237fbe97e341`.

In a declared paired recheck on the three development maps, starting Method
p10 and candidate p20 each passed all three maps. P20 used 10 actions and
loaded nine coal, compared with 13 actions and 130 coal for p10. Mean full
time was 10.11 seconds for p20 and 9.82 seconds for p10. This result does not
show a speed improvement. Separate Factorio work was active during part of
the search, which limits wall-time comparisons.

The later p27 Method checks one new plate before handoff and uses an exact
internal Method check. It passed three maps with 12 actions and nine coal.
These new Methods have no unseen-map final result. The earlier final
comparison remains separate. This is a supplied-kit production test, not a
rocket launch.

The five failures include three malformed batch-request tests, one runtime
setup failure, and one game process killed before its terminal save was
written. Failed records and linked replacements remain saved. One rejected
Method draft is also retained. Every passing attempt has a matching save
check. No execution-time model request or paid API call was made; subscription
authoring cost is unknown. No screen recording was made.

See the [continuous search report](evidence/continuous-policy-search-2026-09-10/README.md)
and the [new Method index](policies/continuous-v3/README.md) for hypotheses,
source hashes, exact commands, failures, checks, costs, and limits.

## StarCraft II environment setup, 10 September 2026

A separate [StarCraft II setup](environments/sc2/README.md) now fixes PySC2
and its dependencies in an isolated Python environment. The setup script checks
the official mini-game archive hash. Offline observation, step, reset, and
protocol action checks passed on macOS with Apple Silicon. The new bounded
live-control script retains actions, game loops, wall time, errors, and replays.

Battle.net is installed, but sign-in and the StarCraft II game install remain
open. No live StarCraft II game test, Method integration, policy search, match
win, or parallel capacity result is claimed. PySC2, Blizzard's API, the maps,
and the game are prior work. Only setup code and checks are new work here.
