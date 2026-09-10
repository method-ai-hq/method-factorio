# What we did, why it helped, and what to test next

## The main claim

We used Astra to improve a reusable procedure for repairing factories. We tested the selected procedure on factories that were not used to improve it. It used less execution time and fewer input tokens than a fresh direct Astra run on this test set.

We did not change the model's weights. We changed the procedure around the model: its steps, helper code, observations, prompts, and checks. The result is a saved Method that can run again with a fresh model session.

Both approaches repaired all twenty final factories. The Method had twenty full-rule passes; direct Astra had eighteen because two runs made unsupported tool requests. This is evidence of better tool compliance in this sample. It is not enough evidence for a general reliability claim.

## Motive

A strong model can often solve a problem when given enough time. The useful question is whether experience from earlier attempts can become a reusable procedure that makes later attempts cheaper, faster, or more dependable.

The original aspiration was to find a task where direct Astra fails and a searched Method succeeds. This repair study found a narrower result: both could repair the factories, but the searched procedure used less time and input. That is still useful when the same kind of work must be done many times.

Factorio provides visible cause and effect and an external success check. A machine either receives power and inputs or it does not. Production can be measured from the game. We do not need another model to decide whether the factory works.

## What the task actually was

These were supplied, damaged factories. They were not empty-world construction tasks or rocket launches. Each had machines, supply paths, power equipment, and repair supplies. Damage varied: missing equipment, wrong directions, wrong or missing recipes, and power faults. Layouts and combinations of faults varied too.

The player had five real minutes and 200 game actions. Both approaches used the same Astra model and reasoning setting. Both could inspect the game, write and run code, repair equipment, check their work, and correct errors within the attempt. The game ran at speed 20. The player used a programmatic game interface, not mouse and keyboard control.

Before admitting a factory, the operator checked three conditions in the real game: the healthy factory passes, the damaged version fails, and a legal repair passes. The player never received the reference repair or the hidden fault list.

The external checker removed stored materials and crafting progress. After a warmup, it measured three production windows. The factory had to mine fresh iron and copper, make intermediate parts, and produce and retain enough red and green science in every window. The saved game was checked independently. A model's “done” message did not count as success.

## The two loops, literally

**During a game:** a fixed procedure observes the current factory, chooses actions, sees the results, and continues until it finishes or runs out of budget. It can adapt its actions to this factory. It cannot edit the experiment or reset its budget.

**Between practice games:** the author sees approved development records, identifies a failure or cost, edits a new Method version, and tests that version. A better factory is one game outcome. A better Method is a procedure that performs better across the practice cases.

The supervising Astra coordinated the case builder, runner, checks, policy author, evidence review, and version selection. A separate author was given the public task and approved development feedback. That author proposed changes to the Method. This was a small, model-guided search through procedure versions, not a large random search or weight training.

Some revisions used early results while other development trials continued. This was not a strictly sequential process that waited for every old version to finish before writing the next one. All eligible versions eventually had the full ten practice results before selection. Every version and failed attempt was retained.

The search had four tested versions and 31 Method game attempts. It used 51 fresh Codex sessions because the first version used three sessions per attempt. There were also ten direct-Astra practice attempts. The selected Method then faced twenty new factories, each paired with a fresh direct Astra run on a separate copy of the same save. No final result was used to edit the selected Method.

## How the procedure changed

| Version | Literal procedure | Feedback and change | Practice result |
| --- | --- | --- | --- |
| v01 | Fresh agent inspects; a second repairs; a third checks and finishes. They share one overall deadline. | The first stage often hit its 65-second limit without a final report. Later stages repeated inspection and reasoning. | 9/10 full-rule passes; median full successful time 215.49 s. All ten factories repaired. |
| v02 | Code makes one allowed observation, compresses belt geometry, and gives the result to one fresh agent to diagnose, repair, check, and finish. | Avoids repeated agent startup and handoffs. But power equipment still occupies most of the prepared observation. | 10/10 passes; median 91.83 s. |
| v03 | Code also compresses repeated power equipment. The prompt passes plain JSON, asks for small outputs, and lets a successful production-check program call finish immediately. | On one complete public observation, prepared text shrank from 112,008 to 17,908 characters. Exact belt geometry and power positions were checked. | One retained pass, 70.81 s full time. A candidate file change stopped the batch before case 2; this version was not eligible for selection. |
| v04 | Same repair policy and compression as corrected v03, with a confirmed available Python executable named in the prompt. | Fixes an unsuitable interpreter path instruction. The old v03 files were restored and kept; v04 was tested as a new fixed version. | 10/10 passes; median 73.18 s. Selected. |

These are medians among each version's successful practice attempts, not all identical success subsets. They explain selection and history; the final speed comparison uses the same eighteen successful case pairs.

The selection rule was fixed: most practice passes, then lowest median full successful time, then reported token use. Only versions with all ten practice cases were eligible. v04 beat v02 on time while keeping all ten passes. Its files and the checker reader were frozen before final testing.

The interpreter change between v03 and v04 is an implementation correction, not a new reasoning strategy. v03's single game had succeeded using another interpreter. We have no basis to attribute a measured speed gain specifically to that correction.

## What the winning Method does on a new factory

1. Code sends one ordinary observation request through the allowed game interface. This consumes one of the 200 actions.
2. Code turns long runs of belt tiles into compact run descriptions and repeated power equipment into coordinate groups. It preserves the locations needed to repair them. Belt item counts are aggregated, so the model can request local detail when necessary.
3. A fresh Astra Codex session receives the public task, compact observed map, and learned repair instructions. It receives no saved answers for this factory.
4. The agent traces missing inputs back through the production chain, makes supported repairs, and inspects uncertain areas. The instructions warn that a temporarily idle machine is not sufficient evidence of a fault.
5. The agent measures fresh output. If the evidence is sufficient, its program calls finish without a separate model turn just to approve that check. Otherwise it continues repairing within the same deadline.
6. The fixed external checker clears materials, measures production, and checks the saved game.

This uses the real Method v3 runtime. The model session is invoked by a code step through the fixed Codex subscription helper. Native paid API calls are disabled. It is one agent session with multiple reasoning and tool steps, not a single model response and not a model-free script.

## Why it appears faster

Several observations support the explanation that the Method reduces work around reasoning:

- **Less repeated context.** The final trials used 2,939,690 reported input tokens for the Method versus 6,642,107 for direct Astra, including cached input: about 56% less. Uncached input was 594,730 versus 915,259, about 35% less. Output tokens fell only about 10%. This points more toward better input handling than simply writing shorter final answers.
- **Fewer shell command steps.** Retained final traces contain 118 completed shell commands for the Method and 191 for direct Astra. The median per attempt is five versus nine. These counts are not model request counts. They include file reads, code execution, and game-client calls.
- **Less printed text.** Those shell commands printed about 0.79 million characters for the Method versus 2.63 million for direct Astra. This is a diagnostic text-volume measure, not an alternative token bill.
- **No handoff between three fresh agents.** The poor first version showed the cost of losing or repeating work between stages. The selected version keeps diagnosis, repair, and checking in one agent context.
- **More precise execution instructions.** The learned prompt names allowed equipment, a working interpreter, output limits, and the condition for finishing. It saves repeated discovery and reduces opportunities for unsupported requests.

It did **not** win by taking fewer game actions overall. The Method used 213 final game actions, versus 205 for direct Astra. Median action count was eight versus seven. The gain came with a slightly higher game-action count.

These are supported explanations, not isolated causal proofs. We changed several things together. We have not shown how much of the time gain came from compression, prompt wording, interpreter choice, command grouping, or service latency. Nor have we shown that the Method file format or runtime is faster than plain code running the same learned procedure. The measured gain belongs to the complete searched procedure.

## A concrete recorded repair

In final case 003, the selected Method placed a missing electric mining drill, corrected a belt direction, and turned an inserter. All three changes were accepted. It then checked production and finished. Original full time was 68.18 seconds, versus 114.93 seconds for direct Astra on that same case. This is an illustrative case, not the aggregate result.

Case 011 is useful because it shows mistakes and recovery. Several furnace placements were blocked. The agent removed two inserters, found a valid furnace position three tiles away, redirected and extended belts, and placed the inserters at the new route. It finished with a working factory. Original full time was 124.85 seconds versus 182.08 seconds for direct Astra. The Method did not have a flawless plan from the start.

The demonstration footage reapplies these recorded changes to copies of the original starting saves. It checks the accepted/rejected outcomes and final equipment layout. It changes action spacing, game speed, and camera positions. It omits model thinking and observation requests. It must remain labeled as a visual replay, not footage of the measured runs or an exact tick-for-tick replay.

## What the numbers do and do not say

Full final-rule passes were 20/20 for the Method and 18/20 for direct Astra. Both repaired 20/20 factories. The exact paired success test gives p=0.5. This is too little evidence to claim a dependable success-rate advantage.

On the same eighteen successful pairs, median full time was 71.22 seconds for the Method and 92.83 seconds for direct Astra: about 23% less time. The Method was faster on seventeen of all twenty pairs, including the two request-rule failures. Direct Astra was faster on three. Full time includes startup, player completion, production measurement, and independent save checks.

The final token totals are complete for all twenty attempts per approach. Subscription dollar cost is unknown. Fewer reported tokens do not translate directly into the same percentage reduction in money, especially when cached input has different treatment.

Search was not free. Known Method practice usage alone was 8.57 million input tokens. Ten early sessions lack final usage, so total practice use is unknown. Authoring, setup, and operator work are not fully costed. A one-off task may not repay the search effort. Repeated work is the more plausible use case.

A checker export defect was found during development. A versioned reader recovered exact recipe objects from the retained native history and applied the unchanged production rules to all attempts. Original verdicts were preserved, and the reader was frozen before final tests. See the linked evidence report for the full record.

## Best next steps

These are proposed experiments, not new measured results.

1. **Test which change matters.** On a new private set, compare direct Astra, direct Astra with the learned repair instructions, direct Astra with compact observations, and the complete selected Method. Keep the model and limits fixed. Repeat each condition enough to measure variation. This separates the prompt and representation effects and helps explain the real contribution of search.
2. **Make the next task require ongoing decisions.** Use longer production chains, limited spare parts, competing output targets, and faults that occur after the first repair. Keep valid reference solutions and an external checker. Use a smaller model-time budget only if it reflects a real use case, not merely to manufacture baseline failure.
3. **Let the policy choose when extra reasoning is useful.** Try one main agent with a specialist or second check only after unresolved evidence, repeated failed repairs, or a predicted limit. The first version warns against adding agents to every step without measuring the cost.
4. **Measure reuse economics.** Record complete authoring and trial use. Compare search cost with savings across 10, 100, and 1,000 later tasks. Report quality, time, and usage separately. Do not claim a financial break-even point until actual costs are known.
5. **Test transfer more strictly.** Use new factory families and objectives, not only new layouts from the existing generator. Once final cases have been viewed, retire them from claims about unseen performance.

The immediate priority is step 1. It gives the cleanest answer to “why did this help?” The next task family should follow once that result is clear.

## Where this could apply

The shared pattern is repeated work, varied inputs, a stable tool interface, and an external result check. The Method can preserve a useful procedure while the model handles the parts that vary.

| Possible application | What code could prepare | What the agent could decide | External check |
| --- | --- | --- | --- |
| Software repair | Relevant files, failing tests, dependency facts | Cause of failure and a repair plan | Tests and review constraints |
| Data pipeline repair | Schema differences, failed stages, sample records | Mapping or transformation changes | Data assertions and expected outputs |
| Operations troubleshooting in a test environment | Small log extracts and dependency state | Which fault to investigate and how to recover | Health checks and a declared recovery target |
| Document extraction | Parsed pages, table structure, validation rules | Ambiguous fields and reconciliation | Labeled answers and consistency checks |
| Repeated browser workflows in a sandbox | Current page state and known field constraints | How to handle a new exception | Correct final state and allowed actions |

These are applications to test. The Factorio result does not establish gains in any of them. Tasks with frequent reuse and expensive repeated inspection are promising first candidates. Tasks with a poor success check are harder to search safely and harder to evaluate honestly.

The wider idea has precedents: [DSPy](https://arxiv.org/abs/2310.03714) studies optimizing language-model programs against a metric, and [Automated Design of Agentic Systems](https://arxiv.org/abs/2408.08435) studies searching agent designs. Our result should be presented as this specific Method-and-Factorio experiment, not as invention of the entire research direction.

## Takeaways for the presentation

- Reusable procedure knowledge can improve execution without changing model weights.
- Code is useful for exact, repeated work; model reasoning is useful where the case varies.
- More agents were worse in the first tested version. Search should be allowed to simplify a procedure.
- Keep practice separate from final tests. Retain failures and use game evidence.
- The current win is lower time and input use. The harder capability claim remains open.

Sources: [full experiment report](../../evidence/repair-search-2026-09-10/README.md), [version selection](../../evidence/repair-search-2026-09-10/selection.json), [Method v04](../../methods/repair-search/v04/repair.method), and retained local action/model traces. The additional shell-command counts are documented in the demo evidence record.
