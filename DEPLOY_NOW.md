# SafarMa + Belink AI — Production Deployment

SafarMa V16 is prepared as two frontend editions: a private personal gift edition and a neutral public/business edition. The public edition is launch-safe even before the connected AI backend is deployed: it hides technical setup prompts and keeps the built-in planner available.

The remaining external authorization is creating the hosted backend inside the owner's Render account and adding the server-side OpenAI secret.

## 1. Deploy the backend

Open the Render Blueprint flow:

`https://render.com/deploy?repo=https://github.com/kmswp7ms8t-arch/SafarMa`

The root `render.yaml` deploys `belink-ai-v2/backend` as a non-root Docker service with:

- a persistent SQLite disk;
- `/ready` deployment health checks;
- production CORS for the GitHub Pages origin;
- a generated persistent `BELINK_SESSION_SECRET`;
- explicit AI and chat turn limits;
- request-size and rate limits.

When Render asks for a secret, enter:

- `OPENAI_API_KEY`: the SafarMa/Belink AI production key.

The Blueprint already supplies the model, CORS, production mode, session-secret requirement, database path and safety limits.

Never paste the OpenAI key into GitHub, frontend files, localStorage, screenshots, issue comments or ordinary chat.

## 2. Verify the service

After deployment, Render returns an HTTPS URL similar to:

`https://safarma-belink-ai.onrender.com`

Verify:

- `/health` returns `status: ok`;
- `ai_connected` is `true`;
- `persistent_session_secret` is `true`;
- `/ready` returns `status: ready`;
- production docs are disabled;
- the service reports signed client isolation, export and deletion.

The repository includes a manual **Verify SafarMa V16 production** workflow and `scripts/verify-production.py`.

## 3. Connect the required edition

Personal gift edition:

`https://kmswp7ms8t-arch.github.io/SafarMa/?v=16&api=https://YOUR-BACKEND-URL`

General public/business edition:

`https://kmswp7ms8t-arch.github.io/SafarMa/public.html?v=16&api=https://YOUR-BACKEND-URL`

The browser stores only the public backend URL, a signed anonymous browser identity, and the local travel profile. The OpenAI key never reaches the browser. Connected analysis runs only after the user presses the Belink Commander button.

## 4. V16 staging acceptance

Test in Persian and English:

1. The personal link retains the birthday opening and optional Trabzon preset.
2. Personal pages contain `noindex` metadata.
3. The public link starts directly with neutral onboarding.
4. The public link has canonical, Open Graph, robots and sitemap metadata.
5. Without a backend, the public edition never asks ordinary visitors for a server URL.
6. Without a backend, connected-analysis buttons show a launch notice and the built-in result remains usable.
7. With a backend, the connection badge, final analysis and contextual chat work.
8. Every questionnaire step, date check and destination result works.
9. Visa, passport, safety, route and budget findings show evidence status correctly.
10. Two browsers produce isolated trips and conversations.
11. Export and complete deletion work without exposing the signed token.
12. Both manifests install to the correct edition on iPhone.
13. Missing, estimated or conflicting evidence never becomes a false confirmed result.
14. AI analysis never starts without explicit user action.

## 5. Publish

Personal link for Sanaz:

`https://kmswp7ms8t-arch.github.io/SafarMa/?v=16`

Public/business link:

`https://kmswp7ms8t-arch.github.io/SafarMa/public.html?v=16`

Pilot pricing:

`https://kmswp7ms8t-arch.github.io/SafarMa/pricing.html`

Search engines are directed to the public edition through `robots.txt`, `sitemap.xml` and canonical metadata. The personal edition remains accessible by direct link but is marked not to be indexed.

## Current architecture

- Frontend: GitHub Pages bilingual PWA with personal and public editions.
- Backend: FastAPI + OpenAI Agents SDK.
- Orchestrator: Belink Commander.
- Specialists: Pilot, Tour Leader, Visa Officer, Safety Analyst, Budget Controller, Concierge.
- Memory: per-client private SQLite records.
- Identity: signed anonymous browser token.
- Privacy controls: JSON export and complete deletion.
- Secrets: server only.
- AI usage: explicit user action, rate-limited and turn-limited.
