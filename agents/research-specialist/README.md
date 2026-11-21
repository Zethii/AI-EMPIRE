# Research Specialist (MVP)

Model-backed, analysis-only terminal agent using the shared OpenRouter client.

## Important scope
This MVP **does not browse the web or collect sources**. If no evidence notes are provided, it must produce an explicitly preliminary, hypothesis-based analysis. It cannot contact people, publish, purchase, or change files.

## Run from repository root
```sh
python3 agents/research-specialist/research_agent.py "Research demand for a digital product targeting gaming editors"
```

Add evidence snippets or source links supplied by you:
```sh
python3 agents/research-specialist/research_agent.py "Research demand for gaming-editor tools" --notes "Source URL: ... Summary: ..."
```

Optional model override: `--model provider/model-name`. Credentials remain in local .env.
