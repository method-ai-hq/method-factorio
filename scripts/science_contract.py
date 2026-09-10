"""Fixed rules for the separate red-and-green science benchmark."""
import hashlib
import json

CONTRACT = "automatic-science/1"
KIT = {"electric-mining-drill": 12, "electric-furnace": 12,
       "assembling-machine-3": 16, "solar-panel": 80,
       "medium-electric-pole": 800, "transport-belt": 1200,
       "underground-belt": 100, "splitter": 20, "fast-inserter": 100,
       "long-handed-inserter": 40, "steel-chest": 20}
RECIPES = ["iron-plate", "copper-plate", "iron-gear-wheel", "copper-cable",
           "electronic-circuit", "transport-belt", "inserter",
           "automation-science-pack", "logistic-science-pack"]
PACKS = RECIPES[-2:]
ITEMS = ["iron-ore", "copper-ore", *RECIPES]
BOUNDARIES = [7200, 10800, 14400, 18000]
RULES = {"contract": CONTRACT, "kit": KIT, "recipes": RECIPES,
         "factorio_version": "2.0.77",
         "speed": 20, "always_day": True, "boundaries": BOUNDARIES,
         "packs_per_window": 10, "window_ticks": 3600,
         "ore_per_window": 10, "seconds": 1800, "actions": 2000,
         "clear_materials_at_finish": True}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def evaluate(record):
    """Fail closed on missing or malformed native measurements. No model verdict."""
    try:
        initial, clean, measurement = record["initial"], record["clean"], record["measurement"]
        states = measurement["samples"]
        checks = {
            "contract": record["contract"] == CONTRACT and record["rules_hash"] == digest(RULES),
            "base_game_version": record["game_version"] == RULES["factorio_version"]
                                 and record["mods"] == {"base": RULES["factorio_version"]},
            "initial_kit": initial["inventory"] == KIT,
            "empty_start": not initial["entities"] and not initial["ground_items"]
                           and all(initial["produced"][n] == 0 for n in ITEMS),
            "initial_settings": initial["speed"] == 20 and initial["always_day"] is True,
            "materials_removed": all(clean["stock"][n] == 0 for n in ITEMS)
                                 and clean["ground_items"] == 0
                                 and all(e.get("progress", 0) == 0 for e in clean["entities"]),
            "exact_boundaries": [s["tick"] - measurement["start"] for s in states] == BOUNDARIES,
            "completed": measurement["done"] is True and len(states) == 4,
            "fixed_settings": all(s["speed"] == 20 and s["always_day"] is True for s in states),
            "no_play_after_finish": record["audit"]["violations"] == 0,
            "within_limits": 0 < record["audit"]["actions"] <= RULES["actions"]
                             and record["audit"]["elapsed_seconds"] <= RULES["seconds"],
        }
        windows = []
        for a, b in zip(states, states[1:]):
            produced = {n: b["produced"][n] - a["produced"][n] for n in ITEMS}
            stock = {n: b["stock"][n] - a["stock"][n] for n in PACKS}
            ore = {n: a["ore"][n] - b["ore"][n] for n in ("iron-ore", "copper-ore")}
            before = {e["id"]: e for e in a["entities"]}
            machine_products = dict.fromkeys(RECIPES, 0)
            stable = True
            for e in b["entities"]:
                old = before.get(e["id"])
                if not old or (old["name"], old.get("recipe")) != (e["name"], e.get("recipe")):
                    stable = False
                if old and e.get("recipe") in machine_products:
                    machine_products[e["recipe"]] += e["products"] - old["products"]
            stable = stable and set(before) == {e["id"] for e in b["entities"]}
            gates = {"exact_minute": b["tick"] - a["tick"] == 3600,
                     "stable_factory": stable,
                     "new_packs": all(produced[n] >= 10 for n in PACKS),
                     "retained_packs": all(stock[n] >= 10 for n in PACKS),
                     "machine_made_packs": all(machine_products[n] >= 10 for n in PACKS),
                     "mining": all(ore[n] >= 10 and produced[n] >= 10 for n in ore),
                     "all_stages_active": all(produced[n] > 0 and machine_products[n] > 0 for n in RECIPES)}
            windows.append({"produced": produced, "pack_stock_gain": stock, "ore_depletion": ore,
                            "machine_products": machine_products, "checks": gates,
                            "passed": all(gates.values())})
        checks["three_passing_minutes"] = len(windows) == 3 and all(w["passed"] for w in windows)
        return {"production_pass": all(checks.values()), "checks": checks, "windows": windows}
    except (KeyError, TypeError, ValueError, IndexError) as error:
        return {"production_pass": False, "error": "Incomplete or invalid evidence: " + str(error)}
