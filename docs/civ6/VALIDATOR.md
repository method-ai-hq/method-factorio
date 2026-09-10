# Civ 6 validator contract

Status: design v1. This is the specification for an owner-controlled live
validator and its offline result reducer. Neither is implemented by this
change. An MCP response, a policy report, or a well-formed JSON file is not
proof of a win. Use with [matched-games-v1](EXPERIMENT.md).

## Separate authority

| Component | Reads | Writes |
| --- | --- | --- |
| Designer A or B | Its permitted development evidence; public documentation | Its own candidate bundles |
| Playing Method | Its allowed view and its private scratch state | Requests to the broker; private state |
| Game broker | Full local game connection; locked tool definitions | Legal actions for the assigned player; trusted action/state records |
| Supervisor | Lock, run queue, starting saves, budget ledger | Loads, process control, append-only run index, terminal saves |
| Independent inspector | Terminal save, pinned game build, locked inspector | Raw inspected state and inspection report |
| Result reducer | Trusted lock and evidence from the components above | Verdicts, pair results, promotion decisions, final matrix |

The broker alone owns the FireTuner connection. The player has no direct
connection to the installed desktop MCP, local ports, dashboard, process
control, logs, saves, validator, or other policy's state. Isolate designer and
player processes at the operating-system or remote-worker boundary. A port
allowlist in a provided Python helper does not constrain arbitrary helpers.

Give each run an opaque, short-lived broker capability, bound to that run,
policy hash, assigned player, and current turn. Use unique action IDs. Reject
stale, duplicate, cross-run, cross-seat, and out-of-turn requests. Do not pass
credentials into candidate-generated subprocesses beyond their restricted
broker capability. The capability cannot reach administration endpoints.

A batch stops after the first failed operation and returns a result for each
attempted member. Each member is authorized and metered separately. Retry of
an unknown result requires supervisor state reconciliation, not a fresh action
ID with the same effect. The active-turn lease prevents an old queued action
from running after end turn.

## Tool and observation contract

Do not use the upstream set of 76 tools as an automatic allowlist. Audit each
operation and every returned field, including narration, errors, map images,
side effects, and background services. The local install is a starting point.

The trusted manifest contains an explicit list of tool names, exact parameter
schemas, implementation hashes, primitive-action counting rules, and observation
schemas. Only rule-enforcing game requests are allowed. The broker verifies
ownership, normal cost, movement, range, prerequisites, and actual post-state.
A successful transport return is not a successful action.

Exclude raw Lua/code execution, player switching, arbitrary reads, save/load,
launch/kill, administrative creation or deletion, resource/research grants,
movement restoration, and unrestricted filesystem or HTTP tools. A helper
may calculate a plan locally but cannot execute arbitrary Lua in the game.
Disable upstream background automation unless its effects are explicitly
allowed, logged, and attributed. Cosmetic camera movement must not leak data.

Allowed observations are own units, own cities, own yields, researched and
available choices, legally available diplomacy, and the player's map view.
Previously revealed terrain may remain known. Enemy units and changing enemy
state require current visibility or a specific, tested in-game information
source. Meeting an opponent does not by itself authorize reading all of its
resources, research, city yields, or hidden cities. A visible enemy identifier
must not allow later hidden-state queries.

The pinned upstream source includes broad rival and victory queries. For
example, `build_rival_snapshot_query` returns yields and resources for met
players, and `build_victory_progress_query` reads multiple players. Their
presence is a reason to audit and filter; this design does not assert that
all those fields are normally public. Privileged validator fields are never
returned to players. Denied-target errors must not reveal hidden entities.

## Fixed evidence contract

Every attempt gets a supervisor-created directory and unique ID before launch.
Do not reuse or overwrite a directory. Save at least these artifacts:

| Artifact | Required content |
| --- | --- |
| `binding.json` | Trusted experiment-lock hash, scenario commitment, phase, round, policy bundle hash, assigned seat, run ID, supervisor identity |
| `initial.json` | Save hash, content/build/settings fingerprint, initial turn/phase, player IDs, normal starting state, no pre-existing terminal result |
| `actions.jsonl` | Contiguous sequence, monotonic time, UTC time, run/turn/seat binding, request and action IDs, validated parameters, response, actual effect and errors |
| `observations.jsonl` | Exact player-facing data, schema hash, source turn and visibility checks; include model-visible tool failures |
| `state.jsonl` | Trusted checkpoints before/after actions and at turn boundaries, terminal event when present |
| `usage.jsonl` | All model requests and agents, model/settings, input/cached/output usage, prices, reservations, settled charges, unknown usage |
| `timing.json` | Start and stop times, completed human turns, turn phase, game speed, pauses, all limit stops and process events |
| `terminal.Civ6Save` | Supervisor-created terminal save and SHA-256; no candidate-selected save |
| `inspection.json` | Fresh inspector process identity, inspected save SHA-256, game/build/hash binding, raw state, comparison outcome, inspection timestamps |
| `result.json` | Reducer's status, game outcome, success flag, reason codes, evidence hashes, earliest decisive event |

Retain policy source, Method trace, helper hashes, prompts, tool definitions,
lock, initial-save fingerprint, software hashes, and human interventions too.
Raw game saves and full logs stay in ignored local storage by default.

SHA-256 detects changed bytes; it does not establish who produced them. The
supervisor/inspector write evidence outside candidate permissions. Their
manifests are authenticated with a supervisor-held key or an equivalently
protected channel, whose identity is in the trusted lock. The reducer obtains
the expected lock and policy hashes from the scheduled job, not from files
supplied by the candidate. Missing trust binding fails closed.

## Terminal truth

Implement a small, separate game-side reader for current game-over state,
winner player/team ID, victory type, current round, turn owner, and player
alive status. Use authoritative engine state or a trusted engine event;
never infer a win from military strength, score, captured city count, narrative,
or `get_victory_progress`. Exact API/event names are an implementation gate.
Prove them on the pinned build before adding them to the lock.

At a possible terminal event, the broker stops new player actions. The
supervisor records the engine result, state, time, and complete counters, and
saves immediately. The inspector starts separately, with no Method and no
candidate code, loads that exact save, and reads the state before any turn or
action advances. It compares winner, victory type, turn/phase, player/team
mapping, settings, alive status, and a fixed fingerprint of cities, units,
research, and treasury against the trusted terminal checkpoint.

If the game does not preserve terminal victory state in saves, the lock cannot
claim that it does. Before launch either demonstrate independent inspection of
a persisted authoritative result or define a new, reviewed evidence contract
with a tamper-resistant engine event and an independent reconstruction of its
terminal condition. Do not weaken the contract during a winning run. Inspector
queries must not repair, advance, grant items, or change the saved world.

## Decision order

The reducer is deterministic. It performs these checks in this order:

1. Verify expected lock and scheduled run identity. Reject missing fields,
   unknown schema versions, non-finite or negative counters, malformed hashes,
   and duplicate run or sequence IDs. Check exact expected artifact set.
2. Verify evidence origin and file hashes. Verify starting-save commitment,
   game/settings/tool/runtime/policy hashes, player mapping, and start state.
3. Verify that limits were enforced before each request. Recompute all totals,
   elapsed times, action counts, completed turns, and missing usage. A late
   tool response cannot erase an earlier stop. Verify actions cannot occur
   after a terminal event, lease end, or deadline.
4. Verify allowed operations, data visibility, process isolation, lack of
   human gameplay, and no policy changes. Reconcile actions with recorded
   game state. Distinguish attributable policy faults from host faults.
5. Verify terminal-save hash, independent inspector identity, unchanged turn
   during inspection, exact required state equality, and terminal result.
6. Emit status and outcome using the table below. Only then compute success.

| Situation | Status | Outcome / success |
| --- | --- | --- |
| Valid engine domination victory for assigned player before any limit, with matching independent inspection | `valid` | `win`, 1 |
| Valid engine victory for opponent or player's verified elimination | `valid` | `loss`, 0 |
| Horizon or enforced budget/time stop, valid evidence, no earlier valid win | `valid` | `incomplete`, 0 |
| Attributable Method crash, exhausted budget, or prohibited-access attempt with healthy trusted host and intact evidence | `policy_failure` | `forfeit`, 0 |
| Wrong world, unexpected settings/victory type, absent or conflicting winner, partial logs, changed hashes, missing usage, broken meter, or failed inspection | `evidence_failure` | `unknown`, no fitness |
| Game crash or failed trusted service that prevents a complete result | `infrastructure_failure` | `unknown`, no fitness |

A stopped run needs valid terminal-state evidence even when it did not win.
If a policy failure also loses required evidence, retain both reasons and use
`evidence_failure` for fitness. A policy cannot turn missing evidence into a
win, draw, promotion, or replay. Preserve any pre-failure result as provisional.

Limits are inclusive ceilings: an event at the exact allowed counter is in
budget; an event after any ceiling is not. Use integer counters and monotonic
clock values. The event must occur no later than the earliest active deadline.
Independent inspection has its own reserved deadline and cannot extend play.
Count completed human turns from trusted ownership transitions, not an assumed
zero- or one-based game turn number. Validate the final pending turn at the
250-turn boundary. Never issue a 251st human turn.

## Promotion and report reducer

Use the paired rule in EXPERIMENT.md exactly. A pair must have the same lock,
scenario hash, phase, prescribed policy versions, recording mode, and budgets.
Both results must be fitness-bearing. An evidence or infrastructure fault
blocks promotion and final winner selection. No implicit score of zero for
an unknown result.

Check the expected schedule, not just the submitted results. Reject a missing
incumbent, duplicate seed, omitted failure, reused result ID, foreign-round
confirmation result, unapproved candidate version, or any extra scored trial.
Release final data only after all four policies' bundles are frozen and the
whole final schedule has a result or an explicit missing-result record.

An offline reducer can be tested with synthetic trusted fixtures. Such tests
prove the decision logic only. They are not live game results. Full validation
also requires the broker, game reader, independent inspector, isolation, and
negative controls below.

## Required acceptance tests

Every test needs retained evidence tied to the exact protected source hashes.
All must pass before the operator seals a scored lock.

| Test | Required result |
| --- | --- |
| Small legal move, research choice, production choice, city founding, attack, end turn | Correct effect and normal cost; own-player authority holds |
| Insufficient movement, funds, range, or prerequisites | No forbidden effect; rejected call remains metered |
| Prepared near-victory fixture followed by one legal winning action | Engine result, live reader, terminal save, and fresh inspector agree |
| Non-winning start, high score, and almost-complete victory | No win |
| Opponent wins; unexpected victory type; wrong winner ID | Loss for opponent win; reject inconsistent rules or mapping |
| Win before/on/after wall, turn, token, action, and spending limits | Only in-budget, fully evidenced wins pass |
| Missing/null/NaN/negative usage, unmetered child, late response | Reject unknown or invalid accounting; no overspend request starts |
| Modify policy/helper/tool/lock/save after freeze | Reject changed bytes |
| Forged candidate `result.json` or fake inspector hash | Reject untrusted origin even when JSON and hashes are internally consistent |
| Replay old event, swap saves, duplicate action, gap in action trace | Reject or deduplicate before mutation; no double action |
| Hidden enemy, met-but-hidden city, remembered tile with moved unit | No data beyond the defined player view, including errors/images/narration |
| Raw Lua, host shell, direct port 4318, dashboard, other seat, other save | Access denied by the process boundary |
| Human action or automatic background game mutation | Detected and disallowed unless already in the locked contract |
| Candidate crash versus game crash | Correct distinct status; no silent retry |
| Reload terminal save in separate process | Exact required state match without advancing the game |
| Starting-save reset repeated three times | Same initial fingerprint; each new trial has separate identity and state |
| Omit losing run or substitute a confirmation seed | Schedule check blocks promotion/report |
| Equal paired results; one paired regression | Keep incumbent |
| Equal final win counts; incomplete final matrix | No competitive winner |

Prepared fixtures are administrative setup tests, not policy achievements.
They need a separate setup allowance and cannot enter search or final samples.
Up to eight game launches of at most ten minutes each are proposed for initial
setup; several prepared controls may run per launch. If coverage does not fit,
stop and request a new setup allocation. Offline parser/reducer tests require
no game launches. These allocations are not adopted spending authorization.

## Additional gates for direct play

Direct play adds tests for both seats on at least three full round transitions:

- A delayed agent cannot let the built-in AI select research, production,
  diplomacy, movement, attacks, purchases, governors, or end turn for its seat.
- Both seats can perform the same allowed actions through normal game rules.
  Switching local context cannot add movement, attacks, free production, or
  research progress. No script repairs the world to hide a control defect.
- A stale capability, simultaneous requests, a batch crossing end turn, and a
  forged `player_id` cannot control the wrong player.
- Each seat sees only its own permitted view; the inspector remains private.
- Crash and timeout while holding a turn lease stop or forfeit as specified,
  without giving either side an extra action or charging the other's clock.
- Side-swapped legs start from the specified state, with equal privileges,
  verified elimination/capital ownership and a correct engine winner.

Unit freezing and a successful player-switch call alone do not pass these
checks. If fair control cannot be demonstrated, direct play remains blocked.
