"""Native recipe export review tests. No real game or model is started."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from repair_contract import evaluate
from repair_review import normalize, review
from repair_trial import NATIVE_CHECKS
from test_repair_contract import record


def fixture():
    value = record()
    history = {"tick": value["measurement"]["samples"][-1]["tick"], "paused": True, "samples": []}
    for sample in value["measurement"]["samples"]:
        proof = {"tick": sample["tick"], "entities": []}
        for e in sample["entities"]:
            e["type"] = "furnace" if e["recipe"] in {"iron-plate", "copper-plate"} else "assembling-machine"
            native = {"id": e["id"], "type": e["type"], "products": e["products"],
                      "recipe_type": "string", "recipe_name": e["recipe"]}
            if e["recipe"] == "copper-plate":
                native.update(recipe_type="userdata", recipe_object="LuaRecipePrototype")
                e["recipe"] = None
            proof["entities"].append(native)
        history["samples"].append(proof)
    value["final"] = copy.deepcopy(value["measurement"]["samples"][-1])
    value["final"]["paused"] = True
    return value, history


class NormalizeTests(unittest.TestCase):
    def test_native_reference_recovers_recipe_without_other_changes(self):
        raw, proof = fixture()
        normalized, corrections = normalize(raw, proof)
        self.assertFalse(evaluate(raw)["production_pass"])
        self.assertTrue(evaluate(normalized)["production_pass"])
        self.assertEqual(len(corrections), 4)
        reverted = copy.deepcopy(normalized)
        for correction in corrections:
            entity = next(e for e in reverted["measurement"]["samples"][correction["sample_index"]]["entities"]
                          if e["id"] == correction["entity_id"])
            entity["recipe"] = None
        self.assertEqual(reverted, raw)

    def test_missing_native_recipe_is_not_inferred_from_products(self):
        raw, proof = fixture()
        for sample in proof["samples"]:
            for e in sample["entities"]:
                if e["recipe_type"] == "userdata":
                    e["recipe_type"] = "nil"
                    e.pop("recipe_name")
        normalized, corrections = normalize(raw, proof)
        self.assertEqual(normalized, raw)
        self.assertEqual(corrections, [])
        self.assertFalse(evaluate(normalized)["production_pass"])

    def test_invalid_proof_is_rejected(self):
        mutations = {
            "wrong_tick": lambda p: p.update(tick=1),
            "unpaused": lambda p: p.update(paused=False),
            "sample_count": lambda p: p["samples"].pop(),
            "sample_tick": lambda p: p["samples"][0].update(tick=2),
            "wrong_id": lambda p: p["samples"][0]["entities"][1].update(id=999),
            "wrong_products": lambda p: p["samples"][0]["entities"][1].update(products=999),
            "wrong_object": lambda p: p["samples"][0]["entities"][1].update(recipe_object="LuaEntity"),
            "wrong_recipe": lambda p: p["samples"][0]["entities"][1].update(recipe_name="made-up"),
        }
        for name, mutate in mutations.items():
            raw, proof = fixture()
            mutate(proof)
            with self.subTest(name=name), self.assertRaises(ValueError):
                normalize(raw, proof)

    def test_request_limit_is_not_repaired(self):
        raw, proof = fixture()
        raw["audit"]["violations"] = 1
        normalized, _ = normalize(raw, proof)
        self.assertFalse(evaluate(normalized)["production_pass"])


class ReviewTests(unittest.TestCase):
    def simulate(self, *, protocol=False, bad_native=False, changed_legacy=False):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            trial = root / "trial"
            host = trial / "host"
            (host / "game").mkdir(parents=True)
            case = root / "case"
            case.mkdir()
            (case / "case.json").write_text('{"case_id":"test"}')
            raw, proof = fixture()
            if protocol: raw["audit"]["violations"] = 1
            legacy = evaluate(raw)
            legacy.update(scored_pass=False, verification=dict.fromkeys(NATIVE_CHECKS, True))
            legacy["verification"]["finish_is_last_action"] = not protocol
            (host / "record.json").write_text(json.dumps(raw))
            (host / "verdict.json").write_text(json.dumps(legacy))
            (host / "actions.jsonl").write_text('{"request":{"action":"finish"},"response":{"ok":true}}\n')
            (host / "game/world.zip").write_bytes(b"fake native save")
            original = {"kind": "direct", "case_id": "test", "status": "fail", "scored_pass": False,
                        "total_wall_seconds": 20, "execution": {"status": "completed"}, "host_returncode": 0,
                        "verdict": legacy}
            (trial / "summary.json").write_text(json.dumps(original))
            watched = [trial / "summary.json", host / "record.json", host / "verdict.json", host / "game/world.zip", host / "actions.jsonl"]
            before = {str(p): p.read_bytes() for p in watched}

            class Native:
                def __init__(self, *args, **kwargs): pass
                def __enter__(self): return self
                def __exit__(self, *_): pass
                def install(self): pass
                def read(self, expression):
                    if expression == "storage.science":
                        return {} if bad_native else {k: v for k, v in raw.items() if k != "final"}
                    return proof

            independent = copy.deepcopy(legacy)
            if changed_legacy: independent["production_pass"] = True
            with patch("repair_review.verify", return_value=independent), patch("repair_review.Server", Native):
                result = review(trial, case)
            self.assertEqual(before, {str(p): p.read_bytes() for p in watched})
            self.assertEqual(json.loads((trial / "review.json").read_text()), result)
            return result

    def test_adjudication_preserves_original_files_and_adds_review_time(self):
        result = self.simulate()
        self.assertEqual(result["review_contract"], "repair-recipe-export/2")
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["scored_pass"])
        self.assertFalse(result["legacy_scored_pass"])
        self.assertEqual(len(result["corrections"]), 4)
        self.assertGreater(result["total_wall_seconds"], 20)
        self.assertEqual(result["original_total_wall_seconds"], 20)

    def test_protocol_failure_remains_failure(self):
        result = self.simulate(protocol=True)
        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["scored_pass"])
        self.assertFalse(result["verdict"]["checks"]["no_play_after_finish"])

    def test_independent_native_mismatch_is_infrastructure_failure(self):
        for options in ({"bad_native": True}, {"changed_legacy": True}):
            with self.subTest(options=options):
                result = self.simulate(**options)
                self.assertEqual(result["status"], "infrastructure_failure")
                self.assertFalse(result["scored_pass"])


if __name__ == "__main__":
    unittest.main()
