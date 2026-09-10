"""Offline checks for required model and benchmark evidence."""
import json
from pathlib import Path
import tempfile
import unittest

from search_trial import runtime_evidence, sha


class RuntimeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.trial = Path(self.directory.name)
        self.runtime = self.trial / "runtime"
        (self.runtime / "method").mkdir(parents=True)

    def write(self, name, content):
        (self.runtime / name).write_text(json.dumps(content) + "\n")

    def fixture(self, count=0):
        self.write("runtime.json", {"limits": {"max_model_requests": 60}})
        self.write("runtime-pin.json", {"config_sha256": sha(self.runtime / "runtime.json"),
                                        "revision": "pinned", "cli_sha256": "known"})
        self.write("execution.json", {"returncode": 0})
        self.write("usage-estimate.json", {"requests": count})
        self.write("method/manifest.json", {"files": {}})
        self.write("method/summary.json", {"status": "completed", "model_requests": count})
        (self.runtime / "method/events.jsonl").write_text(
            ''.join(json.dumps({"event": "model.request"}) + '\n' for _ in range(count))
            + json.dumps({"event": "run.completed"}) + '\n')

    def test_zero_model_method_is_valid(self):
        self.fixture()
        self.assertEqual(runtime_evidence(self.trial), {
            "complete": True, "within_model_limit": True, "model_requests": 0})

    def test_sixty_requests_is_valid_and_sixty_one_fails(self):
        self.fixture(60)
        self.assertTrue(runtime_evidence(self.trial)["within_model_limit"])
        self.fixture(61)
        self.assertFalse(runtime_evidence(self.trial)["within_model_limit"])

    def test_missing_trace_is_not_zero_usage(self):
        self.fixture()
        (self.runtime / "method/events.jsonl").unlink()
        result = runtime_evidence(self.trial)
        self.assertFalse(result["complete"])
        self.assertIsNone(result["model_requests"])

    def test_request_count_must_match_summary(self):
        self.fixture(1)
        self.write("method/summary.json", {"status": "completed", "model_requests": 0})
        self.assertFalse(runtime_evidence(self.trial)["complete"])

    def test_changed_config_rejects_evidence(self):
        self.fixture()
        self.write("runtime.json", {"limits": {"max_model_requests": 61}})
        self.assertFalse(runtime_evidence(self.trial)["complete"])

    def test_running_summary_is_incomplete(self):
        self.fixture()
        self.write("method/summary.json", {"status": "running", "model_requests": 0})
        self.assertFalse(runtime_evidence(self.trial)["complete"])


if __name__ == "__main__":
    unittest.main()
