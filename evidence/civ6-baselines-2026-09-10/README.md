# Direct Astra Civ baselines, 10 September 2026

This panel is in progress. These are actual game outcomes from fresh Astra
Codex processes, with no previous run history or reference plan supplied.
The model is gpt-6-astra with medium reasoning and ChatGPT authentication.
Each baseline permits 20 minutes of play and 1,500 total game requests.

| Case | Attempt | Task and save checks | Turns | Playing time | Requests |
| --- | --- | --- | ---: | ---: | ---: |
| Nearby food | 1 | Passed | 35 | 331.18 seconds | 253 |

The first run ended with 24.234375 science per turn, gold 80.37890625,
net gold income 11.5, and food surplus 4 in the capital. Both new cities had
population 5, with food surpluses 6 and 4. The trace establishes five complete
hold rounds. A separate process inspected the reloaded terminal save and
found the same state. The full run and reload check took 377.21 seconds.

This run supplies a legal completion witness for this starting case. The
verifier reports `calibration_goal_met`; its `verified_pass` field remains
false because the full benchmark release and calibration review are pending.
It is a successful direct-Astra task attempt, not evidence of a Method advantage.

See `economy-food-1.json` for usage, limits, source and trace hashes, and save
hashes. The original starting and terminal saves, signed traces, and full
model logs remain local under `runs/civ6-economy-food-baseline-1`. No separately
billed API calls were used. Subscription cost and authoring cost are not
reported as zero.

The earlier [interface attempts](../civ6-interface-2026-09-10/README.md) remain
separate. In particular, the apparent success with a late boundary record was
not converted into a verified result. This is a new run with corrected capture.

Five further economy baselines, the other economy map cases, live combat
validation, and combat baselines remain. Continuous Method search has not
started for Civ.
