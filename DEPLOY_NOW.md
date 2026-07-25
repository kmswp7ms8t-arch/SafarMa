# SafarMa + Belink AI — Production Deployment

SafarMa RC4/V13 is ready for a private production pilot. The remaining external authorization is creating the hosted service inside the owner's Render account and adding the server-side OpenAI secret.

## 1. Deploy the backend

Open the Render Blueprint flow:

https://render.com/deploy?repo=https://github.com/kmswp7ms8t-arch/SafarMa

The root `render.yaml` deploys `belink-ai-v2/backend` as a non-root Docker service with:

- a persistent SQLite disk;
- `/ready` deployment health checks;
- production CORS for the current GitHub Pages origin;
- a generated persistent `BELINK_SESSION_SECRET`;
- explicit AI and chat turn limits;
- request-size and rate limits.

When Render asks for a secret:

- `OPENAI_API_KEY`: add the Belink AI production key.

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

## 3. Connect the public app

Open SafarMa once with the production backend URL:

`https://kmswp7ms8t-arch.github.io/SafarMa/?v=13&api=https://YOUR-BACKEND-URL`

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

1. Birthday gift opening.
2. Every questionnaire step.
3. Date validation and final destination result.
4. Passport-expiry comparison.
5. Visa and entry evidence with supported claims.
6. Safety evidence with supported claims.
7. Route evidence and transit assumptions.
8. Budget component totals and contingency.
9. Specialist findings, source links and server timestamps.
10. Ask Belink AI contextual chat.
11. Two browsers produce isolated trips and conversations.
12. Data export downloads local and authenticated server data without the signed token.
13. Complete deletion removes server data before local identity and cache removal.
14. Failed server deletion preserves the client identity for retry.
15. iPhone Safari Add to Home Screen.
16. Missing, estimated or conflicting evidence never becomes a false confirmed result.
17. AI analysis does not run until the user explicitly presses the button.

## 5. Publish the private pilot

After staging succeeds, share:

`https://kmswp7ms8t-arch.github.io/SafarMa/?v=13`

Open it once with the `api=` parameter on each pilot device. The backend URL remains saved on that device.

Before clearing Safari/Chrome data or changing devices, use **Export My Data**. The anonymous signed identity is device/browser-specific; it is not a multi-device account.

## Current architecture

- Frontend: GitHub Pages bilingual PWA.
- Backend: FastAPI + OpenAI Agents SDK.
- Orchestrator: Belink Commander.
- Specialists: Pilot, Tour Leader, Visa Officer, Safety Analyst, Budget Controller, Concierge.
- Memory: per-client private SQLite records.
- Identity: signed anonymous browser token.
- Privacy controls: JSON export and complete deletion.
- Secrets: server only.
- AI usage: explicit user action, rate-limited and turn-limited.
