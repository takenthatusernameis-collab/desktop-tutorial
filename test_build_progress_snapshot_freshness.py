from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / ".github" / "scripts" / "build_progress_snapshot.py"
spec = importlib.util.spec_from_file_location("build_progress_snapshot_freshness_test", TARGET)
assert spec is not None and spec.loader is not None
MODULE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MODULE)


def valid_result(benchmark_id: str = "run-123") -> dict:
    return {
        "benchmark_id": benchmark_id,
        "commitment_verified": True,
        "ground_truth_exposed": False,
        "overall_score": 0.0,
        "discovery_rate": 0.0,
        "reproduction_rate": 0.0,
        "precision_component": 0.0,
        "evidence_quality": 0.0,
        "finding_count_submitted": 0,
        "reproduced_claim_count": 0,
        "unmatched_claim_count": 0,
    }


class EvaluationFreshnessTests(unittest.TestCase):
    def test_skipped_evaluation_is_not_evaluated_even_if_old_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "benchmark-run-123.json"
            path.write_text(json.dumps(valid_result()), encoding="utf-8")
            state, result, error = MODULE.load_evaluation_result(path, "skipped")
        self.assertEqual(state, "NOT_EVALUATED")
        self.assertEqual(result, {})
        self.assertIn("skipped", error)

    def test_success_with_missing_file_is_invalid_not_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "benchmark-run-123.json"
            state, result, error = MODULE.load_evaluation_result(path, "success")
        self.assertEqual(state, "INVALID_RESULT")
        self.assertEqual(result, {})
        self.assertIn("missing", error)

    def test_mismatched_result_id_is_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "benchmark-run-123.json"
            path.write_text(json.dumps(valid_result("old-run")), encoding="utf-8")
            state, _, error = MODULE.load_evaluation_result(path, "success")
        self.assertEqual(state, "STALE")
        self.assertIn("does not match", error)

    def test_malformed_json_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "benchmark-run-123.json"
            path.write_text("{not json", encoding="utf-8")
            state, _, _ = MODULE.load_evaluation_result(path, "success")
        self.assertEqual(state, "INVALID_RESULT")

    def test_missing_metric_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "benchmark-run-123.json"
            result = valid_result()
            result.pop("overall_score")
            path.write_text(json.dumps(result), encoding="utf-8")
            state, _, _ = MODULE.load_evaluation_result(path, "success")
        self.assertEqual(state, "INVALID_RESULT")

    def test_non_finite_metric_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "benchmark-run-123.json"
            result = valid_result()
            result["overall_score"] = math.inf
            path.write_text(json.dumps(result), encoding="utf-8")
            state, _, _ = MODULE.load_evaluation_result(path, "success")
        self.assertEqual(state, "INVALID_RESULT")

    def test_valid_fresh_result_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "benchmark-run-123.json"
            path.write_text(json.dumps(valid_result()), encoding="utf-8")
            state, result, error = MODULE.load_evaluation_result(path, "success")
        self.assertEqual(state, "FRESH")
        self.assertEqual(result["benchmark_id"], "run-123")
        self.assertIsNone(error)

    def test_flat_valid_evaluation_increments_streak_even_with_process_progress(self):
        previous = {
            "consecutive_non_improving_evaluations": 1,
            "benchmark": {"overall_score": 0.5},
        }
        self.assertEqual(
            MODULE.consecutive_non_improvement_count("FRESH", {"overall_score": 0.5}, previous),
            2,
        )

    def test_improvement_resets_streak(self):
        previous = {
            "consecutive_non_improving_evaluations": 4,
            "benchmark": {"overall_score": 0.5},
        }
        self.assertEqual(
            MODULE.consecutive_non_improvement_count("FRESH", {"overall_score": 0.52}, previous),
            0,
        )

    def test_skipped_or_invalid_evaluation_does_not_increment_streak(self):
        previous = {
            "consecutive_non_improving_evaluations": 2,
            "benchmark": {"overall_score": 0.5},
        }
        self.assertEqual(
            MODULE.consecutive_non_improvement_count("NOT_EVALUATED", {}, previous),
            2,
        )
        self.assertEqual(
            MODULE.consecutive_non_improvement_count("INVALID_RESULT", {}, previous),
            2,
        )


if __name__ == "__main__":
    unittest.main()
