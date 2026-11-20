#!/usr/bin/env python3
"""Small, dependency-free smoke test for AI-EMPIRE's OpenRouter connection.

Reads OPENROUTER_API_KEY from the process environment or a local .env file.
Never print the API key.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.getenv("AI_EMPIRE_TEST_MODEL", "openrouter/free")


def load_local_env():
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def main():
    load_local_env()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Missing OPENROUTER_API_KEY. Add it to your local .env file.")
        sys.exit(1)

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Reply with exactly: AI-EMPIRE connection successful"
            }
        ],
        "temperature": 0,
        "max_tokens": 80,
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Zethii/AI-EMPIRE",
            "X-Title": "AI-EMPIRE Connection Test",
        },
        method="POST",
    )

    print(f"Sending smoke test to OpenRouter (model: {MODEL})...")
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
        answer = data["choices"][0]["message"]["content"]
        print("\nModel response:")
        print(answer)
        print("\nSUCCESS: AI-EMPIRE received a response from OpenRouter.")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"OpenRouter returned HTTP {exc.code}.")
        print(body[:1200])
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"Connection failed: {exc.reason}")
        sys.exit(1)
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        print(f"Unexpected response format: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
