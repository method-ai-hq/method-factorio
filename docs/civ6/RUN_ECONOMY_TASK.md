# Civ 6 economy task: setup and verifier

This is an implemented **base-game calibration case**, not a frozen scored
benchmark. The task is the accepted three-city research economy. Its targets
are unchanged: retain the capital; found two cities; reach population 3 in each;
keep science at least 20, gold and net income nonnegative, and food surplus
nonnegative in the three cities for five full rounds; finish within 35 turns.

The installed game returned `OwnershipRequired` for Gathering Storm. Setting
`RULESET_EXPANSION_2` alone did not load its rules. This case therefore uses
`RULESET_STANDARD`, with an explicit check that Gathering Storm is absent.
A future Gathering Storm case needs a different save and profile. Do not
compare their results as the same task.

## What is ready

- An actual local starting save, with a SHA-256 hash and inspected state.
- Operator commands to create, save, load, and inspect the game.
- A read-only state reader with full numeric precision and no queue repair.
- A live event monitor for turn boundaries and city birth/removal events.
- An exact predicate and trace verifier with signed evidence, action order,
  turn limits, capital retention, a fixed city pair, and a separate reload check.
- Offline control tests and an operator-only empty-turn control.

The evidence directory is
`evidence/civ6-economy-setup-2026-09-10`. Game saves and private signed traces
stay under the local game save directory and `runs/`; they are not in Git.

## Fixed starting case

The local save is **CivTask_Economy_Base_Start_v2**. The filename revision records
setup corrections; it is not Method v2. The profile fixes the actual save hash.

- Trajan/Rome; Prince; Ancient era; Online speed; Duel Pangaea, 44 by 26 tiles.
- Map seed 6100910; game seed 6100911.
- One human major player, no AI major players, and no city-states.
- Barbarians and tribal villages disabled. The engine still lists its dormant
  barbarian player 63. The base rules have no Gathering Storm disasters.
- No community mods. The official Aztec pack is active and recorded.
- One capital at (32, 12), population 4, food store 0, food surplus 2,
  housing 6, production 6, and science 4.796875.
- Palace and Trajan's free Monument only; city center only; empty production
  queue; zero stored production for units, buildings, districts, and projects.
- 50 gold; net gold income 5; one undamaged Warrior, Scout, and Builder.
  The Builder has three charges. There is no Settler or Trader.
- Mining, Pottery, and Animal Husbandry complete. Writing is absent. There are
  no other completed technologies, civics, or stored research/civic progress.
- Chiefdom; empty policy slots. Governors are absent in the base rules.
- Quick movement and combat enabled; automatic end turn and advisor tutorials disabled.

The save pins the whole world, including terrain, fog, improvements, bonuses,
and purchase rules. The JSON reader lists selected state fields; it is not a
complete replacement for the binary save. Starting-kit checks do not certify
that the map has enough useful settlement choices or that the task is feasible.
Those are calibration checks still to do. Do not give the operator's hidden
state or files to the playing Method.

## Commands on this Mac

Use the installed MCP environment's Python. The system Python is not used.

```sh
CIV_PY="$HOME/.local/share/civ6-mcp/.venv/bin/python"
"$CIV_PY" scripts/civ6_admin.py --load CivTask_Economy_Base_Start_v2
```

Close the leader loading screen with Escape. The debug connection does not
respond while that screen is open. A load request is not proof of a reload.
Use a new process to inspect the resulting state:

```sh
"$CIV_PY" scripts/civ6_admin.py --snapshot --output runs/start-inspection.json
"$CIV_PY" scripts/civ6_verify.py --start evidence/civ6-economy-setup-2026-09-10/start-state.json
"$CIV_PY" -m unittest discover -s scripts -p test_civ6.py -v
```

The snapshot command wraps the state in `result` and records read time.
The verifier's `--start` input is the unwrapped state. Its starting-kit result
is a setup check, not task completion.

For the live empty-turn control, first load the exact starting save. Use a new
output directory for each attempt. The command refuses an existing directory.

```sh
"$CIV_PY" scripts/civ6_smoke.py --output runs/civ6-control-NEW --turns 35
```

The command prints the terminal save name. Load that name through
`civ6_admin.py --load`, close the load screen, then run in a new process:

```sh
"$CIV_PY" scripts/civ6_smoke.py --output runs/civ6-control-NEW --finish
```

The control writes a signed partial trace after each turn. After the terminal
save it changes the live treasury as a reload marker, outside the trial.
The separate finish process must find the exact pre-marker saved state.
It includes capture, save, reload, and inspection time in the final duration.
Keep the private key and partial traces. Do not publish the key. A delayed
manual reload can exceed the profile's 600-second control limit; preserve that
failure and use a new attempt rather than changing its clock.

The current control profile allows one graphical game, no recording, no model
calls, 35 turns, 600 seconds, and 1,500 actions. These are local calibration
limits. They are not authorization for paid continuous search.

## Rebuild the case

Use the existing hashed save for comparisons. A seed alone is not a reset.
To rebuild, start at the main menu, disable community mods, and run these
operator scripts in order:

1. `civ6_new_game.lua` in `main` context. Close the loading screen.
2. `civ6_found_start.lua` in `ingame` context. Check that the capital exists.
3. `civ6_prepare.lua` in `gamecore` context.
4. Inspect the state, save to a new name, reload it, and inspect again.
5. Review a new manifest and hash. Do not replace the old profile silently.

The preparation script uses engine administration to supply the starting kit.
It is never a playing tool. An early setup used `SetTech` alone; the UI remained
stale. Preparation now completes research through `SetResearchProgress`.
Validate the resulting technologies in the loaded save.

Only one client may own the FireTuner connection. The operator wrapper uses a
local file lock. Unmodified MCP servers do not obey that lock. Stop or disable
other Civ MCP connections during a control. Do not kill unrelated game clients
or erase user saves. User mod preferences must be restored after setup.

## Evidence and trust

`civ6_monitor.lua` runs in InGame after `civ6_snapshot.lua`. It takes an atomic
snapshot in the player's `PlayerTurnActivated` callback. The operator also
requests a checkpoint after every game-changing action and before ending a
turn. The capture process must drain every event in order and reject gaps.

The verifier requires six successive healthy turn boundaries spanning five
rounds. The same pair of self-founded cities must qualify throughout. An
unhealthy action checkpoint resets that pair's count. Capital loss rejects the
attempt even if the capital returns. Science 19.96 fails; a displayed rounded
20 does not change the threshold. A one-time research boost is not recurring
science. Gross gold income does not replace net income.

The trace format has start, action begin, action result, city birth/removal,
turn-end, boundary, and finish records. Each line has an HMAC linked to the
previous line. This proves that a protected recorder wrote the bytes, provided
its key and process are protected. It cannot prove that an unrestricted agent
with the same filesystem and FireTuner access behaved honestly.

The current command always reports `verified_pass: false`. It can report
`calibration_goal_met` for complete control evidence. Scored use is blocked
until the action broker, player isolation, and calibration are reviewed. Do
not remove that gate merely because a synthetic fixture passes.

## Remaining work before continuous search

- Build and test the restricted playing broker. The raw upstream MCP includes
  Lua, save/load, and administration. It is not the experiment interface.
- Validate all allowed actions, event completeness, and city ownership changes.
  Simple founding and removal events passed live fixture checks. Capture,
  recapture, and all action interleavings still need checks.
- Run a legal reference policy that reaches the target. Establish that 35 turns
  is feasible, then check that a simple greedy policy does not make it trivial.
- Check settlement alternatives and delayed effects. Create the rest of the
  development, promotion, and held-out starting corpus before scored search.
- Set the playing model, token and action limits, spending cap, and full trial
  clock. Pin the broker, reader, verifier, and local MCP patch hashes.
- Test a live successful trace and its independent terminal reload. The current
  positive traces are synthetic verifier controls, not game achievements.

## Speed and headless operation

Civ 6 has no supported Factorio-style 5x or 20x simulation clock in this setup.
The installed speed data has cost multipliers of 100 for Standard, 67 for Quick,
and 50 for Online. Online reduces many turn-based costs; it does not make the
engine process turns at 20x speed. It can be used in single-player.

Quick movement and quick combat remove animation delays. The actual throughput
also depends on map size, actors, tool calls, model latency, save/load, and
rendering. Empty-turn measurements do not predict a full policy's run time.

No supported native headless mode was found for the installed Mac game or
[this MCP](https://github.com/lmwilki/civ6-mcp/blob/dd2019056371b92ea4854e879ddf05a8cad95e8a/README.md).
This setup uses the normal graphical client without video recording. Background,
minimized, or virtual-display operation has not been validated here; none is
claimed as a native headless server.
