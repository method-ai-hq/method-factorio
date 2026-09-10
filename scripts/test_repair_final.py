"""Final-run guards with synthetic cases and mocked players only."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from repair_batch import candidate_hashes, file_hash
from repair_final import check_selection, run_final


class FinalTests(unittest.TestCase):
    def setup_files(self, root, count=2):
        cases = root / "cases"
        cases.mkdir()
        for index in range(1, count + 1):
            case = cases / f"final-{index:03d}"
            case.mkdir()
            (case / "case.json").write_text(json.dumps({"case_id": case.name, "split": "final"}))
        bundle = root / "candidate"
        bundle.mkdir()
        policy = bundle / "v01.method"
        policy.write_text("synthetic test policy")
        selection = root / "selected.json"
        selection.write_text(json.dumps({"candidate_files": candidate_hashes(policy), "version": "v01"}))
        return cases, policy, selection, root / "output"

    def summary(self, case, policy, status="pass"):
        execution = {"candidate_files": candidate_hashes(policy)} if policy else {}
        return {"case_id": case.name, "case_sha256": file_hash(case / "case.json"),
                "task_sha256": "task", "kind": "method" if policy else "direct",
                "status": status, "scored_pass": status == "pass", "execution": execution}

    def run_mocked(self, paths, *, hook=None):
        calls = []
        cases, policy, selection, output = paths
        def play(case, path, *, slot, method):
            calls.append((case.name, "method" if method else "direct"))
            result = self.summary(case, method)
            if hook:
                hook(case, method, result)
            path.mkdir()
            (path / "summary.json").write_text(json.dumps(result))
            return result
        def check(case):
            return json.loads((case / "case.json").read_text()), {}, {"certificate": True}
        with patch("repair_final.check_case", side_effect=check), \
                patch("repair_final.freeze", return_value={"task_sha256": "task"}), \
                patch("repair_final.freeze_candidate"), patch("repair_final.trial", side_effect=play), \
                patch("repair_final.review", side_effect=lambda output, case, **kw: json.loads((output / "summary.json").read_text())), \
                patch("repair_final.group", return_value={"rows": [], "recipe_reviewed_attempts": 2}), \
                patch("repair_final.compare", return_value={"paired_cases": 2}), patch("builtins.print"):
            try:
                result = run_final(cases, policy, selection, output, count=2)
            except Exception as exc:
                return calls, exc
        return calls, result

    def test_selection_hash_and_candidate_changes_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            _, policy, selection, _ = self.setup_files(Path(temp))
            chosen = json.loads(selection.read_text())
            frozen_hash = file_hash(selection)
            check_selection(policy, selection, frozen_hash, chosen)
            selection.write_text(selection.read_text() + "\n")
            with self.assertRaisesRegex(ValueError, "Selection document changed"):
                check_selection(policy, selection, frozen_hash, chosen)
            policy.write_text("changed")
            with self.assertRaisesRegex(ValueError, "Selected Method changed"):
                check_selection(policy, selection, file_hash(selection), chosen)

    def test_completed_pairs_resume_without_new_trials(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = self.setup_files(Path(temp))
            calls, result = self.run_mocked(paths)
            self.assertNotIsInstance(result, Exception)
            self.assertEqual(len(calls), 4)
            calls, result = self.run_mocked(paths)
            self.assertEqual(calls, [])
            self.assertNotIsInstance(result, Exception)

    def test_changed_case_between_pairs_stops_new_trials(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = self.setup_files(Path(temp))
            def change(case, policy, result):
                target = paths[0] / "final-002/case.json"
                target.write_text('{"case_id":"final-002","split":"final","changed":true}')
            calls, error = self.run_mocked(paths, hook=change)
            self.assertIsInstance(error, ValueError)
            self.assertEqual({name for name, _ in calls}, {"final-001"})

    def test_changed_case_on_resume_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = self.setup_files(Path(temp))
            self.run_mocked(paths)
            (paths[0] / "final-002/case.json").write_text('{"case_id":"final-002","split":"final","changed":true}')
            calls, error = self.run_mocked(paths)
            self.assertEqual(calls, [])
            self.assertIsInstance(error, ValueError)

    def test_infrastructure_failure_stops_following_pair(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = self.setup_files(Path(temp))
            def fail(case, policy, result):
                if not policy:
                    result.update(status="infrastructure_failure", scored_pass=False)
            calls, error = self.run_mocked(paths, hook=fail)
            self.assertIsInstance(error, RuntimeError)
            self.assertEqual({name for name, _ in calls}, {"final-001"})
            self.assertTrue((paths[3] / "direct/direct-final-001/summary.json").exists())

    def test_retained_infrastructure_failure_blocks_both_new_arms(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = self.setup_files(Path(temp))
            # Even a failure in a later pair must stop new earlier work on resume.
            output = paths[3] / "direct/direct-final-002"
            output.mkdir(parents=True)
            (output / "summary.json").write_text(json.dumps(self.summary(paths[0] / "final-002", None, "infrastructure_failure")))
            calls, error = self.run_mocked(paths)
            self.assertEqual(calls, [])
            self.assertIsInstance(error, RuntimeError)

    def test_incomplete_attempt_blocks_new_opposite_arm(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = self.setup_files(Path(temp))
            (paths[3] / "method/method-final-001").mkdir(parents=True)
            calls, error = self.run_mocked(paths)
            self.assertEqual(calls, [])
            self.assertIsInstance(error, RuntimeError)


if __name__ == "__main__":
    unittest.main()
