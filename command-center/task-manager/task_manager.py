#!/usr/bin/env python3
"""List and inspect AI-EMPIRE task records stored locally."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from task_store import get_task, list_tasks  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect locally saved AI-EMPIRE tasks.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List saved tasks.")
    show = sub.add_parser("show", help="Show one saved task by ID.")
    show.add_argument("task_id")
    args = parser.parse_args()

    if args.command == "list":
        tasks = list_tasks()
        if not tasks:
            print("No saved tasks yet.")
            return
        for task in tasks:
            print(f'{task["task_id"]} | {task["status"]} | {task["title"]}')
        return

    task = get_task(args.task_id.upper())
    if task is None:
        print("Task not found. Check the task ID and try again.")
        raise SystemExit(1)
    print(json.dumps(task, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
