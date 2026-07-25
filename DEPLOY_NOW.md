# SafarMa + Belink AI — Production Deployment

SafarMa V15 is ready as two frontend editions: the personal gift edition for Amir and Sanaz, and a separate neutral public/business edition. The remaining external authorization is creating the hosted service inside the owner's Render account and adding the server-side OpenAI secret.

## 1. Deploy the backend

Open the Render Blueprint flow:

https://render.com/deploy?repo=https://github.com/kmswp7ms8t-arch/SafarMa

The root `render.yaml` deploys `belink-ai-v2/backend` as a non-root Docker service with:

- a persistent SQLite disk;
- `/ready` deployment health checks;
- production CORS for the GitHub Pages origin;
- a generated persistent `BELINK_SESSION_SECRET`;
- explicit AI and chat turn limits;
- request-size and rate limits.

When Render asks for a secret:

- `OPENAI_API_KEY`: add the SafarMa/Belink AI production key.

The Blueprint already supplies:

- `BELINK_CORS_ORIGINS=https://kmswp7ms8t-arch.github.io`
- `BELINK_AI_MODEL=gpt-5-mini`
- `BELINK_AI_MAX_TURNS=20`
- `BELINK_CHAT_MAX_TURNS=10`
- `BELINK_ENV=production`
- `BELINK_REQUIRE_AI=true`
- `BELINK_REQUIRE_SESSION_SECRET=true`

Never paste the OpenAI key into GitHub, HTML, JavaScript, localStorage, screenshots, issue comments or ordinary chat.

## 2. Verify the service

After deployment, Render returns an HTTPS URL similar to:

`https://safarma-belink-ai.onrender.com`

Verify:

- `/health` returns `status: ok`;
- `/health` reports `ai_connected: true`;
- `/health` reports `persistent_session_secret: true`;
- `/ready` returns `status: ready`;
- production docs are disabled;
- the service version is `0.4.0` or later.

## 3. Connect the required edition

Personal gift edition:

`https://kmswp7ms8t-arch.github.io/SafarMa/?v=15&api=https://YOUR-BACKEND-URL`

General public/business edition:

`https://kmswp7ms8t-arch.github.io/SafarMa/public.html?v=15&api=https://YOUR-BACKEND-URL`

The app stores only:

- the public backend URL;
- a signed anonymous browser identity;
- the user's local travel profile and language preference.

The OpenAI key never reaches the browser. Connected AI analysis runs only when the user presses the Belink Commander analysis button.

The connection badge shows one of these states:

- Belink AI connected;
- Server connected · offline AI;
- Secure offline core.

## 4. Run staging acceptance

Test in Persian and English:

1. Personal link retains the birthday opening and optional Trabzon preset.
2. Public link skips the birthday opening and starts with neutral onboarding.
3. Public link contains no Amir, Sanaz or personal Trabzon content.
4. Public plan links open `pricing.html`.
5. Every questionnaire step works.
6. Date validation and final destination result work.
7. Passport-expiry comparison works.
8. Visa and entry evidence include supported claims.
9. Safety evidence includes supported claims.
10. Route evidence and transit assumptions are displayed.
11. Budget components and contingency reconcile.
12. Specialist findings, source links and server timestamps render.
13. Ask Belink AI contextual chat works.
14. Two browsers produce isolated trips and conversations.
15. Data export downloads local and authenticated server data without the signed token.
16. Complete deletion removes server data before local identity and cache removal.
17. Failed server deletion preserves the client identity for retry.
18. Both manifests install to the correct edition on iPhone Add to Home Screen.
19. Missing, estimated or conflicting evidence never becomes a false confirmed result.
20. AI analysis does not run until the user explicitly presses the button.

## 5. Publish

Personal link for Sanaz:

`https://kmswp7ms8t-arch.github.io/SafarMa/?v=15`

Public/business link:

`https://kmswp7ms8t-arch.github.io/SafarMa/public.html?v=15`

Pilot pricing:

`https://kmswp7ms8t-arch.github.io/SafarMa/pricing.html`

Open the chosen app link once with the `api=` parameter on each pilot device. The backend URL remains saved on that device.

Before clearing Safari/Chrome data or changing devices, use **Export My Data**. The anonymous signed identity is device/browser-specific; it is not a multi-device account.

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
