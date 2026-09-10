# Decisions

Created 10 September 2026.

## Accepted direction

- Use Factorio as the task domain.
- Build on Method, in a fresh repository inside the Method workspace.
- Make the hackathon repository public and distinguish new work from dependencies.
- Start with a plain-English problem statement, plan, and design.
- Study Astra's ability to invent reusable playing policies and improve them through trials.
- Treat speed and model cost as part of policy design.
- Consider collaboration, competition, and Rise of Nations as later experiments.

## Initial implementation choices

These choices make the first design concrete. They are recorded assumptions, not measured results or permanent constraints.

| Choice | Initial direction | Reason |
| --- | --- | --- |
| Final task | Launch a rocket in base Factorio. | Clear external endpoint. |
| Controls | Programmatic game actions; evaluate FLE first. | Focus the first experiment on policy design and execution cost. |
| World | Fresh world with declared starting inventory and no factory. | Separate reusable policy from a prepared factory. |
| Enemies | Disabled initially. | Isolate production, planning, and recovery. |
| Improvement | Change policy versions between development trials. | Make each comparison inspectable. |
| Evaluation | Frozen policy on separate map seeds. | Test reuse beyond development worlds. |
| First scope | Single-policy experiment. | Establish a working basis for later collaboration. |

Keyboard-and-mouse gameplay is not part of the first implementation assumption. Changing that choice changes the experiment and should be recorded here before the relevant trials.

## Open before implementation or scored use

- Exact Factorio, adapter, and Method SDK versions, with compatibility evidence.
- Which desired execution types exist in the selected SDK and which need new code.
- Local or cloud game host, available licensed game installation, and setup requirements.
- Exact world settings, initial inventory, and allowed tool observations and actions.
- Continuous or paused simulation during model calls, and simulation speed.
- Available execution models and cost accounting.
- Operator-set development and evaluation spending caps and time limits.
- Development seed set, evaluation seed handling, and trial count.
- A fixed policy for resets, infrastructure failures, and human interventions.

## Change record

When an experiment rule changes, record the date, reason, and affected trial set. Do not rewrite earlier results as if they used the new rule.

## Sources reviewed during design

- [Factorio rocket silo and base-game endpoint](https://wiki.factorio.com/Rocket_silo).
- [Factorio Learning Environment source](https://github.com/JackHopkins/factorio-learning-environment).
- [FLE v0.3.0 design and evaluation notes](https://jackhopkins.github.io/factorio-learning-environment/versions/0.3.0.html).

These sources inform the design. They do not establish compatibility with an installed version. Exact dependency versions remain open.
