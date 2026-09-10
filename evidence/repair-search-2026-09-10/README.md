# Factory repair policy search

Completed on 10 September 2026. The selected Method was frozen before either approach played the 20 final factories.

The Method used about 23% less full time on the same successful cases and 56% fewer reported input tokens across all twenty attempts. It did not show a repair that direct Astra could not perform. The two strict-score differences were request-rule failures; both factories still passed all production checks.

## Final result

| Measure | Direct Astra | Searched Method v04 |
| --- | ---: | ---: |
| Full-rule passes | 18/20 | 20/20 |
| Factories with verified production restored | 20/20 | 20/20 |
| Request-rule failures | 2 | 0 |
| Time-limit failures | 0 | 0 |
| Production or completion failures | 0 | 0 |
| Infrastructure failures | 0 | 0 |
| Median full time on the same successful pairs | 92.83 s | 71.22 s |
| Fresh Codex sessions | 20 | 20 |
| Reported input tokens, including cached input | 6,642,107 | 2,939,690 |
| Cached input tokens | 5,726,848 | 2,344,960 |
| Reported output tokens | 31,207 | 27,998 |

Both passed 18 cases. Only direct Astra passed 0; only the Method passed 2; neither passed 0. The exact paired two-sided success test gives p=0.5000; this small sample does not establish a reliable success-rate difference. Twenty cases provide an initial comparison, not a broad claim about all Factorio tasks.

There are 18 pairs where both passed. Across these pairs, the median of direct time divided by Method time is 1.303. A value above one means the Method took less time. Full time includes world startup, player work, the native production check, and all independent save checks, including the recipe review. It excludes queue time between cases. Development save reviews ran later; their measured processing time is added, and the intervening wait is excluded. The JSON also reports game-host time separately.

[All final measurements](final-report.json) include case hashes, task hashes, actions, time, token use, request failures, and recipe-reader evidence. A model statement never determines a pass. The [publication audit](publication-audit.json) passed for all 40 final attempts. It checked the retained evidence hashes, recomputed the fixed-rule decisions, and reproduced the report. Public file paths are relative; the [publication record](provenance.json) keeps hashes of both the original local report and its public copy. All 54 focused repair tests passed.

## What ran

There are 30 different damaged factories: ten for development and twenty for final testing. Every factory had native proof that it works before damage, fails after damage, and works after a legal repair. Final cases use new layouts and fault combinations from the same factory family. They are not new objectives or proof of transfer to unrelated games.

Direct Astra received a fresh, multi-turn Codex session for each case. It could inspect the game, write and run code, make repairs, test them, and correct errors within its attempt. It received no results from other cases. The Method used the same model, reasoning setting, game interface, 300-second limit, and 200-action limit. Each approach received a separate copy of the same save. The final runner played one matched pair at a time on two headless worlds. It made no screen recording.

The selected Method has two steps:

1. Code makes one allowed observation and compresses the factory map while preserving machine locations and belt geometry.
2. One fresh Astra Codex session reads that map, finds faults, repairs them, checks new production, and calls finish.

This is an actual Method v3 run. The code step calls the fixed Codex subscription helper for the model session. Method-native paid API calls are disabled. It is not a model-free script. Direct Astra also has code tools, but does not receive the searched compression code or repair prompt.

## Policy search

| Version | Game attempts | Full-rule passes | Production restored | Median full successful time, seconds | Codex sessions |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct Astra | 10 | 8 | 10 | 92.25 | 10 |
| v01 | 10 | 9 | 10 | 215.49 | 30 |
| v02 | 10 | 10 | 10 | 91.83 | 10 |
| v03 | 1 | 1 | 1 | 70.81 | 1 |
| v04 | 10 | 10 | 10 | 73.18 | 10 |

v01 used three model stages. Its first stage often reached its time limit, and later stages repeated work. v02 used code to prepare observations and one model session. v03 compressed repeated power equipment data and simplified the prompt. Its first attempt passed, but a file change was detected before the second attempt. The original v03 was restored and retained as a one-attempt result. The corrected version became v04 and ran all ten cases. No results were merged between versions.

Only versions with all ten development results could be selected. The rule chose the most passes, then the lowest median full successful time, then reported token use. v04 won this rule. The [selection record](selection.json) contains candidate file hashes, the fixed reader hash, and the development evidence hashes. The policy author received only public interfaces and approved development evidence. Final outcomes did not change the selected Method.

The search used 31 Method game attempts and 51 Codex sessions, in addition to ten direct baseline attempts. Known Method search usage was 8,574,880 input tokens, including 7,206,144 cached tokens, and 55,786 output tokens. 10 sessions lack final usage, so total search tokens are unknown. These figures exclude authoring, setup, and operator work. They are not the cost of executing the selected Method on a new case. Model use consumed the signed-in subscription; its dollar cost is unknown. Session counts are not model request counts.

See the [development baseline](development-baseline.json) and [all candidate measurements](development-search.json). Development direct Astra restored all ten factories, including the two that failed request rules. These tasks did not show that policy search was required to repair the development factories.

## Fixed verification and limits

The checker clears stored materials and crafting progress, waits for the factory to warm up, and measures three production windows. Each window must produce and retain new red and green science, mine new iron and copper, and make the required intermediate items. It then checks the original saved game independently.

A development test exposed a recipe-name JSON export fault. The [separate reader](checker-note.md) recovers exact recipe objects retained in the original historical save samples. It applies the unchanged production rules and preserves original verdicts. Every development and final attempt receives the same read. Its source was frozen before final tests. No factory was replayed to replace a model outcome.

Player file restrictions were checked. Network access is enabled for the local game connection; the helper restricts its assigned endpoint and rejects redirects. This is not a proof of complete operating-system or network isolation. Trusted Method code has broader host access and was reviewed to use only public observations and the fixed model helper. No private case access was found.

The outcome supports only the differences measured above. It does not establish that a deterministic program cannot solve the task, that multi-agent policies are necessary, or that the Method beats Astra on unrelated tasks. Runtime differences can include service latency and local load. More unseen cases and repeat runs would be needed for a stronger estimate.

## Per-case final results

Times below include verification. Failed attempts remain in the table and are excluded from successful-time comparisons.

| Case | Direct Astra | Method v04 | Direct seconds | Method seconds |
| --- | --- | --- | ---: | ---: |
| final-001 | Pass | Pass | 71.53 | 66.39 |
| final-002 | Pass | Pass | 87.32 | 64.79 |
| final-003 | Pass | Pass | 114.93 | 68.18 |
| final-004 | Pass | Pass | 90.72 | 68.90 |
| final-005 | request_rule | Pass | 144.44 | 133.94 |
| final-006 | Pass | Pass | 88.89 | 68.42 |
| final-007 | Pass | Pass | 93.26 | 104.77 |
| final-008 | Pass | Pass | 85.59 | 87.45 |
| final-009 | Pass | Pass | 87.00 | 66.60 |
| final-010 | Pass | Pass | 92.55 | 70.86 |
| final-011 | Pass | Pass | 182.08 | 124.85 |
| final-012 | Pass | Pass | 142.85 | 173.23 |
| final-013 | Pass | Pass | 91.28 | 70.66 |
| final-014 | Pass | Pass | 103.79 | 73.65 |
| final-015 | Pass | Pass | 78.85 | 77.47 |
| final-016 | Pass | Pass | 99.74 | 68.05 |
| final-017 | Pass | Pass | 100.07 | 71.87 |
| final-018 | Pass | Pass | 93.10 | 71.59 |
| final-019 | request_rule | Pass | 161.59 | 110.24 |
| final-020 | Pass | Pass | 98.69 | 76.53 |

See [the fixed experiment](../../docs/repair-experiment.md), [the task](../../docs/repair-task.md), [the run guide](../../docs/run-repair-search.md), and [the selected Method](../../methods/repair-search/v04/repair.method). Raw saves and traces remain in ignored local `runs/` folders. No game assets, credentials, or recordings are published here.
