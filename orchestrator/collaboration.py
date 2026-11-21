#!/usr/bin/env python3
"""Hybrid multi-model collaboration: lead draft, independent reviews, final synthesis."""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "integrations" / "model-gateway"))
from client import GatewayError, chat_completion, message_text


def load_config(path: Path | None = None) -> dict[str, Any]:
    path = path or ROOT / "config" / "collaboration.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"Collaboration config not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid collaboration config JSON: {exc}") from None
    if not isinstance(data, dict) or not isinstance(data.get("models"), dict):
        raise ValueError("Config must contain a models object.")
    return data


def model_id(config: dict[str, Any], role: str) -> str:
    item = config["models"].get(role)
    value = item.get("model_id") if isinstance(item, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing model_id for role {role!r}.")
    return value.strip()


def ask(model: str, prompt: str, max_tokens: int) -> str:
    response = chat_completion(
        [{"role": "user", "content": prompt}],
        model=model, temperature=0.2, max_tokens=max_tokens,
    )
    return message_text(response)


def run_hybrid(task: str, *, config: dict[str, Any] | None = None,
               lead_model: str | None = None,
               reviewer_models: list[str] | None = None,
               max_tokens: int = 1800) -> dict[str, Any]:
    task = task.strip()
    if not task:
        raise ValueError("Task cannot be blank.")
    if max_tokens < 256:
        raise ValueError("max_tokens must be at least 256.")
    config = config or load_config()
    lead = lead_model or os.getenv("AI_EMPIRE_LEAD_MODEL") or model_id(config, "lead")
    if reviewer_models is None:
        env_value = os.getenv("AI_EMPIRE_REVIEWER_MODELS", "").strip()
        reviewer_models = ([x.strip() for x in env_value.split(",") if x.strip()]
                           if env_value else
                           [model_id(config, role) for role in config.get(
                               "default_reviewers", ["reviewer_1", "reviewer_2"])])
    if not reviewer_models:
        raise ValueError("At least one reviewer model is required.")
    if lead in reviewer_models:
        raise ValueError("The lead model must be different from reviewer models.")

    draft_prompt = (
        "You are the lead model in AI-EMPIRE. Produce a useful first-pass answer. "
        "State assumptions and uncertainty. Do not claim to have taken actions or "
        "verified facts you have not verified.\n\nTASK:\n" + task
    )
    draft = ask(lead, draft_prompt, max_tokens)
    reviews = []
    for reviewer in reviewer_models:
        prompt = (
            "You are an independent reviewer. Critically review the lead draft. "
            "Identify factual risks, missing steps, weak logic, alternative approaches "
            "and specific improvements. Do not merely agree. If you cannot verify a "
            "claim, say so.\n\nTASK:\n" + task + "\n\nLEAD DRAFT:\n" + draft
        )
        try:
            reviews.append({"model": reviewer, "status": "completed",
                            "review": ask(reviewer, prompt, max_tokens)})
        except GatewayError as exc:
            reviews.append({"model": reviewer, "status": "failed", "review": str(exc)})

    review_text = "\n\n".join(
        f"REVIEWER {i} — {r['model']} ({r['status']}):\n{r['review']}"
        for i, r in enumerate(reviews, 1)
    )
    synthesis_prompt = (
        "You are the lead model completing a hybrid collaboration. Synthesize your "
        "draft and the independent reviews into one answer. Resolve disagreements "
        "explicitly, incorporate valid corrections, preserve unresolved dissent and "
        "state remaining uncertainty. Never claim external actions were performed.\n\n"
        f"TASK:\n{task}\n\nYOUR FIRST DRAFT:\n{draft}\n\n"
        f"INDEPENDENT REVIEWS:\n{review_text}\n\n"
        "Return the final answer followed by a short Review notes section."
    )
    final = ask(lead, synthesis_prompt, max_tokens)
    return {"task": task, "mode": "hybrid", "lead_model": lead,
            "reviewers": reviews, "final": final}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run AI-EMPIRE hybrid multi-model collaboration through OpenRouter.")
    parser.add_argument("task")
    parser.add_argument("--lead", help="Override lead model ID.")
    parser.add_argument("--reviewers", help="Comma-separated reviewer model IDs.")
    parser.add_argument("--max-tokens", type=int, default=1800)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    reviewers = ([x.strip() for x in args.reviewers.split(",") if x.strip()]
                 if args.reviewers else None)
    try:
        result = run_hybrid(args.task, lead_model=args.lead,
                            reviewer_models=reviewers, max_tokens=args.max_tokens)
    except (GatewayError, ValueError) as exc:
        print(f"AI-EMPIRE collaboration error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Lead: {result['lead_model']}")
        print("Reviewers:")
        for item in result["reviewers"]:
            print(f"- {item['model']}: {item['status']}")
        print("\n" + result["final"])


if __name__ == "__main__":
    main()
