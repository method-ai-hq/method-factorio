"""Operator-only checker fixture, not a candidate or input to policy authors.

Builds a known factory through the same restricted action function as the HTTP
host. It uses the seed-zero reference map. It makes no model calls.
"""
import json
import time

from science_host import action


def tree(recipe, *children):
    return {"recipe": recipe, "children": list(children)}


def iron():
    return tree("iron-plate", tree("iron-ore"))


def copper():
    return tree("copper-plate", tree("copper-ore"))


def gear():
    return tree("iron-gear-wheel", iron())


def build(server, trace, started, send=None):
    red = tree("automation-science-pack", copper(), gear())
    green = tree("logistic-science-pack",
                 tree("transport-belt", iron(), gear()),
                 tree("inserter", iron(), gear(), tree("electronic-circuit", iron(), tree("copper-cable", copper()))))
    nodes = []
    leaves = []

    def position(node, depth):
        nodes.append(node)
        if not node["children"]:
            node.update(x=-70 + 20 * len(leaves) + .5, y=80.5)
            leaves.append(node)
        else:
            for child in node["children"]:
                position(child, depth + 1)
            node.update(x=(node["children"][0]["x"] + node["children"][-1]["x"]) / 2,
                        y=depth * 14 + .5)
            # All 3x3 machines and belts use tile-center coordinates.
            node["x"] = int(node["x"] // 1) + .5
    position(red, 0)
    position(green, 0)
    placed = []

    def call(req, optional=False):
        result = send(req) if send else action(server, req)
        trace.write(json.dumps({"request": req, "elapsed_seconds": time.monotonic() - started,
                               "response": result}) + "\n")
        if not result["ok"] and not optional:
            raise RuntimeError(str(req) + ": " + result.get("error", "unknown error"))
        return result

    def place(name, x, y, direction="UP", optional=False):
        result = call({"action": "place", "item": name, "position": {"x": x, "y": y},
                       "direction": direction}, optional)
        if result["ok"]:
            placed.append((name, x, y))
        return result

    for n in nodes:
        recipe = n["recipe"]
        kind = "electric-mining-drill" if recipe.endswith("-ore") else (
            "electric-furnace" if recipe.endswith("-plate") else "assembling-machine-3")
        place(kind, n["x"], n["y"])
        if kind == "assembling-machine-3":
            call({"action": "recipe", "name": kind, "position": {"x": n["x"], "y": n["y"]}, "recipe": recipe})

    belts = {}
    def belt_path(points):
        for (x,y), (nx,ny) in zip(points, points[1:] + [points[-1]]):
            direction = "UP" if ny < y or (nx,ny)==(x,y) else "DOWN" if ny>y else "RIGHT" if nx>x else "LEFT"
            if (x,y) in belts:
                raise RuntimeError(f"Reference belts overlap at {x},{y}")
            belts[x,y] = direction

    for parent in nodes:
        kids = parent["children"]
        offsets = {1: [0], 2: [-1,1], 3: [-1,0,1]}.get(len(kids), [])
        for i,(child,offset) in enumerate(zip(kids, offsets)):
            x,y = child["x"],child["y"]
            # Inserter direction points toward its pickup, so DOWN outputs north.
            if not child["recipe"].endswith("-ore"):
                place("fast-inserter", x, y-2, "DOWN")
                y -= 3
            else:
                y -= 2  # North-facing electric drill drops two tiles north.
            tx,ty = parent["x"]+offset,parent["y"]+3
            join = parent["y"] + (7 if len(kids)==3 and i==1 else 5)
            points = [(x,y)]
            while y > join:
                y-=1; points.append((x,y))
            while x != tx:
                x += 1 if tx>x else -1; points.append((x,y))
            while y > ty:
                y-=1; points.append((x,y))
            belt_path(points)
            place("fast-inserter", tx, parent["y"]+2, "DOWN")
    for (x,y),direction in belts.items():
        place("transport-belt", x,y,direction)
    for n in (red,green):
        place("fast-inserter", n["x"], n["y"]-2, "DOWN")
        place("steel-chest", n["x"], n["y"]-3)
    for row in range(4):
        for col in range(20):
            place("solar-panel", -80+col*4+.5, -42+row*4+.5)
    for row in range(4):
        for col in range(20):
            place("medium-electric-pole", -80+col*4+2.5, -42+row*4+2.5)
    for n in nodes:
        for dy in [-2,2]:
            place("medium-electric-pole", n["x"]-2,n["y"]+dy,optional=True)
    # A dense grid avoids any artificial power source. Blocked pole placements
    # are ordinary recoverable actions, and remain in the trace.
    for x in range(-83, 86, 6):
        for y in range(-47, 92, 6):
            place("medium-electric-pole", x+.5,y+.5,optional=True)
    return {"red": red, "green": green, "nodes": nodes, "placed": placed}
