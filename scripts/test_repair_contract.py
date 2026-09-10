"""Offline repair rules and save-verifier tests. Fixtures are not game evidence."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from repair_contract import CONTRACT, RULES, SPARES, ITEMS, RECIPES, digest, evaluate, public_case
from repair_verify import check_case, file_hash, verify
from test_science import record as science_record


def record():
    value = science_record()
    value.update(repair_contract=CONTRACT, repair_rules_hash=digest(RULES),
                 rules=copy.deepcopy(RULES), items=list(ITEMS), recipes=list(RECIPES))
    value["initial"].update(inventory=dict(SPARES), paused=True, tick=0,
                            entities=[{"id": 10, "name": "transport-belt", "direction": 4}])
    value["case"] = {"case_id": "offline-only", "split": "development",
                     "rules_hash": digest(RULES), "initial_sha256": digest(value["initial"]),
                     "broken_save_sha256": "a" * 64, "certificate_sha256": "b" * 64,
                     "healthy_verified": True, "broken_verified": True, "recoverable_verified": True}
    value["clean"]["tick"] = 0
    return value


class RepairRuleTests(unittest.TestCase):
    def test_prebuilt_start_uses_real_windows(self):
        result = evaluate(record())
        self.assertTrue(result["production_pass"])
        self.assertEqual(len(result["windows"]), 3)
        self.assertNotIn("empty_start", result["checks"])

    def test_bad_start_and_limits(self):
        mutations = {
            "changed_initial": lambda r: r["initial"]["entities"][0].update(direction=8),
            "empty_factory": lambda r: r["initial"].update(entities=[]),
            "unpaused_initial": lambda r: r["initial"].update(paused=False),
            "extra_inventory": lambda r: r["initial"]["inventory"].update({"iron-plate": 1}),
            "uncertified_case": lambda r: r["case"].update(recoverable_verified=False),
            "missing_certificate_hash": lambda r: r["case"].pop("certificate_sha256"),
            "wrong_rules": lambda r: r.update(repair_rules_hash="changed"),
            "changed_runtime_rules": lambda r: r["rules"].update(actions=500),
            "excess_time": lambda r: r["audit"].update(elapsed_seconds=301),
            "negative_time": lambda r: r["audit"].update(elapsed_seconds=-1),
            "nan_time": lambda r: r["audit"].update(elapsed_seconds=float("nan")),
            "excess_actions": lambda r: r["audit"].update(actions=201),
        }
        for name, change in mutations.items():
            value = record()
            change(value)
            with self.subTest(name=name):
                self.assertFalse(evaluate(value)["production_pass"])

    def test_science_buffer_and_windows_unchanged(self):
        mutations = {
            "buffer": lambda r: r["clean"]["stock"].update({"automation-science-pack": 100}),
            "progress": lambda r: r["clean"].update(entities=[{"progress": .1}]),
            "ground": lambda r: r["clean"].update(ground_items=1),
            "shifted_boundary": lambda r: r["measurement"]["samples"][1].update(tick=10801),
            "missing_window": lambda r: r["measurement"]["samples"].pop(),
            "no_mining": lambda r: r["measurement"]["samples"][2]["ore"].update({"iron-ore": 9980}),
            "no_stage": lambda r: r["measurement"]["samples"][2]["produced"].update({"copper-cable": 20}),
            "no_machine_work": lambda r: r["measurement"]["samples"][2]["entities"][0].update(products=20),
            "discarded_packs": lambda r: r["measurement"]["samples"][2]["stock"].update({"logistic-science-pack": 20}),
        }
        for name, change in mutations.items():
            value = record()
            change(value)
            with self.subTest(name=name):
                self.assertFalse(evaluate(value)["production_pass"])


def bundle(root):
    """Make explicitly fake files for mocked verifier branch tests."""
    case = root / "case"
    run = root / "run"
    case.mkdir()
    (run / "game").mkdir(parents=True)
    actual = record()
    (case / "broken.zip").write_bytes(b"fake initial save")
    (case / "initial.json").write_text(json.dumps(actual["initial"]))
    actual["case"]["broken_save_sha256"] = file_hash(case / "broken.zip")
    certificate = {key: actual["case"][key] for key in
                   ("case_id", "rules_hash", "broken_save_sha256", "initial_sha256")}
    for stage in ("healthy", "broken", "recoverable"):
        directory = case / stage
        directory.mkdir()
        (directory / "world.zip").write_bytes(b"fake terminal " + stage.encode())
        evidence = science_record()
        evidence["final"] = {"paused": True}
        if stage == "broken":
            evidence["measurement"]["samples"][1]["produced"]["logistic-science-pack"] = 0
        (directory / "record.json").write_text(json.dumps(evidence))
        passed = stage != "broken"
        verdict = {"production_pass": passed, "scored_pass": passed,
                   "verification": {"saved_record_matches": True},
                   "save_sha256": file_hash(directory / "world.zip")}
        (directory / "verdict.json").write_text(json.dumps(verdict))
        entry = {"production_pass": passed, "verification_pass": True}
        for kind, filename in (("record", "record.json"), ("save", "world.zip"), ("verdict", "verdict.json")):
            entry[kind + "_path"] = stage + "/" + filename
            entry[kind + "_sha256"] = file_hash(directory / filename)
        certificate[stage] = entry
    (case / "certificate.json").write_text(json.dumps(certificate))
    actual["case"]["certificate_sha256"] = file_hash(case / "certificate.json")
    (case / "case.json").write_text(json.dumps(actual["case"]))
    (run / "game/world.zip").write_bytes(b"fake run terminal")
    row = {"request": {"action": "finish"}, "response": {"ok": True}, "elapsed_seconds": 1}
    (run / "actions.jsonl").write_text(json.dumps(row) + "\n")
    actual["audit"]["trace_sha256"] = file_hash(run / "actions.jsonl")
    actual["sources"] = {"test": "fixed"}
    final = copy.deepcopy(actual["measurement"]["samples"][-1])
    final["paused"] = True
    expected = copy.deepcopy(actual)
    expected["final"] = copy.deepcopy(final)
    (run / "record.json").write_text(json.dumps(expected))
    return run, case, actual, final


class RepairVerifierTests(unittest.TestCase):
    def test_corrupt_evidence(self):
        cases = ("valid", "missing_certificate", "changed_initial", "changed_broken_save",
                 "changed_linked_verdict", "missing_save", "changed_record", "changed_final",
                 "native_initial_changed", "after_measurement", "changed_trace", "bad_trace_time",
                 "changed_source", "unpaused_final", "missing_trace")
        for name in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                run, case, actual, final = bundle(Path(temp))
                initial = copy.deepcopy(actual["initial"])
                if name == "missing_certificate": (case / "certificate.json").unlink()
                if name == "changed_initial": (case / "initial.json").write_text("{}")
                if name == "changed_broken_save": (case / "broken.zip").write_bytes(b"altered")
                if name == "changed_linked_verdict": (case / "healthy/verdict.json").write_text("{}")
                if name == "missing_save": (run / "game/world.zip").unlink()
                if name == "changed_record": (run / "record.json").write_text("{}")
                if name in ("changed_final", "after_measurement"):
                    final["tick"] += 1
                    if name == "after_measurement":
                        expected = copy.deepcopy(actual)
                        expected["final"] = final
                        (run / "record.json").write_text(json.dumps(expected))
                if name == "native_initial_changed": initial["tick"] += 1
                if name == "changed_trace": (run / "actions.jsonl").write_text("{}\n")
                if name == "bad_trace_time":
                    row = {"request": {"action": "finish"}, "response": {"ok": True}, "elapsed_seconds": -1}
                    (run / "actions.jsonl").write_text(json.dumps(row) + "\n")
                    actual["audit"]["trace_sha256"] = file_hash(run / "actions.jsonl")
                    expected = copy.deepcopy(actual)
                    expected["final"] = final
                    (run / "record.json").write_text(json.dumps(expected))
                if name == "changed_source": actual["sources"] = {"test": "changed"}
                if name == "unpaused_final": final["paused"] = False
                if name == "missing_trace": (run / "actions.jsonl").unlink()

                class FakeServer:
                    def __init__(self, *args, **kwargs): self.initial = Path(kwargs["save"]).name == "broken.zip"
                    def __enter__(self): return self
                    def __exit__(self, *_): pass
                    def install(self): pass
                    def command(self, _): return "repair installed"
                    def read(self, expression):
                        if self.initial: return initial
                        return actual if expression == "storage.science" else final

                host = types.ModuleType("repair_host")
                host.sources = lambda: {"test": "fixed"}
                with patch.dict("sys.modules", {"repair_host": host}), patch("repair_verify.Server", FakeServer):
                    result = verify(run, case)
                self.assertEqual(result["scored_pass"], name == "valid", result)

    def test_certificate_truth_flags_do_not_replace_files(self):
        with tempfile.TemporaryDirectory() as temp:
            _, case, _, _ = bundle(Path(temp))
            (case / "healthy/world.zip").unlink()
            with self.assertRaises(ValueError):
                check_case(case)

    def test_certificate_cannot_read_outside_case(self):
        with tempfile.TemporaryDirectory() as temp:
            _, case, _, _ = bundle(Path(temp))
            certificate = json.loads((case / "certificate.json").read_text())
            certificate["healthy"]["record_path"] = "../private.json"
            (case / "certificate.json").write_text(json.dumps(certificate))
            with self.assertRaises(ValueError):
                check_case(case)


if __name__ == "__main__":
    unittest.main()
