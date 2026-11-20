# Model Gateway Integration

## Candidate for first proof-of-concept: OpenRouter

Research notes: `docs/MODEL_GATEWAY_RESEARCH.md`.

This directory will hold gateway adapter notes, request/response contract, model selection and test results. Nothing is connected yet.

## Guardrails
- Keep provider API keys in local environment/secret storage only.
- Never commit keys or paste them into issues/PRs.
- Prefer pinned model IDs for reproducible tests; dynamic routing should be clearly labeled.
- Enforce request timeouts and bounded retries.
- Check tool/function calling support per model before assigning tool tasks.
- Maintain provider-neutral internal interfaces so gateways can be replaced.

## Next
Create a small, isolated test client only after the gateway is selected and credentials are locally configured. Test one free model, capture sanitized results, and verify zero-cost usage before expanding.
