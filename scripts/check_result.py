"""Check saved game evidence against the fixed small-production goal."""
import argparse
import json
from pathlib import Path


def check(run):
    initial = json.loads((run / "initial.json").read_text())
    final = json.loads((run / "final.json").read_text())
    settings = json.loads((run / "settings.json").read_text())
    actions = [json.loads(line) for line in (run / "actions.jsonl").read_text().splitlines()]
    furnaces = final["furnaces"] or []
    produced = final["iron_plates_produced"] - initial["iron_plates_produced"]
    finished = sum(f["products_finished"] for f in furnaces)
    output = sum(i["count"] for f in furnaces for i in (f["output"] or []) if i["name"] == "iron-plate")
    observed_initial = {i["name"]: i["count"] for i in initial["inventory"]}
    checks = {
        "declared_inventory": observed_initial == settings["inventory"],
        "no_starting_factory": not initial["furnaces"],
        "no_starting_research": not initial["research"],
        "zero_starting_production": initial["iron_plates_produced"] == 0,
        "enemies_disabled": initial["enemies"] == final["enemies"] == 0,
        "normal_speed": initial["speed"] == final["speed"] == 1,
        "new_iron_plates": produced >= 20,
        "furnace_finished_products": finished >= 20,
        "iron_plates_in_furnace_output": output >= 20,
        "action_limit": len(actions) <= settings["action_limit"],
        "game_time_limit": (final["tick"]-initial["tick"])/60 <= settings["seconds_limit"],
        "inspection_save": (run / "game/final.zip").exists(),
        "clean_shutdown": not (run / "shutdown-error.txt").exists(),
    }
    return {"passed": all(checks.values()), "checks": checks, "produced": produced,
        "furnace_finished": finished, "furnace_output": output, "requests": len(actions),
        "errors": sum(not a["response"]["ok"] for a in actions),
        "game_seconds": (final["tick"]-initial["tick"])/60,
        "action_window_seconds": actions[-1]["ended_at"]-actions[0]["started_at"] if actions else None,
        "scope": "small production integration test, not complete control or a rocket launch"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    result = check(args.run)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
