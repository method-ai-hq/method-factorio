# Changes from Method v2

The trial reported calibration goal completion in 33 completed turns, with a full five-round hold, 128 requests, and 366.66 seconds of play. It was not a verified scored pass (`verified_pass: false`). Method v3 preserves the task, budgets, hold, and connection-failure handling.

Science was the final bottleneck: at boundary turn 26 both new cities had population 3 or more, positive food, and nonnegative finances, but science was 18.97. It remained below 20 at turns 27–28 and first crossed at turn 29 (20.93). The revision requires a numerical science forecast before builds finish and compares earlier production in the youngest city against additional science in established cities.

The first expansion reached population 3 at boundary turn 15, then population 4 with +5 food at turn 19. The decision list places a granary after its Library purchase and before its Campus project. This supports scrutinizing the granary's opportunity cost and reassessing food focus sooner, without claiming that removing it alone would save a known number of turns. The later city first appears at turn 18 and reaches population 3 at turn 26; site selection and Builder allocation therefore consider its growth and Campus completion together.

Science fluctuated from 18.97 to 18.09 before qualification and from 21.96 to 20.78 during the qualifying period. The method retains project renewal and round-by-round verification rather than assuming a peak will persist. The evidence does not isolate each fluctuation's cause or prove an alternative build order.

Five requests were rejected: four unavailable unit operations and one unavailable research choice. Arrival/movement checks, refreshed availability after rejection, and avoiding unchanged retries address this overhead. Compact state-delta reasoning targets the trial's large token usage without removing necessary verification. No new gameplay trial was run; earlier completion remains an objective, not a measured result.
