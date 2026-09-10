"""Trial failure classification and cleanup tests. No game or model is started."""
import json
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from repair_trial import NATIVE_CHECKS, classify, finished, trial, wait_ready
from repair_batch import candidate_hashes, freeze_candidate, validate_resume


class FinishTests(unittest.TestCase):
    def test_only_successful_last_finish_counts(self):
        cases = [([], False), ([{"request": {"action": "observe"}, "response": {"ok": True}}], False),
                 ([{"request": {"action": "finish"}, "response": {"ok": False}}], False),
                 ([{"request": {"action": "finish"}, "response": {"ok": True}}], True),
                 ([{"request": {"action": "finish"}, "response": {"ok": True}},
                   {"request": {"action": "observe"}, "response": {"ok": False}}], False)]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "actions.jsonl"
            self.assertFalse(finished(path))
            for rows, expected in cases:
                path.write_text("".join(json.dumps(row) + "\n" for row in rows))
                with self.subTest(rows=rows):
                    self.assertEqual(finished(path), expected)

    def test_host_exit_before_ready_is_infrastructure_error(self):
        class Exited:
            returncode = 2
            def poll(self): return self.returncode
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError, "exited before ready"):
                wait_ready(Exited(), Path(temp) / "ready.json", seconds=.1)


class TrialTests(unittest.TestCase):
    def simulate(self, *, verdict, execution=None, finish=True, wait_timeouts=0):
        """Keep real file handling while replacing child processes and native reads."""
        verdict = {**verdict, "verification": {**dict.fromkeys(NATIVE_CHECKS, True), **verdict.get("verification", {})}}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            case = root / "development-001"
            case.mkdir()
            (case / "case.json").write_text('{"case_id":"development-001"}')
            (root / "docs").mkdir()
            (root / "docs/repair-task.md").write_text("Unit test task only.")
            output = root / "trial"

            class Host:
                pid = 424242
                returncode = None
                def __init__(self, command, **kwargs):
                    self.signals = []
                    self.wait_calls = []
                    self.timeouts_left = wait_timeouts
                    directory = Path(command[command.index("--run") + 1])
                    directory.mkdir()
                    (directory / "ready.json").write_text(json.dumps({
                        "endpoint": "http://127.0.0.1:18950/action", "deadline_epoch": time.time() + 30}))
                    request = {"action": "finish" if finish else "observe"}
                    (directory / "actions.jsonl").write_text(json.dumps({"request": request, "response": {"ok": True}}) + "\n")
                    (directory / "record.json").write_text(json.dumps({"audit": {"actions": 1, "elapsed_seconds": 10}}))
                def poll(self): return self.returncode
                def send_signal(self, value): self.signals.append(value)
                def wait(self, timeout=None):
                    self.wait_calls.append(timeout)
                    if self.timeouts_left:
                        self.timeouts_left -= 1
                        raise subprocess.TimeoutExpired("fake host", timeout)
                    self.returncode = 0
                    return self.returncode

            children = []
            def spawn(*args, **kwargs):
                child = Host(*args, **kwargs)
                children.append(child)
                return child
            with patch("repair_trial.ROOT", root), patch("repair_trial.check_case", return_value=({}, {}, {"valid": True})), \
                    patch("repair_trial.subprocess.Popen", side_effect=spawn), \
                    patch("repair_trial.run_codex", return_value=execution or {"status": "completed"}), \
                    patch("repair_trial.verify", return_value=verdict), patch("repair_trial.os.killpg") as kill:
                result = trial(case, output)
                saved = json.loads((output / "summary.json").read_text())
                self.assertEqual(saved, result)
                return result, children[0], kill.call_args_list

    def test_valid_production_failure_remains_policy_failure(self):
        verdict = {"scored_pass": False, "production_pass": False,
                   "verification": {"saved_state_matches": True, "source_matches": True}}
        result, _, _ = self.simulate(verdict=verdict)
        self.assertEqual(result["status"], "fail")

    def test_native_integrity_failure_is_infrastructure_failure(self):
        for field in ("saved_state_matches", "saved_record_matches", "source_matches", "native_initial_matches"):
            verdict = {"scored_pass": False, "production_pass": True, "verification": {field: False}}
            with self.subTest(field=field):
                result, _, _ = self.simulate(verdict=verdict)
                self.assertEqual(result["status"], "infrastructure_failure")

    def test_no_finish_stops_host_and_is_policy_failure(self):
        verdict = {"scored_pass": False, "production_pass": False,
                   "verification": {"saved_state_matches": True, "source_matches": True,
                                    "finish_is_last_action": False}, "error": "'measurement'"}
        result, host, _ = self.simulate(verdict=verdict, finish=False)
        self.assertEqual(result["status"], "fail")
        self.assertIn(signal.SIGTERM, host.signals)

    def test_model_failure_remains_infrastructure_failure(self):
        result, _, _ = self.simulate(verdict={"scored_pass": False}, execution={"status": "infrastructure_failure"})
        self.assertEqual(result["status"], "infrastructure_failure")

    def test_host_hang_gets_bounded_cleanup(self):
        result, host, kills = self.simulate(verdict={"scored_pass": False}, wait_timeouts=2)
        self.assertEqual(result["status"], "infrastructure_failure")
        self.assertIn(signal.SIGTERM, host.signals)
        self.assertEqual(kills[0].args, (host.pid, signal.SIGKILL))
        self.assertIsNotNone(host.returncode)


class FreezeTests(unittest.TestCase):
    def test_candidate_change_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = root / "candidate"
            output = root / "output"
            bundle.mkdir()
            output.mkdir()
            policy = bundle / "v01.method"
            policy.write_text("first")
            freeze_candidate(output, policy)
            policy.write_text("changed")
            with self.assertRaisesRegex(RuntimeError, "Candidate changed"):
                freeze_candidate(output, policy)

    def test_resume_checks_case_task_and_candidate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            case = root / "development-001"
            case.mkdir()
            (case / "case.json").write_text("frozen case")
            from repair_batch import file_hash
            result = {"case_id": case.name, "case_sha256": file_hash(case / "case.json"),
                      "task_sha256": "task", "kind": "direct"}
            validate_resume(result, case, None, "task")
            for field in ("case_id", "case_sha256", "task_sha256", "kind"):
                with self.subTest(field=field), self.assertRaises(RuntimeError):
                    validate_resume({**result, field: "changed"}, case, None, "task")
            bundle = root / "candidate"
            bundle.mkdir()
            policy = bundle / "v01.method"
            policy.write_text("first")
            result.update(kind="method", execution={"candidate_files": candidate_hashes(policy)})
            validate_resume(result, case, policy, "task")
            policy.write_text("changed")
            with self.assertRaisesRegex(RuntimeError, "different candidate"):
                validate_resume(result, case, policy, "task")

    def test_missing_native_proof_cannot_be_policy_failure(self):
        self.assertEqual(classify({"scored_pass": False}, {"status": "completed"}), "infrastructure_failure")

    def test_candidate_failure_is_not_runner_failure(self):
        verdict = {"scored_pass": False, "verification": dict.fromkeys(NATIVE_CHECKS, True)}
        for status in ("policy_failure", "timeout"):
            self.assertEqual(classify(verdict, {"status": status}), "fail")


if __name__ == "__main__":
    unittest.main()
