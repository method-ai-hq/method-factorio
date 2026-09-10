"""Fixed rules for repair of a prepared automatic-science factory."""
import math

from science_contract import (BOUNDARIES, ITEMS, KIT, PACKS, RECIPES,
                              RULES as SCIENCE_RULES, digest, evaluate as science_evaluate)

CONTRACT = "automatic-science-repair/1"
SPARES = {"transport-belt": 64, "underground-belt": 16, "fast-inserter": 16,
          "medium-electric-pole": 20, "solar-panel": 8, "electric-furnace": 4,
          "electric-mining-drill": 4, "assembling-machine-3": 4,
          "steel-chest": 4, "splitter": 4, "long-handed-inserter": 8}
RULES = {**SCIENCE_RULES, "contract": CONTRACT, "kit": SPARES,
         "allowed_buildings": sorted(KIT), "seconds": 300, "actions": 200,
         "start": "certified_prebuilt_damaged_factory"}
CASE_FIELDS = ("case_id", "split", "broken_save_sha256", "initial_sha256",
               "healthy_verified", "broken_verified", "recoverable_verified",
               "certificate_sha256", "rules_hash")


def public_case(case):
    return {key: case[key] for key in CASE_FIELDS}


def sha256_string(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def evaluate(record):
    """Reuse fixed science windows with the actual damaged starting snapshot."""
    result = {"production_pass": False, "checks": {}, "windows": []}
    try:
        base = science_evaluate(record)
        if "error" in base:
            return {**result, "error": base["error"]}
        # Only the starting task and budgets differ. Never replace native evidence.
        checks = {k: v for k, v in base["checks"].items()
                  if k not in {"contract", "initial_kit", "empty_start", "within_limits"}}
        case, initial, audit = record["case"], record["initial"], record["audit"]
        checks.update({
            "runtime_rules": record["rules"] == RULES and record["items"] == ITEMS
                             and record["recipes"] == RECIPES,
            "repair_contract": record["repair_contract"] == CONTRACT
                               and record["repair_rules_hash"] == digest(RULES),
            "case_manifest": bool(case["case_id"]) and case["split"] in {"development", "final", "dev", "validation"}
                             and case["rules_hash"] == digest(RULES)
                             and all(sha256_string(case[k]) for k in
                                     ("broken_save_sha256", "initial_sha256", "certificate_sha256")),
            "case_certified": all(case[k] is True for k in
                                  ("healthy_verified", "broken_verified", "recoverable_verified")),
            "initial_spares": initial["inventory"] == SPARES,
            "prepared_start": bool(initial["entities"]) and initial["paused"] is True,
            "initial_case_binding": digest(initial) == case["initial_sha256"],
            "within_limits": type(audit["actions"]) is int and 0 < audit["actions"] <= RULES["actions"]
                             and type(audit["elapsed_seconds"]) in (float, int)
                             and math.isfinite(audit["elapsed_seconds"])
                             and 0 <= audit["elapsed_seconds"] <= RULES["seconds"],
        })
        result.update(checks=checks, windows=base["windows"], production_pass=all(checks.values()))
    except (KeyError, TypeError, ValueError, IndexError, AttributeError) as error:
        result["error"] = "Incomplete or invalid repair evidence: " + str(error)
    return result
