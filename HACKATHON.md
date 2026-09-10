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

## Harder automatic-science task

The new [science task](docs/science-task.md) requires automatic red and green
science production from mined iron and copper. It adds multiple assembly
stages, ingredient routing, and power. Equipment is supplied; this task does
not include research or building equipment from raw materials.

New original code provides a separate headless host, restricted playing
actions, exact-tick measurements, material-buffer clearing, a fixed validator,
and independent terminal-save verification. The old iron-plate evaluator and
its trial records are unchanged. No policy-search result on the science task
is claimed.

All ten real-game checker cases passed: the complete reference factory was
accepted, and nine incomplete or invalid attempts were rejected. Every
terminal save matched a separate reload. All 46 offline test methods passed.
The reference used the HTTP playing interface and made 15 red packs and
12–13 green packs per measured game minute. See the
[reviewed checker evidence](evidence/science-validator-2026-09-10/README.md)
for source hashes, exact measurements, earlier setup faults, and limits.
No paid model API calls or screen recordings were used for these checks.

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

## Final closure of the supplied-kit search

The owner marked this search finished. The [final report](evidence/policy-search-final-2026-09-10/README.md)
compares the direct Astra agent, initial and selected Methods, the 16-version
hill climb, and the deterministic reference checks. The headless job retained
78 attempt records; these are not pooled into a general success-rate estimate.

The report separates the earlier 5.71-fold full-time difference on two unseen
maps from the later hill climb, which did not show a speed gain. It identifies
the direct agent's restricted Python interface and the absence of a matched
scored reference-script comparison. The 93.1% reduction was in coal loaded,
not a measured reduction in coal burned. No new game or paid call was needed
for this final report. The original validator, Methods, and results remain
unchanged.

## Civ 6 economy setup, 10 September 2026

Update: the first [full-budget direct Astra baseline](evidence/civ6-baselines-2026-09-10/README.md)
passed the task, trace, and independent save checks. It finished in 35 turns
and 331.18 seconds of play, with 24.234375 science and a five-round hold. This
is a legal completion witness for the starting case, while the full benchmark
remains in calibration. Earlier [interface failures](evidence/civ6-interface-2026-09-10/README.md)
remain separate. A second valid baseline passed in 33 turns and 335.96 seconds
of play, including the full hold and independent save check. An intervening
attempt remains invalid due to a stale completed-building production record;
it is not counted as a gameplay failure. Four economy baseline runs on two
other maps and the combat work remain. No Method advantage is claimed, and
Civ Method search has not started.

The [Civ 6 economy setup](docs/civ6/RUN_ECONOMY_TASK.md) now has a real starting
save, exact state reader, live event monitor, and trace verifier. The installed
game lacks a Gathering Storm entitlement, so the case is explicitly base-game
calibration. The original population, science, budget, and 35-turn targets stay
unchanged. The save contains one population-4 Roman capital, 50 gold, and a
Warrior, Scout, and three-charge Builder.

All 28 verifier controls passed. A live empty control completed 35 turns in
36.66 seconds of turn steps, or 86.16 seconds with saving, manual reload, and
independent inspection. It correctly failed the task. Live founding/removal
events also passed a separate fixture check. The first empty control stopped
at an advisor tutorial; its failed partial trace is retained.

No legal winning Method, full playing broker, map-feasibility result, native
headless mode, or 5x/20x simulation clock is claimed. No playing-model call or
paid API call was made. The [evidence report](evidence/civ6-economy-setup-2026-09-10/README.md)
separates observed checks from the remaining calibration work.

## Factory repair policy search, 10 September 2026

The [repair comparison](docs/repair-experiment.md) is complete. Thirty factories
have native proof that the healthy factory passes, damage causes failure, and
a legal repair passes. Ten cases supported policy search; twenty new cases
were kept outside policy development.

Fresh direct Astra Codex sessions ran all thirty cases. Four Method versions
were tested in 31 development game attempts. v03 has one retained attempt;
the other three have ten each. v04 was selected and frozen before final tests.
It uses code to make a compact public observation, then one fresh Astra session
to diagnose, repair, check production, and finish. The Method uses the actual
Method v3 runtime. Both approaches use the same fixed subscription model runner.

Final scores: Method 20/20, direct Astra 18/20. Both restored production in all
20 factories. Direct Astra's two strict failures were unsupported tool
requests. This does not show that the Method could repair a factory that
direct Astra could not repair. The small paired success difference has
p=0.5 and does not establish a reliable success-rate difference.

On the same 18 successful pairs, median full processing time was 71.22 seconds
for the Method and 92.83 seconds for direct Astra, about 23% less. Full time
includes startup, player completion, production checks, and independent save
reads. Across all twenty attempts, reported input tokens were 2,939,690 for
the Method and 6,642,107 for direct Astra, about 56% less; these counts include
cached input. Search and authoring costs are separate. Subscription dollar
cost is unknown.

The [evidence report](evidence/repair-search-2026-09-10/README.md) keeps every
version and final outcome. All 40 final evidence audits and 54 focused repair
tests passed. A versioned reader fixes an exact saved recipe-name export fault
without changing production rules or replaying players. All attempts received
the same read, frozen before final tests. Search and final tests used headless
worlds, with no screen recording or paid API backend.

This is evidence of lower execution time and input use in one generated
factory family. It is not proof about arbitrary Factorio tasks, a need for
multiple model agents, or an advantage over deterministic programs.

## One-minute repair demo

The [presentation package](docs/repair-demo/README.md) adds a 142-word narration,
a 60-second silent video, two native Factorio action replays, and detailed notes
on the policy search and possible next experiments. Media stays local in
`runs/repair-demo-20260910/presentation/`. The clips replay retained repairs on
copies of the original saves. They check action outcomes and final equipment,
use edited timing, and make no new model calls. They are not footage of the
headless benchmark or new scored trials.

Additional trace counts support the input-handling explanation: the final
Method runs used 118 completed shell commands versus 191 for direct Astra,
while game actions were 213 versus 205. This does not isolate the cause of the
speed gain. The demo preserves the distinction between full-rule passes and
actual factory repairs.

## Civ economy Method pilot, 10 September 2026

**Correction:** The Civ pilot used strategy prompts, not the Method CLI.
The [plain-English results](evidence/civ6-method-pilot-2026-09-10/PLAIN_ENGLISH_RESULTS.md)
record what ran and the limits of the comparison. The historical “Method”
labels in this section refer to those prompts.

The [fixed-map pilot](evidence/civ6-method-pilot-2026-09-10/README.md) tested
three Method versions and then ran four fresh comparisons in alternating
direct/Method order. Both direct Astra and frozen Method v1 passed 2/2 trials.
Direct used 33 turns on average; the Method used 32.5. The Method took 7.3%
more playing time, 14.0% more game requests, and 22.2% more input tokens.
This is a small tradeoff, not a clear or repeatable overall improvement.

V1 remained best in development: v2 took more turns, and v3 failed the
five-round hold. All seven traces and separate save checks were validated,
and all 49 unit controls passed. No infrastructure failure or replacement
trial occurred. The actor used Astra during execution. No fixed-rule
ablation or unseen-map evaluation was run. The wider Civ map and combat
work remains pending.

## Project story page

The [HTML story source](story/README.md) brings the full experiment history
into one page: project aims, first control tests, failed recorded setup,
headless candidate selection, continuous policy revisions, unseen repair
results, native action replays, and a dated Civ VI development snapshot.
It explains Methods as saved procedures that can be tested and changed.

The local build at `runs/method-story/index.html` contains all three demo
videos and interactive charts in one offline HTML file. The source and
builder are public; game media remains outside Git. The page keeps the
20/20 physical repair result for both approaches separate from strict
request-rule scores, and it states the limits of the measured speed and
input reductions. No new model or game trial was run to make this page.

The story was shortened by about one-third after four writing audits. It now
states the Civ VI setup error directly: the pilot passed a written strategy
to Astra through Codex and did not execute it through the Method CLI. The
old numerical results remain as a written-strategy comparison in a note.
The Factorio repair experiment did use the Method v3 runtime.

The complete story is now published as `story/complete.html`, with the three
reviewed demo clips embedded. Its media hash manifest is included. Raw
recordings, game saves, private logs, and secrets remain excluded.

The [public story page](https://method-ai-hq.github.io/method-factorio/)
serves that complete HTML file through GitHub Pages. The publish workflow
copies only the reviewed page into the website. It runs when the complete
page changes on `main`, and it can also be started manually.
