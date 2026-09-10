# Automatic red-and-green science

Build a factory that mines iron and copper and automatically makes both red
science packs (`automation-science-pack`) and green science packs
(`logistic-science-pack`). Supply its power and connect all production stages.
It must make at least **10 of each pack per game minute, for three consecutive
minutes, without player actions**.

This is a separate task, `automatic-science/1`. It leaves the earlier iron-plate
task and its recorded results unchanged.

## Why this is harder

The old task connected a drill, belt, inserter, and furnace. This task needs two
raw materials, smelting, several assembly recipes, ingredient distribution,
power, and enough output from every stage. A correct machine layout can still
fail because another stage supplies too little material.

The task tests factory design and control. Equipment is supplied, the required
recipes are enabled, and solar power works throughout the test. It does not
test research, fuel supply, combat, or building equipment from scratch.

## Fixed starting conditions

Use base Factorio **2.0.77**, without other mods. The world starts without a
factory or loose items. Eight separate ore deposits contain iron and copper.
Different seeds change deposit order and distance. Seed zero is reserved for
operator checks. The building area is flat land within coordinates -120..120.
The player can place equipment anywhere in that area through the game tools;
character movement and reach are not part of this task.

| Supplied equipment | Count |
| --- | ---: |
| Electric mining drill | 12 |
| Electric furnace | 12 |
| Assembling machine 3 | 16 |
| Solar panel | 80 |
| Medium electric pole | 800 |
| Transport belt | 1,200 |
| Underground belt | 100 |
| Splitter | 20 |
| Fast inserter | 100 |
| Long-handed inserter | 40 |
| Steel chest | 20 |

No ore, plates, intermediate parts, or science packs are supplied. The tools
cannot craft items by hand, transfer ingredients, extract output, grant items,
change game settings, or run raw game code. Picking up equipment returns that
piece of equipment and discards its contents. Changing a recipe also discards
removed ingredients. Ordinary blocked placements can be repaired. Forbidden
actions invalidate the attempt, even when the request was rejected.

The game runs at speed 20 while the player thinks. One game minute is exactly
3,600 ticks; it is not one minute on the computer clock. A trial has a fixed
30-minute elapsed-time limit, including startup and measurement, and a limit
of 2,000 actions. Observations, rejected requests, and each batch member count.
These are per-attempt limits, not authorization to spend money on model calls.

## The fixed checker

1. The player calls `finish`. Playing access is then closed.
2. The checker removes all items from factory inventories, belts, inserter
   hands, and the ground. It also cancels work in progress. Buildings and their
   recipes remain. This removes any prepared material stockpile.
3. The factory gets two game minutes to restart from mining.
4. The game records four exact tick boundaries around three one-minute windows.
5. Every window must produce at least 10 new red packs and 10 new green packs.
   The same minimum must appear in assembler completion counts and in retained
   pack stock. At least 10 new iron ore and 10 new copper ore must be mined in
   each window. Smelting and every required intermediate recipe must also
   produce something in each window.
6. The host pauses and saves the game. A separate Factorio process opens a copy
   of that save. Its actual state and stored measurements must match the host
   record. The checker also checks the source hashes, game version, action
   trace hash, action count, time limit, and final handoff.

All three windows must pass. Red packs alone, stored packs, two good windows,
missing files, changed records, or an unreadable save do not pass. The final
result comes from game evidence, not from a model's report.

The checker reports the item counts and failed conditions to support policy
improvement. Keep its rules and source fixed during a search. A rule change
requires a new task version and separate results.

## Run and evidence

See [the host, tools, and verifier commands](run-science-task.md).
The operator-only reference factory is a checker test; do not supply its
construction plan to policy authors. Checker validation is not a Method win
or evidence that policy search improved a Method.
