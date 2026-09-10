"""Repair-only review of recipe references retained in native saved samples.

This review fixes JSON export of LuaRecipePrototype values. It does not infer
recipes from final inventories, change production gates, or change run limits.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import time

from repair_contract import RECIPES, evaluate
from repair_trial import classify, finished
from repair_verify import verify
from science_server import FACTORIO, Server

VERSION = "repair-recipe-export/2"
HISTORY = """(function()
  local out={tick=game.tick,paused=game.tick_paused,samples={}}
  for _,sample in ipairs(storage.science.measurement.samples) do
    local row={tick=sample.tick,entities={}}
    for _,e in ipairs(sample.entities) do
      local r=e.recipe
      table.insert(row.entities,{id=e.id,type=e.type,products=e.products,
        recipe_type=type(r),recipe_name=type(r)=='string' and r or
          (type(r)=='userdata' and r.name or nil),
        recipe_object=type(r)=='userdata' and r.object_name or nil})
    end
    table.insert(out.samples,row)
  end
  return out
end)()"""


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize(record, history):
    """Change only names exported as null, using exact saved native references."""
    normalized = copy.deepcopy(record)
    if history["paused"] is not True or history["tick"] != record["final"]["tick"]:
        raise ValueError("Recipe proof is not from the paused terminal tick")
    samples = normalized["measurement"]["samples"]
    if len(samples) != len(history["samples"]):
        raise ValueError("Recipe proof has a different sample count")
    corrections = []
    for index, (sample, proof) in enumerate(zip(samples, history["samples"])):
        if sample["tick"] != proof["tick"] or len(sample["entities"]) != len(proof["entities"]):
            raise ValueError("Recipe proof does not match the saved sample")
        seen = set()
        for entity, native in zip(sample["entities"], proof["entities"]):
            if (entity["id"] in seen or entity["id"] != native["id"]
                    or entity.get("type") != native.get("type")
                    or entity.get("products") != native.get("products")):
                raise ValueError("Recipe proof does not match the saved entity")
            seen.add(entity["id"])
            kind = native["recipe_type"]
            if kind == "userdata":
                if (entity.get("type") != "furnace" or entity.get("recipe") is not None
                        or native["recipe_object"] not in {"LuaRecipePrototype", "LuaRecipe"}
                        or native["recipe_name"] not in RECIPES):
                    raise ValueError("Unsupported native recipe reference")
                entity["recipe"] = native["recipe_name"]
                corrections.append({"sample_index": index, "tick": sample["tick"],
                                    "entity_id": entity["id"], "field": "recipe", "exported_value": None,
                                    "native_value": native["recipe_name"], "native_type": native["recipe_object"]})
            elif kind == "string":
                if entity.get("recipe") != native["recipe_name"]:
                    raise ValueError("String recipe differs from native evidence")
            elif kind == "nil":
                if entity.get("recipe") is not None:
                    raise ValueError("Missing native recipe differs from exported evidence")
            else:
                raise ValueError("Unsupported historical recipe type")
    return normalized, corrections


def provenance(trial_dir, case_dir):
    host = trial_dir / "host"
    return {"raw_summary_sha256": file_hash(trial_dir / "summary.json"),
            "raw_record_sha256": file_hash(host / "record.json"),
            "raw_save_sha256": file_hash(host / "game/world.zip"),
            "raw_trace_sha256": file_hash(host / "actions.jsonl"),
            "raw_verdict_sha256": file_hash(host / "verdict.json"),
            "case_manifest_sha256": file_hash(case_dir / "case.json"),
            "review_source_sha256": file_hash(Path(__file__))}


def review(trial_dir, case_dir, *, rcon_port=27943, game_port=34943, factorio=FACTORIO):
    trial_dir, case_dir = Path(trial_dir).resolve(), Path(case_dir).resolve()
    started = time.monotonic()
    original = json.loads((trial_dir / "summary.json").read_text())
    result = copy.deepcopy(original)
    result.update(review_contract=VERSION, original_status=original.get("status"),
                  original_kind=original.get("kind"), original_scored_pass=original.get("scored_pass"),
                  status="infrastructure_failure", scored_pass=False, legacy_scored_pass=original.get("scored_pass"),
                  original_total_wall_seconds=original.get("total_wall_seconds"))
    try:
        before = provenance(trial_dir, case_dir)
        result["review_provenance"] = before
        result.update(raw_summary_sha256=before["raw_summary_sha256"], raw_record_sha256=before["raw_record_sha256"],
                      save_sha256=before["raw_save_sha256"], source_sha256=before["review_source_sha256"])
        host = trial_dir / "host"
        record = json.loads((host / "record.json").read_text())
        legacy = json.loads((host / "verdict.json").read_text())
        result["legacy_verdict"] = legacy
        # The original verifier writes verdict.json. Run it on a separate copy.
        # Neither the original verdict nor its source files are ever rewritten.
        with tempfile.TemporaryDirectory(prefix="recipe-review-", dir=trial_dir) as temp:
            temp = Path(temp)
            checked = temp / "legacy"
            (checked / "game").mkdir(parents=True)
            for name in ("record.json", "actions.jsonl"):
                shutil.copyfile(host / name, checked / name)
            shutil.copyfile(host / "game/world.zip", checked / "game/world.zip")
            verified = verify(checked, case_dir, rcon_port=rcon_port, game_port=game_port, factorio=factorio)
            result["independent_legacy_verdict"] = verified
            if verified != legacy or original.get("verdict") != legacy:
                raise ValueError("Original verdict does not match an independent verification")
            # Preserve legal incomplete attempts and their original failure. They
            # have no completed production samples that need recipe correction.
            history = None
            corrections = []
            normalized = record
            if record.get("measurement", {}).get("done") is True:
                with Server(temp / "native", save=host / "game/world.zip", rcon_port=rcon_port,
                            game_port=game_port, factorio=factorio) as server:
                    server.install()
                    if server.read("storage.science") != {k: v for k, v in record.items() if k not in ("final", "host_error")}:
                        raise ValueError("Recipe proof save does not match the original record")
                    history = server.read(HISTORY)
                normalized, corrections = normalize(record, history)
            after = provenance(trial_dir, case_dir)
            if after != before:
                raise ValueError("Original evidence changed during review")
            adjudicated = copy.deepcopy(verified)
            adjudicated.update(evaluate(normalized))
            # All legacy native/protocol checks stay in force, unchanged.
            adjudicated["scored_pass"] = (adjudicated["production_pass"]
                                           and bool(verified.get("verification"))
                                           and all(v is True for v in verified["verification"].values()))
            result["verdict"] = adjudicated
            result["corrections"] = corrections
            result["native_recipe_history"] = history
            result["status"] = classify(adjudicated, original.get("execution", {}),
                                        host_returncode=original.get("host_returncode", 0),
                                        did_finish=finished(host / "actions.jsonl"))
            result["scored_pass"] = adjudicated["scored_pass"] and result["status"] == "pass"
    except Exception as error:
        result["review_error"] = f"{type(error).__name__}: {error}"
    result["review_wall_seconds"] = time.monotonic() - started
    original_time = original.get("total_wall_seconds")
    result["total_wall_seconds"] = original_time + result["review_wall_seconds"] if type(original_time) in (int, float) else None
    target = trial_dir / "review.json"
    if target.exists():
        # Keep every prior review, including unsuccessful attempts.
        backup = trial_dir / ("review-" + file_hash(target) + ".json")
        if not backup.exists():
            shutil.copyfile(target, backup)
    target.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trial", type=Path)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--rcon-port", type=int, default=27943)
    parser.add_argument("--game-port", type=int, default=34943)
    args = parser.parse_args()
    result = review(args.trial, args.case, rcon_port=args.rcon_port, game_port=args.game_port)
    print(json.dumps({k: result.get(k) for k in ("case_id", "original_status", "status", "scored_pass", "review_wall_seconds", "review_error")}, indent=2))
    return 0 if result["status"] != "infrastructure_failure" else 1


if __name__ == "__main__":
    main()
