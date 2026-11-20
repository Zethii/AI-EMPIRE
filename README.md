# AI-EMPIRE

AI-EMPIRE is a modular, multi-model AI workspace designed to coordinate AI providers and specialist agents.

## Principles
- Free-first: begin with free/open-source options and disclose costs.
- Provider-flexible: avoid lock-in to one AI provider.
- Human-controlled: approval before risky or irreversible actions.
- Secure: keep secrets out of Git and logs.
- Verifiable: distinguish planned, attempted, tested, and verified work.
- Incremental: build and test one phase at a time.

## Planned infrastructure (candidates, not installed)
| Component | Purpose | Status |
|---|---|---|
| GitHub | Code, docs, configuration and version history | Repository created |
| OpenRouter or direct provider APIs | Model gateway | Research pending |
| LibreChat | Unified chat interface | Research pending |
| n8n | Workflow automation | Research pending |
| PostgreSQL/Supabase | Shared task data and memory | Research pending |

## Planned divisions
- Digital Business
- YouTube & AI Media
- Gaming Content
- Software Development
- Research & Intelligence

## Roadmap
1. [x] Create repository
2. [ ] Foundation: docs, structure, safety, templates, model registry
3. [ ] Evaluate and configure model gateway
4. [ ] Configure unified interface
5. [ ] Build orchestrator and specialist agents
6. [ ] Add shared memory/database
7. [ ] Add automation workflows
8. [ ] Build dashboard
9. [ ] Test and expand

## Current state
**Phase:** 1 — Foundation  
**Status:** In progress

See [Project Status](docs/PROJECT_STATUS.md) and [Architecture](docs/ARCHITECTURE.md).

No runtime is implemented yet. When secrets are introduced, keep them in a local ignored environment file, never commit credentials.

This project is under development. Features are considered complete only after implementation and verification.
