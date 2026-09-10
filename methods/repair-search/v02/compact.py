"""Compress public observations. This module has no game or model access."""
from collections import defaultdict


EQUIPMENT = [
    "electric-mining-drill", "electric-furnace", "assembling-machine-3",
    "solar-panel", "medium-electric-pole", "transport-belt",
    "underground-belt", "splitter", "fast-inserter",
    "long-handed-inserter", "steel-chest",
]


def xy(position):
    return [round(position["x"], 4), round(position["y"], 4)]


def compact(state):
    entities = state.get("entities", [])
    result = {k: v for k, v in state.items() if k != "entities"}
    result["actions_used_by_method"] = 1
    result["legend"] = {
        "machines": "[id,name,x,y,direction,status,energy,recipe,products,nonempty_inventories,drill_drop]",
        "inserters": "[id,name,x,y,direction,status,energy,pickup,drop,pickup_entity,drop_entity]",
        "endpoint_entity": "[id,name,x,y] or null when no observed collision box contains the endpoint",
        "belts": "[direction,start_xy,end_xy,total_contents_across_both_lanes]. Each run contains a belt every 1 tile, inclusive. Contents are aggregate; no item location or lane is implied.",
        "other": "Non-belt entities not covered by the compact rows. Empty inventories and collision boxes omitted.",
    }

    def endpoint(point, exclude):
        if not point:
            return None
        for entity in entities:
            if entity.get("id") == exclude:
                continue
            box = entity.get("box", {})
            lo, hi = box.get("left_top"), box.get("right_bottom")
            if lo and hi and lo["x"] <= point["x"] <= hi["x"] and lo["y"] <= point["y"] <= hi["y"]:
                return [entity.get("id"), entity["name"], *xy(entity["position"])]
        return None

    machines, inserters, others = [], [], []
    belt_groups = defaultdict(list)
    for entity in entities:
        name = entity["name"]
        pos = entity["position"]
        direction = entity.get("direction")
        if name == "transport-belt" and direction in (0, 4, 8, 12):
            varying = "x" if direction in (4, 12) else "y"
            fixed = "y" if varying == "x" else "x"
            belt_groups[(direction, pos[fixed], varying)].append(entity)
        elif entity.get("type") == "inserter":
            inserters.append([
                entity.get("id"), name, *xy(pos), direction,
                entity.get("status_name"), round(entity.get("energy", 0), 1),
                xy(entity["pickup"]) if entity.get("pickup") else None,
                xy(entity["drop"]) if entity.get("drop") else None,
                endpoint(entity.get("pickup"), entity.get("id")),
                endpoint(entity.get("drop"), entity.get("id")),
            ])
        elif name in ("electric-mining-drill", "electric-furnace", "assembling-machine-3", "steel-chest"):
            machines.append([
                entity.get("id"), name, *xy(pos), direction,
                entity.get("status_name"), round(entity.get("energy", 0), 1),
                entity.get("recipe"), entity.get("products"),
                {k: v for k, v in entity.get("inventories", {}).items() if v},
                xy(entity["drop"]) if entity.get("drop") else None,
            ])
        else:
            others.append({k: v for k, v in entity.items()
                           if k not in ("box", "status", "inventories", "type")})

    runs = []
    def append_run(run):
        totals = defaultdict(int)
        for belt in run:
            for lane in belt.get("lines", []):
                for item, count in lane.items():
                    totals[item] += count
        runs.append([run[0]["direction"], xy(run[0]["position"]),
                     xy(run[-1]["position"]), dict(totals)])

    for (_, _, axis), belts in sorted(belt_groups.items()):
        run = []
        for belt in sorted(belts, key=lambda e: e["position"][axis]):
            if run and abs(belt["position"][axis] - run[-1]["position"][axis] - 1) > 1e-6:
                append_run(run)
                run = []
            run.append(belt)
        if run:
            append_run(run)
    result.update(machines=machines, inserters=inserters, belts=runs, other=others)
    return result
