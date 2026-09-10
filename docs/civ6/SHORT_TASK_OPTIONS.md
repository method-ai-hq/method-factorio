# Short Civ 6 tasks for continuous Method search

Status: options and recommended design, 10 September 2026. No task has been
calibrated or scored. The owner now wants continuous single-player policy
search. This replaces the earlier proposal to compare two design groups over
full domination games. It does not start a search or authorize model spending.

## Recommendation

Start with **a three-city research economy from one established city**.
Use a saved starting state, a short turn horizon, and a fixed material endpoint.
Keep **mobilize, capture, and hold one city** as the stronger combat alternative.

The useful horizon is a chain of dependent choices, not a large turn count.
A decision about spending now should change what can be done ten turns later.
Several cities or units should compete for limited resources. The task should
allow different plans and require adjustment to the map. Waiting for a nearly
completed technology or moving a prepared winning army is not enough.

A prepared start removes setup turns that contribute little to the measured
skill. It must leave the work in the task undone. Publish its provenance and
exact resources. A result from it is a scenario completion, not a fresh-world
win or a complete Civ victory.

## Options

All turn ranges below are design targets, not measured completion times.
Use 5–10 minutes per full trial as the draft wall-time target, including load
and independent verification. Combat may take longer because it needs more
actions per turn. Exact saves, thresholds, and limits require calibration.

| Option | Prepared start and objective | Proposed horizon | Why decisions have delayed effects | Main risk |
| --- | --- | --- | --- | --- |
| A. Three-city research economy | One established city, no spare settlers, no Campus. Found two cities and sustain a population, science, and budget target. | 30–40 turns | Settlers consume production and population; expansion competes with research infrastructure; locations change growth and yields. | A rich starting map can make it routine. |
| B. Mobilize, capture, and hold | Two modest cities and an inadequate field force. Capture a specified nearby AI border city, then hold it for five rounds while retaining both starting cities. | 20–30 turns | Research, reinforcement, travel, attack order, healing, city defense, and post-capture control interact. | A strong starting army makes it a tactical script; a weak one makes it impossible. AI variance and combat calls increase time. |
| C. Research and build industry | Two underdeveloped cities, no Apprenticeship, no Industrial Zone. Research Apprenticeship and finish an operational Industrial Zone and Workshop in a designated city. | 20–35 turns | Research boosts, builders, production investment, technology order, district placement, and gold spending compete. | A prepared research path or excessive income can reduce it to waiting and purchasing. |
| D. Repair a damaged economy | Two or three cities with damaged infrastructure, limited builders, and a negative budget. Restore the specified assets and sustain minimum production and a nonnegative budget for five rounds. | 12–20 turns | Repair order, travel, worker charges, growth, and spending affect recovery time. | Fastest option, but it may collapse into a fixed repair route and provide less strategic depth. |

A is the best first search task because its endpoint is clear and map variation
can change the best plan without adding many opponents. B is the best choice
if adaptation to an active opponent matters more than predictable throughput.
C is a good second economic task. D is a useful infrastructure pilot but is
not automatically a hard planning benchmark.

Do not combine all four into one initial score. That would multiply run cost
and make it harder to tell what changed. Freeze one task family first. A later
transfer test can use a different family and report it separately.

## Option A: candidate contract

Proposed task instruction:

> Starting from the supplied save, build a research economy with your original
> capital and at least two cities that you found during this attempt. Each of
> the two new cities must reach population 3. Maintain at least 20 science per
> turn, a nonnegative gold balance and net gold income, and nonnegative food
> surplus in the three qualifying cities for five complete rounds. Finish
> within 35 player turns and the fixed execution budget.

Use Trajan/Rome, Gathering Storm rules, Online game speed, and a small fixed
map family. Online is the name of a game-speed preset; the game remains
single-player. The first family has no combat, city-states, tribal villages,
disasters, or optional modes. Keep one remote built-in AI if required by the
engine; the scenario definition prevents contact and diplomatic income during
the short task. Whether the chosen map arrangement actually does so is a setup
test, not an assumption to leave unchecked. An enemy invasion would be a
separate harder profile.

Draft starting kit: one population-4 capital; one Warrior, one Scout, and one
three-charge Builder; no Settler, Trader, Campus, Library, or Industrial Zone;
50 gold; no queued or stored production toward a Settler or district. Pin the
capital's food, improvements, buildings, policy cards, era, governor state,
technologies, civics, culture/research progress, and all available purchase
options in each save manifest. Mining, Pottery, and Animal Husbandry may be
complete; Writing is not. Finalize the whole manifest before scored use.

Provide several legal settlement sites with different food, production,
travel, and Campus-placement tradeoffs. The map view has ordinary fog of war.
The player receives its current information, not the hidden map or a supplied
route. Variants change the decision, not just tile coordinates. For example,
a nearer low-growth site and a farther high-growth site can require different
settler and builder timing. Keep total starting resources within a declared
range; do not select final maps based on how a candidate performs on them.

The kit and thresholds above are hypotheses to calibrate. A capital able to
buy two settlers immediately, free culture/research bonuses, preloaded growth,
or high starting science could remove the intended difficulty. Their absence
must be checked from the actual save and effective game rules. Initial task
progress and all one-time bonuses are recorded.

The endpoint deliberately does not prescribe a build order, number of Campuses,
policy cards, improvements, or research route. Those are policy decisions.
Science can come from any legal recurring source. The fixed starting leader
prevents a switch to another civilization from changing the benchmark.

Why this is long-horizon:

- Early production and population spent on settlers can delay science.
- A good distant site can arrive too late to grow before the deadline.
- Builder charges spent near the capital cannot serve the new cities.
- A Campus can raise science while delaying expansion and other production.
- A short science spike does not satisfy the five-round requirement.

These are expected tradeoffs to verify during calibration. They are not a
claim that 35 turns is already known to be difficult or achievable.

## Option A: exact verifier

Identify the capital and each founded city by a stable game identity plus its
map tile and founding event. Names and current city IDs alone are insufficient:
capture and reload behavior must be tested. A qualifying new city must be
founded by this player after the initial checkpoint and stay under its control
through the measured window. Bought or captured cities do not count. The
starting capital may never be lost during the attempt. A city that changes
owner and is later recovered cannot hide that loss through a reused name.

Use a fixed observation phase: start of the human player's turn, after all
intervening players have finished and before the Method receives control.
Take one atomic, trusted snapshot at that phase. At each such snapshot define:

```
healthy(S, city_1, city_2) =
    original_capital_owned(S)
    and two_distinct_new_self_founded_cities_owned(S, city_1, city_2)
    and population(S, city_1) >= 3
    and population(S, city_2) >= 3
    and empire_recurring_science(S) >= 20
    and gold_balance(S) >= 0
    and net_gold_per_turn(S) >= 0
    and food_surplus(S, original_capital) >= 0
    and food_surplus(S, city_1) >= 0
    and food_surplus(S, city_2) >= 0
```

Pass requires a fixed pair of new cities for which `healthy` holds at six
successive boundary snapshots spanning five completed rounds. The broker
also rejects ownership loss or population falling below the threshold between
those snapshots. End the attempt before giving control for player turn 36.
The five-round window is included in the 35-turn ceiling. Boundary counting is
relative to the loaded start, not the game's displayed absolute turn number.

The Method may continue legal play during this window. The monitor also takes
an atomic checkpoint after every state-changing action and before end turn.
Any checkpoint where `healthy` becomes false resets the hold window; it cannot
be hidden by restoring citizen assignments before the next turn. A turn-end
rate check confirms the settings used for actual yield processing. This tests
sustained operation under the policy; it does not claim unattended operation. Food and
yield settings must hold in the same snapshot. The verifier never combines
science from one citizen assignment with food from another assignment.

Read the engine's recurring science rate, not score, research progress, or a
technology boost. Read net income after maintenance, not gross income. Read
food surplus after citizen consumption, not gross food production. Use raw
precision and a frozen numeric comparison rule; a displayed rounded value of
20.0 is not proof that the real value is at least 20. One-time gold receipts
cannot repair negative net income. Domestic routes are permitted; foreign
trades and gifts are excluded in this economic profile.

If rates fail to update reliably at the chosen phase, stop before scoring and
fix the reader/phase contract. Do not fill missing values with zero. Test the
rate values against actual changes over controlled turns, accounting explicitly
for growth, production choices, overflow, and one-time boosts. Research-progress
deltas are a consistency check, not a replacement for the recurring-rate rule.

The player cannot alter the verifier, use raw Lua, grant resources, reveal the
map, read saves, or bypass the action broker. The underlying game accepts only
normal-cost actions during play. Administrator-prepared fixtures exist only
before the initial locked checkpoint. Reuse the separation of authority in
[VALIDATOR.md](VALIDATOR.md), with this endpoint replacing domination victory.
The earlier full-game budgets and tournament schedule do not apply.

The supervisor records all six raw boundary snapshots and the intervening
post-action checkpoints in an authenticated, append-only trace outside player
write access. Bind each record to the starting save, action sequence, monotonic
time, turn identity, policy hash, and protected component hashes. A separate
monitor observes city founding, ownership changes, and the five-round window;
it does not accept self-reports from the playing Method.

Save once at the verified endpoint, then have a fresh inspector process load
that exact file without candidate code or turn advancement. Compare city
identity, ownership, population, rate values, settings, treasury, and the final
state fingerprint. The protected live history establishes the five-round
claim; the independent reload checks its final state. Reloading the final save
alone cannot establish the history. A candidate-authored trace cannot replace
the protected monitor. Test the monitor's historical decisions with prepared
positive and negative game controls before using it for scoring.

This contract needs one reload per trial. Additional saved checkpoints may
support audits, but are not a hidden per-trial replay requirement. Record
checkpoint-write and inspection costs as part of full trial time. A failed
independent inspection or missing trusted history is an evidence fault, not a
task success. An infrastructure fault stops new trials for diagnosis; preserve
the attempt. A clean, fully recorded timeout or unmet endpoint is a task failure.

## Verifiers for the other options

**B — capture and hold:** bind the target to its original map tile and initial
city identity. Require a trusted hostile-capture event, current ownership of
the same unrazed city, and continuous retention for five complete rounds.
Retain both starting cities. Verify the protected timeline, boundary snapshots, and final save as
above. A peace deal, loyalty acquisition, renamed city, empty city tile, brief
capture followed by recapture, or replacement city on that tile does not pass.
Check actual engine ownership; zero city HP is not proof of capture. The AI
keeps its normal controls. This is a scenario goal, not a domination victory.

**C — industry:** verify the exact technology is complete, the designated city
is still owned, and its new Industrial Zone and Workshop are finished and
unpillaged at the endpoint. Placement alone and an item in the build queue do
not count. Require those assets to remain operational for three complete
rounds, with a nonnegative treasury and net income. Preserve the initial state
showing the technology and assets absent, and independently inspect the terminal save; the protected monitor
establishes the three-round history. Normal research boosts, purchases, and chops are permitted;
starting resources must prevent immediate completion by a trivial purchase.

**D — recovery:** freeze a list of damaged assets by tile and type and an
explicit population/production/budget target per city. Require repair of all
listed assets, retention of the starting cities, and five complete rounds above
the target. Replacing an asset with a different type or destroying a city does
not count as repair. Check actual unpillaged status and effective yields.
Disbanding an unnecessary military unit is a legitimate way to reduce upkeep
unless the declared scenario also requires its survival; do not call a legal
strategy cheating after observing it.

## Fast execution is an engineering measurement

Wall time is approximately:

```
load + observation/action work + model latency + AI-turn processing
     + checkpoint writes + independent inspection
```

No trial-time measurements exist here. With a hypothetical two-minute total
load/checkpoint/inspection overhead, a 35-turn task must average about 14 seconds
per turn to finish in ten minutes. Five minutes would leave about five seconds
per turn. Measure startup, checkpoint writes, and the single final reload
first. Game-speed presets shorten in-game costs; they do not
remove model latency or make the engine a headless server.

Use one game process, a small map, few actors, no video, quick movement/combat
settings, and a compact allowed observation. Cache static rules. Let the Method
use local code and bounded per-turn action batches. A batch must meter every
action and stop at an error or turn change. Do not expose administrative fast
forward or automatic economy management as a hidden player capability.

Model calls need not occur for every unit or every turn. Deciding when a new
observation or a deeper plan is needed is part of the policy-search problem.
Call limits apply to all child agents and internal checks together.

The installed upstream overview exposes science and treasury rates; city tools
expose population, food, and damaged assets. These support feasibility, not a
finished verifier. The upstream city query also contains a build-queue repair
side effect, and several returned rates are rounded. Build a small read-only
inspector from reviewed engine queries; do not use the narrated city response
unchanged as trusted validation. Hash local patches as well as upstream code.

## Calibration before freeze

Use a separate calibration corpus and no optimized candidate feedback to set
v1. Calibration ends before the continuous search starts.

1. Measure load, one legal turn, common actions, checkpoint write, and a fresh
   save inspection. Test both normal and worst observed paths. Do not assume
   Factorio's headless throughput transfers to Civ 6.
2. Test a do-nothing policy, a simple greedy policy, and a competent reference
   on three different calibration saves. Model-backed references require a
   prior operator cap. The reference shows feasibility, not a policy result.
3. Require a complete legal reference trace that meets the proposed endpoint
   on each calibration save within the horizon. Require do-nothing to fail.
   Check whether the greedy policy saturates the task; if so, redesign before
   freeze. Do not promise any desired initial win rate without measuring it.
4. Check planning depth with controlled early choices: e.g., delay expansion
   by five turns, spend initial gold differently, or select a nearer lower-growth
   site. The outcomes should expose meaningful tradeoffs, not only API errors.
   These controls diagnose the task, not prove an optimal strategy.
5. Choose and publish the exact starting family, target, turn limit, wall limit,
   numeric rules, execution limits, permitted tools, and verifier version.
   Freeze them with the test report. Do not change them to match later results.

If 5–10 minutes is infeasible, choose a shorter prepared task such as D or
accept a longer trial time. Do not silently remove historical verification to
meet a speed target. If a single save permits a memorized action sequence,
expand the scenario family before freezing it. The question is reuse on varied
states, not whether fixed coordinates can be replayed quickly.

## Continuous Method v3 search

The repeating unit is: frozen Method -> fresh copy of a development save ->
trusted result and failure facts -> a new frozen Method -> matched comparison.
An existing Method may be adapted to the Civ tools to create M0, but no tested
Civ playing Method has been identified here. Validate M0 and preserve it before
using feedback. Format/runtime success is separate from game success.

Use four development saves and four additional promotion saves, all fixed
before search. Screen new versions cheaply on a rotating development case.
Only promising versions receive matched child/incumbent trials on the full
promotion set. Charge those additional runs to search. Promotion-set reuse is
selection data, not an unseen evaluation. Give the candidate no protected
files or hidden map information, even on development saves.

Rank by verified completion rate first, then total completed turns on cases
both policies complete. Use measured full wall time and known model cost as
secondary reports. A candidate may not replace the incumbent if its paired
win count decreases. Require strict improvement on the declared primary or
tie-break measure; ties retain the incumbent. Repeat an apparent narrow gain
on new preregistered development runs before a strong claim. Freeze replication
rules before launch; do not add attempts only for a favored candidate.

For failures, return concrete deficits: missing cities, each city's population,
science rate, food surplus, net income, longest valid hold window, lost units,
blocked commands, and remaining turns. These facts guide the next edit. They
do not redefine success. Avoid a weighted sum of science, gold, and population
that rewards one resource while ignoring a missing city. A partial candidate
can remain an exploratory branch, but is not a verified better incumbent solely
because an AI says its plan improved.

Before calibration ends, ensure the starting difficulty permits useful search;
if all candidates fail, the loop may still investigate failures but cannot
claim improved completion. After freeze, a different difficulty is a new task
version. Once a task saturates, preserve it and open a harder version rather
than moving its threshold.

Prepare eight sealed final saves independently. At an operator checkpoint,
freeze the selected policy and M0, and run both on all eight. Do not disclose
those results until the comparison is complete. Once final data is used to
write another Method, that corpus is no longer final for subsequent claims;
use a new sealed set. A continuously changing policy never gets credit for a
final test performed on an older hash.

Continuous means repeat within the operator's total wall-time, game-launch,
model, and spending limits. It does not mean run indefinitely. Every failure,
rejected candidate, usage record, and restart stays in the run index. Separate
search cost from the cost to execute one selected Method. Do not inherit the
old 64-game competition schedule or its budgets.

## Minimum negative tests for Option A

- Two cities, three captured cities, or reused starting cities: fail.
- A new city at population 2, capital lost then recaptured: fail.
- Science 19.96 displayed as 20.0: fail under the exact threshold.
- Gross income positive but net income negative: fail.
- Food production positive but food surplus negative: fail.
- A one-time boost without the recurring science rate: fail.
- Five snapshots spanning only four rounds: fail.
- One missing boundary, one unhealthy intervening boundary, or changed city pair: fail.
- Qualifying endpoint after turn or wall limit: fail.
- Forged policy report, wrong save, mutation during inspection, mismatched reload,
  unknown usage, or missing evidence: no verified pass.
- A legal alternate build order meeting every predicate: pass.

## Sources and limits

- [Upstream MCP capabilities](https://github.com/lmwilki/civ6-mcp/blob/dd2019056371b92ea4854e879ddf05a8cad95e8a/README.md).
- [Upstream overview queries](https://github.com/lmwilki/civ6-mcp/blob/dd2019056371b92ea4854e879ddf05a8cad95e8a/src/civ_mcp/lua/overview.py).
- [Upstream city queries](https://github.com/lmwilki/civ6-mcp/blob/dd2019056371b92ea4854e879ddf05a8cad95e8a/src/civ_mcp/lua/cities.py).
- [Upstream full-game scenarios](https://github.com/lmwilki/civ6-mcp/blob/dd2019056371b92ea4854e879ddf05a8cad95e8a/evals/scenarios.py)
  use 330-turn limits; they are not evidence of short-task throughput.

The local installed game XML contains the named technologies, districts, and
buildings. Expansion overrides and effective loaded-game behavior still need
validation. No game assets are copied into this document. All numeric task
thresholds and runtime targets are proposed choices, not measured results.
