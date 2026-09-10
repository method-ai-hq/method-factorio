# Method 3 runtime

**Status: runtime checks passed; game scoring is not approved. Zero scored
policy trials ran.** The setup episode limit was reached before the required
negative game references passed. The scripts below are retained for review.
Do not treat the trial or scheduler integration as validated game execution.

The search uses the public `@withmethod/runtime` executor version 0.1.0.
It does not use SDK 0.3.0 or the earlier Method CLI. The source revision is
`eec2cfd1a5f0bd8254fb8213b88be76cff44ad21`.

The [public Method 3 reference](https://github.com/method-ai-hq/method-spec/blob/eec2cfd1a5f0bd8254fb8213b88be76cff44ad21/spec/method-3.md)
defines the file format and execution rules. Install the public source in the
ignored local run directory:

```sh
git clone https://github.com/method-ai-hq/method-spec.git runs/method3-runtime
git -C runs/method3-runtime checkout eec2cfd1a5f0bd8254fb8213b88be76cff44ad21
npm ci --ignore-scripts --prefix runs/method3-runtime
npm run check --prefix runs/method3-runtime
scripts/method3 --version
```

Node 22 or later is required. The tested Node version was 22.22.2. The version
command returned `0.1.0 (method/3)`. The public schema checks and all 40 tests
passed on 10 September 2026.

## Model profiles

The runtime sends `call` and `agent` steps directly to the OpenAI Responses API.
It runs `run` steps as JSON input/output processes. No helper script makes a
model call. The game tools receive no API key.

The generic `compute` tool is a prepared integration. It accepts bounded Python
code with calculations and permitted game actions. It rejects imports and
attribute access. It has no model calls. A local calculation passed before the
final cleanup edit; the complete agent use was not tested. This is a language
restriction, not an operating-system security boundary or a memory quota.

| Profile | API model | Reasoning effort | Maximum output tokens per request |
| --- | --- | --- | --- |
| `planner` | `gpt-6-astra` | `medium` | 4096 |
| `fast` | `gpt-6-astra` | `low` | 4096 |

An authenticated `GET /v1/models/gpt-6-astra` confirmed access on 10 September
2026. The [official model page](https://developers.openai.com/api/docs/models/gpt-6-astra)
lists both reasoning settings, function tools, and structured output support.
The live runtime smoke test used one `call`, one `agent`, and a real local
increment tool. It returned the expected value 42. Its three model requests
used 442 input tokens and 43 output tokens. Runtime elapsed time was 8.02 seconds.
This checks runtime integration. It is not a game trial.

The known smoke cost estimate was $0.00657. Estimates use the published standard
rates of $10 per million input tokens, $1 per million cached input tokens, and
$50 per million output tokens. Long input rates are applied above 272,000 input
tokens. These are estimates, not invoices. Unknown usage and possible cache-write
charges remain unknown. Each trial retains the estimate and its source.

## Run one Method

The wrapper validates the Method before execution. It checks the public source
revision and rejects changes to that source. Each output folder contains the
configuration, CLI and Node hashes, private source copy, runtime manifest,
trace, timing, and usage estimate. It never reuses an output folder.

The operator must supply a live restricted game endpoint and an authorized
absolute job deadline. For example, during the original job:

```sh
python3 scripts/method3_run.py \
  policies/search-v3/bundles/p01-initial/p01-initial.method \
  --endpoint http://127.0.0.1:18901/action \
  --output runs/example-trial-runtime \
  --deadline 2026-09-10T17:17:12Z \
  --seconds 270
```

This wrapper reads only `OPENAI_API_KEY` from `~/.codex/secrets.env` and supplies
it only to the Method runtime when a model step exists. A run-only smoke check
passed with zero model requests and no key in its helper environment. It does
not print the value. A new job needs a
new authorized deadline. The old command refuses to run after its deadline.

The shared run limits allow at most 60 model requests, 60 tool calls, and 100
step invocations. Step limits can be lower. The game host separately checks
game action limits. All limits apply to the whole Method, including checks and
repeated steps. A batch member counts as a game action at the host.

## Game transport and complete trials

The `observe` tool takes `{endpoint}`. The `act` tool takes `{endpoint, action}`,
where `action` is a JSON string. Both return `{response}`, where `response` is
the full JSON game reply encoded as text. The host checks permitted actions.
The helper has no game administration connection. The prepared helper accepts
any loopback HTTP endpoint supplied as input; it does not enforce the operator's
exact game URL. Stronger endpoint binding remains work for a future setup.

The `search_trial.py` command starts a fresh host, runs the Method, stops its
processes, reloads the terminal save in a separate server, and records the
fixed verdict. It requires an approved `benchmark-freeze.json` in the job
directory and verifies its file hashes before and after the trial. Every
attempt appends a result to `index.jsonl`, including failures.

```sh
.venv/bin/python scripts/search_trial.py \
  --job-dir runs/search-v3-20260910 \
  --policy policies/search-v3/bundles/p01-initial/p01-initial.method \
  --case initial-development-1 --seed 61001 --map-x 16 --map-y 0 \
  --lane 1 --deadline 1789060632 --kind development
```

Each lane needs separate ports and a recording peer. The trial directory links
the video, action trace, runtime trace, terminal save, independent inspection,
and verdict. A process result or a model report does not establish a game pass.

The save inspector reinstalls only the trusted snapshot function. It does not
advance or repair the game. It compares tick, pause setting, speed, position,
inventory, machine state, furnace state, research, production, remaining ore,
and enemies. List positions and item values must match. Inspection stops
within 30 seconds or at the job deadline.

Raw game files, model records, and recordings stay in ignored `runs/` folders.
Review evidence before public release. Model execution uses the paid API;
policy author work in Codex uses the subscription and is reported separately.

## Headless trials and recovery

The owner now permits optimization without video. The trial runner reads
`recording_mode` from the approved fixed manifest. Mode `none` requires
contract `automatic-production/headless-1`; it still requires action/state
records and a matching terminal save inspection. See
[the current contract and commands](headless-policy-search.md).

`search_schedule.py` defaults to two worlds and rejects concurrency above the
validated level in the manifest. It starts native clients one at a time.
It keeps pending work when it stops launching and can perform one recorded
serial replacement for a declared graphics-loading fault when the fixed
settings authorize it. See [the proposed next goal](headless-search-goal.md)
for the supervisor's repair procedure and explicit next-job limits.
