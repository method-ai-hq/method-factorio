# Method v3 search: setup stopped

The job stopped before policy scoring. All 12 allowed setup episodes were used.
Six parallel graphical clients failed to join their game servers within 60
seconds. The negative live evaluator checks did not run. The evaluator is not
approved for scoring. There is no selected policy or measured policy improvement.

The job started at 16:17:12 UTC on 10 September 2026. New work stopped at
16:30:28 UTC, before the 15-minute setup limit. The total job deadline was
17:17:12 UTC. Setup, reporting, and cleanup all count toward that deadline.

## Completed checks

| Check | Result |
| --- | --- |
| Public Method v3 | CLI 0.1.0, `method/3`; fixed source revision; 40 runtime tests passed. |
| Real model backend | One native call and one native agent used three API requests and a real script tool. |
| Direct code execution | Native run passed; no API key reached the helper; zero model requests. |
| Policy validation | 11 candidates and 2 baselines passed `method3 validate`; all frozen bundle hashes match. |
| Evaluator predicates | Eight unit tests passed. These are not live failure-case checks. |
| Working operator reference | Each of three exact 1,200-tick windows had 5 new plates and 5 newly mined ore, after 600 warmup ticks. |
| Reference save | Separate server reload matched tick, settings, machine state, inventory, resources, and production. |
| PNG recording | Two worlds recorded at the same time; a separate working host recorded 98 frames. |
| JPEG recording | Implemented to reduce storage; no live capture check completed. |
| Negative live cases | Zero completed; all six attempts failed during graphical-client startup. |

The working reference was an operator fixture built with the playing tools.
It was not an Astra policy trial. It had one rejected furnace placement, then
an observed repair in the same episode. Both traces remain saved. FLE reverses
inserter placement direction relative to the native entity direction. The
reference used the observed pickup and drop positions to repair it.

The reference used native Factorio 2.0.77, FLE fast mode, game speed 20, and a
running game during controller work. Setup cleared a grass area from -64 to 64
and supplied a 9-by-9 iron patch with 1,000 ore per tile. The kit came from the
fixed contract. This was not a fresh-world rocket task.

See [the production measurements](reference-production.json),
[the separate save inspection](reference-save-inspection.json), and
[the full reviewed summary](summary.json). The production record separates a
passed production check from an unscored result. Its evidence flags were false
when that record was first made; the later recording and reload checks passed.

## Counts and costs

- 12 setup episodes, including failures and the early recording retry.
- 11 frozen candidate policies and 2 baseline designs; 13 validated Methods.
- 0 scored trials, 0 development policy trials, and 0 final comparisons.
- 144 recorded source frames and 4 local videos. One video has only a cleanup
  frame and is incomplete. Three episodes have complete recording records.
- Three paid API setup requests: 442 input tokens and 43 output tokens.
- Known setup API estimate: **$0.00657**. Policy execution API cost: **$0**,
  because no policy execution trial ran. Codex authoring and supervision cost
  is unknown. The estimate is not an invoice.

The original targets of 16 policies and 60 trials were not reached. The fixed
12-episode setup cap prevented more attempts. No quota reset was used. Final
maps were not opened or frozen. The development map panel also remained a
proposal; only its first map setup was exercised.

## Local evidence and commands

The complete local index is `runs/search-v3-20260910/index.html`, with JSON at
`setup-index.json` and `index.jsonl` in that folder. It lists every episode,
recording, trace, available save, verdict, and missing artifact. Failed raw
records remain local. No game images, binaries, saves, account files, or raw
model logs are included in this public evidence folder.

The [policy directory](../../policies/search-v3/README.md) lists each bundle,
parent, hypothesis, and hash. The initial Method was frozen before gameplay
feedback. There is no best tested Method. Preserve all these designs as untested.

Use the [runtime instructions](../../docs/method3-runtime.md) to install the
pinned public runtime and run validation. From the project root:

```sh
scripts/method3 --version
scripts/method3 validate policies/search-v3/bundles/p01-initial/p01-initial.method
.venv/bin/python scripts/test_automatic_evaluator.py
.venv/bin/python scripts/build_search_setup_report.py
```

The complete trial command is documented in the runtime instructions. It
refuses this job's unapproved `benchmark-freeze.json`. The original deadline
must not be extended. A new experiment needs new operator authorization,
completed live failure checks, a tested recorder, and a new fixed configuration.

## Remaining limits

The prepared host, trial runner, and scheduler are not a validated benchmark.
The final JPEG source differs from the PNG source used in the successful
recording checks. The six-client startup failure suggests a resource limit;
the exact cause was not proved. Two concurrent recording worlds were checked.
A later job should test client startup scheduling before raising concurrency.

The policy tools exclude game administration. Local process isolation is not
complete. The current transport helper accepts a model-supplied loopback URL;
it is not bound to one exact game endpoint. The baseline's calculation tool
has only a basic local check. The baseline has no dynamic model-profile switch.
These limitations must be resolved or fixed in the next experiment's rules
before claiming a fair scored comparison.

The old evaluator `scripts/check_result.py` is unchanged. The root benchmark
contract is unchanged. Source hashes for the prepared, unapproved code are in
[source-hashes.json](source-hashes.json). No deployment target exists.
