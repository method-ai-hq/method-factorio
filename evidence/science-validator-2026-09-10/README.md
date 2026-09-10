# Science task checker validation

All ten live checker tests passed on base Factorio 2.0.77. The working factory
was accepted. Nine incomplete or invalid attempts were rejected. All ten
terminal saves matched their separately reloaded game state and stored
measurements. The action after finish was also detected in the action trace.

This is operator validation of the new [science task](../../docs/science-task.md).
It is not a policy-search result, a Method win, or a rocket launch. The
reference construction program is test equipment and must not be supplied
as a plan to policy authors.

| Live case | Expected result | Observed result |
| --- | --- | --- |
| Working factory through the full HTTP host | Accept | Accept |
| Empty factory | Reject | Reject |
| Red packs only | Reject | Reject |
| No solar power | Reject | Reject |
| Copper drill outputs disconnected | Reject | Reject |
| Green assembler set to the wrong recipe | Reject | Reject |
| Stored packs, with mining drills removed | Reject | Reject |
| Assembly stops after two measured minutes | Reject | Reject |
| Forbidden manual ingredient transfer | Reject | Reject |
| Observation requested after finish | Reject | Reject |

The working factory produced 15 red packs in each measured minute. Green pack
counts were 13, 12, and 13. The required minimum was 10 of each. Newly mined
ore, smelting, and every required intermediate recipe also passed in each
minute. The late-stop case passed its first two windows and failed its third.
The stored-pack case had its materials removed by the checker before warmup.

The full offline suite passed all 46 test methods. The six new science test
methods include multiple cases for missing or changed records, changed action
logs, missing saves, missing production stages, incorrect time boundaries,
partial windows, stockpiles, game settings, action limits, and time limits.

## Provenance and limits

[summary.json](summary.json) records exact source hashes, measurements, action
counts, elapsed times, save hashes, and local run paths. The final live suite
is `runs/science-validation-v2`. Raw traces, game saves, and private native
logs remain local and ignored by Git. The source hashes identify the tested
code independently of the later commit that publishes this report.

Earlier local setup attempts found an unavailable game API, an incorrect
scalar JSON read, and incomplete power connections in the reference factory.
These failed attempts remain in `runs/science-smoke-*` and
`runs/science-reference-*`. The first full suite was stopped during its fourth
save inspection because large RCON responses were slow to parse. The transfer
was changed to bounded chunks. The final suite reran all ten cases on that
code. No earlier result was relabeled as a final-code result.

These checks use an operator-prepared reference on reserved seed zero. They
establish that the task is achievable and that the tested rejection cases
work. They do not establish agent success on other seeds or the performance
of an iterative Method search. The player interface restricts game actions;
operating-system isolation from hostile local code is not claimed.

No paid model API calls or screen recordings were used. Subscription authoring
cost was not measured. See [run and verification commands](../../docs/run-science-task.md)
to reproduce the checker tests or start a new task attempt.
