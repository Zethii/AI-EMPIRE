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
    skills_file = data.get("skills_file", "config/model_skills.json")
    if not isinstance(skills_file, str) or not skills_file.strip():
        raise ValueError("skills_file must be a non-empty path.")
    skills_path = Path(skills_file)
    if not skills_path.is_absolute():
        skills_path = ROOT / skills_path
    try:
        skills = json.loads(skills_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"Model skills file not found: {skills_path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid model skills JSON: {exc}") from None
    if not isinstance(skills, dict) or not isinstance(skills.get("models"), dict):
        raise ValueError("Model skills file must contain a models object.")
    data["model_skills"] = skills
    return data


def shared_skill_context(config: dict[str, Any], selected_models: list[str]) -> str:
    skills = config.get("model_skills", {})
    profiles = skills.get("models", {}) if isinstance(skills, dict) else {}
    lines = [
        "SHARED MODEL CAPABILITY REGISTRY (all participating models receive this):",
        str(skills.get("purpose", "Use these as capability guidance, not guarantees.")),
    ]
    for principle in skills.get("shared_principles", []) if isinstance(skills, dict) else []:
        lines.append(f"- Shared rule: {principle}")

    configured = config.get("models", {})
    seen: set[str] = set()
    for role, item in configured.items():
        if not isinstance(item, dict):
            continue
        model = item.get("model_id")
        if not isinstance(model, str) or model in seen:
            continue
        seen.add(model)
        profile = profiles.get(model, {})
        label = item.get("label") or profile.get("label") or role
        strengths = profile.get("strengths", []) if isinstance(profile, dict) else []
        focus = profile.get("review_focus", []) if isinstance(profile, dict) else []
        lines.append(
            f"- {label} ({model}) — strengths: {', '.join(strengths) or 'general model capabilities'}; "
            f"focus: {', '.join(focus) or 'provide an independent, evidence-aware perspective'}"
        )

    for model in selected_models:
        if model not in seen:
            profile = profiles.get(model, {})
            label = profile.get("label", model) if isinstance(profile, dict) else model
            strengths = profile.get("strengths", []) if isinstance(profile, dict) else []
            focus = profile.get("review_focus", []) if isinstance(profile, dict) else []
            lines.append(
                f"- Selected model {label} ({model}) — strengths: "
                f"{', '.join(strengths) or 'no repository profile; use general model capabilities'}; "
                f"focus: {', '.join(focus) or 'provide an independent, evidence-aware perspective'}"
            )
    return "\n".join(lines)


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

    model_context = shared_skill_context(config, [lead, *reviewer_models])
    draft_prompt = (
        "You are the lead model in AI-EMPIRE. Produce a useful first-pass answer. "
        "Use the shared capability registry to anticipate complementary review, but "
        "make your own evidence-based judgment. State assumptions and uncertainty. "
        "Do not claim to have taken actions or verified facts you have not verified.\n\n"
        f"{model_context}\n\nTASK:\n{task}"
    )
    draft = ask(lead, draft_prompt, max_tokens)
    reviews = []
    for reviewer in reviewer_models:
        prompt = (
            "You are an independent reviewer. Critically review the lead draft. "
            "Identify factual risks, missing steps, weak logic, alternative approaches "
            "and specific improvements. Do not merely agree. If you cannot verify a "
            "claim, say so. Use your model's listed strengths while considering the "
            "full registry so your review complements the other models.\n\n"
            f"{model_context}\n\nTASK:\n{task}\n\nLEAD DRAFT:\n{draft}"
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

    discussion: list[dict[str, str]] = []
    discussion_config = config.get("discussion", {})
    if isinstance(discussion_config, dict) and discussion_config.get("enabled", False):
        participants = [lead, *reviewer_models]
        for turn, participant in enumerate(participants, 1):
            prior_dialogue = "\n\n".join(
                f"{entry['model']} ({entry['status']}):\n{entry['contribution']}"
                for entry in discussion
            ) or "No one has spoken in the discussion yet. You are opening it."
            prompt = (
                "You are taking part in the AI-EMPIRE post-review discussion. All "
                "independent reviews are complete. Respond directly to the strongest "
                "points and disagreements in the reviews and any earlier discussion. "
                "Correct your own earlier claims if needed, distinguish evidence from "
                "assumptions, and identify what the final plan must resolve. Do not "
                "simply repeat your review.\n\n"
                f"{model_context}\n\nTASK:\n{task}\n\nLEAD DRAFT:\n{draft}\n\n"
                f"ALL INDEPENDENT REVIEWS:\n{review_text}\n\n"
                f"EARLIER DISCUSSION TURNS:\n{prior_dialogue}\n\n"
                f"Your turn: {turn} of {len(participants)}. Speak as {participant}."
            )
            try:
                contribution = ask(participant, prompt, max_tokens)
                status = "completed"
            except GatewayError as exc:
                contribution = str(exc)
                status = "failed"
            discussion.append({"model": participant, "status": status,
                               "contribution": contribution})

    discussion_text = "\n\n".join(
        f"DISCUSSION — {entry['model']} ({entry['status']}):\n{entry['contribution']}"
        for entry in discussion
    ) or "Discussion phase disabled."
    synthesis_prompt = (
        "You are the lead model completing a hybrid collaboration. Use the draft, "
        "all independent reviews and the post-review discussion to suggest a clear, "
        "actionable final plan. Resolve disagreements explicitly, incorporate valid "
        "corrections, preserve unresolved dissent, and state remaining uncertainty. "
        "Never claim external actions were performed.\n\n"
        f"{model_context}\n\nTASK:\n{task}\n\nYOUR FIRST DRAFT:\n{draft}\n\n"
        f"INDEPENDENT REVIEWS:\n{review_text}\n\n"
        f"POST-REVIEW DISCUSSION:\n{discussion_text}\n\n"
        "Return a suggested final plan with ordered steps, dependencies or decision "
        "points, risks, and a short section noting how model feedback was resolved."
    )
    final = ask(lead, synthesis_prompt, max_tokens)
    return {"task": task, "mode": "hybrid", "lead_model": lead,
            "reviewers": reviews, "discussion": discussion, "final": final}


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
        print("Individual model reviews:")
        for item in result["reviewers"]:
            print(f"\n--- {item['model']} ({item['status']}) ---")
            print(item["review"])
        if result.get("discussion"):
            print("\nPost-review model discussion:")
            for item in result["discussion"]:
                print(f"\n--- {item['model']} ({item['status']}) ---")
                print(item["contribution"])
        print(f"\n--- Suggested final plan by {result['lead_model']} ---\n")
        print(result["final"])


if __name__ == "__main__":
    main()
