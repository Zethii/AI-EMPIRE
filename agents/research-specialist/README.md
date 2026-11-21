# Research Specialist

Analysis agent with optional public web search result snippets. Uses the shared OpenRouter gateway and Python standard library only.

## Capabilities and limits
- Without `--web`: analyzes your question and any `--notes` evidence only; outputs must label conclusions as preliminary if no evidence is provided.
- With `--web`: sends up to 5 search queries to DuckDuckGo HTML search and collects titles, links, and snippets. The model only receives snippets; it does not open or verify full pages. Search results may be incomplete, blocked, or change over time.
- The agent is read-only: it does not message anyone, publish, purchase, edit files, or run external actions.

## Run from the repo root
```sh
python3 agents/research-specialist/research_agent.py "gaming editor workflow tools"
```
Optional web search:
```sh
python3 agents/research-specialist/research_agent.py "gaming editor workflow tools" --web
```
Optional notes:
```sh
python3 agents/research-specialist/research_agent.py "gaming editor workflow tools" --web --notes "Source URL: https://example.org; excerpt: ..."
```
Options: `--searches 1-5`, `--results-per-query 1-10`, `--model provider/model-id`. No external Python dependencies.
