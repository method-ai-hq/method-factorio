# Method × Factorio

Can Astra invent and improve executable Methods that finish long tasks when the final result is clear, but the value of each action is uncertain?

Our task is to build a factory and launch a rocket in base Factorio. Astra will design the playing procedure, inspect its results, and test changes. The procedure can use plain-English instructions, agents, model calls, bounded loops, and code. It must choose where reasoning and verification are worth their time and cost.

**Status: a headless supplied-kit comparison is complete.** The selected Method and the frozen initial Method each passed three development maps and two unseen final maps. The direct agent passed two of three development maps. Mean full final time was 9.06 seconds for the selected Method and 51.78 seconds for the initial Method. See the [reviewed comparison](evidence/headless-policy-search-2026-09-10/README.md), including failures, source versions, and known cost. This is a small production test, not a rocket launch or a fresh-world win.

## Run the small test

Read [the setup and run instructions](docs/run-control-test.md). The test uses
the installed Method SDK, Codex signed in through ChatGPT, and a pinned FLE
revision. Docker is not required. The [initial Method](policies/iron-plates-v1.method)
gives Astra the goal and the allowed tools, without a factory construction recipe.

The root design remains the plan for the larger experiment. This small test
does not replace its rules or establish a scored result.

The first parallel [environment tests](evidence/environment-validation-2026-09-10/README.md)
now compare direct-agent, Method, FLE-connection, and fixed-script control.
Small production works, accelerated simulation is fast, and advanced probes
found control defects. Full games and complete control remain unverified.
See the [test design](docs/environment-validation.md) and
[run commands](docs/run-environment-validation.md).

To start the next stage, use the [complete policy-search goal prompt](docs/policy-search-goal.md).
It requires the Method v3 CLI and a 60-minute total limit, with parallel policy
search, a supplied-kit production evaluator, and gameplay recordings. The prompt
is ready; the new benchmark and search have not run.

## Read the design

| File | Purpose |
| --- | --- |
| [GOALS.md](GOALS.md) | The research question, task, and success conditions. |
| [DESIGN.md](DESIGN.md) | How the proposed system works, in plain English. |
| [EXPERIMENT.md](EXPERIMENT.md) | Fixed evaluation rules and measurements. |
| [PLAN.md](PLAN.md) | Work stages and evidence needed to complete each stage. |
| [DECISIONS.md](DECISIONS.md) | Accepted direction, initial choices, and open decisions. |
| [HACKATHON.md](HACKATHON.md) | What is new, what is prior work, and what the demo may claim. |

These files describe the experiment. Playing agents must not edit them. Candidate Methods live in `policies/`. Local run records stay in ignored `runs/` folders.

## Foundation

[Method](https://withmethod.ai) provides the procedure format and execution foundation. [Factorio Learning Environment](https://github.com/JackHopkins/factorio-learning-environment) provides the game controls. The small test uses Method SDK 0.3.0 and FLE 0.4.8 at the revision in the run instructions. Compatibility beyond this tested setup remains open.

This is a separate repository created for the hackathon on 10 September 2026. The Method product and FLE are prior work. Factorio is a separate commercial game; its files and assets are not part of this repository.

Our original code and documentation use the [MIT license](LICENSE). Third-party software keeps its own license.
