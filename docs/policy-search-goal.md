# Goal prompt: one-hour Method v3 policy search

Copy this prompt into an Astra task in this repository. It does not start work
until you launch the task.

---

**Astra: design, test, and improve Factorio policies in Method v3. Run many
candidates in parallel. Finish within 60 minutes TOTAL. Save every result and
record the gameplay of every attempt.**

1. **Use Method v3.** All candidate Methods must use `format: method/3` and run
   through `method3 validate` and `method3 run`. Check `method3 --version` and pin
   the executable, configuration, and source revision. Install the public runtime
   if needed; follow the [v3 reference](https://github.com/method-ai-hq/method-spec/blob/main/spec/method-3.md).
   Never fall back to `method`, `method-run`, or Method 2.

2. **Use the authorized model access.** The operator authorizes paid OpenAI API
   calls for this one-hour job; no separate dollar ceiling was specified. Use the
   saved `OPENAI_API_KEY` from `~/.codex/secrets.env`, loaded only into the processes
   that need it. Never print it, include it in a Method, or commit it. Use the real
   v3 model backend for `call` and `agent` steps, and direct code execution for
   `run` steps. Verify the API model identifiers and record the selected profiles.
   Astra authors may use the Codex subscription. Record model usage and known or
   estimated cost; do not hide model calls inside scripts. No weight training,
   credit-reset redemption, or expansion of the 60-minute job is authorized.

3. **Work in parallel.** Use up to **8 separate game worlds and 4 Astra workers**,
   including the supervisor, within available worker slots. Keep candidate design,
   testing, and analysis in flight together. Use separate bundles, ports, saves,
   and recorders. One supervisor owns the evaluator and shared results. Reduce
   concurrency only when resource, recording, or subscription limits require it.

4. **Keep the hard deadline.** Spend at most minutes **0–15 on setup**, search until
   minute **40**, finish final comparisons by **55**, and save, clean up, brief,
   commit, and push by **60**. Installation and all cleanup count. Persist the
   deadline and apply it to every child process. Aim for **16 distinct policies
   and 60 trials**, capped at **32 policies and 120 scored trials**. These are
   targets, never reasons to exceed the hour or omit evidence.

5. **Freeze the evaluator first.** Read and implement
   [the fixed benchmark contract](automatic-production-evaluator.md). The task is
   to build drill → belt → inserter → furnace from a supplied kit. Success requires
   **5 new plates and 5 newly mined ore in each of three fixed game-time windows**,
   with no policy actions during measurement. Validate the evaluator against
   working and broken factories before scoring. Leave the old evaluator unchanged.
   Policy workers cannot edit the evaluator, game rules, hidden maps, or budgets.

6. **Create and improve policies.** Freeze an initial Astra-authored v3 Method
   before learning from its gameplay. Also measure a direct-agent baseline under
   the same conditions. Have workers explore different control logic, layouts,
   observations, batching, and repair strategies. Test on the same development
   maps, study failures, and improve multiple promising versions. Save each
   version's parent, hypothesis, code, and results. Do not supply a factory plan,
   count renames as new policies, or change model weights.

7. **Record everything.** For every attempt, keep actual game footage, action/state
   traces, policy and runtime hashes, timings, usage, errors, evaluator results,
   and a terminal save with an independent inspection. Include failures. Build a
   local index linking each policy, video, trace, and verdict. Actual-game time-lapse
   is sufficient; JSON alone or reconstructed animation is not. Keep raw footage,
   saves, private logs, and secrets out of Git.

8. **Compare fairly.** Rank by valid passes, then complete trial time, then model
   use. Apply the failure penalty in the contract. Use matching maps and conditions;
   report infrastructure failures and missing usage. Reserve four final trials:
   initial versus selected Method on two unseen maps. Freeze the winner before
   opening those maps and do not tune from final results. Prioritize this comparison
   over extra designs. If recording forces serial play, start it by minute 31 or
   earlier as needed to finish on time.

9. **Checkpoint and stop safely.** Follow AGENTS.md. Update the run index after each
   trial and give a progress brief every five minutes. Continue beyond the first
   success while time remains. Stop on deadline, quota, storage limits, or broken
   evidence capture. If setup cannot work within 15 minutes, report the blocker
   and completed checks. Never invent trials, relax the evaluator, or expand the authorized scope.

10. **Brief me by minute 60.** Deliver the best v3 Methods, exact rerun commands,
    baseline/final comparison, complete gameplay index, and a short account of
    what improved and what failed. Separate search cost from policy execution cost.
    Report actual counts and limits. Commit and push completed code and reviewed
    evidence, update HACKATHON.md, and stop all job-owned processes.
