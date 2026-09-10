# Civ baseline work: accepted goal and completion checks

The owner requested both the economy and combat tasks, fresh Astra Codex
processes with no prior game context, and completed direct baselines before
continuous Method search. Source: the goal attachment dated 10 September 2026.
The earlier empty control is not an Astra baseline.

## Required work

1. Finish a restricted playing interface. No raw Lua, save/load, game setup,
   hidden map, task evaluator, other run logs, or reference policy for players.
2. Validate new Astra Codex processes with separate workspaces, no inherited
   conversation, no project instructions, and no prior trial access.
3. Keep the economy target unchanged: population-4 capital plus two new cities
   of population 3; science at least 20; nonnegative gold and net income; food
   surplus nonnegative in all three; five full rounds within 35 turns.
4. Make three distinct economy calibration saves covering food/production,
   travel/growth, and Campus/working-tile tradeoffs. Keep the starting kit fixed.
5. Establish a legal reference completion per economy case before certifying
   feasibility. Keep reference evidence separate from direct baselines.
6. Run direct Astra twice on each of the three economy saves. Preserve every
   failure and distinguish game failure from infrastructure failure.
7. Build the combat task: two population-4 cities, two Warriors, two Slingers,
   a Builder, 50 gold, three initial technologies, one normally controlled AI,
   and an initially unwalled population-4 target. Capture through combat, retain
   both starting cities, and hold the target five rounds within 30 turns.
8. Validate combat acquisition, ownership history, and independent save reload.
   Make varied approach cases and run fresh direct Astra baselines. Report the
   initial-force control and any calibration change as a separate profile.
9. Report actual baseline results, source and save hashes, model settings,
   usage, timing, interventions, failures, and remaining limits. Commit/push
   completed work. Do not claim Method improvement in this phase.

## Execution choices

Use the installed base game, one graphical Civ client, Online speed, quick
animations, tutorials disabled, and no recording. The game waits during model
thinking. Run through ChatGPT-authenticated Codex with exactly gpt-6-astra,
medium reasoning, fresh ephemeral processes, and no billed API-key calls.
Subscription cost remains unknown; zero API billing is not zero authoring cost.

Use 20 minutes of playing time per baseline and up to five minutes for terminal
save/reload verification, with 1,500 metered game requests. This replaces the
old 600-second no-model control budget for these new baseline profiles only.
Freeze each profile before its baseline panel. No trial gets a renewed clock.
Run game clients serially. Infrastructure repair may create a linked new
attempt; it never erases or converts the old attempt.

The task does not require Astra to fail. If it succeeds reliably, report that
and still complete the requested combat baseline work. Continuous search and
runtime-LLM ablation follow after this baseline stage, as the owner requested.

## Current evidence

The first full-budget nearby-food baseline passed the complete task trace and
independent save check in 35 turns and 331.18 seconds of play. It supplies a
legal completion witness for that starting case. See the
[baseline report](../../evidence/civ6-baselines-2026-09-10/README.md).
The second valid run passed in 33 turns and 335.96 seconds of play. Both
valid runs passed the independent save check. One intervening attempt remains
invalid because its cached production state did not match the reload; it is
not counted as a gameplay failure. Four economy baselines on two other maps
and the combat baseline work remain.
