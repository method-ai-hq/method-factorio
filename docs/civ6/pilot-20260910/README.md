# Fixed-map economy Method pilot

The owner requested this pilot on 10 September 2026, with less than one hour
available. This changes the immediate work order: the other map cases and
combat baselines remain pending while this comparison runs.

The job starts at 20:09:30 UTC and stops at 21:04:30 UTC. The frozen lock
records the original economy profile hash, three candidate versions, three
authoring calls, seven playing trials at most, and the comparison order.
No separately billed API calls are allowed. One graphical client runs at a
time. No Method receives the game administration or evaluator interfaces.

The original starting save and task limits stay fixed. Each actor uses a
fresh Astra Codex process, medium reasoning, the same task, the same tools,
20 minutes of playing time, and 1,500 game requests. The Method arm also gets
the exact supplied Method text. A run cut short by the job stop is incomplete;
it is not a full-budget trial or evidence of a gameplay failure.

## Search

An isolated Astra author writes Method v1 from the task and the aggregate
results of the two earlier valid direct baselines. It receives no winning
action script or map coordinates. A fresh Astra actor tests the Method.
The next author receives the previous Method and its actual trial evidence,
then writes a revision. Repeat for v3. Keep every author call, version,
trial, and invalid result. Each author call has a 90-second limit.

Select among valid development trials in this order: task success, fewer
completed game turns, fewer game requests, then less playing time. If no
candidate passes, freeze the best valid failure only for a clearly labelled
comparison; do not call it a successful Method. Write the selected Method
hash and all development results to `frozen.json` before comparison starts.
The runner rejects a different Method in the comparison phase.

## Comparison

Run direct, Method, direct, Method in that order, as time permits. Reset to
the same starting save each time. Do not revise the frozen Method after
seeing a comparison result. The old direct baselines are context and are
not substituted for new comparison trials.

Both comparison arms receive the same explicit efficiency goal: meet every
task condition first, then minimize completed turns, requests, and playing
time in that order. They also receive a request to keep model use efficient.
This common instruction was set before the first comparison trial. Search
actors receive these priorities through their Method. Search results are
used for selection and are not pooled with final comparison results.

Report success counts first. For successful runs, show game turns, playing
time, total game requests, input tokens, cached input tokens, output tokens,
and reported reasoning tokens. Do not add reasoning tokens to output tokens
as if they were disjoint. Report invalid and incomplete trials separately.
The independent save check and setup time are separate from playing time.

Search cost consists of the authoring calls and development playing trials.
Report those separately from frozen execution. Subscription dollar cost and
supervisor authoring cost remain unknown. Do not describe them as zero.

This is a small, same-map calibration pilot. It cannot establish general
performance across maps. The actor uses LLM reasoning during execution, but
a later comparison with fixed decision rules is needed to establish that
runtime LLM decisions contribute to the result. The benchmark release review
also remains pending.
