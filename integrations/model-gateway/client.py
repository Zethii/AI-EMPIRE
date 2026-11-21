"""Dependency-free OpenRouter gateway client."""
from __future__ import annotations
import json, os, urllib.error, urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openrouter/free"


class GatewayError(RuntimeError):
    """Safe gateway error."""


def load_local_env():
    p = ROOT / ".env"
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def chat_completion(messages: list[dict[str, Any]], *, model: str | None = None,
                    temperature: float = 0.2, max_tokens: int = 500) -> dict[str, Any]:
    load_local_env()
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise GatewayError("OPENROUTER_API_KEY is missing. Add it to local .env.")
    payload = {
        "model": model or os.getenv("AI_EMPIRE_MODEL") or DEFAULT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Zethii/AI-EMPIRE",
            "X-Title": "AI-EMPIRE",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read(1000).decode("utf-8", errors="replace")
        except Exception:
            detail = "No details"
        raise GatewayError(f"OpenRouter HTTP {exc.code}: {detail}") from None
    except urllib.error.URLError as exc:
        raise GatewayError(f"Network error: {exc.reason}") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise GatewayError("Gateway returned invalid JSON.") from None
    if not isinstance(data, dict) or not isinstance(data.get("choices"), list) or not data["choices"]:
        raise GatewayError("Gateway response contained no choices.")
    return data


def extract_message_text(content: Any) -> str:
    """Extract only user-facing text, never hidden reasoning or tool arguments."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                # OpenAI-compatible text blocks and common provider variants.
                for field in ("text", "content"):
                    value = item.get(field)
                    if isinstance(value, str) and value.strip():
                        parts.append(value.strip())
                        break
        return "\n".join(part for part in parts if part.strip()).strip()
    return ""


def message_text(response: dict[str, Any]) -> str:
    try:
        choice = response["choices"][0]
        message = choice.get("message") or {}
    except (KeyError, IndexError, TypeError, AttributeError):
        raise GatewayError("Response has no assistant message.") from None

    content = message.get("content")
    text = extract_message_text(content)
    if text:
        return text

    # Some OpenAI-compatible providers expose a top-level text field.
    fallback = choice.get("text")
    if isinstance(fallback, str) and fallback.strip():
        return fallback.strip()

    # A refusal is visible assistant text and is safe to surface.
    refusal = message.get("refusal")
    if isinstance(refusal, str) and refusal.strip():
        return refusal.strip()

    # Give actionable, non-sensitive diagnostics without printing response bodies,
    # prompts, headers, tool arguments, or credentials.
    finish_reason = choice.get("finish_reason") or "not supplied"
    message_keys = ",".join(sorted(str(key) for key in message.keys())) or "none"
    if message.get("tool_calls"):
        detail = "The model attempted a tool call, but this request supplied no executable tools."
    elif message.get("audio") or message.get("images"):
        detail = "The response appears to contain non-text media."
    else:
        detail = "The provider returned an empty or unsupported assistant content format."
    if finish_reason == "length":
        guidance = (
            "The model exhausted its token budget before producing readable text. "
            "Increase --max-tokens or select a text-capable model with a larger output limit."
        )
    else:
        guidance = "Try another text-capable model or inspect the provider response format."
    raise GatewayError(
        f"Model returned no readable text ({detail} "
        f"finish_reason={finish_reason}; message_fields={message_keys}). {guidance}"
    )


def ask(prompt: str, *, model: str | None = None) -> str:
    return message_text(chat_completion([{"role": "user", "content": prompt}], model=model))
