"""Offline checks for isolation records and timeout cleanup; no model requests."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from repair_codex import run_codex, validate_endpoint


class RunnerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.auth = self.root / "auth"
        self.auth.mkdir()
        (self.auth / "auth.json").write_text('{"fake":true}')
        self.binary = self.root / "codex-fake"

    def tearDown(self):
        self.temp.cleanup()

    def fake(self, code):
        self.binary.write_text('#!/usr/bin/python3\n' + code)
        self.binary.chmod(0o700)

    def run_fake(self, seconds=5):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "must-not-leak", "PRIVATE_VALUE": "must-not-leak"}):
            return run_codex("Test only", self.root / "result", wall_seconds=seconds,
                             binary=self.binary, auth_home=self.auth)

    def test_fresh_context_and_known_usage(self):
        self.fake('''import os, json, pathlib, sys
assert "OPENAI_API_KEY" not in os.environ
assert "PRIVATE_VALUE" not in os.environ
assert sorted(p.name for p in pathlib.Path.cwd().iterdir()) == ["game.py", "task.md"]
assert sorted(p.name for p in pathlib.Path(os.environ["CODEX_HOME"]).iterdir()) == ["auth.json"]
assert pathlib.Path.cwd().parent.parent.name == "isolated-factorio"
assert "--ephemeral" in sys.argv and "--ignore-user-config" in sys.argv
print(json.dumps({"type":"thread.started","thread_id":"fresh"}))
print(json.dumps({"type":"turn.completed","usage":{"input_tokens":12,"output_tokens":3,"cached_input_tokens":2}}))
pathlib.Path(sys.argv[sys.argv.index("-o")+1]).write_text("done")
''')
        result = self.run_fake()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["usage"]["input_tokens"], 12)
        workspace = Path(result["command"][result["command"].index("-C") + 1])
        self.assertFalse(workspace.exists())
        self.assertFalse((self.root / "result/auth").exists())
        with self.assertRaises(FileExistsError):
            self.run_fake()

    def test_timeout_keeps_events_and_stops(self):
        self.fake('import time\nprint(\'{"type":"thread.started","thread_id":"timeout"}\', flush=True)\ntime.sleep(10)\n')
        result = self.run_fake(1)
        self.assertEqual(result["status"], "timeout")
        self.assertEqual(result["usage"]["thread_id"], "timeout")
        self.assertIsNone(result["usage"]["input_tokens"])
        self.assertLess(result["wall_seconds"], 3)
        with self.assertRaises(ProcessLookupError):
            os.kill(result["pid"], 0)

    def test_failed_event_cannot_count_as_completion(self):
        self.fake('print(\'{"type":"turn.failed","error":{"message":"test"}}\')\n')
        self.assertEqual(self.run_fake()["status"], "infrastructure_failure")

    def test_reject_nonlocal_and_admin_endpoints(self):
        for endpoint in ("http://example.com/action", "http://127.0.0.1:8000/admin", "http://a@127.0.0.1:8000/action"):
            with self.assertRaises(ValueError):
                validate_endpoint(endpoint)
        validate_endpoint("http://127.0.0.1:8000/action")


if __name__ == "__main__":
    unittest.main()
