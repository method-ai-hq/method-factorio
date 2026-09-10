# Goals

## Research question

Can Astra design and improve a reusable procedure for a long task when the final result is easy to check, but the value of individual actions is uncertain?

We test this by asking it to win base Factorio: start in a fresh world, build the required production system, and launch a rocket.

In this project, a policy means a procedure for choosing actions from observations and retained state. It can include instructions, model calls, code, loops, and checks. It is not a change to model weights.

## Why Factorio

Factorio exposes detailed facts: inventory, buildings, research, power, and production. Those facts do not establish that a decision was good. More iron production can be measured exactly, yet building more furnaces may delay a more important task.

The policy must decide what to do, what to measure, when to wait, when to inspect, and when to change its plan. A successful local check does not prove progress toward the final goal.

The base game's rocket launch gives the experiment an external endpoint. See the [Factorio rocket-silo reference](https://wiki.factorio.com/Rocket_silo). Space Age has a different endpoint and is outside the first experiment.

## What Method contributes

Method makes a procedure readable, executable, and inspectable. Named inputs and outputs connect operations. Saved results and checks expose failures. Versions let us compare changes to the procedure.

The original pattern of a fresh worker agent and a separate checking agent for every step can be slow. We want Astra to decide which work needs that treatment and which work can use a small call, code, a bounded loop, or a longer agent operation.

We will test whether the full procedure improves results. We will not assume that English instructions alone cause an improvement.

## Primary goal

A fresh execution of an Astra-authored Method launches a rocket from the declared starting conditions, within a recorded time and compute budget, without human gameplay actions.

Launching a rocket is a result for that run. It does not, by itself, establish that hill climbing helped or that the policy works on other maps.

## Evidence of improvement

Compare a direct agent, the initial Method, and an improved Method under the rules in [EXPERIMENT.md](EXPERIMENT.md). Test selected policies on seeds that were not used to develop them. Publish failures as well as successes.

We want to learn whether the improved Method:

- Completes more runs within the budget.
- Uses less time or model spending for successful runs.
- Recovers from mistakes and blocked production.
- Transfers useful procedure knowledge to a fresh execution.

These are questions to measure, not current results.

## Later questions

1. Can two Astras operate one factory more effectively than one under the same total budget?
2. How do independently developed policies compare in a race on identical starting maps?
3. Can the approach handle direct opposition and strict response deadlines in Rise of Nations?

The first submission centers on the single-policy experiment. Collaboration, competition, and Rise of Nations are later stages, with separate results.

## Boundaries

We do not aim to train model weights, prove that a playing policy is optimal, or claim a new general agent capability from one successful game. We do not supply a complete factory plan and then describe its execution as policy invention.

The agent may use its existing knowledge and the declared documentation. "Invent" means construct and test a policy for this experiment; it does not mean discover Factorio without prior knowledge.
