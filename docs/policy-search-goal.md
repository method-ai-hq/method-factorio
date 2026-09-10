# Goal prompt: search for automatic-production Methods

Status: ready-to-use instructions, not an active or completed search. Copy the
prompt below into a new Astra task in this repository. The limits are proposed
defaults; starting that task adopts them unless the operator supplies overrides.
This document does not start a background task or schedule a later run.

---

You are Astra. Run a bounded policy search in this Factorio project. Design,
execute, compare, and improve reusable policies expressed as executable Methods.
Continue without routine confirmation until a stop condition below applies.
Use actual game results to select policies. Preserve all versions and failures.

Our research question is whether Astra can improve task performance by changing
executable Methods, without changing model weights. A policy includes its Method,
helper code, internal checks, state representation, and allowed model choices.
The final policy may use code, individual model calls, agents, or a mixture.
Do not require model calls during gameplay if code can solve the task reliably.

## 1. Scope, limits, and authority

Use these limits unless the operator gives explicit replacements before launch:

| Setting | Limit |
| --- | --- |
| Whole job | 8 hours from task start, including setup, authoring, trials, and reporting |
| Setup and evaluator validation | At most 90 minutes |
| Distinct candidate Method versions | At most 24, including the initial Method |
| Scored trials | At most 120, including baselines, failures, retries, and final evaluation |
| Setup smoke tests | At most 12; record them separately, never as scored successes |
| Parallel game worlds | At most 3, with separate ports, saves, and run folders |
| Concurrent model-backed playing runs | At most 2; code-only runs may use another world |
| Task deadline per trial | 300 wall-clock seconds, from game-host launch through the external production verdict |
| Trial cleanup allowance | A further 30 seconds for final save, recording close, and records |
| Playing actions per trial | At most 200; count every batch member and rejected request |
| Model requests per trial | At most 60 across playing, planning, and internal checks |
| New local run data | At most 20 GiB; stop new trials if free disk space falls below 10 GiB |
| Billing | Existing Codex ChatGPT subscription only; separate paid API spending cap is US$0 |

Aim for at least 20 valid, materially different policy versions and 80 scored
trials if the limits and prerequisites permit. These are targets, not permission
to exceed a cap, invent variation, or claim unrun work. Reserve at least the final
60 minutes and 20 scored-trial slots for evaluation and reporting. Increase that
time reserve if measured trial duration requires it. Do not start work that
cannot finish and save its evidence before the remaining deadline.

Do not purchase credits, redeem a usage reset, use separately billed model APIs,
or switch to paid infrastructure. A configured API key is not authorization to
use it. Check subscription-backed execution before model work. A `call` or `run`
step that invokes a model must obey the same billing limits and report its use.
If a required execution backend cannot use the subscription, exclude that backend.
Do not treat missing usage information as zero.

Read AGENTS.md, README.md, GOALS.md, DESIGN.md, EXPERIMENT.md, PLAN.md,
DECISIONS.md, HACKATHON.md, and the reviewed environment results. Follow the
project's file, secret, and release rules. Do not inspect the parent workspace's
sensitive directory, private source, account data, or run history.

This is a separate, supplied-kit automatic-production benchmark. It does not
replace the root rocket experiment or count as a fresh-world rocket result.
Do not edit its existing evaluator or rewrite earlier results.

As the setup supervisor, you may add a new benchmark host, evaluator, recorder,
and search runner inside this project. Complete and freeze them before scored
search. Playing and policy-improvement workers may edit only their assigned
candidate bundles and local reports. They must not edit the evaluator, host,
recording system, seeds, limits, or experiment manifest.

Start policy authors in fresh contexts with this task, the allowed tool guide,
and permitted development evidence. Do not supply the operator's reference
construction code or fixture placement plan. A playing process may read its own
frozen bundle and workspace, the supplied guide, and game observations; it may
not read other candidates, benchmark internals, or unrelated trial folders.
Improvement workers may read candidate parents and development traces explicitly
assigned to them. Record any prior solution material that was supplied.

## 2. First verify the execution system

Read the public Method specification at:
https://github.com/method-ai-hq/method-spec

Inspect the actual installed executor and any explicitly supplied public executor
revision. Pin the specification and executor versions used for this search.
Do not assume that draft syntax is executable. Do not change the owner's separate
format/executor project or copy private code into this repository.

Test actual supported execution types with small conformance examples. The desired
choices are an agent operation, a single model call, and a code operation. Record
which work without hidden agent launches. A code operation must not secretly
start an agent merely to execute a script. Record any subprocess and model work
inside helper code. Do not require all three types if one is unavailable.

Require working code and agent execution for the mixed-execution search. If they
are unavailable, report the exact missing backend or interface. Do not spend the
whole job writing a competing executor or label an agent-only run as this search.
Finish any useful setup checks within the setup allowance, then report the block.

Use native Factorio and the restricted HTTP game connection unless preflight
finds a concrete reason to change it. Pin the game, FLE, tool schema, runtime,
model settings, and recorder. Do not update these during a scored comparison.
Normal belt and inserter placement, rotation, inspection, and fuel transfer must
work before this benchmark starts. Keep game administration outside the playing
interface. Enforce available process and file restrictions; record their limits.
Same-account shell access is not hardened isolation. Any access to hidden test
data, administrative controls, or protected evaluator state invalidates the run.

## 3. Fixed task: build automatic iron production

The policy must build an iron-production line from an empty factory. Iron must
be mined by the supplied drill, travel over at least one transport belt, pass
through the supplied inserter, and be smelted by the supplied furnace.

Starting inventory is exactly:

- 1 burner mining drill;
- 1 stone furnace;
- 1 burner inserter;
- 10 transport belts;
- 150 coal.

There are no starting ores or plates in inventory, no placed factory, no completed
research, and no enemies. This is an explicitly supplied construction kit. It
does not test acquiring the kit from scratch. The character may move, inspect,
place, rotate, retrieve, and fuel the supplied equipment. Manual item insertion
is restricted to coal in valid fuel inventories. Disable manual ore mining,
ore/item loading, crafting, item grants, and other actions that bypass this task.
Returned items from normal equipment pickup must retain their real contents;
they do not permit otherwise forbidden item transfers.

Use small valid map areas with an accessible iron patch and space for the line.
Vary observed patch position and layout across seeds. Use generated terrain or
declared operator-made terrain fixtures; record which, the generator, ore amounts,
and all setup changes. No undeclared terrain or resource changes are allowed after
the run starts. Do not give the policy a factory blueprint or fixed placement plan.

Freeze the map-generation settings, exact seed sets, kit, allowed actions, and
observations before search. Choose map eligibility by game-state conditions and
reference feasibility checks before seeing candidate results. Do not remove a
map because a candidate performs poorly on it.

Set game speed to 20 and enable the same recorded FLE fast-mode settings for every
candidate. The game runs during policy thinking. Policies cannot pause the game,
change speed, reset, or request administrative actions. The evaluator may stop at
exact ticks for measurement and save inspection; record these stops separately.

## 4. Implement and freeze the external evaluator

The existing `scripts/check_result.py` checks the earlier 20-plate, speed-1 task.
It is not the evaluator for this benchmark. The existing continuous-production
fixture proves only a prepared line and uses a different threshold. Keep both
unchanged. Add a new, separately named evaluator for the rules below.

Use fixed code and authoritative game-state reads, not a model's judgment. The
policy may request evaluation once through a normal `finish` operation. On receipt,
revoke further playing actions, finish or cancel in-flight actions, and record
the handoff state. Do not let background policy processes keep acting. The
evaluator performs no repairs, refuelling, layout changes, or buffer clearing.

Advance 600 game ticks for warmup, then measure three consecutive windows of
exactly 1,200 game ticks each. At 60 ticks per game second, these are a 10-second
warmup and three 20-second game-time windows. Use host tick boundaries, not three
wall-clock sleeps. Record actual ticks and achieved game rate.

A pass requires ALL of these conditions:

1. The initial state, kit, game settings, policy hash, and action restrictions
   match the frozen manifest. No prohibited or unrecorded game effects occurred.
2. A real route connects the drill output through belts and the inserter to the
   furnace. Validate positions, directions, pickup/drop points, and observed item
   flow. Entity presence alone is insufficient. No direct drill-to-furnace shortcut.
3. Furnace output gains at least 5 new iron plates in EACH of the three windows.
   Furnace completed-product count and the game's iron-production count confirm
   those gains. Plates present before a window do not count for that window.
4. The connected drill removes at least 5 iron ore from its source patch in EACH
   window. Use trusted resource-depletion or extraction evidence. Combined with
   the forbidden manual ore transfers and observed route, this must establish
   ongoing automatic supply. Stored ore alone cannot satisfy the test.
5. No policy action, manual transfer, fuel addition, grant, or repair occurs during
   warmup or the three windows. Fuel loaded before handoff is permitted.
6. The production verdict arrives within the 300-second task deadline and all
   action/model limits hold. A missing finish request is a timeout, not success.
7. Required traces and actual-game visual evidence exist. A clean terminal save
   and its later inspection agree with the relevant final production state.

Write a machine-readable verdict with every predicate, its measured values,
timestamps, source evidence, and a stop reason. Distinguish gameplay success from
evidence completeness. Missing or conflicting evidence is never a scored pass.
Save inspection occurs after timing the trial; report its time separately.

Before search, test the evaluator on a known working line and deliberate failures:
empty world, preloaded furnace without ongoing mining, broken belt connection,
reversed inserter, insufficient fuel, production in only two windows, attempted
manual ore insertion, forbidden actions after handoff, timeout, and incomplete
evidence. Test exact tick boundaries and deadline enforcement. Keep these as
operator-authored fixtures, not policy inventions or scored search successes.

The earlier prepared fixture produced 5 plates in each 1,200-tick window. That is
supporting evidence, not proof that this new evaluator, kit, map set, or interface
works. Complete the reference construction through the same allowed playing
actions, and validate the stronger mining/route predicates before freezing.

Hash the tested evaluator, host, map generator, observation/action schema, recorder
configuration, and benchmark manifest. Freeze them before the first scored trial.
Do not lower thresholds or widen budgets when candidates fail. If a real harness
defect appears later, preserve affected records, stop scoring, and save a new
benchmark revision. Never pool scores across revisions without matched reruns.

## 5. Record every trial, including failures

Create a unique run ID before starting any game or model process. Never reuse or
overwrite a run folder. Capture, from initial state through final result:

- Every action request and response, errors, before/after state where applicable,
  Method step/state transitions, and host measurement samples.
- Monotonic wall-clock times and game ticks, policy/version hashes, resolved model
  and runtime settings, game seed/settings, and all operator interventions.
- Model requests, input/cached/output tokens where available, script/runtime time,
  startup, time to verdict, complete trial time, and evidence-save time.
- Initial/final game state, evaluation windows, terminal save, save-inspection
  result, evaluator verdict, and stop reason.
- A viewable visual recording of the ACTUAL game for each episode, linked to its
  trace. Also keep a thumbnail and a short description of what occurred.

Structured JSON alone is not the requested gameplay recording. Validate actual
game-image capture or a spectator client during preflight. Prefer game-only
capture; do not record unrelated desktop windows, credentials, or private data.
Target a modest 720p, 2-frame-per-wall-second time-lapse, plus initial/final images
and action-boundary images where practical. Store source capture times. Label
the capture rate, game speed, gaps, and any later playback speed change. Do not
call reconstructed diagrams, synthetic animation, or a re-enacted run original
game footage. If using replay, prove it corresponds to the original saved run
and clearly label it as replay.

Use the same capture mode across compared policies and include its overhead in
timings. If only one world can be recorded, run gameplay serially while policy
authoring and analysis continue in parallel. Do not omit recordings to inflate
the number of trials. If visual recording cannot be made reliable within setup
limits, report that blocker instead of claiming a fully recorded search.

Keep full traces, native logs, saves, and raw footage in ignored local run/data
folders. Write a local HTML or Markdown run index with a playable-video link,
policy link, verdict, timing, and failure reason for every attempt. Publish only
reviewed evidence; keep game assets and private logs out of Git. Do not delete
failed recordings to stay below the storage cap; stop starting trials instead.

## 6. Baselines and maps

Have the evaluator supervisor choose six development maps and five separate final
evaluation maps before search. Final maps must not be among the earlier published
pilot seeds or development cases. Store and hash the final map list outside
candidate access. Give the search workers development observations and results
only. The evaluator service returns the final-set hash and readiness to the search
process, not the hidden seeds or layouts. Final evaluation happens after policy
selection and is not feedback for another revision in this job.

Save these baselines under the same new benchmark rules:

1. A direct Astra agent, with the same tools, permitted helper-code capability,
   model availability, limits, and observations as the Methods.
2. The first valid Astra-authored Method, frozen BEFORE using its gameplay results
   to revise it. This is the initial-policy baseline.
3. The operator-authored reference script, labelled as an engineering reference.
   Do not present it as an Astra discovery or hide its design cost.

The old 20-plate Method has a different objective and cannot supply a comparable
baseline score without a separately versioned adaptation to this task. Give the
initial and improved policies access to the same supported execution types.
Keep a human-designed executor comparison separate from autonomous policy search.

## 7. Search loop

Maintain a persistent search journal, candidate registry, queue, and best-known
policy pointer. Reserve trial slots and resource limits before dispatch so parallel
workers cannot exceed global caps. Recover these records after a supervisor restart;
do not create duplicate attempts or continue an uncertain game as a fresh trial.

Repeat while resources remain:

1. Read development evidence. Identify a concrete failure, wasted time, or costly
   model decision. State a testable hypothesis before editing a candidate.
2. Create a new immutable candidate ID and parent link. Bundle the Method, helper
   code, internal checks, dependencies, and configuration references. Save the
   proposed change and expected benefit. Do not modify a running bundle.
3. Validate syntax, types, limits, permitted tools, and helper paths before opening
   a game. Record rejected candidates; they are not tested gameplay policies.
4. Screen valid candidates on the same first two development maps. Give promising
   candidates all six development maps. Reserve full-map tests for up to eight
   candidates as resources permit; state the promotion rule before screening.
5. Compare candidates only on the same completed map set. Do not compare a one-map
   lucky result with a six-map score. Use partial results to allocate further tests,
   not to declare a final winner.
6. Diagnose losses from trace and game footage. Preserve failures and actual costs.
   Do not silently rerun until success. Branch from successful candidates and keep
   alternatives with useful differences instead of editing only one lineage.
7. Update the registry, leaderboard, evidence index, and short progress report.

Explore materially different policies: code-led placement and control, model-led
layout choice with code execution, agent-led construction, different state and
observation handling, bounded repair strategies, and selective internal checks.
These are areas to investigate, not supplied factory plans. Do not force an agent
step into a policy that works without one. Do not count renames or unchanged reruns
as new policies. Generated helper programs count as policy changes and must be
versioned. Do not change model weights or add training infrastructure.

Failed candidates may inform development. Keep external evaluator internals and
final-map information outside their access. A policy may change working state and
factory plans through its frozen logic, but may not rewrite its executable bundle
mid-trial. Do not use a seed-to-action lookup table or read benchmark metadata to
select memorized coordinates; use the permitted game observations.

## 8. Ranking, failure handling, and final evaluation

For a fixed map panel, rank candidates in this order:

1. Number of valid passes within the limits.
2. Mean complete trial time, assigning 330 seconds to every failed, stopped, or
   evidence-incomplete trial. For valid passes, include startup, all model/report
   work, evaluation, recording close, and cleanup. Never reward an early failure
   for being fast. Also show time to the independent production verdict separately.
3. Total observed model-token use over that same panel, with requests and cached
   tokens reported separately. Missing usage is unknown, not a winning zero.

Show individual run values and success/time/usage tradeoffs. Do not infer stable
tail latency or statistical certainty from a handful of maps. Keep authoring,
search, setup, and final-policy execution costs separate.

Retain task failures, timeouts, model/network failures, and harness failures as
distinct outcomes. They all count against the job's trial/resource caps. Use all
attempts for operational throughput. Do not delete an infrastructure failure from
the primary table. If a verified common infrastructure fault prevents a fair paired
comparison, permit at most one replacement for every affected contender on that
case; report the original and replacement separately under the frozen rule.

Before opening final maps, select and hash at most two improved candidates using
development evidence alone. Run those, the initial Method, and the direct-agent
baseline on the same five final maps. This reserves at most 20 final trials.
Do not tune policies from final results. If resources prevent this panel, report
exactly what ran and make no complete final-evaluation claim.

An improvement claim must compare the initial and selected Method on the same
unseen maps, settings, execution choices, and limits. A faster helper or executor
alone is not proof that policy search helped. A completed automatic line is not
proof of a completed Factorio game or long-horizon research success.

## 9. Stop, save, and brief the operator

Stop starting trials when a cap is reached, the reserved final-test/report window
begins, subscription usage is exhausted, storage is insufficient, game/recording
state is unreliable, or a required dependency is unavailable. Do not retry quota
errors in a loop or switch billing methods. Bound ordinary transport retries and
record uncertain actions. Never repeat a game mutation without checking its state.

The search need not stop at the first passing policy. Continue testing improvements
and alternatives within the limits. A sustained lack of improvement may justify
ending early; report how many candidates and common-map comparisons support that
decision. A user stop request takes precedence: save a checkpoint and shut down
only this job's processes.

Write checkpoint updates after every completed trial and candidate decision. Keep
a readable progress summary at least every 15 minutes while the job is active.
Do not assume this prompt creates a scheduler or survives a closed app. Use the
actual supported long-running task mechanism. If execution cannot remain active,
save an exact resume command and report the limit; do not say work is continuing.

At the end, deliver:

- A concise result: did the selected policy improve success, time, or model use?
  State the sample size and uncertainty, or state that search was blocked.
- A table of baselines, initial policy, and selected policies on development and
  final maps, with each attempt's outcome and all costs/stop reasons retained.
- Links to the best Method bundles and commands to rerun them.
- A complete run index with each trial's actual gameplay recording, trace, verdict,
  save-inspection result, and policy version. Include failed and interrupted trials.
- The frozen benchmark manifest, evaluator and its validation results, known
  enforcement/recording limits, and exact dependency versions.
- A short account of which changes helped, which failed, and what remains untested.
- Total elapsed time, candidate/trial counts, model usage, separately billed spend
  (expected zero), storage use, and whether every job-owned process stopped.

Commit completed project code, candidate bundles, documentation, and reviewed
evidence. Follow the repository's main-branch push rule, preserve unrelated work,
and run an existing deployment workflow only if one exists. Keep raw footage,
game saves, credentials, and private logs out of Git. Update HACKATHON.md with
measured results and their limits. Never present planned work as completed work.
