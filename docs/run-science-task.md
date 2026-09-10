# Run the science task

The [fixed task](science-task.md) uses a new native host. The old
`search_host.py`, trial scheduler, and iron-plate candidates still implement
the old task. Do not send an old candidate to the science task without giving
its author the new objective and tool contract.

## Start a game

From the repository, with the existing Python environment and licensed
Factorio installation:

```sh
.venv/bin/python scripts/science_host.py --run science-dev-1 --seed 101
```

Use a new run name for each attempt. The host prints a ready message with the
endpoint, normally `http://127.0.0.1:18880/action`. It starts one headless game,
makes no model calls, and records no video. All raw evidence stays in ignored
`runs/`. It saves and closes after measurement, a stop signal, or the time limit.

`--port`, `--rcon-port`, and `--game-port` select separate ports. Do not launch
another host on occupied ports. `--factorio` can select another installation;
the verifier still requires the fixed game version.

## Playing tools

POST a JSON object to `/action`. Responses contain `ok`, plus `result` or
`error`. An error does not prove that an action had no effect; inspect before
retrying. A `place` response gives the actual position, which can differ from
the requested position because Factorio snaps entities to its grid.

| Action | Example request |
| --- | --- |
| Inspect the world | `{"action":"observe"}` |
| Locate deposits | `{"action":"resources"}` |
| Read allowed recipes and their costs | `{"action":"recipes"}` |
| Place supplied equipment | `{"action":"place","item":"electric-mining-drill","position":{"x":10.5,"y":80.5},"direction":"UP"}` |
| Set an assembler's recipe | `{"action":"recipe","name":"assembling-machine-3","position":{"x":0.5,"y":0.5},"recipe":"electronic-circuit"}` |
| Rotate equipment | `{"action":"rotate","name":"fast-inserter","position":{"x":4.5,"y":0.5},"direction":"LEFT"}` |
| Recover equipment | `{"action":"pickup","name":"transport-belt","position":{"x":4.5,"y":0.5}}` |
| Start the final check | `{"action":"finish"}` |

Directions are `UP`, `RIGHT`, `DOWN`, and `LEFT`. Underground belt placement
also accepts `"type":"input"` or `"type":"output"`. A batch has the shape
`{"batch":[ACTION,ACTION]}` and accepts 1–50 actions. It stops at the first
error. Send `finish` last and make no further calls after it.

Observations include equipment stock, machine positions, recipes, status,
energy, inventories, completed recipes, inserter pickup and drop positions,
belt contents, remaining ore, and game production totals. Machine status uses
Factorio's numeric status codes. Recipe information comes from the installed
game, not a hard-coded construction plan. By default, the entity list contains
production machines, inserters, and chests. To inspect other equipment, supply
names, for example `{"action":"observe","names":["transport-belt","medium-electric-pole"]}`.
An empty names array returns totals without an entity list.

The existing `scripts/method3_run.py` can give a Method this endpoint through
its `--endpoint` argument. Its `observe`, `act`, and bounded `compute` tools
use the same JSON transport. Code steps can also call the endpoint. A search
must separately preserve the Method bundle, model usage, and its budget.
The old search scheduler is not wired to this new contract.

## Verify the terminal save

After the host exits:

```sh
.venv/bin/python scripts/science_verify.py runs/science-dev-1
```

The verifier opens a copy of `game/world.zip` in another Factorio process. It
does not repair or advance the save. It writes `verdict.json` and exits with
status 0 only for a verified pass. Default inspection ports are 27881 and
34881; use `--rcon-port` and `--game-port` to select free ports.

The main evidence files are `actions.jsonl`, `record.json`, `game/world.zip`,
and `verdict.json`. A pass proves this task's production conditions under the
declared control interface. It does not establish policy authorship, honest
model-cost accounting, a fresh-world rocket win, or improvement between Methods.

## Check the checker

Offline checks:

```sh
.venv/bin/python -m unittest discover -s scripts -p 'test_science.py' -v
```

Operator-only real-game checks, with no model calls:

```sh
.venv/bin/python scripts/science_validation.py --run science-check-1
```

The suite builds a reference through the public HTTP host, then tests an empty
world, red-only production, lost power, disconnected copper, a wrong recipe,
stored materials without mining, failure in the third minute, a forbidden
transfer, and an action after finish. Each terminal save is checked separately.
These tests use ports 18885, 27885, 34885, 27881, and 34881.

The reference code and deliberate faults are operator test equipment. They
must stay outside the playing tool interface and policy-author input.

## Trust boundary

The HTTP action interface has no game administration or arbitrary Lua entry
point. The host holds a private random RCON password. The verifier rejects
missing evidence and differences between saved and live records.

This is a local experiment runner, not an operating-system sandbox. A hostile
code step with unrestricted access to the same user account could attack
processes or files. Use reviewed local code, or put the host and verifier in a
separate security boundary before accepting untrusted code. Do not claim
tamper-proof execution from source hashes alone.

The implementation uses Factorio's [entity inventory and recipe APIs](https://lua-api.factorio.com/latest/classes/LuaEntity.html).
Live validation, rather than the latest documentation version, establishes
compatibility with the pinned 2.0.77 installation.
