"""Offline tests for hybrid collaboration; no network or API key required."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "orchestrator"))
sys.path.insert(0, str(ROOT / "integrations" / "model-gateway"))
import collaboration
from client import GatewayError

CONFIG = {
    "models": {
        "lead": {"model_id": "openai/test-lead"},
        "reviewer_1": {"model_id": "anthropic/test-reviewer"},
        "reviewer_2": {"model_id": "google/test-reviewer"},
    },
    "default_reviewers": ["reviewer_1", "reviewer_2"],
}


class HybridCollaborationTests(unittest.TestCase):
    def test_load_config(self):
        self.assertEqual(collaboration.load_config()["mode"], "hybrid")

    @patch.object(collaboration, "ask")
    def test_lead_review_synthesis_sequence(self, mocked):
        mocked.side_effect = ["draft", "critique one", "critique two", "final"]
        result = collaboration.run_hybrid("Test task", config=CONFIG)
        self.assertEqual(mocked.call_count, 4)
        self.assertEqual(result["final"], "final")
        self.assertEqual([r["status"] for r in result["reviewers"]],
                         ["completed", "completed"])

    @patch.object(collaboration, "ask")
    def test_reviewer_failure_is_reported(self, mocked):
        mocked.side_effect = ["draft", GatewayError("unavailable"),
                              "critique two", "final"]
        result = collaboration.run_hybrid("Test task", config=CONFIG)
        self.assertEqual(result["reviewers"][0]["status"], "failed")
        self.assertEqual(result["reviewers"][1]["status"], "completed")

    def test_blank_task_rejected(self):
        with self.assertRaisesRegex(ValueError, "blank"):
            collaboration.run_hybrid(" ", config=CONFIG)

    def test_lead_cannot_review_itself(self):
        with self.assertRaisesRegex(ValueError, "different"):
            collaboration.run_hybrid("task", config=CONFIG, lead_model="same",
                                     reviewer_models=["same"])

    def test_small_token_budget_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least 256"):
            collaboration.run_hybrid("task", config=CONFIG, max_tokens=100)


if __name__ == "__main__":
    unittest.main()
