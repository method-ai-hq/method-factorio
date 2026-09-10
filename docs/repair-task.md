# Repair the factory

Repair this damaged Factorio factory so it makes both red and green science packs without help. You have 300 seconds of real time and at most 200 game actions. You can inspect the factory, write and run code, and change equipment. Use only the supplied `game.py` client and this workspace. Each attempt starts from its own saved factory. No other run or task is available.

The game is Factorio 2.0.77 with base recipes. Time runs at speed 20, with permanent daylight. Coordinates are within -120 to 120. You do not need to move a character. You have spare equipment, but no ingredients. `observe` shows your remaining equipment. You can recover equipment with `pickup`; its contents are discarded. There is no action to transfer materials, craft items by hand, change the map, or control game time.

When ready, call `finish`. This ends your access. The checker removes all stored materials and crafting progress. It then runs the factory for two game minutes to start production, followed by three separate one-minute checks. In EACH check, the factory must make and retain at least 10 new automation-science-pack and 10 new logistic-science-pack. It must also mine at least 10 new iron ore and 10 new copper ore and produce each required intermediate item. Equipment must stay unchanged during these checks. A separate process reloads the final save to check the result. Send `finish` with at least 25 real seconds left for these checks. Do not send further actions after `finish`.

## Game calls

Use Python: `from game import act`; each call returns an object with `ok` and `result` or `error`. Inspect the result. Every action counts, including observations and failed actions. Invalid or forbidden requests fail the attempt. A blocked placement can be corrected.

```python
act({"action":"observe"})
act({"action":"observe", "names":["transport-belt","fast-inserter"],
     "area":{"left_top":{"x":-20,"y":-20},"right_bottom":{"x":20,"y":20}}})
act({"action":"resources"})
act({"action":"recipes"})
act({"action":"place","item":"transport-belt","position":{"x":1,"y":2},"direction":"RIGHT"})
act({"action":"rotate","name":"transport-belt","position":{"x":1,"y":2},"direction":"DOWN"})
act({"action":"recipe","name":"assembling-machine-3","position":{"x":4.5,"y":4.5},"recipe":"iron-gear-wheel"})
act({"action":"pickup","name":"transport-belt","position":{"x":1,"y":2}})
act({"action":"finish"})
```

Directions in requests are `UP`, `RIGHT`, `DOWN`, `LEFT`. Observed directions use Factorio numbers: 0, 4, 8, 12 respectively. For inserters, use the observed pickup and drop positions to check material flow. Underground placement also accepts `type`: `input` or `output`. Batch up to 50 actions with `act({"batch":[...]})`; each action counts, and a batch stops on its first error.

Default observations include drills, furnaces, assemblers, inserters, and chests. To see belts or power equipment, supply `names`. Observations include positions, recipes, status names, energy, inventories, belt contents, inserter pickup/drop positions, production counts, ore remaining, game tick, and remaining spare equipment. Area filtering is optional. Save large observations to files and process them with code if useful.

Equipment names: electric-mining-drill, electric-furnace, assembling-machine-3, solar-panel, medium-electric-pole, transport-belt, underground-belt, splitter, fast-inserter, long-handed-inserter, steel-chest.

Allowed recipes: iron-plate, copper-plate, iron-gear-wheel, copper-cable, electronic-circuit, transport-belt, inserter, automation-science-pack, logistic-science-pack. Set recipes only on assemblers; furnaces select their recipe from their input.

Solve the task using the game evidence. Return a brief account of what you changed and whether you called `finish`.
