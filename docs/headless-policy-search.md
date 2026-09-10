# Headless optimization and later recorded demonstrations

On 10 September 2026, the owner changed the capture requirement: policy
optimization may run without screen recording. Selected Methods may be run
again later with recording. This is a new evidence contract,
`automatic-production/headless-1`. The earlier contract and results remain
unchanged. This document does not start a new paid experiment or extend the
completed job's deadline.

## Fixed rules

The supplied kit, allowed actions, real connected route, 600-tick warmup,
three 1,200-tick windows, five new ore and five new plates per window, and
no actions during measurement remain the same. Time, action, model-request,
ranking, and independent save checks also remain the same.

A headless pass requires complete initial/final state, settings, action/state
trace, tick-window measurements, policy/runtime hashes, usage records, timing,
terminal save, and a matching independent save inspection. Missing video is
expected. Missing game-state evidence still prevents a pass.

All contenders in a comparison must use the same recording mode. Headless
and recorded timing results must not be pooled. Record concurrency in every
trial. The limit of eight worlds is a ceiling, not a proven machine capacity.

## Source controls

`search_host.py --recording-mode none` starts no graphical client and imports
no recorder. The default remains `native` for compatibility with the old
contract. `search_trial.py` obtains the mode from the fixed manifest, not from
the policy. A headless trial is rejected unless the manifest names the new
contract. The current old-job manifest remains unapproved.

A future tested headless manifest must include:

```json
{
  "contract": "automatic-production/headless-1",
  "approved_for_scoring": false,
  "settings": {
    "recording_mode": "none",
    "validated_concurrent_worlds": 2,
    "startup_recovery": "none"
  }
}
```

This fragment is not a complete manifest. Add the tested source hashes and all
fixed settings. Set approval true only after the full live evaluator and
runtime checks pass. Include `search_startup.py`, the scheduler, the trial
runner, all host/evaluator modules, and runtime helpers in the frozen hashes.
A changed source invalidates the old freeze.

The scheduler defaults to two worlds and refuses a higher value than the
manifest's tested level. Headless startup can run in parallel. For native
recording, a file lock permits only one graphics load and game initialization
at a time. The lock is also used by direct host launches and is released if
the process exits. The client startup allowance is 120 seconds, within the
existing trial deadline. It does not add time to the trial.

## Failure recovery

The recorder writes separate graphics-loading and connection stages. Hosts
write a structured failure code. The scheduler preserves all failed attempts
and unstarted work in `pending.json`.

For a future recorded run, the operator may freeze
`startup_recovery: "one_serial_replacement"` as the allowed response to the
known graphics-loading timeout. On the first such failure at concurrency above
one, the scheduler lowers concurrency to one, lets active trials close, and
makes one linked replacement attempt. This does not change source or settings
inside a running trial. Both attempts count and remain in the index. Other
faults or a failure at concurrency one require diagnosis before another launch.
The replacement rule must be part of the declared experiment; the script does
not infer authorization from a failure.

When the scheduler reports `repair_required`, the supervising Astra must read
the saved failure and continue permitted repair work. This status pauses trial
launches. It does not tell the agent to abandon the task. The agent may correct
infrastructure, run focused checks within the remaining repair allowance, and
freeze a new benchmark version. It must not pool results across changed
versions without matched reruns. Hard job, storage, spending, and trial limits
still apply. A failed policy with valid infrastructure is a result, not a
reason to repair the evaluator.

## Record a selected Method later

Use a separate job and approved native-recording configuration. Run
`search_trial.py` with `--kind demonstration --source-trial PATH/TO/trial.json`,
the original frozen policy, and the same seed and patch coordinates. The runner
checks the original bundle hashes and map, and adds the source link to the new
record. A demonstration requires native recording. It is marked ineligible
for the headless comparison.

This is a new execution, not an exact replay. Model decisions and actions can
differ. The recorded attempt can fail even if the original passed. Keep both
outcomes. Loading an old terminal save can show the finished factory but cannot
recover footage of how it was built. Exact historical replay would need a
separate, tested action-replay system; it is not implemented here.

## Current checks

Two simultaneous headless reference worlds were ready in about 3.4 seconds
and closed with independent save checks in about 8.6 seconds each. Both had
five new plates and five new ore in all three windows. No graphical client or
model call ran. See [the reviewed check](../evidence/headless-control-2026-09-10/README.md).

Eleven control tests check serial native startup, parallel headless startup,
lock release, bounded replacement, preservation of failures and pending work,
deadline handling, and required headless evidence. They use small fake workers.
These are not scored policy trials. Four/eight-world capacity, full negative
live evaluator coverage, full Method-to-host integration, and a recorded
re-execution are still required before the corresponding claims.
