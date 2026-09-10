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
