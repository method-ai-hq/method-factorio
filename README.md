# Method × Factorio

Can Astra invent and improve executable Methods that finish long tasks when the final result is clear, but the value of each action is uncertain?

Our task is to build a factory and launch a rocket in base Factorio. Astra will design the playing procedure, inspect its results, and test changes. The procedure can use plain-English instructions, agents, model calls, bounded loops, and code. It must choose where reasoning and verification are worth their time and cost.

**Status: the supplied-kit policy search is finished.** The [final report](evidence/policy-search-final-2026-09-10/README.md) covers direct Astra, deterministic scripting, and 16 new Methods made from game feedback. The earlier selected code Method completed two unseen maps in a mean 9.06 seconds, versus 51.78 seconds for the initial agent Method. The later hill climb reduced actions from 13 to 10 and coal loaded from 130 to 9, but did not show a further speed gain. No advantage over the deterministic reference script was established. This is a small production test, not a rocket launch or a fresh-world win.

## Harder task: automatic science

The [red-and-green science task](docs/science-task.md) requires an automatic
factory to mine two resources, make intermediate parts, supply power, and
produce at least 10 of each science pack per game minute for three minutes.
Its separate host and fixed checker remove stored materials before measuring
and independently reload the final save. See [run commands](docs/run-science-task.md)
and [checker validation](evidence/science-validator-2026-09-10/README.md).

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

The original [policy-search goal prompt](docs/policy-search-goal.md) is retained as
history. The search is now finished. Its [closure record](evidence/policy-search-final-2026-09-10/closure.json)
preserves the stop, and its [final report](evidence/policy-search-final-2026-09-10/README.md)
links the Methods, measurements, failures, and limits.

## Read the design

The new [factory repair comparison](docs/repair-experiment.md) tests a searched
Method against fresh direct Astra runs on varied damaged factories. It uses
10 development cases and 20 separate final cases, a fixed native game checker,
and the real Method v3 runtime. See the [run guide](docs/run-repair-search.md).
The [completed comparison](evidence/repair-search-2026-09-10/README.md) has
20/20 final passes for the Method and 18/20 for direct Astra. Both repaired all
20 factories; direct Astra's two failures were tool request errors. On the same
18 successful pairs, median full time was 71.22 seconds for the Method and
92.83 seconds for direct Astra. The Method used 56% fewer reported input tokens
across all 20 attempts. This shows an execution benefit on this task family,
not a repair ability that direct Astra lacked.

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
