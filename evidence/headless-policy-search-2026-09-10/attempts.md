# Headless Method v3 policy search

Comparison complete.

Job: `headless-search-20260910T174026Z`. Deadline: `2026-09-10T18:40:26Z`.

Setup checks: 18/18. Scored attempts: 21. Final attempts: 4.

Known API cost estimate: $2.498. Total cost is not fully known.

| Version hash | Phase | Policy | Attempts | Passes | Mean time with failure penalty (s) | Known API cost ($) |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 75e3282e1ce1 | development | b01-direct-code-access.method | 1 | 1 | 44.326 | 0.202 |
| 75e3282e1ce1 | development | p01-initial.method | 1 | 0 | 330.000 | 0.184 |
| 9cfd15d3e5ef | development | b01-direct-code-access.method | 3 | 2 | 138.860 | 0.422 |
| 9cfd15d3e5ef | development | p05-observed-geometry.method | 3 | 3 | 8.737 | 0.000 |
| 9cfd15d3e5ef | development | p08-code-agent-repair.method | 3 | 3 | 19.823 | 0.217 |
| 9cfd15d3e5ef | development | p01-initial.method | 3 | 3 | 51.332 | 0.670 |
| 9cfd15d3e5ef | development | p10-direction-retry.method | 3 | 3 | 8.615 | 0.000 |
| 9cfd15d3e5ef | final | p10-direction-retry.method | 2 | 2 | 9.063 | 0.000 |
| 9cfd15d3e5ef | final | p01-initial.method | 2 | 2 | 51.783 | 0.418 |

Each source version has its own panel in summary.json. All attempts follow.

| Trial | Pass | Production (s) | Save check (s) | Full time (s) | Actions |
| --- | --- | ---: | ---: | ---: | ---: |
| headless-search-20260910T174026Z-b01-direct-code-access-dev1-2074c8 | True | 39.781 | 0.701 | 44.326 | 13 |
| headless-search-20260910T174026Z-p01-initial-dev1-8da74b | False | unknown | unknown | 44.502 | 13 |
| headless-search-20260910T174026Z-b01-direct-code-access-dev1-82daab | False | unknown | 0.651 | 18.524 | 4 |
| headless-search-20260910T174026Z-p05-observed-geometry-dev1-8e50d9 | True | 7.779 | 0.650 | 8.885 | 12 |
| headless-search-20260910T174026Z-p08-code-agent-repair-dev1-ef3249 | True | 13.405 | 0.696 | 17.900 | 14 |
| headless-search-20260910T174026Z-p01-initial-dev1-8e23ab | True | 48.283 | 0.608 | 53.561 | 13 |
| headless-search-20260910T174026Z-p10-direction-retry-dev1-b1c063 | True | 7.493 | 0.647 | 8.924 | 13 |
| headless-search-20260910T174026Z-p01-initial-dev2-301d6d | True | 42.989 | 0.762 | 48.206 | 13 |
| headless-search-20260910T174026Z-b01-direct-code-access-dev2-fa5101 | True | 43.163 | 0.660 | 49.570 | 12 |
| headless-search-20260910T174026Z-p05-observed-geometry-dev2-8f7eda | True | 7.372 | 0.644 | 8.530 | 12 |
| headless-search-20260910T174026Z-p10-direction-retry-dev2-c57959 | True | 7.060 | 0.607 | 8.249 | 13 |
| headless-search-20260910T174026Z-p08-code-agent-repair-dev2-8f1ac4 | True | 17.370 | 0.649 | 21.756 | 14 |
| headless-search-20260910T174026Z-b01-direct-code-access-dev3-577a50 | True | 31.864 | 0.751 | 37.010 | 12 |
| headless-search-20260910T174026Z-p05-observed-geometry-dev3-963518 | True | 7.455 | 0.653 | 8.795 | 12 |
| headless-search-20260910T174026Z-p01-initial-dev3-15ae20 | True | 47.920 | 0.643 | 52.230 | 15 |
| headless-search-20260910T174026Z-p08-code-agent-repair-dev3-cced1f | True | 13.728 | 0.608 | 19.812 | 14 |
| headless-search-20260910T174026Z-p10-direction-retry-dev3-34a8bf | True | 7.330 | 0.604 | 8.671 | 13 |
| headless-search-20260910T174026Z-p10-direction-retry-final1-ea68a7 | True | 7.649 | 0.648 | 9.032 | 13 |
| headless-search-20260910T174026Z-p01-initial-final1-2a83df | True | 43.980 | 0.748 | 49.395 | 13 |
| headless-search-20260910T174026Z-p10-direction-retry-final2-003db5 | True | 7.671 | 0.648 | 9.093 | 13 |
| headless-search-20260910T174026Z-p01-initial-final2-667e9c | True | 47.156 | 0.654 | 54.171 | 13 |

Setup attempts include deliberate broken factories. A rejected broken factory is a successful setup check.

| Setup run | Case | Check passed | Status |
| --- | --- | --- | --- |
| headless-search-20260910T174026Z-setup-working2-072609 | working2 | True | finished |
| headless-search-20260910T174026Z-setup-working-826cc5 | working | True | finished |
| headless-search-20260910T174026Z-setup-working-604b6a | working | True | finished |
| headless-search-20260910T174026Z-setup-empty-fa4e24 | empty | True | finished |
| headless-search-20260910T174026Z-setup-stored_only-ba0143 | stored_only | True | finished |
| headless-search-20260910T174026Z-setup-disconnected-e4d8e4 | disconnected | True | finished |
| headless-search-20260910T174026Z-setup-reversed-69588c | reversed | True | finished |
| headless-search-20260910T174026Z-setup-no_fuel-9abd22 | no_fuel | True | finished |
| headless-search-20260910T174026Z-setup-forbidden-0d8467 | forbidden | True | finished |
| headless-search-20260910T174026Z-setup-two_windows-4f1815 | two_windows | True | finished |
| headless-search-20260910T174026Z-setup-timeout-a6f7ac | timeout | True | finished |
| headless-search-20260910T174026Z-setup-runtime-p05-62d35d | runtime-p05 | True | finished |
| headless-search-20260910T174026Z-setup-runtime-b01-f3ae1b | runtime-b01 | True | finished |
| headless-search-20260910T174026Z-setup-runtime-p01-a799ab | runtime-p01 | True | finished |
| headless-search-20260910T174026Z-setup-working-95a504 | working | True | finished |
| headless-search-20260910T174026Z-setup-malformed-19921a | malformed | True | finished |
| headless-search-20260910T174026Z-setup-working-f82d62 | working | True | finished |
| headless-search-20260910T174026Z-setup-working2-1e4a53 | working2 | True | finished |

Limits and evidence:

- This is a supplied-kit production test. It is not a rocket launch or a fresh-world win.
- Headless trials have no video. Later recorded demonstrations are separate attempts.
- The sample is small. It does not establish stable speed or a general success rate.
- Benchmark versions are kept separate. No result is pooled across changed source.
- Each failed or incomplete attempt receives 330 seconds in the time ranking.
- A documented policy failure with a complete trace and matching independent save check can complete a comparison attempt. It remains a failed production trial.
- API cost is a known-usage estimate, not a bill. Missing usage, cache-write charges, and subscription authoring cost are unknown.
- Missing action counts or runtime pins are reported as unknown. Frozen runtime source hashes are included.
- A later save check is shown separately. It does not change the original failed trial verdict.
- Concurrency is the scheduler capacity. The index times permit a separate overlap check.
- The report uses the saved verdict and evidence flags. It does not repeat the independent save check.
- Exact endpoint binding on supplied tools and compute; custom run steps are reviewed trusted local code, without OS isolation. No helper gets API key.

Exact commands are below. They retain the original deadline and local paths; a new attempt needs a new authorized job.

Trial `headless-search-20260910T174026Z-b01-direct-code-access-dev1-2074c8`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 1 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v1/trial-000-attempt-1.json --policy policies/search-v3/bundles/b01-direct-code-access/b01-direct-code-access.method --case b01-direct-code-access-dev1 --seed 63011 --map-x 16 --map-y 0 --kind baseline
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-b01-direct-code-access-dev1-2074c8 --seed 63011 --map-x 16 --map-y 0 --job-deadline 1789065626.0 --recording-mode none --port 18901 --rcon-port 27301 --game-port 34401
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/b01-direct-code-access/b01-direct-code-access.method --endpoint http://127.0.0.1:18901/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-b01-direct-code-access-dev1-2074c8/runtime --seconds 282.1885061264038 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-b01-direct-code-access-dev1-2074c8 --rcon-port 27401 --game-port 34501 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p01-initial-dev1-8da74b`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 2 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v1/trial-001-attempt-1.json --policy policies/search-v3/bundles/p01-initial/p01-initial.method --case p01-initial-dev1 --seed 63011 --map-x 16 --map-y 0 --kind development
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p01-initial-dev1-8da74b --seed 63011 --map-x 16 --map-y 0 --job-deadline 1789065626.0 --recording-mode none --port 18902 --rcon-port 27302 --game-port 34402
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p01-initial/p01-initial.method --endpoint http://127.0.0.1:18902/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p01-initial-dev1-8da74b/runtime --seconds 282.20005679130554 --deadline 2026-09-10T18:40:26+00:00
```

Trial `headless-search-20260910T174026Z-b01-direct-code-access-dev1-82daab`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 1 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v2/trial-000-attempt-1.json --policy policies/search-v3/bundles/b01-direct-code-access/b01-direct-code-access.method --case b01-direct-code-access-dev1 --seed 63011 --map-x 16 --map-y 0 --kind baseline
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-b01-direct-code-access-dev1-82daab --seed 63011 --map-x 16 --map-y 0 --job-deadline 1789065626.0 --recording-mode none --port 18901 --rcon-port 27301 --game-port 34401
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/b01-direct-code-access/b01-direct-code-access.method --endpoint http://127.0.0.1:18901/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-b01-direct-code-access-dev1-82daab/runtime --seconds 282.0929431915283 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-b01-direct-code-access-dev1-82daab --rcon-port 27401 --game-port 34501 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p05-observed-geometry-dev1-8e50d9`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 1 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v2/trial-002-attempt-1.json --policy policies/search-v3/bundles/p05-observed-geometry/p05-observed-geometry.method --case p05-observed-geometry-dev1 --seed 63011 --map-x 16 --map-y 0 --kind development
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p05-observed-geometry-dev1-8e50d9 --seed 63011 --map-x 16 --map-y 0 --job-deadline 1789065626.0 --recording-mode none --port 18901 --rcon-port 27301 --game-port 34401
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p05-observed-geometry/p05-observed-geometry.method --endpoint http://127.0.0.1:18901/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p05-observed-geometry-dev1-8e50d9/runtime --seconds 282.3111569881439 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-p05-observed-geometry-dev1-8e50d9 --rcon-port 27401 --game-port 34501 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p08-code-agent-repair-dev1-ef3249`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 1 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v2/trial-003-attempt-1.json --policy policies/search-v3/bundles/p08-code-agent-repair/p08-code-agent-repair.method --case p08-code-agent-repair-dev1 --seed 63011 --map-x 16 --map-y 0 --kind development
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p08-code-agent-repair-dev1-ef3249 --seed 63011 --map-x 16 --map-y 0 --job-deadline 1789065626.0 --recording-mode none --port 18901 --rcon-port 27301 --game-port 34401
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p08-code-agent-repair/p08-code-agent-repair.method --endpoint http://127.0.0.1:18901/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p08-code-agent-repair-dev1-ef3249/runtime --seconds 282.21420192718506 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-p08-code-agent-repair-dev1-ef3249 --rcon-port 27401 --game-port 34501 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p01-initial-dev1-8e23ab`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 2 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v2/trial-001-attempt-1.json --policy policies/search-v3/bundles/p01-initial/p01-initial.method --case p01-initial-dev1 --seed 63011 --map-x 16 --map-y 0 --kind development
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p01-initial-dev1-8e23ab --seed 63011 --map-x 16 --map-y 0 --job-deadline 1789065626.0 --recording-mode none --port 18902 --rcon-port 27302 --game-port 34402
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p01-initial/p01-initial.method --endpoint http://127.0.0.1:18902/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p01-initial-dev1-8e23ab/runtime --seconds 282.20803570747375 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-p01-initial-dev1-8e23ab --rcon-port 27402 --game-port 34502 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p10-direction-retry-dev1-b1c063`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 1 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v2/trial-004-attempt-1.json --policy policies/search-v3/bundles/p10-direction-retry/p10-direction-retry.method --case p10-direction-retry-dev1 --seed 63011 --map-x 16 --map-y 0 --kind development
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p10-direction-retry-dev1-b1c063 --seed 63011 --map-x 16 --map-y 0 --job-deadline 1789065626.0 --recording-mode none --port 18901 --rcon-port 27301 --game-port 34401
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p10-direction-retry/p10-direction-retry.method --endpoint http://127.0.0.1:18901/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p10-direction-retry-dev1-b1c063/runtime --seconds 282.1116290092468 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-p10-direction-retry-dev1-b1c063 --rcon-port 27401 --game-port 34501 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p01-initial-dev2-301d6d`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 1 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v2/trial-006-attempt-1.json --policy policies/search-v3/bundles/p01-initial/p01-initial.method --case p01-initial-dev2 --seed 63012 --map-x -18 --map-y 12 --kind development
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p01-initial-dev2-301d6d --seed 63012 --map-x -18 --map-y 12 --job-deadline 1789065626.0 --recording-mode none --port 18901 --rcon-port 27301 --game-port 34401
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p01-initial/p01-initial.method --endpoint http://127.0.0.1:18901/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p01-initial-dev2-301d6d/runtime --seconds 282.4167730808258 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-p01-initial-dev2-301d6d --rcon-port 27401 --game-port 34501 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-b01-direct-code-access-dev2-fa5101`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 2 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v2/trial-005-attempt-1.json --policy policies/search-v3/bundles/b01-direct-code-access/b01-direct-code-access.method --case b01-direct-code-access-dev2 --seed 63012 --map-x -18 --map-y 12 --kind baseline
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-b01-direct-code-access-dev2-fa5101 --seed 63012 --map-x -18 --map-y 12 --job-deadline 1789065626.0 --recording-mode none --port 18902 --rcon-port 27302 --game-port 34402
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/b01-direct-code-access/b01-direct-code-access.method --endpoint http://127.0.0.1:18902/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-b01-direct-code-access-dev2-fa5101/runtime --seconds 282.30212116241455 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-b01-direct-code-access-dev2-fa5101 --rcon-port 27402 --game-port 34502 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p05-observed-geometry-dev2-8f7eda`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 1 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v2/trial-007-attempt-1.json --policy policies/search-v3/bundles/p05-observed-geometry/p05-observed-geometry.method --case p05-observed-geometry-dev2 --seed 63012 --map-x -18 --map-y 12 --kind development
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p05-observed-geometry-dev2-8f7eda --seed 63012 --map-x -18 --map-y 12 --job-deadline 1789065626.0 --recording-mode none --port 18901 --rcon-port 27301 --game-port 34401
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p05-observed-geometry/p05-observed-geometry.method --endpoint http://127.0.0.1:18901/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p05-observed-geometry-dev2-8f7eda/runtime --seconds 282.19920587539673 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-p05-observed-geometry-dev2-8f7eda --rcon-port 27401 --game-port 34501 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p10-direction-retry-dev2-c57959`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 1 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v2/trial-009-attempt-1.json --policy policies/search-v3/bundles/p10-direction-retry/p10-direction-retry.method --case p10-direction-retry-dev2 --seed 63012 --map-x -18 --map-y 12 --kind development
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p10-direction-retry-dev2-c57959 --seed 63012 --map-x -18 --map-y 12 --job-deadline 1789065626.0 --recording-mode none --port 18901 --rcon-port 27301 --game-port 34401
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p10-direction-retry/p10-direction-retry.method --endpoint http://127.0.0.1:18901/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p10-direction-retry-dev2-c57959/runtime --seconds 282.5403039455414 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-p10-direction-retry-dev2-c57959 --rcon-port 27401 --game-port 34501 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p08-code-agent-repair-dev2-8f1ac4`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 2 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v2/trial-008-attempt-1.json --policy policies/search-v3/bundles/p08-code-agent-repair/p08-code-agent-repair.method --case p08-code-agent-repair-dev2 --seed 63012 --map-x -18 --map-y 12 --kind development
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p08-code-agent-repair-dev2-8f1ac4 --seed 63012 --map-x -18 --map-y 12 --job-deadline 1789065626.0 --recording-mode none --port 18902 --rcon-port 27302 --game-port 34402
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p08-code-agent-repair/p08-code-agent-repair.method --endpoint http://127.0.0.1:18902/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p08-code-agent-repair-dev2-8f1ac4/runtime --seconds 282.5177879333496 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-p08-code-agent-repair-dev2-8f1ac4 --rcon-port 27402 --game-port 34502 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-b01-direct-code-access-dev3-577a50`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 1 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v2/trial-010-attempt-1.json --policy policies/search-v3/bundles/b01-direct-code-access/b01-direct-code-access.method --case b01-direct-code-access-dev3 --seed 63013 --map-x 24 --map-y -20 --kind baseline
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-b01-direct-code-access-dev3-577a50 --seed 63013 --map-x 24 --map-y -20 --job-deadline 1789065626.0 --recording-mode none --port 18901 --rcon-port 27301 --game-port 34401
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/b01-direct-code-access/b01-direct-code-access.method --endpoint http://127.0.0.1:18901/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-b01-direct-code-access-dev3-577a50/runtime --seconds 282.5238871574402 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-b01-direct-code-access-dev3-577a50 --rcon-port 27401 --game-port 34501 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p05-observed-geometry-dev3-963518`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 1 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v2/trial-012-attempt-1.json --policy policies/search-v3/bundles/p05-observed-geometry/p05-observed-geometry.method --case p05-observed-geometry-dev3 --seed 63013 --map-x 24 --map-y -20 --kind development
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p05-observed-geometry-dev3-963518 --seed 63013 --map-x 24 --map-y -20 --job-deadline 1789065626.0 --recording-mode none --port 18901 --rcon-port 27301 --game-port 34401
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p05-observed-geometry/p05-observed-geometry.method --endpoint http://127.0.0.1:18901/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p05-observed-geometry-dev3-963518/runtime --seconds 282.2259318828583 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-p05-observed-geometry-dev3-963518 --rcon-port 27401 --game-port 34501 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p01-initial-dev3-15ae20`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 2 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v2/trial-011-attempt-1.json --policy policies/search-v3/bundles/p01-initial/p01-initial.method --case p01-initial-dev3 --seed 63013 --map-x 24 --map-y -20 --kind development
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p01-initial-dev3-15ae20 --seed 63013 --map-x 24 --map-y -20 --job-deadline 1789065626.0 --recording-mode none --port 18902 --rcon-port 27302 --game-port 34402
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p01-initial/p01-initial.method --endpoint http://127.0.0.1:18902/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p01-initial-dev3-15ae20/runtime --seconds 282.5322151184082 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-p01-initial-dev3-15ae20 --rcon-port 27402 --game-port 34502 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p08-code-agent-repair-dev3-cced1f`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 1 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v2/trial-013-attempt-1.json --policy policies/search-v3/bundles/p08-code-agent-repair/p08-code-agent-repair.method --case p08-code-agent-repair-dev3 --seed 63013 --map-x 24 --map-y -20 --kind development
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p08-code-agent-repair-dev3-cced1f --seed 63013 --map-x 24 --map-y -20 --job-deadline 1789065626.0 --recording-mode none --port 18901 --rcon-port 27301 --game-port 34401
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p08-code-agent-repair/p08-code-agent-repair.method --endpoint http://127.0.0.1:18901/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p08-code-agent-repair-dev3-cced1f/runtime --seconds 282.20195603370667 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-p08-code-agent-repair-dev3-cced1f --rcon-port 27401 --game-port 34501 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p10-direction-retry-dev3-34a8bf`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 2 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/development-v2/trial-014-attempt-1.json --policy policies/search-v3/bundles/p10-direction-retry/p10-direction-retry.method --case p10-direction-retry-dev3 --seed 63013 --map-x 24 --map-y -20 --kind development
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p10-direction-retry-dev3-34a8bf --seed 63013 --map-x 24 --map-y -20 --job-deadline 1789065626.0 --recording-mode none --port 18902 --rcon-port 27302 --game-port 34402
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p10-direction-retry/p10-direction-retry.method --endpoint http://127.0.0.1:18902/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p10-direction-retry-dev3-34a8bf/runtime --seconds 282.3254861831665 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-p10-direction-retry-dev3-34a8bf --rcon-port 27402 --game-port 34502 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p10-direction-retry-final1-ea68a7`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 2 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/final-v2/trial-001-attempt-1.json --policy policies/search-v3/bundles/p10-direction-retry/p10-direction-retry.method --case p10-direction-retry-final1 --seed 9031847 --map-x -26 --map-y -18 --kind final
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p10-direction-retry-final1-ea68a7 --seed 9031847 --map-x -26 --map-y -18 --job-deadline 1789065626.0 --recording-mode none --port 18902 --rcon-port 27302 --game-port 34402
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p10-direction-retry/p10-direction-retry.method --endpoint http://127.0.0.1:18902/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p10-direction-retry-final1-ea68a7/runtime --seconds 282.0982940196991 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-p10-direction-retry-final1-ea68a7 --rcon-port 27402 --game-port 34502 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p01-initial-final1-2a83df`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 1 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/final-v2/trial-000-attempt-1.json --policy policies/search-v3/bundles/p01-initial/p01-initial.method --case p01-initial-final1 --seed 9031847 --map-x -26 --map-y -18 --kind final
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p01-initial-final1-2a83df --seed 9031847 --map-x -26 --map-y -18 --job-deadline 1789065626.0 --recording-mode none --port 18901 --rcon-port 27301 --game-port 34401
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p01-initial/p01-initial.method --endpoint http://127.0.0.1:18901/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p01-initial-final1-2a83df/runtime --seconds 282.0880661010742 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-p01-initial-final1-2a83df --rcon-port 27401 --game-port 34501 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p10-direction-retry-final2-003db5`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 1 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/final-v2/trial-003-attempt-1.json --policy policies/search-v3/bundles/p10-direction-retry/p10-direction-retry.method --case p10-direction-retry-final2 --seed 7219631 --map-x 30 --map-y 22 --kind final
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p10-direction-retry-final2-003db5 --seed 7219631 --map-x 30 --map-y 22 --job-deadline 1789065626.0 --recording-mode none --port 18901 --rcon-port 27301 --game-port 34401
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p10-direction-retry/p10-direction-retry.method --endpoint http://127.0.0.1:18901/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p10-direction-retry-final2-003db5/runtime --seconds 282.11858892440796 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-p10-direction-retry-final2-003db5 --rcon-port 27401 --game-port 34501 --job-deadline 1789065626.0
```

Trial `headless-search-20260910T174026Z-p01-initial-final2-667e9c`:

```sh
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_trial.py --job-dir /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z --deadline 1789065626.0 --lane 2 --concurrency 2 --status-file /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/final-v2/trial-002-attempt-1.json --policy policies/search-v3/bundles/p01-initial/p01-initial.method --case p01-initial-final2 --seed 7219631 --map-x 30 --map-y 22 --kind final
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_host.py --run headless-search-20260910T174026Z-p01-initial-final2-667e9c --seed 7219631 --map-x 30 --map-y 22 --job-deadline 1789065626.0 --recording-mode none --port 18902 --rcon-port 27302 --game-port 34402
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/method3_run.py /Users/ryanprendergast/Documents/workflow-corp/factorio/policies/search-v3/bundles/p01-initial/p01-initial.method --endpoint http://127.0.0.1:18902/action --output /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z/trials/headless-search-20260910T174026Z-p01-initial-final2-667e9c/runtime --seconds 282.4295048713684 --deadline 2026-09-10T18:40:26+00:00
/Users/ryanprendergast/Documents/workflow-corp/factorio/.venv/bin/python /Users/ryanprendergast/Documents/workflow-corp/factorio/scripts/search_inspect.py /Users/ryanprendergast/Documents/workflow-corp/factorio/runs/headless-search-20260910T174026Z-p01-initial-final2-667e9c --rcon-port 27402 --game-port 34502 --job-deadline 1789065626.0
```

See [summary.json](summary.json) for exact measurements, all setup attempts, usage by phase, policy hashes, and frozen source hashes.
