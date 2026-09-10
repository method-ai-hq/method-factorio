# StarCraft II setup

This is the first setup stage for a separate Method policy-search environment.
It uses [DeepMind PySC2](https://github.com/google-deepmind/pysc2) and
[Blizzard's StarCraft II API](https://github.com/Blizzard/s2client-proto).
The game runs on the local computer. The control library comes from the web;
this setup does not run StarCraft II in a browser.

## Current result

Checked on 10 September 2026, on macOS 26.0.1 with an Apple Silicon processor:

- Python 3.10.16 and PySC2 4.0.0 are installed in `local/sc2/.venv`.
- All 27 installed package versions are fixed in `requirements.lock`.
- Imports and the package dependency check passed.
- The offline test passed: simulated observations, step, reset, and movement
  action encoding through Blizzard's protocol. This test does not use a game.
- The seven official PySC2 mini-game maps are downloaded and their archive
  hash is checked. They are staged in `local/sc2/Maps/mini_games`.
- Battle.net is installed in `/Applications/Battle.net.app` and needs sign-in.
- StarCraft II is not installed. The live control test has not run.

There is no measured game result, Method integration, policy search, or tested
parallel game capacity yet. No model API call is part of these setup commands.

## Install

Run commands from the repository root. Install `uv` first if it is unavailable.

```sh
bash environments/sc2/setup.sh
```

The script uses a separate Python environment. It does not change the Factorio
environment. Python 3.10 is used to support this older PySC2 release. Protobuf
3.20.3 and NumPy 1.26.4 are fixed for the installed stack. Do not remove these
version limits without another compatibility check.

On this Mac, open Battle.net, sign in, select StarCraft II, and install the free
game. Use `/Applications/StarCraft II` unless another location is needed. Start
the game once and finish its first-run setup, then exit the game. Enter account
information only in Battle.net. Game files and account data stay outside Git.

PySC2's guide specifies the normal Battle.net client for macOS and Windows.
Blizzard also supplies separate Linux game packages. Linux installation and
Apple Silicon game execution have not been tested here.

After the game is installed, copy the staged maps and check the setup:

```sh
export SC2PATH='/Applications/StarCraft II'
mkdir -p "$SC2PATH/Maps"
cp -Rn local/sc2/Maps/mini_games "$SC2PATH/Maps/"
local/sc2/.venv/bin/python environments/sc2/control.py doctor
```

Set `SC2PATH` to the game folder if the path differs. The doctor checks the game
executable and reads the test map through PySC2. It returns code 2 if a required
file is missing. `ready_for_live_check` means files are present; it does not mean
the game API works.

## Check control

```sh
local/sc2/.venv/bin/python environments/sc2/control.py offline
local/sc2/.venv/bin/python environments/sc2/control.py smoke
```

The live check launches one game on `MoveToBeacon`, with seed 1, a 64 by 64
feature screen, and fog of war enabled. It uses PySC2's existing scripted agent.
It has a limit of 256 action steps, 2,048 game loops, and 180 wall-clock seconds.
Game speed uses the game API default and has not been measured. With `realtime=False`, game time
advances through API step calls. The game may still open a native window on Mac;
`visualize=False` disables PySC2's extra viewer.

The check must send a movement action, observe advancing game loops, receive a
positive game reward, and save a replay. It saves settings, actions, reward,
game loops, separate wall time, errors, and a replay hash under a new
`runs/sc2/` folder. Failed attempts stay in place. A saved replay is not an
independent replay-verification result. This check does not establish full-game
control, a match win, or a valid policy-search evaluator.

For custom Python control, use `pysc2.env.sc2_env.SC2Env`. Call `reset()` for an
initial observation, submit `pysc2.lib.actions.FunctionCall` values with `step()`,
and read observations and rewards from the returned time steps. See the
[upstream environment guide](https://github.com/google-deepmind/pysc2/blob/master/docs/environment.md).
The small live check in `control.py` is a complete local example.

## Before policy search

Choose the task, seed sets, action and observation interface, game-time mode,
and limits before scored trials. Keep game setup, debug commands, and evaluation
outside the playing interface. The full upstream API has administrative powers;
this operator script is not a restricted Method tool server or a security
boundary. Validate one native client before testing a higher capacity. Set an
operator spending cap before any paid model experiment.

PySC2, Blizzard's protocol, the mini-game maps, and StarCraft II are prior work.
This repository adds only dependency pins, setup instructions, and control
checks. Game files, downloaded maps, and raw local results are ignored by Git.
