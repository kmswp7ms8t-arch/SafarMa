# SafarMa + Belink AI — Release status

Version: **8.1.0 RC3**

Release commit: `82954ed0e3ad0eea86a6f5ba17e83c31a1bfa3ab`

## Completed

- SafarMa remains the primary product identity; Belink AI remains its intelligence layer.
- The approved futuristic interface, birthday opening, Persian/English and RTL/LTR are preserved.
- Public PWA assets are updated for the V11 release URL.
- Belink Commander supports connected analysis, contextual chat and transparent offline fallback.
- Pilot, Tour Leader, Visa Officer, Safety Analyst, Budget Controller and Concierge remain integrated.
- Trips, preferences and chat sessions are isolated per signed anonymous browser client.
- Private data endpoints require a valid signed `X-Belink-Client` token.
- No OpenAI secret or raw client token is embedded in public source files.
- Runtime API paths, `.env.local` loading and backend readiness behavior are corrected.
- Service-worker asset failures can no longer return HTML as JavaScript.
- CSP, referrer and browser permissions restrictions are active.
- The production container runs as a non-root user and has an internal health check.
- Render Blueprint generates a persistent signing secret and uses `/ready` for deployment health.
- Frontend CI passed JavaScript, manifest, CSP, asset-reference and secret scans.
- Backend CI passed on Python 3.11 and 3.13.
- API readiness smoke test passed.
- Docker production-image build passed.
- Cross-client data-isolation, authentication and trust-boundary tests passed.

## Public frontend

`https://kmswp7ms8t-arch.github.io/SafarMa/?v=11`

## Secure backend deployment

Repository Blueprint:

`https://render.com/deploy?repo=https://github.com/kmswp7ms8t-arch/SafarMa`

The hosting-account owner must authorize service creation and enter the server-side `OPENAI_API_KEY`. The Blueprint automatically supplies the database disk, CORS origin, production mode, generated session-signing secret and readiness settings.

After Render returns the backend HTTPS URL, open SafarMa once with:

`https://kmswp7ms8t-arch.github.io/SafarMa/?v=11&api=https://YOUR-BACKEND-URL`

The browser stores only the public backend URL and a signed anonymous client token. It never stores the OpenAI API key.
