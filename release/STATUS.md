# SafarMa + Belink AI — Release status

Version: **8.4.0 · V15**

Release code commit: `b75aaa23b6e4a054ba77567fe01b41fe51f2a4a8`

## Completed

- SafarMa remains the primary product identity; Belink AI remains its intelligence layer.
- The approved futuristic interface, Persian/English and RTL/LTR are preserved.
- The personal edition keeps the birthday opening for Sanaz and the optional Amir-and-Sanaz Trabzon preset.
- A separate general public/business edition starts directly with neutral travel onboarding and contains no birthday or personal-preset content.
- Public visitors are routed to a dedicated pilot pricing page rather than the personal plans path.
- Both editions use a unified V15 PWA cache with exact versioned assets and separate install manifests.
- Belink Commander supports manual connected analysis, contextual chat and transparent offline fallback.
- Pilot, Tour Leader, Visa Officer, Safety Analyst, Budget Controller and Concierge remain integrated.
- Trips, preferences and chat sessions are isolated per signed anonymous browser client.
- Private data endpoints require a valid signed `X-Belink-Client` token.
- Users can export local data plus their authenticated browser identity's server data as JSON.
- Complete deletion removes identified server preferences, trips and conversations before clearing local SafarMa data and caches.
- Export files never contain the OpenAI API key or the raw signed browser token.
- Date windows, budget totals, source claims and official evidence requirements are validated.
- Connected AI analysis requires explicit user action and has bounded turn limits.
- CSP, referrer and browser permissions restrictions are active.
- The production container runs as a non-root user and has an internal health check.
- Render Blueprint generates a persistent signing secret and uses `/ready` for deployment health.
- Frontend V15 CI passed JavaScript, both manifests, personal/public separation, PWA references, privacy controls and secret scans.
- Backend CI passed Python 3.11 and 3.13 tests, readiness smoke checks, production-verifier compilation and Docker production build.
- The V15 release bundle passed its secret scan, assembly and checksum workflow.

## Published frontend editions

Personal gift edition:

`https://kmswp7ms8t-arch.github.io/SafarMa/?v=15`

General public/business edition:

`https://kmswp7ms8t-arch.github.io/SafarMa/public.html?v=15`

Pilot pricing page:

`https://kmswp7ms8t-arch.github.io/SafarMa/pricing.html`

## Secure backend deployment

Repository Blueprint:

`https://render.com/deploy?repo=https://github.com/kmswp7ms8t-arch/SafarMa`

The hosting-account owner must authorize service creation and enter the server-side `OPENAI_API_KEY`. The Blueprint automatically supplies the database disk, CORS origin, production mode, generated session-signing secret, turn limits and readiness settings.

After Render returns the backend HTTPS URL, open the required edition once with:

Personal:

`https://kmswp7ms8t-arch.github.io/SafarMa/?v=15&api=https://YOUR-BACKEND-URL`

Public:

`https://kmswp7ms8t-arch.github.io/SafarMa/public.html?v=15&api=https://YOUR-BACKEND-URL`

The browser stores only the public backend URL and a signed anonymous client token. It never stores the OpenAI API key. Export data before clearing the browser or changing devices because this anonymous identity is device/browser-specific.
