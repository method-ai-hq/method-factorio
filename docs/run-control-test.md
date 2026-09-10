# Run the first production test

This test uses the native macOS Factorio server, FLE, and the installed Method
SDK. Docker is not required. It uses Codex signed in through ChatGPT. It makes
no separate paid API calls and does not purchase credits or use a reset.

## Requirements

- A licensed full Factorio installation at `/Applications/factorio.app`.
- Python 3.12 and uv.
- Method SDK 0.3.0 with the `method` and `method-run` commands.
- Codex CLI signed in with ChatGPT and access to `gpt-6-astra`.
- Local ports 18765, 27117, and 34217 available.

The installed Method SDK is prior work. Do not copy private workspace source
into this repository. The test does not establish support for other SDK or
game versions.

## Setup

Run these commands from this repository:

```sh
mkdir -p local/deps
git clone https://github.com/JackHopkins/factorio-learning-environment.git local/deps/fle
git -C local/deps/fle checkout e2a829d22a635a9a111d21bf5523e09e903ae145
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
codex login status
method doctor
method validate policies/iron-plates-v1.method
```

If the dependency checkout or environment already exists, inspect it before
making a new one. Use `codex login` for browser sign-in if needed. Do not put
credentials in chat or in this repository.

## Run

```sh
.venv/bin/python scripts/run_method_test.py --run my-first-test --seed 44340
```

Use a new run name each time. The command starts an isolated game data folder,
runs the Method, stops the game, and checks the recorded production. Run it
again with another seed to test the same Method in a new world. Neither run
is a scored rocket trial or evidence of a reliable success rate.

The host limit is 20 minutes and 200 actions. An individual action can use at
most 90 seconds. The playing step is instructed to use at most 12 minutes and
120 requests. Method enforces a 12-minute process limit per operation; the
host enforces the overall limit. The game runs during model thinking at speed
1. Setup and final save operations can pause the game. Save operations do not
form part of gameplay.

## Evidence

Each ignored `runs/NAME/` folder contains starting and final observations,
settings, action records, and Method outputs. `game/fresh.zip` is the original
map. `game/final.zip` is a terminal inspection save. FLE runtime functions are
removed before this save, because Factorio cannot save them in its storage.
This save is for inspection; the test does not yet support resuming the FLE
playing process from it. Failed setup and gameplay records must be kept.

`scripts/check_result.py` checks the fixed goal from recorded game data.
Method also makes an independent read of the live game after the playing step.
A model's claim alone does not pass the test.

The HTTP interface rejects undeclared actions and never accepts raw code or
administrative commands. The current Method runtime still gives its Codex
processes shell access under the same macOS account. This is an API boundary,
not an operating-system security boundary against a hostile playing process.
Stronger process isolation remains work for a scored experiment.

Read [control-api.md](control-api.md) for the available actions and their limits.
Raw logs and game saves stay out of Git. Publish only reviewed result data.
