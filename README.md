# Method × Factorio

Can Astra invent and improve executable Methods that finish long tasks when the final result is clear, but the value of each action is uncertain?

Our task is to build a factory and launch a rocket in base Factorio. Astra will design the playing procedure, inspect its results, and test changes. The procedure can use plain-English instructions, agents, model calls, bounded loops, and code. It must choose where reasoning and verification are worth their time and cost.

**Status: design only.** No game run, performance result, agent integration, or supported game version is claimed yet.

## Read the design

| File | Purpose |
| --- | --- |
| [GOALS.md](GOALS.md) | The research question, task, and success conditions. |
| [DESIGN.md](DESIGN.md) | How the proposed system works, in plain English. |
| [EXPERIMENT.md](EXPERIMENT.md) | Fixed evaluation rules and measurements. |
| [PLAN.md](PLAN.md) | Work stages and evidence needed to complete each stage. |
| [DECISIONS.md](DECISIONS.md) | Accepted direction, initial choices, and open decisions. |
| [HACKATHON.md](HACKATHON.md) | What is new, what is prior work, and what the demo may claim. |

These files describe the experiment. Playing agents must not edit them. Candidate Methods and run records will live separately.

## Foundation

[Method](https://withmethod.ai) provides the procedure format and execution foundation. [Factorio Learning Environment](https://github.com/JackHopkins/factorio-learning-environment) is the proposed game interface. We will check compatibility before selecting exact versions.

This is a separate repository created for the hackathon on 10 September 2026. The Method product and FLE are prior work. Factorio is a separate commercial game; its files and assets are not part of this repository.

Our original code and documentation use the [MIT license](LICENSE). Third-party software keeps its own license.
