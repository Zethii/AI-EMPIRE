#!/usr/bin/env python3
"""AI-EMPIRE v0.1 executive orchestrator: turn one request into a reviewable plan.

This version plans only. It does not execute subtasks, use tools, or take external actions.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GATEWAY_DIR = ROOT / "integrations" / "model-gateway"
sys.path.insert(0, str(GATEWAY_DIR))

from client import GatewayError, chat_completion  # noqa: E402


SYSTEM_PROMPT = """You are the planning component of AI-EMPIRE.
Convert the user's request into a safe, practical execution plan.
Return ONLY one valid JSON object with this exact structure:
{
  "task_title": "short title",
  "goal": "one or two sentence goal",
  "assumptions": ["assumption"],
  "steps": [
    {
      "step_id": "S1",
      "title": "short action",
      "description": "specific, actionable explanation",
      "suggested_agent": "research-specialist | strategist | developer | content-producer | quality-auditor",
      "depends_on": [],
      "approval_required": false
    }
  ],
  "risks": ["risk or uncertainty"],
  "requires_human_approval": false
}
Create 3 to 7 ordered steps. Use dependencies such as ["S1"] only when needed.
Set approval_required true for steps involving publishing, sending messages, purchases,
spending money, deleting data, sharing private information, or production changes.
Never claim a step has been completed. Do not invent access, facts, or capabilities.
If the request is ambiguous, list assumptions rather than pretending certainty.
The plan is a proposal for the human to review, not permission to execute it."""


def extract_json(content: Any) -> dict[str, Any]:
    if not isinstance(content, str):
        raise ValueError("Model returned a non-text response.")
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Model response did not contain a JSON object.")
    data = json.loads(text[start:end + 1])
    if not isinstance(data, dict):
        raise ValueError("Plan must be a JSON object.")
    return data


def validate_plan(plan: dict[str, Any]) -> None:
    required = {"task_title", "goal", "steps", "requires_human_approval"}
    missing = required - plan.keys()
    if missing:
        raise ValueError("Plan is missing fields: " + ", ".join(sorted(missing)))
    if not isinstance(plan["steps"], list) or not 3 <= len(plan["steps"]) <= 7:
        raise ValueError("Plan must contain between 3 and 7 steps.")
    for index, step in enumerate(plan["steps"], start=1):
        if not isinstance(step, dict):
            raise ValueError(f"Step {index} is not an object.")
        for field in ("step_id", "title", "description", "suggested_agent", "depends_on", "approval_required"):
            if field not in step:
                raise ValueError(f"Step {index} is missing '{field}'.")
        if not isinstance(step["depends_on"], list):
            raise ValueError(f"Step {index} dependencies must be a list.")
        if not isinstance(step["approval_required"], bool):
            raise ValueError(f"Step {index} approval_required must be true or false.")
    if not isinstance(plan["requires_human_approval"], bool):
        raise ValueError("requires_human_approval must be true or false.")


def create_plan(user_request: str, model: str | None = None) -> dict[str, Any]:
    response = chat_completion(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_request},
        ],
        model=model,
        temperature=0.1,
        max_tokens=1400,
    )
    content = response["choices"][0]["message"]["content"]
    plan = extract_json(content)
    validate_plan(plan)
    plan["status"] = "PLANNED"
    plan["execution_enabled"] = False
    return plan


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python3 command-center/executive-agent/orchestrator.py "Describe your task"')
        raise SystemExit(2)
    user_request = " ".join(sys.argv[1:]).strip()
    if not user_request:
        print("Please provide a task description.")
        raise SystemExit(2)
    try:
        plan = create_plan(user_request)
    except (GatewayError, ValueError, json.JSONDecodeError) as exc:
        print(f"Could not create a valid plan: {exc}")
        raise SystemExit(1)
    print(json.dumps(plan, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
