# Fixed contract for the one-hour policy search

This specifies a new evaluator to implement and validate before scoring. It is
not an implemented evaluator or measured result. Do not modify the earlier
`scripts/check_result.py`, which checks a different task.

## Starting state and tools

Use native Factorio, fixed game speed 20, and recorded FLE fast-mode settings.
The game runs during policy thinking. Start with no factory, research, or enemies,
and exactly one burner mining drill, one stone furnace, one burner inserter,
ten transport belts, and 150 coal. No starting ore or plates. This is a supplied-kit
benchmark, not a fresh-world rocket run.

Permit observations, movement, placement, rotation, pickup, coal insertion into
fuel inventories, and one `finish` request. Disable manual ore mining/loading,
crafting, grants, raw game-code execution, speed changes, resets, and other ways
to bypass the task. Preserve real contents during equipment pickup; pickup does
not authorize forbidden transfers. Keep game administration outside policy access.

Choose and freeze three development maps and two unseen final maps. All need
accessible iron and room for the line. Vary patch positions/layouts. Declare any
operator-made terrain or resources before trials. Decide map eligibility before
candidate results; do not discard maps on which a candidate fails. Keep final
seeds/layouts hidden from search workers, including during reference checks.
Exclude earlier published pilot seeds from the final set.

## Pass condition

On `finish`, revoke playing access and stop all outstanding policy mutations.
The evaluator does not repair, refuel, or clear buffers. Advance 600 warmup ticks,
then three consecutive windows of exactly 1,200 game ticks each. These are
10 seconds plus three 20-second windows of game time. Do not substitute wall sleeps.

A scored pass requires all of the following:

- Correct initial state, fixed settings, unchanged policy bundle, and legal actions.
- A real connected route from the drill through at least one belt and the inserter
  into the furnace. Verify positions, directions, pickup/drop points, and item flow.
  Entity presence or a direct drill-to-furnace shortcut is insufficient.
- At least **5 additional iron plates in furnace output in every window**, confirmed
  by furnace completed-product and game production counters. Earlier plates do not count.
- At least **5 newly extracted iron ore from the connected drill's patch in every
  window**, confirmed by trusted extraction or resource-depletion evidence. Together
  with the route and forbidden manual loading, this establishes continuing supply.
- No policy action during warmup or measurement. Fuel loaded before handoff is allowed.
- An independent production verdict within the fixed task deadline and action limits.
- Complete visual/action evidence and a clean terminal save whose independent reload
  agrees with the final production state. A model's claim is not proof.

Write each predicate and its actual measurements to JSON with evidence references.
Separate production success from evidence completeness; missing or conflicting
evidence cannot become a scored pass. Later save inspection is timed separately.

Validate using a working line and deliberate failures: empty world, stored-ore-only
production, disconnected belt, reversed inserter, insufficient fuel, only two
passing windows, forbidden transfers or post-handoff actions, timeout, and missing
recordings. Test exact tick boundaries. Construct the reference through the same
playing tools; label it operator-authored and keep its code out of policy-author
contexts. Hash and freeze the tested host, evaluator, recorder, schemas, and settings.
A later harness defect stops scoring; preserve the old results and do not pool
scores from different benchmark versions without matched reruns.

## Limits, ranking, and records

Each trial has 300 wall-clock seconds from host launch through production verdict,
plus at most 30 seconds to close records, video, and save. Both fit inside the
job's 60-minute total. Maximum 200 playing actions, counting batch members and
rejections; maximum 60 model requests across model actions and internal checks. Record API usage and cost; never expose keys. Allow
at most 12 separately labelled setup smoke episodes. Reserve four scored slots
for the initial and selected Method on both unseen maps.

Rank common completed map panels by number of valid passes, then mean complete
trial time, then observed model-token use. Charge 330 seconds to every failed,
stopped, or evidence-incomplete trial. Valid trial time includes startup, model
and report work, evaluation, recording close, and cleanup. Report time to the
production verdict separately. Unknown model usage is not zero. Separate authoring,
search, and execution costs. Record concurrency; small samples do not establish
stable latency or general success rates.

Preserve task, network, and infrastructure failures. No silent retries until success.
For a verified common harness fault, permit at most one replacement per affected
contender/case, counting and reporting both attempts. A changed policy gets a new
version and fresh trial. Hidden-map results cannot feed another revision in this job.

Capture actual-game video for each attempt. Game-only 720p time-lapse at roughly
2 frames per wall-clock second is sufficient; keep capture times and initial/final
images. Label speed, gaps, and any replay. Validate capture before scoring, use the
same mode across contenders, and include its overhead. JSON or synthetic animation
alone is insufficient. If only serial capture works, move final evaluation earlier.

Each run index entry links the video, immutable policy bundle, settings, action/state
trace, verdict, usage/timing, errors, stop reason, save, and save inspection. Keep
checkpoints after each trial. Stop new trials at 20 GiB of new run data or below
10 GiB free disk space; never delete failed evidence to make room. Keep secrets,
raw game recordings/saves, and private logs out of Git. Publish reviewed evidence
only. Follow the repository's access and release rules, and record isolation limits.
