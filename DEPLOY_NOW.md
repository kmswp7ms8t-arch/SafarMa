# SafarMa + Belink AI — Production Deployment

The code is ready. The only external approval is creating the hosted service and adding the server-side OpenAI secret.

## 1. Deploy the backend

Open the Render Blueprint flow:

https://render.com/deploy?repo=https://github.com/kmswp7ms8t-arch/SafarMa

The root `render.yaml` deploys `belink-ai-v2/backend` as a Docker service with a persistent SQLite disk.

When Render asks for environment variables:

- `OPENAI_API_KEY`: add the Belink AI production key as a secret.
- `BELINK_CORS_ORIGINS`: keep `https://kmswp7ms8t-arch.github.io` for the current frontend.
- `BELINK_AI_MODEL`: `gpt-5-mini`
- `BELINK_REQUIRE_AI`: `true`

Never paste the key into GitHub, HTML, JavaScript, localStorage, screenshots, or chat.

## 2. Verify the service

After deployment, Render returns a URL similar to:

`https://safarma-belink-ai.onrender.com`

Verify:

- `/health` returns `status: ok`
- `/ready` returns `status: ready`
- `ai_connected` is `true`

## 3. Connect the public app

Open the connected SafarMa entry point with the backend URL:

`https://kmswp7ms8t-arch.github.io/SafarMa/app.html?api=https://YOUR-BACKEND-URL`

The app stores only the public backend URL. It never stores the OpenAI key.

The small connection badge shows one of these states:

- Belink AI connected
- Server connected · offline AI
- Secure offline core

## 4. Run staging acceptance

Test in Persian and English:

1. Gift opening
2. All questionnaire steps
3. Final destination result
4. Passport expiry comparison
5. Visa and entry evidence
6. Safety evidence
7. Budget result
8. Specialist findings
9. Source links and timestamps
10. Ask Belink AI contextual chat
11. iPhone Safari Add to Home Screen
12. Missing evidence never becomes a false confirmed answer

## 5. Publish

After staging succeeds, share:

`https://kmswp7ms8t-arch.github.io/SafarMa/app.html`

The saved backend URL keeps the connection active on that device.

## Current architecture

- Frontend: GitHub Pages PWA
- Backend: FastAPI + OpenAI Agents SDK
- Orchestrator: Belink Commander
- Specialists: Pilot, Tour Leader, Visa Officer, Safety Analyst, Budget Controller, Concierge
- Memory: private server-side SQLite
- Secrets: server only
