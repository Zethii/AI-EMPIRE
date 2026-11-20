"""Local JSON task storage for AI-EMPIRE. No database or dependencies required."""
from __future__ import annotations
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TASKS_DIR = ROOT / "data" / "tasks"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def save_plan(plan: dict[str, Any], original_request: str) -> Path:
    """Save a proposed plan as a uniquely identified local task record."""
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    task_id = "TASK-" + uuid.uuid4().hex[:10].upper()
    requires_approval = bool(plan.get("requires_human_approval", False))
    record = {
        "task_id": task_id,
        "title": plan["task_title"],
        "description": plan["goal"],
        "original_request": original_request,
        "status": "PLANNED",
        "priority": "normal",
        "created_at": _now(),
        "updated_at": _now(),
        "approval_required": requires_approval,
        "approval_status": "pending" if requires_approval else "not_required",
        "execution_enabled": False,
        "plan": plan,
    }
    destination = TASKS_DIR / (task_id + ".json")
    destination.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return destination

def list_tasks() -> list[dict[str, Any]]:
    """Return saved task records, newest first."""
    if not TASKS_DIR.exists():
        return []
    records = []
    for path in TASKS_DIR.glob("TASK-*.json"):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return sorted(records, key=lambda item: item.get("created_at", ""), reverse=True)

def get_task(task_id: str) -> dict[str, Any] | None:
    """Find one task by its exact ID."""
    if not re.fullmatch(r"TASK-[A-F0-9]{10}", task_id):
        return None
    path = TASKS_DIR / (task_id + ".json")
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
