# Work plan

## 0. Set the experiment

Review these documents. Select the remaining game, interface, timing, model, and budget settings in [DECISIONS.md](DECISIONS.md). Freeze the first experiment configuration.

Complete when the win condition, starting state, permitted actions, budgets, and comparison rules are explicit.

## 1. Connect to a controlled game

Check the available Factorio installation and license, then select a compatible adapter version. Start a fresh test world. Read state, perform one permitted action, and confirm its actual effect. Check game-time behavior and restart from a known save.

Review the adapter's administrative capabilities and exclude them from the playing interface. Use exact versions and document setup.

Complete when one small real action and its independent state check work, and setup can be repeated. This does not count as gameplay success.

## 2. Run the smallest useful Method

Check the selected SDK against the execution choices in [DESIGN.md](DESIGN.md). Implement only the missing choices needed for an initial playing loop. Connect observation, bounded execution, state, measurements, and stopping.

Complete when a small Method acts in the game, saves its result, checks the effect, and stops at its configured limit. Recovery must inspect state before repeating a possibly completed action.

## 3. Establish the baseline and initial policy

Run the direct-agent baseline under the frozen rules. Ask Astra to author an initial Method with the same goal and available tools. Preserve that version before using trial feedback to change it.

Use short integration trials to remove infrastructure defects, then clearly mark the start of measured gameplay trials. Save unsuccessful runs.

Complete when both approaches produce inspectable records with known settings and actual usage. Winning is not required to complete this measurement stage.

## 4. Improve the procedure

Give Astra development-run evidence. Ask for a specific proposed change and the expected effect. Test candidate versions against the initial policy under matching conditions. Keep useful alternatives and record why a version was selected.

Measure whether changing call size, model choice, check frequency, decomposition, or helper code improves the complete procedure. Do not assume each change is beneficial.

Complete when the loop can produce and compare real policy versions. That proves the mechanism works; the measured results determine whether it helps.

## 5. Attempt the full task and evaluate transfer

Select and freeze a policy. Start fresh worlds on evaluation seeds. Attempt the rocket launch within the fixed budgets. Record all outcomes, and independently inspect any claimed launch.

The primary goal is complete only after a valid launch. A stopped or partial run remains incomplete. A claim of improvement also requires the comparison evidence in [EXPERIMENT.md](EXPERIMENT.md).

## 6. Prepare the public demonstration

Show actual gameplay and the exact Method that produced it. Explain one measured procedural change. Include time and cost with their sources. Label any accelerated recording or replay. State the starting conditions and all human interventions.

Complete when the public repository distinguishes today's work from dependencies, includes runnable instructions, and supports every result claimed in the demo.

## Later stages

- Shared factory: two Astras cooperate under a fixed total budget.
- Race: independently developed policies play identical starting maps.
- Direct opposition: define a separate competitive experiment.
- Rise of Nations: design an experiment with strict response deadlines.

These stages do not delay reporting the first experiment honestly. Do not claim them as implemented until their code and results exist.
