# Method v3 policy candidates

Status: setup stopped before policy trials. There are eleven candidate
Methods and two baseline Methods. All thirteen passed `method3 validate`.
None ran in a scored game trial. No winner was selected and no improvement
was measured. See `validation-summary.json` for the complete frozen index.

These policies were authored by Astra through the Codex subscription. The
author received the task, tool shapes, kit, limits, and observation fields.
The author did not inspect the evaluator, reference factory, or hidden maps.

The initial Method was saved and validated before any gameplay feedback.
The first eleven candidates were also authored before gameplay feedback.
Their hypotheses are design claims, not measured results.

Use the separate folders under `bundles/` for trials. Each folder contains
the Method, its helper files, metadata, and a SHA256 freeze record. Do not
edit a frozen bundle. Create a new version to make a change. `index.json`
lists the exact Method paths.

| ID | Control logic | Parent |
| --- | --- | --- |
| b00 | Initial direct agent with the objective and game tools | None |
| b01 | Direct agent with the same objective and generic bounded Python tool | b00 |
| p01 | Initial agent with observe, build, and inspect checkpoints | None |
| p02 | Observation and plan agent, then a fresh build agent | p01 |
| p03 | Build agent, then a fresh repair agent | p01 |
| p04 | Low-reasoning agent with explicit geometry checks | p01 |
| p05 | Code derives a short route from actual drop and pickup positions | p01 |
| p06 | Code extends the route by one belt to increase clearance | p01 |
| p07 | Code makes a right-angle route to use space beside the drill | p01 |
| p08 | Code builds a seed factory, then an agent inspects and repairs it | p05 |
| p09 | Up to five short agent cycles with compact saved memory | p01 |
| p10 | Code recovers the kit and tries another downstream direction | p05 |
| p11 | Fixed read code, one planning call, then an acting agent | p02 |

All thirteen documents passed the public `method3 validate` command. Execution
and game results belong to the supervisor's trial index. A valid document
or a Method check does not prove that the factory passed the game test.

Both baselines use the same model profile and game action interface as the
initial Method. Their single agents choose their own procedures from the
objective. b01 adds the generic bounded `compute` tool, so it can write code
that uses the allowed game actions. It receives no factory plan. All can use
the `act` tool to submit batches. Native dynamic model-profile selection is
not available to these agents; the baseline uses the planner profile. Code-only
candidates make no model calls. The helper code contains only restricted
game requests; it has no API key or evaluator access.

For example, from the repository root:

```sh
python3 scripts/method3_run.py \
  policies/search-v3/bundles/p01-initial/p01-initial.method \
  --endpoint http://127.0.0.1:18901/action \
  --output runs/example-p01-runtime \
  --deadline 2026-09-10T17:17:12Z --seconds 270
```

The endpoint must belong to a fresh trial under the fixed contract, with
recording already active. This command alone does not start a game, record
footage, evaluate the factory, or inspect the terminal save. The supervisor
must provide those controls and preserve failed attempts.
