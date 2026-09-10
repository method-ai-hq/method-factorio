# System design

This is a proposed design. Implementation and compatibility checks are still required.

## Two loops

The playing loop observes the world, reads retained state, selects an operation, executes it, and decides what to do next.

The improvement loop reads completed trial records, identifies a failure or cost, proposes a new Method version, and compares it with earlier versions. It may keep several candidates when they have different strengths.

An improved factory is not necessarily an improved Method. Each trial therefore records both the game state and the exact policy version. Evaluation starts a fresh game with a selected, frozen policy.

## Fixed experiment and editable policy

The experiment defines the task, permitted actions, starting conditions, budgets, and external checks. The policy defines how to play within those rules.

Astra may change its candidate Method, helper code, internal checks, state representation, and choice of execution type. It may not change the evaluator, win condition, budget, game rules, or evaluation seeds.

During evaluation, the selected Method and its executable files remain fixed. The policy may update its working state and revise its factory plan through operations already defined by that Method. A change to the policy itself creates a new development version and requires a new evaluation.

## Game interface

Use programmatic controls for the first implementation. FLE is the proposed adapter. Check its exact action semantics, game compatibility, observation access, and time controls before use.

Expose a declared set of game actions and observations. Do not expose administrative commands that grant items, unlock research, alter recipes, or mark the task complete. Keep setup and measurement privileges outside the playing interface. The adapter must enforce this boundary; prompt instructions alone are insufficient.

Record action timing and any adapter shortcuts. Programmatic control is the declared interaction mode. It is not evidence of keyboard-and-mouse play.

## Policy execution

The desired execution choices are:

| Choice | Intended use |
| --- | --- |
| General agent operation | Work that needs several tool calls and adaptive reasoning. |
| One structured model call | A bounded decision with a defined result shape. |
| Bounded loop | Repeated calls or actions with a clear stop condition. |
| Code operation | Routine calculations, repeated actions, or exact checks. |
| Model selection | Spend more reasoning on difficult decisions and less on routine work. |
| Separate verification | Inspect a meaningful result independently when the benefit justifies the cost. |

Verify which choices the selected Method SDK already supports. Any missing support required here must be implemented and identified as new work. Do not treat this table as an existing API specification.

Every operation needs a time limit. Every loop needs a limit or stop condition. A longer agent operation must still fit within the run's remaining budget.

## What Astra designs

Astra chooses the division of work, the data passed between operations, retained state, escalation rules, and internal checks. We provide tool documentation and the objective, not a complete sequence for building a factory.

For example, a candidate might inspect production periodically and request a deeper diagnosis only after repeated failure to meet demand. That is an illustration, not a required policy or a measured result.

Code may handle repetition while English describes decisions and intent. Save both as part of the candidate. Attribute improvement to the complete policy unless a controlled comparison isolates a smaller cause.

## Verification

Internal checks help a policy decide what to do. The policy may improve them.

External checks determine the result of the experiment. They remain fixed. Read the rocket-launch result from game state or a trusted game event, and retain enough information to check it again. Also check that the declared starting conditions and action restrictions were used.

Production, research, and inventory measurements explain progress. They must not let an agent replace the final objective with an easier metric. A model's statement that it won is not evidence of a launch.

## Saved records

For each trial, retain:

- The Method version and hashes of its helper code.
- Model identifiers, settings, and tool definitions.
- Game version, adapter version, seed, settings, and starting state.
- Inputs, outputs, actions, checks, errors, and policy state.
- Game ticks, wall-clock timestamps, usage, and budget stops.
- Save files or checkpoints needed to inspect the result.
- Human interventions and the reason for ending the run.

These records support inspection and rerunning. They do not promise identical model outputs. Local records stay out of Git by default. Only reviewed, shareable evidence is published.

## Recovery

A process failure must not lead to blind repetition of an action. Read saved records and inspect current game state before continuing. Bind a checkpoint to its policy version and game state. Record any reset or restart.

Keep process recovery distinct from improving the playing policy. A trial interrupted by infrastructure failure needs an explicit outcome under the experiment rules.

## Collaboration and competition

Later, a shared-world experiment can give two Astras separate responsibilities and shared artifacts. It will need rules for action ownership, shared state, and conflicting changes. Two agents improving policies offline is a different experiment from two agents playing together.

A first competition can run two policies on separate copies of one starting map. Direct opposition in a shared world is a further change. Rise of Nations will require its own controls, timing rules, and evaluation design.

## Proposed project areas

Keep implementation, candidate policies, evaluation rules, and run data separate. The initial repository contains design documents only. Add source, policies, tests, and reviewed evidence as each stage requires them. Do not create empty subsystems before they have a concrete use.
