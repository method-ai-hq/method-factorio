# Factory repair search

Status: Method development is in progress. Final tests have not started.

Direct Astra restored production in all ten development factories. It earned
eight strict passes. The other two attempts requested observations of equipment
types outside the allowed interface. Both still restored the factory, and all
three production windows passed. These are request-rule failures, not failed
repairs. This development set has not shown that policy search is needed to
solve the factory repairs.

The [baseline record](development-baseline.json) contains case hashes, outcomes,
time, actions, and reported token use. Each case used a fresh Astra Codex session
with code tools, the same game tools, a 300-second limit, and a 200-action limit.
The median full time among strict passes was 85.29 seconds. The median time
from game activation through the production check was 79.74 seconds. Ten
sessions reported 3,371,030 input tokens, of which
2,902,272 were cached, and 15,137 output tokens. These are execution totals;
they do not include setup, authoring, or operator work. Subscription dollar
cost is unknown.

The checker removes stored materials, measures three production windows,
then reloads the saved game independently. All ten direct attempts passed the
independent evidence checks. A model report does not determine the score.

Methods are being improved using development results. Every version and
unsuccessful attempt is retained. One Method will be selected and frozen before
both approaches play the same twenty new cases. Final outcomes will be added
here without changing the selected Method from those outcomes.

See [the fixed experiment](../../docs/repair-experiment.md),
[the task](../../docs/repair-task.md), and [the run guide](../../docs/run-repair-search.md).
Raw saves and traces remain in ignored local `runs/` folders. No game assets,
credentials, or raw recordings are included in this evidence directory.
