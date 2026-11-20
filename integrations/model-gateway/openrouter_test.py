#!/usr/bin/env python3
"""Smoke test for the reusable AI-EMPIRE OpenRouter client."""
import os
import sys

from client import GatewayError, ask, load_local_env


def main() -> None:
    load_local_env()
    model = os.getenv("AI_EMPIRE_TEST_MODEL") or os.getenv("AI_EMPIRE_MODEL") or "openrouter/free"
    print(f"Sending smoke test to OpenRouter (model: {model})...")
    try:
        answer = ask(
            "Reply with exactly: AI-EMPIRE connection successful",
            model=model,
        )
    except GatewayError as exc:
        print(f"Connection test failed: {exc}")
        sys.exit(1)

    print("\nModel response:")
    print(answer)
    print("\nSUCCESS: AI-EMPIRE received a response from OpenRouter.")


if __name__ == "__main__":
    main()
