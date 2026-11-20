# Task Manager

## Current implementation

AI-EMPIRE can save planning results as local JSON task records without installing a database or third-party Python packages.

- `task_store.py` — creates, lists, and retrieves task records.
- `task_manager.py` — command-line interface for listing and inspecting saved tasks.
- `task.schema.json` — initial task data contract.
- Local records are stored in `data/tasks/`, which is excluded from Git because task descriptions may contain private information.

## Create and save a plan

From the repository root:

```bash
python3 command-center/executive-agent/orchestrator.py --save "Research demand for a digital product targeting gaming editors"
```

The orchestrator prints the plan and its generated task ID/path. Saving a plan does not execute it.

## List saved tasks

```bash
python3 command-center/task-manager/task_manager.py list
```

## Inspect a task

```bash
python3 command-center/task-manager/task_manager.py show TASK-XXXXXXXXXX
```

Replace the example ID with the actual ID printed when the plan was saved.

## Boundaries

- Local JSON storage only; this is not yet a shared database or cloud memory.
- Task status remains `PLANNED`; no execution or agent delegation occurs.
- Records are not synchronized between devices.
- Never commit the local `data/tasks/` directory.
