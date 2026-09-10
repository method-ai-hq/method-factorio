# Civ player interface

Use `from game import act, observe` in Python. `act(dict)` sends one game
request and returns JSON. You may write code, plan, inspect results, and
recover from rejected moves. Do not send concurrent actions or retry an
action after an uncertain connection result. There is no access to game
setup, saves, hidden tiles, raw Lua, or other trials.

Every request uses an `action` field. These are the other fields:

| action | Fields |
| --- | --- |
| observe | None. Own cities, units, yields, research, production and policies. |
| map | None. Revealed terrain and currently visible yields, units and cities. |
| choices | Optional `city_id`, `unit_id`. Available research, policies, production, district placements, and improvements at that unit's tile. |
| rules | `table`, optional `type`. Public game rules. Tables: Units, Buildings, Districts, Projects, Technologies, Civics, Policies, Improvements, UnitPromotions, TechnologyPrereqs, CivicPrereqs, District_Adjacencies, Adjacency_YieldChanges, Improvement_YieldChanges, Building_YieldChanges, GlobalParameters. |
| research / civic | `type`, for example TECH_WRITING or CIVIC_CODE_OF_LAWS. |
| production | `city_id`, `kind` (UNIT, BUILDING, DISTRICT, PROJECT), `type`; also `x`, `y` for district or wonder placement. Replaces current production. |
| purchase | `city_id`, `kind`, `type`. Uses gold at normal game cost. |
| policies | `assignments`: list of objects with `slot` and `type`. Normal change costs apply. |
| focus | `city_id`, `type` such as YIELD_FOOD. Toggles that yield's priority. |
| buy_tile | `city_id`, `x`, `y`. Normal gold cost. |
| move / attack | `unit_id`, `x`, `y`. Move may explore. Attack requires current sight. |
| found | `unit_id` of a Settler. Found on its current tile. |
| improve | `unit_id`, `type` such as IMPROVEMENT_MINE. Build on its current tile. |
| skip / fortify / heal / remove_feature / harvest / repair | `unit_id`. Uses its current tile. Skip ends that unit's moves for this turn. |
| unit_command | `unit_id`, `command` (UPGRADE, PROMOTE, CANCEL); `type` for a promotion. |
| end_turn | None. Requests one player turn and waits. Queued movement can stop for more orders; resolve the returned blocker and request end_turn again. |
| finish | None. Ends the attempt and records the final game state. |

Use actual IDs from observations. Map yields are ordered food, production,
gold, science, culture, faith. Production `turns` is the game's current
estimate. `base_cost` is the unscaled rules value, not a final cost. Roads,
terrain, research, population, and policies can change action results.

`submitted` means the normal game command was sent. Inspect state to check its
effect. A rejected game action still uses one request. All reads use the
request budget too. State after `end_turn` includes completed turns and the
current task hold count. A trial closes at its turn limit or after success.
An `infrastructure_failure` means stop; do not infer success from it.
The host closes information-only research, civic, boost, and natural wonder
screens. It does not select policies or make diplomacy choices for you.
