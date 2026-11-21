"""Offline gateway parser and approval heuristic tests; no API calls."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "integrations" / "model-gateway"))
sys.path.insert(0, str(ROOT / "command-center" / "executive-agent"))
from client import extract_message_text, message_text, GatewayError
from orchestrator import extract_json, validate_plan


class GatewayParsing(unittest.TestCase):
    def test_string(self):
        self.assertEqual(extract_message_text("plain"), "plain")

    def test_text_blocks(self):
        self.assertEqual(
            extract_message_text([{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]),
            "a\nb",
        )

    def test_content_blocks_with_content_field(self):
        self.assertEqual(
            extract_message_text([{"type": "output_text", "content": "visible answer"}]),
            "visible answer",
        )

    def test_nontext_empty(self):
        self.assertEqual(extract_message_text([{"type": "image"}]), "")

    def test_tool_only_response_has_actionable_error(self):
        response = {"choices": [{"finish_reason": "tool_calls", "message": {
            "content": None, "tool_calls": [{"id": "call_1"}]
        }}]}
        with self.assertRaisesRegex(GatewayError, "attempted a tool call"):
            message_text(response)

    def test_empty_message_error(self):
        with self.assertRaisesRegex(GatewayError, "no readable text"):
            message_text({"choices": [{"message": {"content": [{"type": "image"}]}}]})

    def test_top_level_choice_text_fallback(self):
        self.assertEqual(message_text({"choices": [{"text": "fallback text", "message": {}}]}), "fallback text")

    def test_refusal_text(self):
        self.assertEqual(
            message_text({"choices": [{"message": {"content": None, "refusal": "I cannot help with that."}}]}),
            "I cannot help with that.",
        )

    def test_json_markdown(self):
        self.assertEqual(extract_json('```json\n{"ok":true}\n```'), {"ok": True})


class PlanValidation(unittest.TestCase):
    def plan(self):
        return {"task_title": "demo", "goal": "demo", "requires_human_approval": False, "steps": [
            {"step_id": "S1", "title": "Read sources", "description": "research public information", "suggested_agent": "research-specialist", "depends_on": [], "approval_required": False},
            {"step_id": "S2", "title": "Draft survey", "description": "draft questions internally", "suggested_agent": "research-specialist", "depends_on": ["S1"], "approval_required": False},
            {"step_id": "S3", "title": "Distribute survey", "description": "distribute survey externally", "suggested_agent": "research-specialist", "depends_on": ["S2"], "approval_required": False},
        ]}

    def test_external_action_flag(self):
        p = self.plan()
        validate_plan(p)
        self.assertTrue(p["steps"][2]["approval_required"])
        self.assertTrue(p["requires_human_approval"])

    def test_no_external_action(self):
        p = self.plan()
        p["steps"][2]["title"] = "Analyze draft"
        p["steps"][2]["description"] = "Review internally"
        validate_plan(p)
        self.assertFalse(p["requires_human_approval"])

    def test_unknown_dep(self):
        p = self.plan()
        p["steps"][0]["depends_on"] = ["bad"]
        with self.assertRaises(ValueError):
            validate_plan(p)

    def test_duplicate_step_id(self):
        p = self.plan()
        p["steps"][1]["step_id"] = "S1"
        with self.assertRaises(ValueError):
            validate_plan(p)


if __name__ == "__main__":
    unittest.main()
