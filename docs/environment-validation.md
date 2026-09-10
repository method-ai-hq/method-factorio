# Environment validation: control coverage and speed

Status: proposed test series, 10 September 2026. The new comparisons have not
run. Existing evidence covers two small Method production runs only.

## Purpose

Select an environment that lets Astra play Factorio correctly and lets us run
many useful trials in a reasonable time. This is environment validation. It
is not the later experiment in which Astra searches over Methods to improve
long-horizon task performance without changing model weights.

The owner confirmed that the direct agent baseline means Astra using the
current game controls without Method. Keyboard-and-mouse play is not part of
this series.

## Baselines

| ID | Controller and game connection | Question |
| --- | --- | --- |
| A: direct agent | One persistent Astra Codex agent → current HTTP controls → FLE → native Factorio | Can an agent use our interface completely, and how quickly? |
| B: Method | A fixed Method → Astra Codex operations → the same HTTP controls → FLE → native Factorio | Does Method preserve control coverage, and what time does its runtime add? |
| C: FLE agent | One persistent Astra Codex agent → a thin, restricted connection to the FLE agent tools → native Factorio | Does our current wrapper hide controls or add avoidable work? |
| D: scripted control | A fixed, reviewed script → each game connection, with no model calls | What time and reliability come from the environment itself? |

The current HTTP wrapper already calls FLE. A and C are two access paths to
the same underlying adapter, not independent game engines. C must keep game
administration outside the playing interface. Do not give the playing agent
an unrestricted FLE instance, arbitrary Lua execution, or RCON credentials.
Use a separate process with an audited action list. If that boundary is not
available, mark C blocked and implement it before a measured agent run.

Start B with one playing operation, using the same goal and action guide as A.
Keep the final external check identical for all baselines. Measure Method's
connection check and internal check separately. A second Method shape can use
several operations to measure handoff cost; record it as a distinct runtime
test, not an improved policy. If C wins the interface comparison, also test
Method through that connection before selecting the combined system.

For the A/C timing comparison, first use matching actions and matching
observation content, including the same post-action checks. Then test native
FLE response handling as a separate variant. Reduced observations, cached
entity handles, batching, and removed checks must each be named changes;
their gains cannot all be attributed to removal of HTTP.

## Current evidence and gaps

The [existing runs](../evidence/control-test-2026-09-10/README.md) used B. Each
needed 12 playing requests to produce 20 new iron plates. Their playing
request intervals were 153.9 and 147.7 seconds at game speed 1. Those intervals
exclude connection checks, report writing, and final checks. There is no
measured A/C comparison and no measured no-model speed floor yet.

The [host](../scripts/control_test.py) exposes a small fixed action list.
Recipe selection, research selection, and rocket launch are not exposed.
The pinned FLE source has tools named `set_entity_recipe`, `set_research`, and
`launch_rocket`; their presence does not establish correct or complete support.
Selecting research is a normal playing action. Granting completed research is
an administrative action and must remain unavailable.

The host's `wait` uses wall-clock sleep. FLE's movement, mining, and crafting
clients also contain waits derived from their action timing. FLE fast mode is
already enabled in the pilot; that does not establish fast episode throughput.
Terminal saves load for inspection, but resuming an active FLE episode from
them is not implemented. The Method runtime still permits shell access under
the host account; the action list alone is not full process isolation.

## 1. Test each control family

Build a versioned capability checklist from the pinned base game and adapter.
Each family needs concrete cases, prerequisites, exact expected state changes,
and a check that reads actual game state. A tool name alone is not a pass.
Use D first to check the adapter, then A, B, and C to check agent access.

| Family | Example case and required evidence |
| --- | --- |
| Observation | Read inventory, position, entities, recipes, fluids, power, research, and production. Compare with an independent state read; test stale and missing data. |
| Movement and access | Reach a resource around obstacles; reject an unreachable destination or an out-of-range interaction without granting remote access. |
| Mining and crafting | Mine resources, hand craft, and handle a full inventory. Check resource and ingredient consumption, output, and time. |
| Placement and removal | Place, rotate, retrieve, and replace entities. Check collision, orientation, inventory, and contents of removed machines. |
| Item transport | Insert and extract items; build belts, underground belts, splitters, and inserters. Verify that items reach the specified destination. |
| Power | Build a working water, boiler, steam, and pole supply. Power a machine; detect and recover from a disconnected or insufficient supply. |
| Machine configuration | Set and change recipes, inspect ingredient shortages, and handle a blocked output. Verify actual product output. |
| Research | Select available research, supply labs, consume science, and observe completion. Check that unavailable research cannot be granted. |
| Fluids and oil | Extract, refine, and move fluids through pipes and pumps. Check fluid identity, amounts, connections, and blocked products. |
| Advanced production | Produce the intermediates and science needed for the declared rocket route. Check recipe prerequisites and material flow. |
| Rocket endpoint | Operate a prepared, legally configured silo through normal actions. Verify the launch in game state or a trusted event. |
| Factory scale | Read and control a larger factory, travel beyond the pilot's coordinate limit, and retrieve observations without silent truncation. |
| Optional production systems | Test trains and schedules, robots and logistics, circuit conditions, modules, and equipment as separate cases. Do not infer support from rocket success. |
| Combat | Test weapons, ammunition, damage, repair, death, and respawn in separate enemy-enabled fixtures. This does not change the enemy-free production comparison. |

Report three separate things: adapter support, access through each baseline,
and observed agent success. Use statuses **passed**, **failed**, **unsupported**,
and **not tested**. When a script succeeds but an agent fails, retain both
results and investigate the instructions, observations, or agent decision.

Define two coverage claims before testing:

- **Rocket-route coverage:** every action and observation required by the
  declared route is supported and verified. An omitted route requirement fails
  this claim, even if an average coverage score is high.
- **Full base-game coverage:** all declared base-game control families pass,
  including systems not needed by that route. List the finite checklist and
  any exclusions. Space Age, menus, and keyboard-and-mouse operation are not
  covered by the first series. Do not call rocket-route coverage “everything.”

## 2. Test short tasks and connected production

Use two clearly labelled tracks. Controlled fixtures can contain operator-set
inventory, research, and machines so one capability can be tested quickly.
Freeze and hash each fixture before the run. No setup privileges are available
to the playing agent. Fixture success is not a fresh-world episode or a win.

| Level | Task | Pass condition |
| --- | --- | --- |
| E0 | One action in a controlled fixture | Expected state change, legal resource use, and a useful result or error. |
| E1 | First iron plates from a fresh world | The existing 20-new-plate condition, unchanged. |
| E2 | Continuous iron production | The agent builds mining, transport, and smelting. After input stocks are accounted for, output increases in each of three fixed game-time windows without agent refuelling or transfers. Freeze window size and minimum output before runs. |
| E3 | Electricity and early research | A powered machine produces output and supplied labs complete a selected research task with measured science consumption. |
| E4 | Oil and advanced science | From matched fixtures, produce selected oil products and science with real material consumption. |
| E5 | Launch operation | From a matched late-game fixture, complete the remaining normal launch actions and verify the launch. Label this a fixture launch. |
| E6 | Long episode | From a fresh world, sustain production across several stages. A full fresh-world rocket attempt follows only when the controls and time budget support it. |

E2 must observe an actual production chain. A large manually loaded furnace
buffer is not continuous automated production. For E3–E5, declare exact target
items, technology, quantities, time windows, and fixture hashes before running.
Do not fill these in after seeing a result.

## 3. Measure where time goes

Instrument the host and runner before drawing speed conclusions. Record
monotonic wall-clock timestamps, game ticks, model usage, and response sizes.

| Measurement | Definition |
| --- | --- |
| Cold start | Start request to a ready game and connected controller. Report game startup, adapter setup, and agent startup separately. |
| Time to first action | Ready environment to the first gameplay action. Includes model and runtime preparation. |
| Time to goal | First playing observation to the first independently verified goal state. Also report total time from the start request. |
| Complete trial time | Start request through final checks, evidence save, and cleanup. Use this for trial throughput. |
| Model time | Time awaiting model responses, plus time spent starting fresh model processes. Keep tool execution out of this interval. |
| Adapter time | Request received to action completion and response delivery. Separate conversion, RCON work, observation checks, and intentional waits. |
| Method time | Connection checks, operation startup, handoffs, state handling, and internal verification. Shared final evaluation stays in its own category. |
| Game rate | Actual game ticks advanced per wall-clock second, with requested speed, achieved rate, and pause intervals. |
| Useful throughput | Correctly completed tasks or episodes per hour, including failures and reset cost. Do not reward many useless actions. |

Game simulation can run while the model thinks. These intervals overlap;
do not add overlapping totals and call the sum elapsed time. Use a timeline
or mutually exclusive wall-clock intervals for attribution. Report median
and p95 tool latency only when sample size supports them. With three episodes,
show every duration and the median; do not claim a stable p95 episode time.

## 4. Speed experiments

Run these in order so the source of a gain is clear:

1. **No-model floor.** Execute the same successful, reviewed action sequence
   through D on both connections from matching fixtures. An operator-authored
   script is allowed here because this measures environment performance, not
   policy invention. Time game simulation separately from request handling.
2. **Connection cost.** Compare matched A/C connection operations using D,
   identical observations, and identical game settings. Count the extra game
   reads caused by target lookup and automatic post-action snapshots.
3. **Batching.** Compare 1, 10, and 50 permitted actions per request on a
   declared sequence. Record individual actions and intermediate failures.
   Stop on uncertainty; do not retry an entire partly applied batch. Give A,
   B, and C equivalent batching access in subsequent agent comparisons.
4. **Simulation speed.** Measure requested speeds 1, 5, and 20 on small and
   larger factories. Report achieved ticks per second, not the requested
   multiplier. Verify material consumption and results at matching game ticks.
5. **Pause and advance.** Test pausing between agent decisions and advancing
   by bounded game ticks, compared with continuous simulation. This is a new
   environment mode that needs implementation and validation. It is not a
   command for the agent to set arbitrary game speed or bypass production.
6. **Agent and Method cost.** Compare A/B on the selected connection and time
   mode. Use one playing operation first, then a separately named multi-step
   Method to measure the cost of fresh processes and handoffs.

Do not remove waits without checking their semantics. Some FLE actions modify
state immediately and account for their duration separately. A tick-based wait
must let the real factory run for the declared duration exactly once. Check
that pausing does not deadlock a queued action and that acceleration does not
duplicate or skip mining, crafting, research, or production. Tick-scheduled
script tests can check equivalence; agent decisions under different time modes
are not expected to be identical.

## 5. Failure, recovery, and long-run tests

- Reject invalid actions, impossible recipes, out-of-range placement, and
  insufficient inventory with no unexplained state change.
- Lose an action response after the game applies it. Reconnect, inspect the
  game and action ID, and recover without repeating the applied action.
- Stop the agent while the game stays running. Resume the same policy with
  the recorded game state and remaining budget. Repeat for a server restart.
- Save and resume a live FLE episode with matching inventory, buildings,
  research, queues, and retained policy state. A terminal inspection save does
  not pass this test.
- Remove fuel, disconnect power, block an output, and fill an inventory in
  declared fixtures. Measure detection and recovery time. Record fault timing
  and the operator's action separately from normal gameplay.
- Run at least 1,000 scripted actions and a 30-minute continuous integration
  trial on a larger factory. Check memory, latency drift, lost responses,
  observation size, action order, and remaining-budget enforcement.
- Check that forbidden administration and evaluator changes cannot be reached
  through either interface. Test the process boundary before scored policy
  evaluation; same-account shell access remains a known gap.

## 6. Proposed acceptance targets

These are engineering targets to review, not measured results or new rocket
experiment rules. Freeze targets before their acceptance run.

| Area | Initial target |
| --- | --- |
| Correctness | Every required route case passes; no unexplained grants, losses, duplicate actions, or false completion. |
| Local response | On a small fixture, p95 observation and simple immediate-action overhead at most 250 ms, excluding intentional game advancement. |
| Ready to run | Cold startup at most 60 seconds; reset to a ready known fixture at most 30 seconds. Measure these independently. |
| Short iteration | E1 completes and verifies within 5 minutes per trial; at least 10 completed E1 trials per hour including startup and cleanup. |
| Longer iteration | Aim for useful multi-stage trials within 15 minutes and a full rocket episode within 60 minutes. The latter is a planning target; estimate feasibility from larger tasks before making it an acceptance promise. |
| Method overhead | For the one-operation Method, median complete-trial time no more than 20% above the matched direct-agent baseline. If missed, identify the added work before choosing a different runtime design. |
| Recovery | All defined disconnect and restart cases recover or stop explicitly without an unrecorded reset or repeated uncertain write. |

A faster failure is not a throughput improvement. Select the fastest
configuration that passes the required correctness and recovery checks. Keep
an honest list of unsupported families. A configuration can be ready for
small development trials while still unready for full policy evaluation.

## Run controls and sample sizes

Use the same pinned game, FLE revision, models, reasoning settings, context
and tool guides, starting states, and total budgets for a matched comparison.
Use clean agent sessions and independent copies of each fixture. Do not leak
one baseline's solution to another. Randomize or rotate baseline order to
reduce cache and machine-load effects. Label cold and warm model context.

Start with one pilot per case and baseline. Freeze the corrected setup before
the comparison. For E1–E3, start with three matching development seeds per
baseline and report all outcomes. Expand repeats only when variability changes
the decision. For local timing, use at least 100 observations and 30 matched
mutating operations per measured family, excluding fixture restoration from
action latency while retaining it in throughput. For correctness, cover edge
cases rather than repeating an easy action many times.

Continue to use the owner's Codex subscription, with no separate paid API
calls, credit purchases, or usage resets. Report input, cached input, and
output tokens and any unavailable cost as unknown. Before launching a batch,
set a total wall-clock and action budget across its episodes, not just a limit
for each individual run. Stop on subscription exhaustion; do not switch to
API billing. This document authorizes no new paid service.

Keep setup failures, unsupported cases, agent failures, timeouts, and valid
successes distinct. Store the controller version, interface version, fixture
hash, time mode, per-action trace, checks, usage, and human interventions.
Preserve previous results when the environment changes. These seeds and
fixtures are development data, not the later hidden evaluation set.

## Work order

1. Add the coverage checklist and timing instrumentation. Keep the current
   two-run evidence as a pilot, not a baseline speed comparison.
2. Build the fixture runner and no-model script tests. Audit the missing FLE
   capabilities and expose normal recipe, research, and launch operations.
3. Run A/B/C on E1, then power and research cases. Measure connection and
   Method costs with matched tools before changing the interface.
4. Test batching and accelerated game time, then recovery and larger factories.
5. Select an environment configuration, publish its supported controls and
   measured throughput, and freeze it for the first policy-search experiment.

Prepared late-game fixtures should test E4/E5 before a long fresh-world attempt.
A failed long episode does not by itself show whether the policy or the
environment is at fault; the smaller checks provide that evidence.
