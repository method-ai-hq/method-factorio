# Headless host repair checks

The owner removed recording from policy optimization after the first job.
Two new, concurrent operator-reference checks then ran with
`search_host.py --recording-mode none`. These checks were part of the code
repair task. They did not resume the expired search job or use paid model calls.

| Check | World 1 | World 2 |
| --- | --- | --- |
| Host ready | 3.41 seconds | 3.42 seconds |
| Complete check, including separate save reload | 8.57 seconds | 8.59 seconds |
| New plates per window | 5, 5, 5 | 5, 5, 5 |
| Newly mined ore per window | 5, 5, 5 | 5, 5, 5 |
| Independent save inspection | Passed | Passed |
| Graphical client started | No | No |
| Model API calls | 0 | 0 |

The supplied kit, operator terrain, game speed 20, 600-tick warmup, and three
1,200-tick measurement windows were unchanged. The operator reference built
the factories through the playing tools. No candidate Method was tested.
Raw actions, saves, and state remain in the local run folders identified by
[summary.json](summary.json). Missing video is intentional under the new mode.

Eleven separate control tests use small fake worker processes. They check
native startup order, headless startup overlap, lock release after process
exit, allowed retry limits, pending-work retention, cutoff handling, and the
required headless evidence files. Run them with:

```sh
.venv/bin/python scripts/test_search_recovery.py
```

These results establish two-world headless host operation and the tested
scheduler controls. They do not establish four/eight-world capacity, full live
negative evaluator coverage, Method-to-host integration, policy improvement,
or a recorded rerun. No new scoring manifest was approved. The earlier
benchmark and its results remain unchanged.
