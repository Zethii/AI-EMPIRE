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

Hierarchy: GPT-6.2 Astra drafts; all seven reviewers critique that same draft independently; then the lead opens a discussion where every reviewer responds in turn to all reviews and earlier discussion; finally, the lead suggests an ordered plan using the full exchange. Reviewers are Claude Opus 5.5, Gemini 4 Neon, Grok 4.7, DeepSeek V4.1 Flash, Qwen4 Max, GLM 5.3 and Claude Fable 5.2. The full capability registry in config/model_skills.json is included in every model prompt so each model can use the team’s strengths. These profiles guide review focus; they do not grant API tools. All models route through OpenRouter; direct provider API connections are not implemented yet.

Run from the repository root:
    python3 orchestrator/collaboration.py "Compare three digital product ideas for gaming editors"

Select a different reviewer panel:
    python3 orchestrator/collaboration.py "Review this plan" --lead openai/gpt-6.2-astra --reviewers qwen/qwen4-max,z-ai/glm-5.3,anthropic/claude-fable-5.2

Use --json for structured output. The default run makes seventeen model requests (one draft, seven reviews, eight discussion turns and the final plan). The normal output shows every model review and discussion turn before the final plan. If a model call fails for lack of credits, the run pauses and does not start the next stage or produce a final plan until all inputs have succeeded. Sharing the registry adds input tokens to each request, so check current model availability and pricing before running.

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
