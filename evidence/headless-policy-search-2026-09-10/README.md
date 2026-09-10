# Headless Method v3 policy search

The comparison is complete. The selected Method, `p10-direction-retry`, passed
all three development maps and both unseen final maps. The frozen initial
Method also passed all five maps. The direct agent passed two of three
development maps.

| Contender | Development passes | Mean ranked development time | Final passes | Mean full final time |
| --- | ---: | ---: | ---: | ---: |
| Direct agent with code access, b01 | 2/3 | 138.86 s | Not scheduled | — |
| Frozen initial Method, p01 | 3/3 | 51.33 s | 2/2 | 51.78 s |
| Selected Method, p10 | 3/3 | 8.61 s | 2/2 | 9.06 s |

Every failure receives 330 seconds in the ranking. The direct agent's failed
attempt used an unsupported attribute call in its bounded compute program.
Its runtime stopped before handoff. The failure, action trace, terminal save,
and matching save check are retained. It is not a production pass.

Two other candidates passed all three development maps: p05 averaged 8.74 seconds
and p08 averaged 19.82 seconds. The fixed ranking selected p10 by full trial time.
The 0.12-second gap between p10 and p05 is too small to establish stable superiority.
The two final maps were fixed before scoring. Selection was saved before final
execution. Hidden results did not lead to a policy change.

## Methods

- [Direct agent with bounded code access](../../policies/search-v3/bundles/b01-direct-code-access/b01-direct-code-access.method).
- [Frozen initial Method](../../policies/search-v3/bundles/p01-initial/p01-initial.method).
- [Selected Method](../../policies/search-v3/bundles/p10-direction-retry/p10-direction-retry.method) and its [code](../../policies/search-v3/bundles/p10-direction-retry/geometry_retry.py).
- [Candidate index](../../policies/search-v3/README.md) and [exact selection record](selection.json).

The selected Method uses observed positions and bounded code to build the line.
It can recover equipment and try another direction. It made zero model requests
during these executions. Existing immutable candidates were tested and selected;
this job did not rewrite policies after feedback or train weights. Candidate
authors did not receive the operator reference factory plan. Subscription
policy-authoring cost is unknown.

## Fixed test and evidence

This is a supplied-kit production benchmark. It is not a rocket launch or a
fresh-world win. Base Factorio 2.0.77 ran headless at game speed 20, with FLE fast
mode and game time running during model thinking. There was no video.

Each final factory passed all three exact 1,200-tick windows after 600 warmup ticks.
Every window had at least five new plates and five newly mined ore. The route
checks and independent terminal-save checks passed. Full time includes launch,
model work, production checks, save inspection, and cleanup. Production time
and save-inspection time are also reported separately.

The new job started at 17:40:26 UTC on 10 September 2026, with an 18:40:26 UTC deadline.
Setup used 18 of 24 allowed episodes, including two repair checks. Six repair
episodes remained. Two playing worlds ran at a time. No higher panel capacity
was claimed. The earlier job and its candidates remain unchanged.

## Failure and repair record

Version 1 completed one direct-agent trial. A disk-use scan then raced with a
Factorio temporary-file deletion and stopped the other active trial. Both
attempts remain in the record. Two live repair checks passed. Version 2 then
reran the complete 15-trial development panel and ran the four final trials.
The two versions are not pooled. Each affected case had one linked replacement.

Scored version 2 source: [`b25d430`](https://github.com/method-ai-hq/method-factorio/tree/b25d4303cbe7e29a4c21fbab3e8a237fbe97e341).
Both exact source versions are also retained in the local job folder. A later
offline test found a separate failure-status/process-exit race. The repair
passed 40 offline tests. No game or API work ran after that repair; the new
scheduler code is not claimed as tested in a live game. See the
[repair record](post-comparison-repair.json).

## Usage and cost

| Phase | API requests | Known input tokens | Known output tokens | Known cost estimate |
| --- | ---: | ---: | ---: | ---: |
| Setup | 26 | 112,303 | 1,692 | $0.385021 |
| Development, including failed version 1 | 107 | 460,660 | 6,985 | $1.694439 |
| Final comparison | 28 | 128,448 | 1,825 | $0.418094 |
| Total | 161 | 701,411 | 10,502 | $2.497554 |

160 responses have known usage. One interrupted request has unknown usage.
Cached input totaled 560,184 tokens. These are estimates from
[OpenAI's published Astra prices](https://developers.openai.com/api/docs/models/gpt-6-astra),
not invoices. Cache-write charges and subscription cost are unknown. No credit
was redeemed. No separate dollar ceiling was set by the operator.

## Exact commands and limits

The [attempt appendix](attempts.md) contains every original trial command.
The [development panel](development-panel.json) and [final panel](final-panel.json)
list the exact policies and map cases. [The freeze](benchmark-freeze-v2.json)
records settings and hashes. The original scheduler commands were:

```sh
.venv/bin/python scripts/search_schedule.py --job-dir runs/headless-search-20260910T174026Z --panel runs/headless-search-20260910T174026Z/panel-development-v2.json --concurrency 2 --search-deadline 1789064426 --deadline 1789065626 --schedule-name development-v2
.venv/bin/python scripts/search_schedule.py --job-dir runs/headless-search-20260910T174026Z --panel runs/headless-search-20260910T174026Z/panel-final-v2.json --concurrency 2 --search-deadline 1789064426 --deadline 1789065626 --final-panel --schedule-name final-v2
```

These commands show the original job. A new execution needs a new authorized
deadline and a new validated freeze. For version 2 reproduction, use the scored
source commit above and the dependency instructions in
[Method 3 runtime setup](../../docs/method3-runtime.md).

The game tools and bounded compute tool enforce the assigned endpoint. Custom
policy code remains trusted local code without operating-system isolation.
The sample is small. The results do not establish a general success rate.
Later recorded demonstrations are separate attempts with a separate time limit.

[Summary JSON](summary.json) contains exact tick measurements, hashes, costs,
all failed attempts, and all setup checks. [Verification JSON](verification.json)
records matching game settings and independent save checks. Raw action/state
traces, model records, and game saves remain in the ignored local job folders.

Cleanup found no job-owned process at 18:00:25 UTC, within the 60-minute limit.
See [cleanup.json](cleanup.json).
