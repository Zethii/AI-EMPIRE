# AI-EMPIRE Architecture

This describes the current MVP and intended direction. Candidate services are not installed or verified unless stated.

## Request flow
1. User submits a task.
2. Executive orchestrator interprets it and creates a plan.
3. Router selects a lead model and supporting reviewers based on task type, capability, cost and availability.
4. The lead produces a first draft.
5. Independent models review the same task and draft.
6. The lead synthesizes feedback, identifies disagreements and returns one result.
7. Specialist workflows can be added around this model collaboration layer.

## Model identities vs specialist agents
These are separate concepts:
- Models/providers: GPT (OpenAI), Claude (Anthropic), Gemini (Google), Grok (xAI) and other model families. Each has its own model ID and provider integration.
- Specialist agents: research, coding, writing, marketing, analysis and QA roles. An agent is a workflow/persona powered by a selected model.

A model is not the same thing as an agent role. The system should assign different models to the same role and different roles to different models.

## Hybrid collaboration pattern
- Lead model creates the first draft and final synthesis.
- Review models independently critique the draft and identify missing evidence, risks, alternatives and errors.
- Synthesis incorporates valid feedback and preserves unresolved disagreements.
- Reviewer failures are recorded and shown, not silently treated as successful reviews.
- Default: one lead plus two reviewers. Additional reviewers are optional.
- Initial transport: OpenRouter. These model IDs represent different model families routed through OpenRouter, not direct provider API connections.
- Current execution is sequential; parallel execution is a future optimization.

## Current MVP entry points
- Gateway: integrations/model-gateway/client.py
- Model roles: config/collaboration.json
- Hybrid runner: orchestrator/collaboration.py
- Tests: tests/test_collaboration.py

## Planned hierarchy
- Executive orchestrator: planning, delegation, synthesis, approval gates and final reporting.
- Division leads: Digital Business, YouTube/AI Media, Gaming, Software Development and Research.
- Specialists: research, writing, coding, analysis, production, SEO and automation.
- Auditors: critique, fact-check, test and identify gaps.

## Task lifecycle
REQUESTED -> PLANNED -> APPROVAL (if required) -> ASSIGNED -> RUNNING -> REVIEW -> REVISION -> VERIFIED -> DELIVERED

Tasks may also become BLOCKED, FAILED or CANCELLED.

## Safety
- Never commit credentials or expose secrets in logs.
- Validate inputs and external responses.
- Use timeouts and bounded retries.
- Treat model output as untrusted input; do not execute it automatically.
- Require approval for publishing, purchases, deletion, production changes and external communications.
- Fact-check important outputs and state uncertainty.
- Never claim an external action succeeded without confirmation.

## Future infrastructure
| Layer | Candidate | Purpose | State |
|---|---|---|---|
| Model gateway | OpenRouter | Initial multi-model routing | Basic connection tested by user |
| Direct provider adapters | OpenAI, Anthropic, Google, xAI | Optional direct API routes | Not implemented |
| Automation | n8n | Scheduled/event-driven workflows | Research pending |
| Database/memory | PostgreSQL/Supabase | Shared task data and memory | Research pending |
| Version control | GitHub | Code, docs and configuration | Repository created |
