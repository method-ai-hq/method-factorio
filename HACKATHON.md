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
bounded search, including a new automatic-production evaluator, actual gameplay
recordings for every attempt, and separate development and final maps. This is a
written launch procedure. The new evaluator, recorder, and search are not claimed
as implemented or measured by publishing the prompt.

## Demo rules

The demo must identify features, code, and results created during the event. Explain dependencies as prior work. Do not present Factorio, FLE, or existing Method features as new inventions.

Show measured gameplay. Label replay, speed changes, partial runs, and human help. If the rocket goal is not reached, report that directly. Passing intermediate checks is not a completed game.

## Public release

Release our original source, Methods, documentation, and reviewed evidence under the repository license. Include exact dependency instructions when implementation exists. Do not copy game binaries, unlicensed assets, private application code, account files, credentials, or unrestricted local run logs.

The hackathon requires a public repository and a team of at most four people. These notes are based on the rules supplied by the project owner. They are not an organizer approval or a claim of eligibility beyond those rules.
