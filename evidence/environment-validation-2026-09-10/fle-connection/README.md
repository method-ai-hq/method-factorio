# C: Astra through the matched FLE connection

All three runs produced 20 new iron plates and passed both the fixed game
check and inspection after loading the terminal save. Each used 12 actions,
with no game-action errors. The starting eight plates stayed in inventory.

C uses a Unix socket to the same restricted FLE dispatcher as A and B. It
preserves the action list and full post-action observations. It does not
expose all native FLE tools. This is the matched connection variant from the
test plan; native responses and cached handles were not tested.

| Seed | Trial role | Start to verified goal | Complete trial | Action window |
| --- | --- | ---: | ---: | ---: |
| 44340 | Pilot; manual shutdown | Excluded | Excluded | 158.75 s |
| 44341 | Matched comparison | 161.94 s | 493.07 s | 132.60 s |
| 44342 | Matched comparison | 179.74 s | 216.57 s | 150.42 s |

Complete time includes startup, model work, report writing, and host cleanup.
The external check runs before the timer ends. The later save reload is
reported separately. The action window runs from the first game request to
the last game response. Game time is stored separately in each check.

Seed 44341 reached the goal long before its report completed. Its large gap
is a real end-to-end delay; these measurements do not identify its cause.
The paired sample is only two seeds, and other tests shared the Mac and
subscription capacity. It cannot establish a stable speed ranking.

## Settings and billing

Factorio 2.0.77, pinned FLE 0.4.8, base game, no enemies, no starting research
or factory, declared starting inventory, game speed 1, FLE fast mode, and
continuous simulation during thinking. Astra ran through Codex signed in to
ChatGPT. API-key overrides were removed. No separate model API calls were
made. Token counts are in the summary; subscription cost in dollars is unknown.

The playing instruction matches the Method's producing step, with only the
connection instruction and baseline label changed. C has no Method preflight
or model verification phase. The independent game check is unchanged.

## Runner correction and retained evidence

The pilot runner had an unsafe shutdown function: it would signal the whole
host process group, including Factorio. The operator stopped that runner
before teardown, let the playing agent finish unchanged, and stopped only
the host so it could save cleanly. The pilot passed game and reload checks,
but its complete-time result is excluded. Two later seeds used the corrected
runner without that intervention.

After all C games ended, a review found that a failed recovery read could
return a null state and break report generation. The current runner handles
that case. A synthetic failed-action report check passed. None of the C game
records contains a null state, so the measured results are unchanged. The
[pilot source](sources/runner-pilot.py.txt) and
[measured source](sources/runner-measured.py.txt) remain archived with hashes.

The [summary](summary.json) links run names to their timing and checks. Each
folder holds initial and final state, action timing, source hashes, save
inspection, and the agent's report. Raw model events, prompts, native logs,
and saves remain under the matching ignored `runs/` folder. Their hashes are
retained. Agent reports are recorded claims; the game and save checks supply
the success evidence.

Recipe selection, research selection, and rocket launch are not exposed in
this interface. Trains, circuits, combat, large factories, full-game play,
and active save resume were not tested by C.
