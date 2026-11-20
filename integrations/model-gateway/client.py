"""Reusable, dependency-free OpenRouter client for AI-EMPIRE.

Configuration:
  OPENROUTER_API_KEY (required)
  AI_EMPIRE_MODEL (optional; defaults to openrouter/free)

Keep credentials in the local, Git-ignored .env file. Never commit secrets.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openrouter/free"


class GatewayError(RuntimeError):
    """Raised when the gateway request fails or returns an invalid response."""


def load_local_env() -> None:
    """Load simple KEY=VALUE entries from the repository's .env file."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def chat_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 500,
) -> dict[str, Any]:
    """Send chat messages and return the decoded OpenRouter response."""
    load_local_env()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise GatewayError(
            "OPENROUTER_API_KEY is missing. Add it to the local .env file."
        )

    selected_model = model or os.getenv("AI_EMPIRE_MODEL") or DEFAULT_MODEL
    payload = {
        "model": selected_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Zethii/AI-EMPIRE",
            "X-Title": "AI-EMPIRE",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Do not print request headers or credentials.
        detail = exc.read().decode("utf-8", errors="replace")
        raise GatewayError(f"OpenRouter returned HTTP {exc.code}: {detail[:1000]}") from None
    except urllib.error.URLError as exc:
        raise GatewayError(f"Could not reach OpenRouter: {exc.reason}") from None
    except json.JSONDecodeError:
        raise GatewayError("OpenRouter returned an unreadable JSON response.") from None

    try:
        result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise GatewayError("OpenRouter response did not contain a chat message.") from None
    return result


def ask(prompt: str, *, model: str | None = None) -> str:
    """Convenience helper for a single user prompt."""
    result = chat_completion(
        [{"role": "user", "content": prompt}],
        model=model,
    )
    content = result["choices"][0]["message"]["content"]
    return content if isinstance(content, str) else json.dumps(content)
