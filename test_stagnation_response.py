from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / ".github" / "scripts" / "campaign_controller.py"
spec = importlib.util.spec_from_file_location("campaign_controller_stagnation_test", TARGET)
assert spec is not None and spec.loader is not None
MODULE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MODULE)


class StagnationResponseTests(unittest.TestCase):
    def _root_with_progress(self, streak: int) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "state/research").mkdir(parents=True)
        (root / "state/research/PROGRESS.json").write_text(
            json.dumps({
                "benchmark_freshness": "FRESH",
                "consecutive_non_improving_evaluations": streak,
            }),
            encoding="utf-8",
        )
        return root

    def test_first_flat_evaluation_prioritizes_distinct_method_at_campaign_start(self):
        root = self._root_with_progress(1)
        task, candidates, _ = MODULE.build_task(11, root, root / "state/campaign", 11)
        self.assertEqual(task["task_id"].split("-")[2], "stagnation")
        self.assertEqual(task["stagnation_gate"]["required_response"], "DISTINCT_METHOD_OR_METRIC_READINESS_REVIEW")
        self.assertEqual(candidates[0]["task_id"], task["task_id"])
        self.assertEqual(MODULE.validate_task(task), [])

    def test_second_flat_evaluation_prioritizes_policy_pivot(self):
        root = self._root_with_progress(2)
        task, candidates, _ = MODULE.build_task(11, root, root / "state/campaign", 11)
        self.assertEqual(task["stagnation_gate"]["required_response"], "POLICY_PIVOT")
        self.assertEqual(candidates[0]["task_id"], task["task_id"])
        self.assertEqual(MODULE.validate_task(task), [])

    def test_stagnation_response_does_not_override_mid_campaign_tasks(self):
        root = self._root_with_progress(2)
        task, _, _ = MODULE.build_task(12, root, root / "state/campaign", 11)
        self.assertNotIn("stagnation_gate", task)

    def test_zero_streak_keeps_default_task_selection(self):
        root = self._root_with_progress(0)
        task, _, _ = MODULE.build_task(11, root, root / "state/campaign", 11)
        self.assertNotIn("stagnation_gate", task)


if __name__ == "__main__":
    unittest.main()
