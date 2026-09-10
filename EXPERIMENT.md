# Experiment rules

Status: draft. The direction is fixed; the run settings marked open below must be selected before scored trials.

## Task

Launch a rocket in base Factorio from a fresh world. No initial factory, supplied blueprint, free research, or administrative resource grants are allowed during a scored run.

The proposed first setting disables enemies. Record that choice in every result. A run in that setting supports a claim about production and planning under those conditions.

## Settings to freeze

Before running a comparison, record:

- Factorio version, enabled mods, and FLE or adapter revision.
- Map generation settings and exact starting inventory.
- Allowed actions, observations, and documentation.
- Whether the game runs during model thinking, game speed, and pause rules.
- Wall-clock limit, game-time limit, spending cap, and operation limits.
- Available models, their settings, and the source of cost estimates.
- Development seeds and the procedure for keeping evaluation seeds separate.
- The number of trials and how infrastructure failures are handled.

No numerical budgets or tested versions have been selected yet. Do not start paid trials until the operator has set a spending cap. Use the same settings for each member of a comparison.

## Comparisons

1. Direct agent: Astra receives the goal and the same permitted game tools and documentation.
2. Initial Method: the first validated Astra-authored policy, saved before feedback from its trials is used to improve it.
3. Improved Method: a policy selected through development trials, frozen before final evaluation.

Give each approach the same allowed building blocks and total execution budget. If a Method can select cheaper models or use helper code, give the baseline equivalent access. Report design and search spending separately from execution spending.

Record how each policy was created. A comparison between the initial and improved Method tests the whole improvement process. It does not alone establish that a particular English instruction caused the gain.

Use matching map seeds across approaches. Keep final evaluation seeds out of policy development. Repeat trials when resources permit, and report the actual sample size. A single run is a demonstration, not a reliable success-rate estimate.

## Results

The primary result is a verified rocket launch within the declared limits and without human gameplay intervention.

Also report wall-clock time, game time, measured model usage, estimated or billed cost with its source, and human interventions. Missing cost data remains unknown. Do not treat missing usage as zero.

For incomplete trials, report the stop reason, research state, production state, and saved evidence. These measurements explain a failure; they do not count as a win. Avoid a single progress score that can reward endless production of an irrelevant item.

Report all trial outcomes, including timeouts and failures. Separate task failure from infrastructure failure under a rule chosen before the comparison. Do not silently reset a failed run and retain only its successful continuation.

## Policy improvement

Development may use saved checkpoints and shorter tests to investigate a specific failure. Record when a candidate starts from a checkpoint. A checkpoint test is not a fresh-world win.

Freeze the evaluator while policies change. Candidate-defined subgoals are internal signals. Passing them does not alter the external task.

## Evidence release

Publish the selected Methods, new source code, run settings, aggregate results, and reviewed evidence sufficient to inspect the reported result. Exclude credentials and game binaries. Explain how a person with their own Factorio installation can rerun the experiment.

No results exist yet.
