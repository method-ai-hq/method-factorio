"""Report checks use synthetic run files, never model or game calls."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from repair_report import compare, group, summarize


def fixture(kind="direct", *, passed=True):
    return {"case_id": "development-001", "kind": kind, "status": "pass" if passed else "fail",
            "scored_pass": passed, "case_sha256": "case", "task_sha256": "task", "actions": 3,
            "game_wall_seconds": 20, "total_wall_seconds": 25,
            "verdict": {"windows": [{"passed": True}] * 3,
                        "verification": {"saved_state_matches": True, "saved_record_matches": True,
                                         "native_initial_matches": True, "source_matches": True,
                                         "finish_is_last_action": True},
                        "checks": {"no_play_after_finish": passed}},
            "execution": {"status": "completed", "usage": {"usage_known": True, "input_tokens": 100,
                           "cached_input_tokens": 20, "output_tokens": 10}}}


def write_run(root, result):
    path = root / "summary.json"
    path.write_text(json.dumps(result))
    return path


class ReportUsageTests(unittest.TestCase):
    def test_exact_recipe_review_is_used_and_stale_review_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = write_run(root, fixture(passed=False))
            original = path.read_bytes()
            reviewed = fixture(passed=True)
            reviewed.update(review_contract="repair-recipe-export/2",
                            raw_summary_sha256=hashlib.sha256(original).hexdigest(),
                            raw_record_sha256="record", save_sha256="save", source_sha256="reader",
                            corrections=[], legacy_scored_pass=False)
            (root / "review.json").write_text(json.dumps(reviewed))
            self.assertTrue(summarize(path)["strict_pass"])
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(group([path])["recipe_reviewed_attempts"], 1)
            path.write_bytes(original + b"\n")
            with self.assertRaisesRegex(ValueError, "does not match"):
                summarize(path)

    def test_missing_child_execution_counted_with_unknown_usage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = fixture("method")
            result["execution"] = {"status": "timeout", "codex_runs": []}
            child = root / "method/codex/unfinished"
            child.mkdir(parents=True)
            (child / "process.json").write_text('{"pid":123}')
            row = summarize(write_run(root, result))
            self.assertEqual(row["agent_sessions"], 1)
            self.assertEqual(row["sessions_missing_execution"], 1)
            self.assertEqual(row["sessions_without_final_usage"], 1)
            self.assertIsNone(row["known_input_tokens"])
            self.assertIsNone(row["total_input_tokens"])
            summary = group([root / "summary.json"])
            self.assertIsNone(summary["known_output_tokens"])
            self.assertIsNone(summary["total_output_tokens"])

    def test_partial_timeout_usage_is_lower_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = fixture(passed=False)
            result["execution"]["status"] = "timeout"
            row = summarize(write_run(root, result))
            self.assertEqual(row["known_input_tokens"], 100)
            self.assertEqual(row["sessions_with_known_usage"], 1)
            self.assertEqual(row["sessions_without_final_usage"], 1)
            self.assertIsNone(row["total_input_tokens"])
            self.assertFalse(row["usage_complete"])

    def test_complete_and_missing_method_children_are_counted_once(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = fixture("method")
            complete = copy.deepcopy(result["execution"])
            result["execution"] = {"status": "timeout", "codex_runs": [complete]}
            for name in ("complete", "missing"):
                (root / "method/codex" / name).mkdir(parents=True)
            (root / "method/codex/complete/execution.json").write_text(json.dumps(complete))
            row = summarize(write_run(root, result))
            self.assertEqual(row["agent_sessions"], 2)
            self.assertEqual(row["known_input_tokens"], 100)
            self.assertEqual(row["sessions_without_final_usage"], 1)
            self.assertIsNone(row["total_input_tokens"])

    def test_full_usage_has_complete_totals(self):
        with tempfile.TemporaryDirectory() as temp:
            row = summarize(write_run(Path(temp), fixture()))
            self.assertTrue(row["usage_complete"])
            self.assertEqual(row["total_input_tokens"], 100)

    def test_group_full_time_median_uses_successful_attempts_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = []
            for index, (passed, game_time, total_time) in enumerate(((True, 10, 100), (True, 30, 200), (False, 999, 999))):
                folder = root / str(index)
                folder.mkdir()
                result = fixture(passed=passed)
                result.update(case_id=str(index), game_wall_seconds=game_time, total_wall_seconds=total_time)
                paths.append(write_run(folder, result))
            report = group(paths)
            self.assertEqual(report["median_success_seconds"], 20)
            self.assertEqual(report["median_success_total_seconds"], 150)
            self.assertEqual(report["successful_attempts_missing_total_time"], 0)

    def test_protocol_failure_keeps_production_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = fixture(passed=False)
            result["verdict"]["verification"]["finish_is_last_action"] = False
            row = summarize(write_run(root, result))
            self.assertFalse(row["strict_pass"])
            self.assertTrue(row["restored_production"])
            self.assertEqual(row["failure"], "request_rule")
            result["verdict"]["verification"]["saved_state_matches"] = False
            row = summarize(write_run(root, result))
            self.assertFalse(row["restored_production"])


class PairTests(unittest.TestCase):
    def row(self, case, seconds=20, passed=True):
        return {"case_id": case, "case_sha256": case + "hash", "task_sha256": "task",
                "strict_pass": passed, "game_wall_seconds": seconds}

    def test_pairing_mismatch_and_missing_binding_rejected(self):
        base = {"rows": [self.row("a")]}
        for other in ({"rows": [self.row("b")]}, {"rows": [self.row("a"), self.row("a")]},
                      {"rows": [{**self.row("a"), "case_sha256": "changed"}]},
                      {"rows": [{**self.row("a"), "task_sha256": None}]}):
            with self.subTest(other=other), self.assertRaises(ValueError):
                compare(base, other)
        with self.assertRaises(ValueError):
            compare({"rows": [{**self.row("a"), "case_sha256": None}]},
                    {"rows": [{**self.row("a"), "case_sha256": None}]})

    def test_partial_progress_is_explicit_and_has_no_p_value(self):
        result = compare({"rows": [self.row("a"), self.row("b")]},
                         {"rows": [self.row("a"), self.row("c")]}, allow_partial=True)
        self.assertTrue(result["partial_comparison"])
        self.assertEqual(result["paired_cases"], 1)
        self.assertEqual(result["unmatched_direct_cases"], ["b"])
        self.assertEqual(result["unmatched_method_cases"], ["c"])
        self.assertIsNone(result["exact_paired_two_sided_p"])

    def test_time_metrics_use_only_common_passes(self):
        direct = {"rows": [self.row("a", 20), self.row("b", 60), self.row("c", 500)]}
        method = {"rows": [self.row("a", 10), self.row("b", 20), self.row("c", 1, False)]}
        result = compare(direct, method)
        self.assertEqual(result["both_pass"], 2)
        self.assertEqual(result["direct_only"], 1)
        self.assertEqual(result["common_success_direct_median_seconds"], 40)
        self.assertEqual(result["common_success_method_median_seconds"], 15)
        self.assertEqual(result["common_success_median_speed_ratio"], 2.5)

    def test_full_time_metrics_are_separate_from_game_time(self):
        direct = {"rows": [{**self.row("a", 20), "total_wall_seconds": 120},
                           {**self.row("b", 60), "total_wall_seconds": 300},
                           {**self.row("c", 500), "total_wall_seconds": 999}]}
        method = {"rows": [{**self.row("a", 10), "total_wall_seconds": 40},
                           {**self.row("b", 20), "total_wall_seconds": 60},
                           {**self.row("c", 1, False), "total_wall_seconds": 2}]}
        result = compare(direct, method)
        self.assertEqual(result["common_success_median_speed_ratio"], 2.5)
        self.assertEqual(result["common_success_direct_total_median_seconds"], 210)
        self.assertEqual(result["common_success_method_total_median_seconds"], 50)
        self.assertEqual(result["common_success_median_total_speed_ratio"], 4)
        self.assertEqual(result["common_success_total_timed_pairs"], 2)

    def test_missing_full_time_stays_unknown(self):
        result = compare({"rows": [self.row("a")]}, {"rows": [self.row("a")]})
        self.assertEqual(result["common_success_pairs_missing_total_time"], 1)
        self.assertIsNone(result["common_success_direct_total_median_seconds"])
        self.assertIsNone(result["common_success_median_total_speed_ratio"])

    def test_missing_or_zero_time_does_not_create_a_ratio(self):
        result = compare({"rows": [self.row("a", None), self.row("b", 30)]},
                         {"rows": [self.row("a", 10), self.row("b", 0)]})
        self.assertEqual(result["common_success_pairs_missing_time"], 2)
        self.assertIsNone(result["common_success_median_speed_ratio"])


if __name__ == "__main__":
    unittest.main()
