# Model Gateway Integration

## Initial gateway: OpenRouter

OpenRouter is the first working gateway integration for the AI-EMPIRE proof of concept. It provides one API endpoint through which the project can request responses from supported models.

## Current implementation
- client.py — reusable, dependency-free Python client.
- openrouter_test.py — connection smoke test.
- OPENROUTER_API_KEY — required local secret in repository-root .env.
- AI_EMPIRE_MODEL — optional default model override.
- AI_EMPIRE_TEST_MODEL — optional smoke-test model override.
- orchestrator/collaboration.py — hybrid multi-model runner using this gateway.

## Multiple model families through one gateway
The hybrid MVP calls different model families using OpenRouter model IDs. GPT-6.2 Astra drafts, all seven configured reviewer models review the draft, then the lead and all reviewers take a discussion turn before GPT-6.2 Astra suggests the final plan. Claude, Gemini and Grok use OpenRouter rolling latest aliases; GPT-6.2 Astra and Qwen4 Max are pinned current flagship IDs. The shared capability registry at config/model_skills.json is included in every model prompt. The profiles describe review perspectives and do not grant API tools. Requests pass through OpenRouter and use the OpenRouter account/key. Direct provider APIs are a later integration.

See config/collaboration.json and the repository README for usage.

## Security and reliability
- Keep provider API keys in the local, Git-ignored .env file or an appropriate secret store.
- Never commit keys or paste them into issues, pull requests, logs or screenshots.
- Do not log authorization headers or API keys.
- Use bounded timeouts and handle provider errors.
- Treat model output as untrusted input; do not execute it automatically.
- Require human approval for publishing, sending messages, spending money, deleting data or production changes.
- Check tool/function-calling support per model before assigning tool tasks.
- Keep the internal interface provider-neutral.

## Verification boundary
The first live OpenRouter smoke test succeeded on the user's Mac. This verifies basic API connectivity only. The hybrid runner is implemented in GitHub, but local unit tests and live multi-model calls have not yet been verified.

## Next
Add model availability/cost checks, optional direct-provider adapters, and connect collaboration to task planning and specialist workflows.
