# Proposed next goal

This is a prompt for a new job. It takes effect only when the owner submits it.
It does not extend the earlier job or authorize new paid calls by itself.
Use the actual outcome as the Codex goal, not only an instruction to read a file.

## Goal text to submit

Run a new headless Method v3 Factorio policy-search job. Complete a valid
comparison of the direct agent, the frozen initial Method, and a selected
improved Method, including four final trials on two unseen maps. Finish all
work and cleanup within 60 minutes. Follow `docs/headless-policy-search.md`
and the production predicates in `docs/automatic-production-evaluator.md`.

I authorize paid OpenAI API calls for this new 60-minute job using the saved
key. No separate dollar ceiling is set. Do not redeem credits, train weights,
or extend the job. Report usage and known cost. Keep secrets out of all reports.

Optimization and final comparison trials use headless servers with no screen
recording. Keep full action/state traces, exact measurements, runtime and policy
hashes, model usage, terminal saves, and independent save checks. Later recorded
demonstrations are separate attempts and need their own time allowance.

Use up to four Astra workers, including the supervisor, and up to eight game
worlds. Start with two headless worlds. Test higher concurrency one level at a
time before using it for a panel. Use matching capture mode and game settings
for all contenders. Four or eight worlds are limits, not targets to force.

Persist the deadline at the start. This job replaces the old 15-minute setup
cutoff and 12-episode setup cap with these explicit limits: up to 25 minutes
and 24 setup episodes, including failed launches. Reserve at least eight of
those episodes for repair and revalidation; do not spend the reserve on
concurrency probes or optional checks. Run the required working and broken
factory checks before scoring. Preserve the earlier job unchanged.

A recoverable infrastructure fault is a request to diagnose and repair, not a
reason to end the task. Pause new trials, keep all evidence, read the failing
stage, make a focused fix or reduce concurrency, and test the correction within
the remaining allowance. Do not send the same failing launch in a large batch.
After a verified common harness fault, allow at most one replacement per
contender/case; record both attempts. If source or fixed settings change,
validate and freeze a new benchmark version before scoring, and keep its
results separate unless matching trials are rerun. Never relax production or
save checks to make a policy pass.

Continue permitted offline code repair and focused tests if the game-launch
allowance is exhausted; do not create more game episodes. Stop paid and game
work at any applicable hard limit. Report a blocker only after the failed
cause, attempted repairs, and limiting condition are supported by evidence.
Do not claim that setup success is policy success.

Prioritize a small valid comparison over trial counts. End search by minute
40, finish final trials by minute 55, and save, brief, commit, push, and stop all
job-owned processes by minute 60. Reserve four final slots before search.
Freeze the selected Method before opening final maps. Keep the existing
32-policy and 120-scored-trial ceilings. Keep the 300-second production verdict,
30-second close allowance, 200-action limit, 60-model-request limit, 20-GiB data
limit, and 10-GiB minimum free space. Report failures with the fixed penalty.

Use the existing immutable candidates as starting points. Do not supply their
authors the operator reference factory plan. Keep evaluator and hidden-map
control with the supervisor. Complete the remaining host/runtime integration
and exact-endpoint restriction checks before approval. Update the local index
after every attempt and give a short progress report every five minutes.
Deliver the Methods, exact commands, comparisons, limitations, and total cost.
If the comparison cannot finish within a hard limit, report it as incomplete.

## Why this prompt differs

The old setup allowance was exhausted by simultaneous graphics loads. This
prompt removes graphics from optimization, allocates a separate repair reserve,
and tells the supervisor to keep working on repair within the hard limits.
It does not permit unlimited retries or changing the success condition.

Codex goals preserve an objective for continued work. They still need clear
completion checks and limits; a goal does not repair a broken launch script.
See [OpenAI's goal guidance](https://learn.chatgpt.com/use-cases/follow-goals).
