# Executive Agent

**Role:** coordinate AI-EMPIRE execution.

## First runnable milestone: planning-only orchestrator

`orchestrator.py` accepts one task description and asks the configured model gateway to return a structured execution plan.

Run from the repository root:

```bash
python3 command-center/executive-agent/orchestrator.py "Research demand for a digital product for gaming editors"
```

The output is a JSON plan with a goal, assumptions, 3–7 proposed steps, suggested specialist roles, dependencies, risks, and approval flags.

## Current boundaries

- Planning only: it does not execute steps or call external tools.
- It does not assign tasks to live agents; agent roles are suggestions.
- The output is validated for required fields and step count.
- Human review is required before any future execution layer is enabled.
- Publishing, sending messages, purchases, spending, deletion, private-data sharing, and production changes must have explicit human approval.

## Responsibilities

Understand requests, make plans, delegate, track progress, reconcile disagreements, request approvals, and report verified outcomes.

**Current status:** first planning-only runtime implementation; specialist agents and execution are not yet active.
