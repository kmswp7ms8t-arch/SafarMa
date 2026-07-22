# Belink AI Travel Intelligence V2

This branch is reserved for the connected Belink AI implementation. The complete reviewed source package is maintained as `Belink_AI_Travel_System_V2_Final.zip` in the project handoff.

## Implemented locally

- FastAPI backend with `/health`, `/ready`, `/api/belink-ai/analyze` and contextual `/api/belink-ai/chat`.
- Belink Commander orchestrating Pilot, Visa Officer, Safety Analyst, Budget Controller and Tour Leader.
- OpenAI Agents SDK hosted web research for connected mode.
- Deterministic offline mode that cannot return `feasible` when critical evidence is missing.
- Evidence models with validated clickable URLs, verification status, assumptions and unknowns.
- SQLite private preferences, trip history, feedback and conversation sessions.
- Strict configurable CORS, bounded requests, safe errors and prototype rate limiting.
- Futuristic bilingual SafarMa frontend with configurable backend URL, connected/offline status, contextual chat and citation cards.
- Dockerfile, environment template, tests and local eval harness.

## Verification completed

- Backend: 12 tests passed.
- Frontend: 41 tests passed.
- Offline evals: 3 cases passed.
- Standalone build: passed.
- `/health` and `/ready`: passed.

## Required server environment

- `OPENAI_API_KEY`
- `BELINK_AI_MODEL=gpt-5-mini`
- `BELINK_CORS_ORIGINS=<exact frontend origin>`
- `BELINK_AI_DATABASE=./data/belink_ai.sqlite3`
- `PORT=8421`

Never place an API key in GitHub, browser code, `config.js`, HTML, or localStorage.
