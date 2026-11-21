# AI-EMPIRE

AI-EMPIRE is a modular multi-model AI workspace designed to coordinate independent AI models and specialist workflows.

## Principles
- Free-first: begin with free/open-source options and disclose costs.
- Provider-flexible: avoid lock-in to one AI provider.
- Human-controlled: approval before risky or irreversible actions.
- Secure: keep secrets out of Git and logs.
- Verifiable: distinguish planned, attempted, tested and verified work.
- Incremental: build and test one phase at a time.

## Current implementation
- OpenRouter model gateway (integrations/model-gateway/client.py).
- Hybrid multi-model collaboration MVP (orchestrator/collaboration.py).
- Configurable model roles (config/collaboration.json).
- Research Specialist MVP and web-search fallback.
- Offline unit tests for gateway parsing, planning and collaboration.

## Hybrid collaboration
1. A lead model produces the first draft.
2. Independent models review the same task and draft.
3. The lead synthesizes feedback into one final answer.
4. Failed reviewers are reported rather than silently ignored.

Initial roles: GPT lead, Claude and Gemini reviewers, Grok optional reviewer. Model IDs are configurable. All models currently route through OpenRouter; direct provider API connections are not implemented yet.

Run from the repository root:
    python3 orchestrator/collaboration.py "Compare three digital product ideas for gaming editors"

Include Grok or override model IDs:
    python3 orchestrator/collaboration.py "Review this plan" --lead openai/gpt-4.1 --reviewers anthropic/claude-sonnet-4,google/gemini-2.5-flash,x-ai/grok-3

Use --json for structured output. The default run makes three model requests (one lead draft, two reviews) plus a final synthesis request, so it can incur usage costs. Check current model availability and pricing before running.

Optional environment overrides:
- AI_EMPIRE_LEAD_MODEL
- AI_EMPIRE_REVIEWER_MODELS (comma-separated model IDs)

Keep OPENROUTER_API_KEY in the local ignored .env file. Never commit secrets.

## Safety boundaries
- Model outputs are untrusted text and are never executed automatically.
- This MVP does not give models tools or permission to publish, purchase, contact people, delete data or modify files.
- Human approval remains required for risky or irreversible actions.
- Calls are currently sequential, not parallel.

## Planned divisions
- Digital Business
- YouTube & AI Media
- Gaming Content
- Software Development
- Research & Intelligence

## Roadmap
1. [x] Create repository and foundation
2. [x] Implement initial OpenRouter gateway
3. [x] Implement hybrid multi-model collaboration MVP
4. [ ] Verify collaboration locally with available model IDs
5. [ ] Add direct-provider adapters and availability/cost checks
6. [ ] Connect collaboration to task planning and specialist agents
7. [ ] Add shared memory/database
8. [ ] Add approval-gated automation
9. [ ] Build dashboard

## Verification status
Changes are committed to GitHub. Local unit tests and live multi-model calls must still be run before this feature is considered verified.
