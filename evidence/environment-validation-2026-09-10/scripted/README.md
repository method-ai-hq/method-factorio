# Scripted environment test results

Eight local test episodes completed. Six production episodes made 20 new iron plates each. Two other episodes tested request batching. All eight terminal saves loaded and matched the recorded game state. No model or paid API calls were made.

Tests ran on the same Mac as the agent tests. These are small-factory results, with one run per setting. They do not establish full game control or policy improvement.

|Connection|Speed|20-plate time(s)|Startup(s)|Whole probe run(s)|Matched100 observation p95(ms)|Measured ticks/s|
|---|---:|---:|---:|---:|---:|---:|
|http|1|109.29|12.23|172.24|43.25|59.98|
|unix|1|109.25|11.81|139.94|35.84|59.89|
|http|5|22.24|9.96|40.38|19.36|298.94|
|unix|5|22.51|10.37|41.03|17.49|300.05|
|http|20|5.92|9.58|23.38|16.05|1192.15|
|unix|20|5.91|9.77|23.67|15.48|1199.16|

The HTTP 1x run also had a 1000-read soak. Its full-run time must not be compared with the other full-run times as a connection benchmark. All runs checked actual 20-plate furnace output, furnace products, ore consumption, and fuel consumption. The fixed 1x evaluator passed both 1x runs. It rejected the four accelerated runs only on its unchanged normal-speed rule. The separate speed probes and saved-game reloads passed.

At 1x, each connection passed 30 drill rotations checked through entity reads, placement and pickup inventory checks, seven rejected-action tests, and a lost craft-response test. The craft response was lost on purpose. The next observation showed one new gear and two consumed plates; the craft was not repeated. Rejected actions did not change inventory, player position, research, or recorded iron production.

The 1000 HTTP observations had a 33.37 ms median, 39.90 ms p95, and 400.56 ms maximum. This was a short read-only soak. It was not a 30-minute larger-factory test.

|Connection|Action family|100 actions, batches of 1 (s)|Batches of 10 (s)|Batches of 50 (s)|
|---|---|---:|---:|---:|
|http|observe|3.328|3.352|3.367|
|http|place_pickup|7.008|6.930|6.942|
|unix|observe|3.382|3.332|3.370|
|unix|place_pickup|7.202|6.919|6.902|

Every batch member kept the same full state check. Each connection passed 300 observation actions and 300 furnace place/pickup actions across the three batch sizes. A batch with craft, denied action, then craft stopped at the denied action. The first craft happened once; the third action did not run. Batching made little difference to the local environment speed. It may reduce agent tool-call overhead; this test did not measure that.

Use the current HTTP connection for now. The thin Unix connection had no useful production-time gain. Speed 20 is a useful candidate for small development tests: the same production task took about 5.9 s instead of 109.3 s. Larger factories, exact tick-matched state checks, and live restart/resume still need tests before using this result for full episodes.

Unsupported in the current playing interface: normal recipe and research selection, rocket launch, live resume, bounded pause/advance, and action-ID recovery. Administration remains unavailable by design. Full power/research/oil/advanced production, trains, robots, circuits, combat, larger-factory load, and full rocket control were not tested by this lane.

The [full structured summary](summary.json) contains all measured results and limits. The [run index](index.json) links run names to local evidence folders. Each published run folder contains checks, settings, source and save hashes, timing summaries, and expected errors. Native game logs, model logs, game saves, and raw action traces are not published here. Their local copies are retained.

The two measured controller versions have these SHA-256 hashes:

- `parallel-d-20260910-controller-v1.py`: `68d58defb62df13bcec4cfc9fe6218a0f4e6aa0949fc0b2e94115cd2de49417e`
- `parallel-d-batch-20260910-controller-v2.py`: `d4060d15102e6045976d696af7980d30c9208a50e26131a096219d3518f2dd81`

The final runner adds aggregate pass/fail reporting and a failure exit code. Those reporting changes were compiled after the measured runs; no game test was repeated. Per-run source hashes identify the code used for the measurements.

| Published run | Checks | Settings | Timing | Errors | Source hashes |
|---|---|---|---|---|---|
| production-http-s1 | [Checks](production-http-s1/checks.json) | [Settings](production-http-s1/settings.json) | [Timing](production-http-s1/timing.json) | [Errors](production-http-s1/errors.json) | [Hashes](production-http-s1/source-hashes.json) |
| production-unix-s1 | [Checks](production-unix-s1/checks.json) | [Settings](production-unix-s1/settings.json) | [Timing](production-unix-s1/timing.json) | [Errors](production-unix-s1/errors.json) | [Hashes](production-unix-s1/source-hashes.json) |
| production-http-s5 | [Checks](production-http-s5/checks.json) | [Settings](production-http-s5/settings.json) | [Timing](production-http-s5/timing.json) | [Errors](production-http-s5/errors.json) | [Hashes](production-http-s5/source-hashes.json) |
| production-unix-s5 | [Checks](production-unix-s5/checks.json) | [Settings](production-unix-s5/settings.json) | [Timing](production-unix-s5/timing.json) | [Errors](production-unix-s5/errors.json) | [Hashes](production-unix-s5/source-hashes.json) |
| production-http-s20 | [Checks](production-http-s20/checks.json) | [Settings](production-http-s20/settings.json) | [Timing](production-http-s20/timing.json) | [Errors](production-http-s20/errors.json) | [Hashes](production-http-s20/source-hashes.json) |
| production-unix-s20 | [Checks](production-unix-s20/checks.json) | [Settings](production-unix-s20/settings.json) | [Timing](production-unix-s20/timing.json) | [Errors](production-unix-s20/errors.json) | [Hashes](production-unix-s20/source-hashes.json) |
| batch-http-s1 | [Checks](batch-http-s1/checks.json) | [Settings](batch-http-s1/settings.json) | [Timing](batch-http-s1/timing.json) | [Errors](batch-http-s1/errors.json) | [Hashes](batch-http-s1/source-hashes.json) |
| batch-unix-s1 | [Checks](batch-unix-s1/checks.json) | [Settings](batch-unix-s1/settings.json) | [Timing](batch-unix-s1/timing.json) | [Errors](batch-unix-s1/errors.json) | [Hashes](batch-unix-s1/source-hashes.json) |
