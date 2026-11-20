# Model Gateway Integration

## Initial gateway: OpenRouter

OpenRouter is the first working gateway integration for the AI-EMPIRE proof of concept. It provides one API endpoint through which the project can request responses from supported models.

## Current implementation

- `client.py` — reusable, dependency-free Python client.
- `openrouter_test.py` — smoke test that sends a prompt and prints the model response.
- `OPENROUTER_API_KEY` — required local secret, stored in the repository-root `.env` file.
- `AI_EMPIRE_MODEL` — optional default model override.
- `AI_EMPIRE_TEST_MODEL` — optional model override for the smoke test.

Default model: `openrouter/free`. Availability and behavior depend on OpenRouter's current free-model routing. A successful request does not by itself prove that every model is free or available.

## Run the connection test

From the repository root:

```bash
python3 integrations/model-gateway/openrouter_test.py
```

## Use the client from Python

When importing from a script in this directory:

```python
from client import ask

reply = ask("Explain the task in simple terms.")
print(reply)
```

For other project modules, import through a package structure once the application runtime is established. This initial adapter intentionally has no third-party Python dependencies.

## Security and reliability guardrails

- Keep provider API keys in the local, Git-ignored `.env` file or an appropriate secret store.
- Never commit keys or paste them into issues, pull requests, logs, or screenshots.
- Do not log authorization headers or API keys.
- Use bounded timeouts and handle provider errors.
- Treat model output as untrusted input; do not execute it automatically.
- Require human approval for publishing, sending messages, spending money, deleting data, or production changes.
- Check tool/function-calling support per model before assigning tool tasks.
- Keep the internal interface provider-neutral so the gateway can be replaced.

## Verification boundary

The first live OpenRouter smoke test succeeded on the user's Mac. This verifies basic API connectivity only. Model selection, usage/cost controls, retries, tool calling, multi-agent orchestration, and production readiness have not yet been verified.

## Next

Add a provider-neutral gateway interface and model-selection policy, then connect the gateway to the task orchestrator.
