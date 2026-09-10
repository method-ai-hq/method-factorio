# Final report: Factorio Method v3 policy search

**Status: finished.** The owner confirmed closure after the search reached its existing time limit. This report uses saved results. No new game or paid model call was needed to write it.

The main result is clear: a saved code policy ran much faster than the direct Astra agent in this small production task. The later hill climb improved action count, fuel allocation, error handling, and internal checks. It did **not** establish a further speed gain, or an advantage over the deterministic reference script.

## Task and fixed test

The task was to build automatic iron production from a supplied kit: one burner drill, one furnace, one burner inserter, ten belts, and 150 coal. It was not a fresh-world rocket task.

A pass required a connected drill → belt → inserter → furnace route. After 600 warmup ticks, each of three exact 1,200-tick windows had to produce at least five new plates and mine five new ore. No policy actions were allowed during measurement. A separate Factorio process loaded the terminal save and checked its state.

Factorio 2.0.77 ran headless at game speed 20 with FLE fast mode. Game time continued during model work. The 4,200 warmup and measurement ticks cover 70 game seconds, or a nominal 3.5 wall-clock seconds at that speed. Reported full trial time also includes launch, policy execution, save inspection, and cleanup. There was no video.

The validated version 2 source was commit `b25d4303cbe7e29a4c21fbab3e8a237fbe97e341`. Its hashes, game rules, development maps, and validator stayed fixed during the hill climb. The first matched comparison ran two worlds at a time; the continuation ran one search world at a time. A separate Factorio task was active during part of the continuation. Timing from these stages is therefore reported separately.

## Work completed

The scope here is the headless job and its continuation. The earlier failed graphical setup job and separate reference-script repair checks remain separate records.

| Stage | Attempts | Passes | Purpose |
| --- | ---: | ---: | --- |
| Earlier benchmark version 1 | 2 | 1 | Retained after a scheduler fault; excluded from version 2 comparisons |
| Version 2 development comparison | 15 | 14 | Five contenders on three common maps |
| Version 2 unseen final comparison | 4 | 4 | Initial Method versus selected code Method on two maps |
| Feedback-driven hill climb | 57 | 52 | New versions, failures, replacements, and paired rechecks |
| Total attempt records | 78 | 71 | Record count only, not an overall success-rate estimate |

The job also used 18 setup episodes. There were 13 initially frozen versions and 16 new frozen versions, for 29 total. One rejected Method draft was retained separately. The limits were 120 trial attempts and 32 frozen versions. The search stopped at **18:20:26 UTC on 10 September 2026**. All continuation trials closed before that stop; the original job deadline was 18:40:26 UTC. No limit was extended.

The first stage selected among existing Methods. Those Methods had been written before gameplay feedback. The later stage was the actual hill climb: inspect a result, change the Method, freeze it, run it, and repeat. Thus the large initial time reduction must not be described as a result of the later hill climb.

## Comparison with direct Astra

The closest measured “raw Astra” baseline is **b01**, a single `gpt-6-astra` agent with medium reasoning, the task, game tools, and a bounded Python tool. It chose its own procedure and received no factory layout. It still ran through the common Method runtime for logging and limits; this was not an unrestricted Codex or shell agent.

These are the matched version 2 development results. API requests and cost estimates cover all three attempts in each row.

| Contender | Execution form | Passes | Mean ranked time | API requests | Known API estimate |
| --- | --- | ---: | ---: | ---: | ---: |
| b01: direct Astra | One agent with bounded code access | 2/3 | 138.86 s | 25 | $0.421560 |
| p01: initial Method | Agent with observation and build checkpoints | 3/3 | 51.33 s | 44 | $0.670193 |
| p05: observed geometry | Deterministic Python | 3/3 | 8.74 s | 0 | $0 |
| p08: code plus agent repair | Python, then agent inspection and repair | 3/3 | 19.82 s | 12 | $0.216908 |
| p10: selected Method | Deterministic Python with direction recovery | 3/3 | 8.61 s | 0 | $0 |

“Ranked time” assigns **330 seconds to every failure**. The b01 value is not its mean elapsed execution time. Its two successful runs took 49.57 and 37.01 seconds; p10 took 8.25 and 8.67 seconds on those same two maps. The means on these common successful maps were **43.29 seconds for b01 and 8.46 seconds for p10**. This comparison excludes the failed b01 map; the pass counts above retain it.

B01 failed when it used an unsupported attribute call in its Python tool. The tool blocked attributes, imports, functions, classes, and file access. Code Methods used trusted Python helper files with wider language access, while retaining the same game-action endpoint. This difference limits claims about equal coding freedom. The results support an advantage for the tested saved procedure over this specific direct-agent interface, not over every way of giving Astra code tools.

The initial Method was not faster than direct Astra on the two maps where both passed: its broader checkpoint procedure also required more model requests. The strongest speed result came from moving known work into code, not from adding more agent steps.

Source: [first comparison and attempt records](../headless-policy-search-2026-09-10/README.md).

## Unseen-map comparison

P10 was selected and frozen before the two final maps were opened. No new policy was written from those final results.

| Contender | Passes | Mean full time | API requests across two trials | Known API estimate |
| --- | ---: | ---: | ---: | ---: |
| p01: initial Method | 2/2 | 51.78 s | 28 | $0.418094 |
| p10: selected code Method | 2/2 | 9.06 s | 0 | $0 |

The initial Method took about **5.71 times as long as p10** in this small paired sample. There was no direct-agent or standalone reference-script final panel. The new hill-climb versions, p12 through p27, have **no unseen-map final result**. The earlier p10 final result cannot be transferred to them.

## What the hill climb improved

The continuation began with p10 and created 16 versions, p12 through p27. Each version keeps its parent, hypothesis, input trial records, source, validation output, and hashes.

| Change | Measured result |
| --- | --- |
| Reuse state returned by actions; remove redundant calls | p12 passed 3/3 maps with 10 actions instead of p10’s 13 |
| Reduce movement and choose the route direction from player position | Short movement caused reach errors; pointing the route toward the player avoided those errors on the three maps |
| Repair a distance error locally | p18 passed 3/3, without removing the whole route for a distance error |
| Allocate fuel from observed use | p19 passed 3/3 with six coal loaded; p20 added a reserve and passed with nine |
| Check geometry, insert counts, and the Method outcome | P21’s offline negative check rejected failed construction; the fixed game validator still decided each trial result |
| Correct the batch request and batch placements | p22–p24 passed all their three-map panels, but did not establish a speed gain |
| Observe actual production before handoff | p25 used five observations; p26 and p27 used two. P27 passed 3/3 with 12 actions and nine coal loaded |

A later declared paired recheck tested p10 against p20 on the same three development maps:

| Measure | p10 | p20 | Change |
| --- | ---: | ---: | --- |
| Passes | 3/3 | 3/3 | Same observed result |
| Mean full time | 9.82 s | 10.11 s | p20 was 2.9% slower |
| Actions | 13 | 10 | 23.1% fewer |
| Coal loaded | 130 | 9 | 93.1% less loaded |
| Execution-time model requests | 0 | 0 | No change |

**Coal loaded is not coal burned.** The change left more coal in the starting inventory and retained a small reserve in each machine. It did not establish lower fuel consumption per plate.

The speed result is consistent with a practical plateau on this task. Most valid code versions finished in roughly 8–11 seconds. The paired rerun did not confirm further improvement. Fixed measurement time, startup, and save inspection account for much of the total. This is not proof that no faster policy exists.

Source: [hill-climb report](../continuous-policy-search-2026-09-10/README.md), [paired recheck](../continuous-policy-search-2026-09-10/paired-recheck.json), and [all new Methods](../../policies/continuous-v3/README.md).

## Comparison with deterministic scripting

The deterministic operator-reference script passed two earlier headless repair checks. Full times were **8.57 and 8.59 seconds**, including independent save reload. Both produced five plates and five ore in each of the three windows, with zero model API calls.

Those were unscored host repair checks, not a frozen contender in the matched development or final panels. Their source stage and timing conditions differed. Their mean of 8.58 seconds is useful context, but it cannot support a fair speed ranking against p10 or p20.

The selected p10 Method and every new hill-climb version are themselves **deterministic Python executed through Method v3**. Astra designed the code between trials; it did not choose actions through model calls during those executions.

The supported conclusion is that Astra can produce, test, and refine a reusable script for this task. We have **not shown that it beats the operator’s deterministic script**, or that the Method wrapper itself improves runtime speed. That claim would need a matched panel with the reference script as a frozen contender under the same source, maps, launch conditions, and accounting.

Source: [deterministic reference checks](../headless-control-2026-09-10/README.md). The older scripted 20-plate tests used a different task and timing interval, so their times are not pooled here.

## Failures, cost, and evidence

The first comparison retained a version 1 scheduler failure and a version 2 direct-agent failure. The hill climb retained five failed attempts: three wrong batch-request tests, one missing-runtime-metadata setup failure, and one game process killed before its terminal save was written. The sender of that kill signal is unknown. Its live production passed, but it remains a failed attempt because the save evidence is missing. Linked replacements did not erase either original failure. The rejected p21 Method draft also remains saved.

Every passing continuation trial has a matching independent save check. The validator hashes and all 16 new policy hashes were checked at closure. The continuation left no owned game process running. Full local traces and available saves remain outside Git; reviewed measurements and source versions are public.

| Phase | API requests | Known API estimate |
| --- | ---: | ---: |
| Headless setup | 26 | $0.385021 |
| Initial development, including version 1 failures | 107 | $1.694439 |
| Initial final comparison | 28 | $0.418094 |
| Feedback-driven continuation | 0 | $0 |
| Total for this headless job and continuation | 161 | $2.497554 |

Usage was known for 160 responses. One interrupted request, cache-write charges, and Codex subscription authoring cost remain unknown. These are saved API estimates, not invoices or a complete cost for the research. The zero continuation API cost does not mean the hill climb had no authoring cost. No weights were trained or credits redeemed.

The small, reused map set and unequal numbers of exploratory trials do not establish a general success rate. This finished search supports a narrow result: strong runtime savings from a saved code procedure, followed by improvements in actions, fuel allocation, and checks, with no further demonstrated speed gain and no demonstrated advantage over the deterministic reference.

[Computed metrics and source hashes](metrics.json). [Closure record](closure.json). [Full continuation commands](../continuous-policy-search-2026-09-10/attempts.md).
