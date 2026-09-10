"""Publication audits on synthetic files. No final results, games, or models."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from repair_audit import audit, audit_trial
from repair_batch import RUNNERS, candidate_hashes, file_hash
from repair_contract import evaluate
from repair_review import VERSION, normalize, provenance
from repair_trial import NATIVE_CHECKS
from test_repair_review import fixture


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def trial_files(root):
    case = root / "case/final-001"
    write(case / "case.json", {"case_id": "final-001", "split": "final"})
    trial = root / "direct-final-001"
    host = trial / "host"
    raw, history = fixture()
    core = {"science_runtime.lua": "frozen-core"}
    runners = {"repair_codex.py": "frozen-player"}
    raw["sources"] = core
    legacy = evaluate(raw)
    legacy.update(scored_pass=False, verification=dict.fromkeys(NATIVE_CHECKS, True))
    execution = {"status": "completed", "model": "gpt-6-astra", "reasoning_effort": "medium", "auth": "chatgpt",
                 "source_sha256": {"runner": runners["repair_codex.py"], "task": "task"}}
    summary = {"case_id": case.name, "kind": "direct", "case_sha256": file_hash(case / "case.json"),
               "task_sha256": "task", "status": "fail", "scored_pass": False, "verdict": legacy,
               "execution": execution, "actions": 1, "game_wall_seconds": 10, "total_wall_seconds": 20,
               "host_returncode": 0}
    write(host / "record.json", raw)
    write(host / "verdict.json", legacy)
    write(trial / "summary.json", summary)
    write(trial / "codex/execution.json", execution)
    (host / "game").mkdir()
    (host / "game/world.zip").write_bytes(b"synthetic save")
    (host / "actions.jsonl").write_text('{"request":{"action":"finish"},"response":{"ok":true}}\n')
    normalized, corrections = normalize(raw, history)
    reviewed = copy.deepcopy(summary)
    verdict = {**legacy, **evaluate(normalized), "scored_pass": True}
    proofs = provenance(trial, case)
    reviewed.update(review_contract=VERSION, review_provenance=proofs,
                    raw_summary_sha256=proofs["raw_summary_sha256"], raw_record_sha256=proofs["raw_record_sha256"],
                    save_sha256=proofs["raw_save_sha256"], source_sha256=proofs["review_source_sha256"],
                    original_status="fail", legacy_scored_pass=False, original_total_wall_seconds=20,
                    review_wall_seconds=5, total_wall_seconds=25, legacy_verdict=legacy,
                    independent_legacy_verdict=legacy, native_recipe_history=history,
                    corrections=corrections, status="pass", scored_pass=True, verdict=verdict)
    write(trial / "review.json", reviewed)
    return trial, case, core, runners


class TrialAuditTests(unittest.TestCase):
    def test_consistent_native_review_is_accepted_without_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            trial, case, core, runners = trial_files(Path(temp))
            before = {p: p.read_bytes() for p in Path(temp).rglob("*") if p.is_file()}
            result = audit_trial(trial, case, kind="direct", task_hash="task", core=core, runners=runners)
            self.assertEqual(result["status"], "pass")
            self.assertEqual(before, {p: p.read_bytes() for p in Path(temp).rglob("*") if p.is_file()})

    def test_changed_original_files_are_rejected(self):
        for name in ("summary.json", "host/record.json", "host/game/world.zip", "host/actions.jsonl", "host/verdict.json"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                trial, case, core, runners = trial_files(Path(temp))
                target = trial / name
                target.write_bytes(target.read_bytes() + b" ")
                with self.assertRaises(ValueError):
                    audit_trial(trial, case, kind="direct", task_hash="task", core=core, runners=runners)

    def test_changed_review_decisions_and_history_are_rejected(self):
        changes = {"score": lambda r: r.update(scored_pass=False),
                   "time": lambda r: r.update(total_wall_seconds=1),
                   "corrections": lambda r: r.update(corrections=[]),
                   "rules": lambda r: r["verdict"]["checks"].update(within_limits=False),
                   "native": lambda r: r["native_recipe_history"]["samples"][0]["entities"][1].update(products=999),
                   "reader": lambda r: r.update(source_sha256="other")}
        for name, change in changes.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                trial, case, core, runners = trial_files(Path(temp))
                reviewed = json.loads((trial / "review.json").read_text())
                change(reviewed)
                write(trial / "review.json", reviewed)
                with self.assertRaises(ValueError):
                    audit_trial(trial, case, kind="direct", task_hash="task", core=core, runners=runners)

    def test_player_model_source_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            trial, case, core, runners = trial_files(Path(temp))
            child = json.loads((trial / "codex/execution.json").read_text())
            child["source_sha256"]["runner"] = "wrong-runner"
            write(trial / "codex/execution.json", child)
            with self.assertRaisesRegex(ValueError, "runner source"):
                audit_trial(trial, case, kind="direct", task_hash="task", core=core, runners=runners)


class PublicationAuditTests(unittest.TestCase):
    def setup(self, root):
        sources = {"core.py": "frozen"}
        for name in [*RUNNERS, "repair_review.py"]:
            target = root / "scripts" / name
            target.parent.mkdir(exist_ok=True)
            target.write_text(name)
        (root / "docs").mkdir()
        (root / "docs/repair-task.md").write_text("fixed task")
        bundle = root / "candidate"
        bundle.mkdir()
        policy = bundle / "repair.method"
        policy.write_text("fixed candidate")
        candidates = candidate_hashes(policy)
        selection = root / "selection.json"
        chosen = {"candidate_files": candidates, "review_source_sha256": file_hash(root / "scripts/repair_review.py"), "review_contract": VERSION}
        write(selection, chosen)
        output = root / "output"
        write(output / "selection.json", chosen)
        write(output / "selection-hash.json", {"sha256": file_hash(selection)})
        write(output / "method/repair.method-candidate-lock.json", {"policy": policy.name, "files": candidates})
        cases = root / "cases"
        manifests = {}
        for i in range(1, 3):
            name = f"final-{i:03d}"
            write(cases / name / "case.json", {"case_id": name, "split": "final"})
            manifests[name] = file_hash(cases / name / "case.json")
            for kind in ("direct", "method"):
                write(output / kind / f"{kind}-{name}/summary.json", {"kind": kind})
        write(output / "cases.json", manifests)
        for kind in ("direct", "method"):
            write(output / kind / "benchmark.json", {"sources": sources, "task_sha256": file_hash(root / "docs/repair-task.md")})
            write(output / kind / "runner-freeze.json", {"sources": {name: file_hash(root / "scripts" / name) for name in RUNNERS}})
        write(output / "report.json", {"direct": {"rows": []}, "method": {"rows": []}, "comparison": {}, "selection": chosen, "case_manifest_hashes": manifests})
        return output, cases, policy, selection, sources

    def run_audit(self, root, values):
        output, cases, policy, selection, sources = values
        def certificate(case): return json.loads((case / "case.json").read_text()), {}, {"valid": True}
        with patch("repair_audit.ROOT", root), patch("repair_audit.sources", return_value=sources), \
                patch("repair_audit.check_case", side_effect=certificate), patch("repair_audit.audit_trial", return_value={"status": "pass"}), \
                patch("repair_audit.group", return_value={"rows": []}), patch("repair_audit.compare", return_value={}):
            return audit(output, cases, policy, selection, count=2)

    def test_paired_locks_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = self.run_audit(root, self.setup(root))
            self.assertTrue(result["audit_pass"])
            self.assertEqual(result["attempts"], 4)

    def test_missing_duplicate_or_changed_inputs_rejected(self):
        for mutation in ("missing", "duplicate", "case", "candidate", "reader", "runner", "task", "report"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                values = self.setup(root)
                output, cases, policy, selection, _ = values
                if mutation == "missing": (output / "direct/direct-final-002/summary.json").unlink()
                if mutation == "duplicate": write(output / "direct/duplicate-final-001/summary.json", {})
                if mutation == "case": (cases / "final-001/case.json").write_text('{"case_id":"final-001","split":"final","changed":true}')
                if mutation == "candidate": policy.write_text("changed")
                if mutation == "reader": (root / "scripts/repair_review.py").write_text("changed")
                if mutation == "runner": write(output / "method/runner-freeze.json", {"sources": {}})
                if mutation == "task": (root / "docs/repair-task.md").write_text("changed")
                if mutation == "report": write(output / "report.json", {"direct": {}, "method": {}, "comparison": {}})
                with self.assertRaises(ValueError): self.run_audit(root, values)


if __name__ == "__main__":
    unittest.main()
