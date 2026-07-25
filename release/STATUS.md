# SafarMa + Belink AI — Release status

Version: **8.2.0 RC4 · V13**

Release code commit: `8ff2a1c9539896632b18dcd3ceb7ad16851ac7ed`

## Completed

- SafarMa remains the primary product identity; Belink AI remains its intelligence layer.
- The approved futuristic interface, birthday opening, Persian/English and RTL/LTR are preserved.
- Public PWA assets use a dedicated V13 cache and exact versioned URLs.
- Belink Commander supports manual connected analysis, contextual chat and transparent offline fallback.
- Pilot, Tour Leader, Visa Officer, Safety Analyst, Budget Controller and Concierge remain integrated.
- Trips, preferences and chat sessions are isolated per signed anonymous browser client.
- Private data endpoints require a valid signed `X-Belink-Client` token.
- The user can export local data plus the authenticated browser identity's server data as JSON.
- Complete deletion removes identified server preferences, trips and conversations before clearing local SafarMa data and caches.
- Failed server deletion preserves the local signed identity so deletion can be retried.
- Export files never contain the OpenAI API key or the raw signed browser token.
- No OpenAI secret or raw client token is embedded in public source files.
- Date windows, budget totals, source claims and official evidence requirements are validated.
- RC2 database migration and cross-client session ownership are protected by regression tests.
- Runtime API paths, `.env.local` loading and backend readiness behavior are corrected.
- Service-worker asset failures cannot return HTML as JavaScript.
- CSP, referrer and browser permissions restrictions are active.
- The production container runs as a non-root user and has an internal health check.
- Render Blueprint generates a persistent signing secret and uses `/ready` for deployment health.
- Connected AI analysis requires explicit user action and has bounded turn limits.
- Frontend CI validates JavaScript, manifest, CSP, V13 references, privacy controls and secret absence.
- Backend CI tests Python 3.11 and 3.13, API readiness, privacy isolation and Docker production build.

## Public frontend

`https://kmswp7ms8t-arch.github.io/SafarMa/?v=13`

## Secure backend deployment

Repository Blueprint:

`https://render.com/deploy?repo=https://github.com/kmswp7ms8t-arch/SafarMa`

The hosting-account owner must authorize service creation and enter the server-side `OPENAI_API_KEY`. The Blueprint automatically supplies the database disk, CORS origin, production mode, generated session-signing secret, turn limits and readiness settings.

After Render returns the backend HTTPS URL, open SafarMa once with:

`https://kmswp7ms8t-arch.github.io/SafarMa/?v=13&api=https://YOUR-BACKEND-URL`

The browser stores only the public backend URL and a signed anonymous client token. It never stores the OpenAI API key. Export data before clearing the browser or changing devices, because this anonymous identity is device/browser-specific.
