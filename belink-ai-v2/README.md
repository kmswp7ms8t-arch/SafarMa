# Belink AI Travel Intelligence V2

Private bilingual Persian/English travel intelligence for Amir and Sanaz.

- Product: **SafarMa — powered by Belink AI**
- Orchestrator: **Belink Commander**
- Specialists: Pilot, Visa Officer, Safety Analyst, Budget Controller and Tour Leader
- Backend: FastAPI + OpenAI Agents SDK + SQLite
- Frontend: futuristic SafarMa PWA with contextual Commander chat and citation cards

## Local backend

```bash
cd backend
cp .env.example .env.local
uv sync --extra dev
uv run pytest
uv run python main.py --demo
PORT=8421 uv run python main.py
```

Health:

```bash
curl http://127.0.0.1:8421/health
curl http://127.0.0.1:8421/ready
```

## API

- `POST /api/belink-ai/analyze`
- `POST /api/belink-ai/chat`
- `GET|PUT|DELETE /api/belink-ai/memory`
- `GET /api/belink-ai/trips`
- `PUT /api/belink-ai/trips/{id}/feedback`
- `DELETE /api/belink-ai/trips/{id}`

## Trust boundary

- `feasible` requires critical entry, safety and route evidence.
- Unknown or conflicting official evidence downgrades the result.
- Live prices, route availability, visa rules and reviews are never invented.
- API keys stay server-side only.

## Deployment

1. Deploy the backend container.
2. Store `OPENAI_API_KEY` as a server secret.
3. Set `BELINK_CORS_ORIGINS` to the exact frontend origin.
4. Set the public backend URL in the frontend runtime config.
5. Keep GitHub Pages as a static frontend only.
