# Compare a searched Method with direct Astra

The question is whether a Method, improved through repeated practice, solves new damaged factories more often or with less work than a fresh direct Astra run. This experiment does not assume that Methods will win. It does not test whether deterministic programs can solve Factorio.

## Fixed task

The player gets the instructions in `repair-task.md`. The task is to repair automatic red and green science production. Each attempt has 300 seconds of real time and 200 game actions. The game runs at speed 20 with permanent daylight. Both approaches have the same game tools, code tools, model, reasoning setting, and limits. Each starts from a separate copy of the same damaged save.

The independent checker removes stored materials before it measures three full game minutes of production. It checks native game evidence and reloads the final save. A model statement is never a passing result. The repair rules are fixed in `repair_contract.py`; the production rules remain in `science_contract.py`.

## Cases

There are 10 development cases and 20 final cases. Layouts, machine positions, supply routes, and groups of faults vary. Faults include missing equipment, incorrect directions, wrong or missing recipes, and power faults. Each case must have native saved-game proof of three conditions: the healthy factory passes, the damaged factory fails, and a legal repair passes. A defective generated case is retained and replaced before any player sees it.

The case builder and checker are operator tools. Players do not receive their code, fault lists, or repair plans. Each fresh Codex run has its own work folder and restricted file access. The policy author receives only the public task and development evidence. Final case details and results remain outside policy development.

## Comparison

1. Run a fresh direct Astra Codex instance on each development case. It can reason, write code, inspect the game, make repairs, and correct its own errors within that attempt. It does not receive results from other cases.
2. Build a Method with the real Method v3 runtime. Its steps can use code and Astra calls. Model calls use the same fixed Codex runner as direct Astra. Save every candidate version.
3. Test a candidate on development cases. Give the author its action records, model reports, scores, time, and token use. Revise the Method and test again. Keep failed trials. Search for at most four tested candidate versions in this experiment, with up to ten development attempts per version. Stop early only if further versions repeat the same outcome and no useful change remains.
4. Select the version with the most development passes. Break ties using the lower median successful attempt time, then lower reported token use. Freeze its files before any final player runs.
5. Run fresh direct Astra and the frozen Method on the same 20 final saves. Do not revise the Method from final results. Each attempt gets the same limits. If final results expose a new problem, a later search must use a new final set.

The initial Method is a single step that calls the direct runner. Searched versions may change their prompts, code, and step structure. They cannot change the game server, checker, model, or per-attempt limits. All Method calls share one trial deadline and one game action budget. A new step does not reset them.

The final report gives pass counts, paired outcomes, time, actions, and available token counts. It reports development work separately from final execution work. A faster result on successful attempts does not compensate for a lower success rate without an explicit tradeoff. Twenty final cases give an initial result, not proof about all Factorio tasks.

## Execution and cost

Use the signed-in Codex subscription. No paid API backend is used. Subscription token use is recorded when Codex reports it; its dollar cost is unknown. No claim of zero model cost is made. Each game is headless. No screen recording runs during search.

At first, one player ran while one case builder ran. A later capacity check passed with three managed worlds active: the native measurement took 15.34 seconds for exactly 18,000 game ticks. Direct and Method development runs can therefore run together while cases are built. Independent worlds use separate ports, directories, and saves. Use two player worlds for the final comparison, with no case builder. Save all local evidence under `runs/`; publish only reviewed summaries and source hashes.

If the server or runner fails, retain the attempt, fix the cause, and repeat affected comparisons under the same corrected setup. Do not turn an infrastructure failure into a game failure or silently discard a failed policy attempt.
