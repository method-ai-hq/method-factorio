# Run the environment tests

Use the local setup in [run-control-test.md](run-control-test.md). These tests
use native Factorio. Docker is not required. Model tests require Codex to be
signed in through ChatGPT. The runners remove API-key overrides and do not
start separate paid API experiments.

Use new run names. The runners preserve earlier results and reject existing
run folders. Start the following commands in separate terminals to run the
four baselines at the same time:

```sh
# A and B run concurrently, each with its own game server.
.venv/bin/python scripts/compare_agent_baselines.py --batch compare-ab --seeds 44341 44342

# C uses a restricted Unix socket with the same FLE actions and state checks.
.venv/bin/python scripts/compare_fle_baseline.py --batch compare-c --seeds 44341 44342

# D runs fixed actions without a model, at three game speeds.
.venv/bin/python scripts/scripted_benchmark.py --prefix compare-d

# Separate operator fixtures test selected advanced FLE controls.
.venv/bin/python scripts/capability_probe.py --run compare-capabilities
```

After D finishes, use its ports for the separate batching checks:

```sh
.venv/bin/python scripts/scripted_benchmark.py --prefix compare-batches --batch-only --speeds 1
```

Each command writes its records to ignored `runs/` folders. Keep those files
for diagnosis. Review evidence before adding it to Git. Do not publish native
server logs, credentials, model event logs, or game saves.

## Ports and limits

| Test | HTTP | RCON | Game UDP |
| --- | --- | --- | --- |
| A | 18801 | 27201 | 34301 |
| B | 18802 | 27202 | 34302 |
| C | Unix socket | 27203 | 34303 |
| D | 18804 or Unix socket | 27204 | 34304 |
| Advanced fixtures | None | 27205 | 34305 |

Do not run two copies of a lane at once. The game host assigns separate save
folders and binds network services to the local machine. Unix socket files
have owner-only permissions. RCON belongs to the operator; the playing agent
receives only the restricted connection.

A, B, and C use game speed 1, FLE fast mode, and a running game during model
thinking. Each host permits 900 seconds and 200 actions. The playing prompt
permits 120 requests and 12 minutes. The default batch limit is 35 minutes.
The Method also runs its connection and output checks. All model work counts
toward the reported trial time and token use where the runtime exposes it.

C is the matched connection test: it keeps the action list and full state
checks from A. It does not expose all native FLE tools. Native responses,
cached handles, and wider controls need separate tests.

The host accepts a separate batch form, `{"batch": [action, action]}`, with
1 to 50 action objects. It counts and records each action, reads state after
each one, and stops at the first error. A, B, and C were given the single-action
guide; the fixed script tested batching separately.

D changes game speed only during operator setup. Its production check tests
real ore and fuel use and 20 furnace outputs at the declared speed. The
original small-test evaluator still requires speed 1, so accelerated runs do
not pass that evaluator. Do not change its rule to make those runs pass.

## Inspect a terminal save

After a host stops cleanly, load its terminal save in a separate server:

```sh
.venv/bin/python scripts/inspect_save.py runs/compare-c-c-44341 --rcon-port 27213 --game-port 34313
```

This compares game state from the loaded save with the host's final snapshot.
It does not resume an active FLE episode. The inspection folder must be new.
Use different inspection ports for simultaneous checks.

## Read results

Keep production success, control errors, and infrastructure errors separate.
A live production result without a valid final save fails the full small-test
check. An operator-prepared fixture is not a fresh-world result. A rocket
event from a prepared silo is not an agent-built rocket.

Compare matching seeds. Report startup, time to first verified production,
complete trial time, game time, tool time, model use, and errors separately.
Parallel runs share the same machine and subscription capacity. Their wall
times are useful pilot measurements, not isolated speed rankings.

See [the test design](environment-validation.md) for the full coverage list
and [the first parallel results](../evidence/environment-validation-2026-09-10/README.md)
for measured results and remaining gaps.
