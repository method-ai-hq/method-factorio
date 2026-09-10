# Small production test interface

This is a local integration test. It does not test all Factorio actions.

Send one JSON object per HTTP POST to the supplied `/action` URL. Use Python
`urllib.request` or curl. A successful response has `ok: true`, a `result`, and
an independently read `state`. An error can occur after an action changed the
game. Observe the state before deciding whether to try another action.

The game runs at speed 1 while you think. FLE fast mode is enabled. This mode
uses programmatic movement, mining, crafting, and placement. These are not
keyboard and mouse controls. FLE adds waits for some action time. Its action
semantics are not proof of normal player timing.

The host allows at most 200 requests and 20 minutes. Each action has at most
90 seconds. A timeout ends the test; do not work around it.

## Requests

| Action | Other fields | Purpose |
| --- | --- | --- |
| `observe` | none | Read inventory, position, furnace input/output/fuel, production, research, and game tick. |
| `nearest` | `resource` | Find `iron-ore`, `coal`, `stone`, `wood`, or `copper-ore`. Returns a position. |
| `move` | `position` | Move to a position. |
| `harvest` | `position`, `quantity` | Mine a resource at a known position. |
| `craft` | `item`, `quantity` | Hand craft an item from inventory. Smelting requires a furnace. |
| `place` | `item`, `position`, optional `exact` | Place an inventory item. Set `exact` false to permit a nearby valid position. |
| `insert` | `item`, `quantity`, `target` | Transfer an item from the character to a machine. |
| `extract` | `item`, `quantity`, `target` | Transfer an item from a machine to the character. |
| `entities` | none | Inspect nearby placed entities. |
| `pickup` | `target` | Pick up a placed entity. |
| `rotate` | `target`, `direction` | Rotate to `UP`, `RIGHT`, `DOWN`, or `LEFT`. |
| `wait` | `seconds` | Wait for between 0 and 30 seconds, then inspect state. |

A position is `{"x": 1, "y": 2}`. A target is
`{"name": "stone-furnace", "position": {"x": 1, "y": 2}}`.
Use actual observed positions. Item names use Factorio spelling, such as
`iron-ore`, `iron-plate`, and `stone-furnace`. Quantity must be an integer from
1 to 100. Position coordinates must be within 1,000 tiles of the origin.

Inventory entries have `name`, `quality`, and `count`. Empty game lists can
appear as `{}`. `iron_plates_produced` is the game's production count.
`products_finished` is the number of completed furnace products. Neither
the initial eight iron plates nor a model's success statement proves new
production.

No raw Lua, Python evaluation, game reset, resource grant, research grant,
speed change, or evaluator change is available in this API.

## Objective

Produce at least 20 **new** iron plates in a furnace. Leave at least 20 iron
plates in furnace output so the independent check can inspect them. Save
your plan, observations, and final result. Stop once the goal is met.

The host starts a fresh world with no factory and no completed research.
The declared inventory is eight iron plates, one wood, one stone furnace,
one burner mining drill, one pistol, and ten firearm magazines. Enemies are
disabled. Choose your own production plan. No factory recipe is supplied.
