# Mobilize, capture, and hold

This is the second accepted task. These setup choices need live calibration.
They are not measured results or a certified feasible benchmark.

## Fixed objective

Capture the designated enemy city through combat. Keep both starting cities
under continuous player control. Keep the captured target under continuous
player control for five complete rounds. Finish within 30 completed player
turns. The same city must satisfy the whole hold period. A replacement city,
gift, deal, or operator transfer does not qualify.

The player starts with two population-4 cities, two Warriors, two Slingers,
one Builder with three charges, and 50 gold. Mining, Pottery, and Animal
Husbandry are complete. Archery is incomplete. Units have full health and
movement. There is no stored production, research progress, or food. The
base rules and Online speed match the economy task.

One built-in AI controls its own research, production, movement, and combat.
The player and AI start at war. The designated enemy city has population 4
and no walls. Normal fog applies. The task text gives the target's name and
location but does not reveal its defenders or surrounding map.

## Calibration choices

Keep a second AI city so that the opponent remains active after the target
falls. Otherwise, the hold period could become five uncontested end turns.
Start the AI with the same early technology plus Archery, two Warriors, and
two Archers. This is an initial balance proposal, not evidence that the
player needs reinforcements. Record the exact AI setup in each save profile.

Use three approach cases: open ground, a river approach, and hills with a
limited route. Keep the player kit and AI kit fixed between cases. Change
only the map and the resulting unit and city locations. Do not add hidden
scheduled attacks or change the opponent during a trial.

Run a control that permits the initial military units to move and attack
but permits no upgrades or added military units. Compare it with unrestricted
legal reference play. Failure of one control is evidence about that control;
it does not prove that every initial-force policy must fail. If balance needs
a change, create a new profile and keep the earlier results.

## Required verifier evidence

- Bind the trace to the initial save, start-state hash, task profile, runner,
  player API, model task, and actual model execution evidence.
- Identify cities by their fixed map tiles plus engine IDs and original
  owners. Read the target's owner from the operator observer even in fog.
- Record target ownership changes and the engine's last transfer type.
  A legal player attack must be active when combat acquisition is recorded.
  A gift or an unexplained owner change fails verification.
- Record both starting-city removals and ownership changes. Losing either
  starting city at any time fails, even if the player later retakes it.
- Use the engine's player-turn boundary events. Start the hold count at a
  boundary after capture, then require five full boundary intervals. Check
  ownership after every action and throughout the opponent's turn.
- Close player access before the terminal save. Load that save in a separate
  inspection process and compare actual game state with the terminal trace.
- Report connection, API, or event-capture failures as infrastructure failures.
  Model statements do not establish capture or success.

Before baseline use, validate the capture event and transfer-type code in a
live legal combat fixture. Test gift, loss and recapture, capital loss, an
incomplete hold, missing events, and a changed terminal save as negative cases.
Do not infer the transfer enum from its name or from an untested API.

## Baseline stage

Use a fresh Astra Codex process for each attempt. It receives only the task,
normal player API, current observations, and fixed execution limits. It has
no reference plan or previous trial history. Use the same 20-minute playing
limit and 1,500-request limit as the economy baseline. Preserve all attempts.
Run two direct baselines on each calibrated approach case. Method search and
runtime-LLM ablation come after this baseline stage.
