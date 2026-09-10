"""Adversarial rule tests; real-game checks are in science_validation.py."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from science_contract import BOUNDARIES, CONTRACT, ITEMS, KIT, RECIPES, RULES, digest, evaluate


def record():
    initial = {"inventory": dict(KIT), "entities": [], "ground_items": 0,
               "produced": dict.fromkeys(ITEMS, 0), "speed": 20, "always_day": True}
    clean = {"stock": dict.fromkeys(ITEMS, 0), "ground_items": 0, "entities": []}
    samples = []
    for i, tick in enumerate(BOUNDARIES):
        samples.append({"tick": tick, "speed": 20, "always_day": True,
            "produced": dict.fromkeys(ITEMS, i * 20), "stock": dict.fromkeys(ITEMS, i * 20),
            "ore": {"iron-ore": 10000-i*20, "copper-ore": 10000-i*20},
            "entities": [{"id": n, "name": "test-machine", "recipe": recipe, "products": i*20}
                         for n, recipe in enumerate(RECIPES)]})
    return {"contract": CONTRACT, "rules_hash": digest(RULES), "initial": initial, "clean": clean,
            "game_version": RULES["factorio_version"], "mods": {"base": RULES["factorio_version"]},
            "measurement": {"start": 0, "done": True, "samples": samples},
            "audit": {"violations": 0, "actions": 1, "elapsed_seconds": 10}}


class ScienceTests(unittest.TestCase):
    def test_positive(self):
        self.assertTrue(evaluate(record())["production_pass"])

    def test_missing_sections_fail(self):
        for key in record():
            r = record(); del r[key]
            with self.subTest(key=key):
                self.assertFalse(evaluate(r)["production_pass"])


class SaveVerifierTests(unittest.TestCase):
    """Test file corruption handling independently of live Factorio coverage."""
    def test_corrupt_or_missing_evidence(self):
        from science_host import sources
        from science_verify import verify
        cases = ["valid", "changed_trace", "changed_record", "changed_final",
                 "missing_save", "missing_trace", "changed_source", "unpaused_save"]
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                run = Path(temp)
                (run / "game").mkdir()
                (run / "game/world.zip").write_bytes(b"mock save for verifier unit test")
                trace = json.dumps({"request": {"action": "finish"}, "response": {"ok": True}}) + "\n"
                (run / "actions.jsonl").write_text(trace)
                actual = record()
                actual["sources"] = sources()
                actual["audit"]["trace_sha256"] = hashlib.sha256(trace.encode()).hexdigest()
                final = {"paused": True}
                expected = copy.deepcopy(actual)
                expected["final"] = dict(final)
                if case == "changed_trace":
                    (run / "actions.jsonl").write_text(trace.replace('"ok": true', '"ok": false'))
                if case == "changed_record":
                    expected["audit"]["actions"] = 2
                if case == "changed_final":
                    expected["final"]["tick"] = 999
                if case == "missing_save":
                    (run / "game/world.zip").unlink()
                if case == "missing_trace":
                    (run / "actions.jsonl").unlink()
                if case == "changed_source":
                    actual["sources"]["science_host.py"] = "changed"
                    expected["sources"] = dict(actual["sources"])
                if case == "unpaused_save":
                    final["paused"] = False
                    expected["final"] = dict(final)
                (run / "record.json").write_text(json.dumps(expected))

                class FakeServer:
                    def __init__(self, *args, **kwargs): pass
                    def __enter__(self): return self
                    def __exit__(self, *args): pass
                    def install(self): pass
                    def read(self, name): return actual if name == "storage.science" else final
                with patch("science_verify.Server", FakeServer):
                    self.assertEqual(verify(run)["scored_pass"], case == "valid")

class ProductionFailureTests(unittest.TestCase):
    def test_each_required_item(self):
        for item in ITEMS:
            r = record()
            for s in r["measurement"]["samples"]:
                s["produced"][item] = 0
            with self.subTest(item=item):
                self.assertFalse(evaluate(r)["production_pass"])

    def test_each_window(self):
        for window in range(1,4):
            r = record()
            r["measurement"]["samples"][window]["produced"]["logistic-science-pack"] = (
                r["measurement"]["samples"][window-1]["produced"]["logistic-science-pack"])
            self.assertFalse(evaluate(r)["production_pass"])

    def test_adversarial_evidence(self):
        mutations = {
            "extra_starting_material": lambda r: r["initial"]["inventory"].update({"iron-plate": 1}),
            "prebuilt_factory": lambda r: r["initial"].update(entities=[{}]),
            "stored_material": lambda r: r["clean"]["stock"].update({"electronic-circuit": 1}),
            "in_progress_recipe": lambda r: r["clean"].update(entities=[{"progress": .5}]),
            "ground_material": lambda r: r["clean"].update(ground_items=1),
            "wrong_boundaries": lambda r: r["measurement"]["samples"][1].update(tick=10801),
            "missing_minute": lambda r: r["measurement"]["samples"].pop(),
            "not_done": lambda r: r["measurement"].update(done=False),
            "changed_speed": lambda r: r["measurement"]["samples"][2].update(speed=40),
            "changed_day": lambda r: r["measurement"]["samples"][2].update(always_day=False),
            "forbidden_action": lambda r: r["audit"].update(violations=1),
            "time_limit": lambda r: r["audit"].update(elapsed_seconds=1801),
            "action_limit": lambda r: r["audit"].update(actions=2001),
            "wrong_rules": lambda r: r.update(rules_hash="changed"),
            "no_machine_work": lambda r: r["measurement"]["samples"][2]["entities"][0].update(products=20),
            "missing_machine": lambda r: r["measurement"]["samples"][2]["entities"].pop(),
            "no_new_ore": lambda r: r["measurement"]["samples"][2]["ore"].update({"iron-ore": 9980}),
            "packs_disappear": lambda r: r["measurement"]["samples"][2]["stock"].update({"logistic-science-pack": 20}),
        }
        for name, mutate in mutations.items():
            r = record(); mutate(r)
            with self.subTest(name=name):
                self.assertFalse(evaluate(r)["production_pass"])


if __name__ == "__main__":
    unittest.main()
