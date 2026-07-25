# SafarMa + Belink AI — Release status

Version: **8.5.0 · V16**

Release commit: `2775ac4b04278a90d35a7cc4489d2da930f7bc56`

## Completed

- SafarMa remains the primary product identity; Belink AI remains its intelligence layer.
- The approved futuristic interface, Persian/English and RTL/LTR are preserved.
- The personal edition retains the birthday opening and optional Amir-and-Sanaz Trabzon preset.
- The personal entry points are marked `noindex` so search engines are directed toward the business edition.
- The public/business edition has neutral onboarding, canonical metadata, Open Graph metadata, a search-engine policy and a sitemap.
- Public visitors do not see a technical backend-configuration prompt while the connected AI server is not deployed.
- Until the backend is connected, the public edition displays a launch-safe notice and keeps the built-in planner available.
- Technical GitHub support links are hidden from ordinary public users.
- The public pricing page remains visible, while charging users remains disabled pending commercial setup.
- Both editions use a unified V16 PWA cache with exact versioned assets and separate install manifests.
- Belink Commander, Pilot, Tour Leader, Visa Officer, Safety Analyst, Budget Controller and Concierge remain integrated.
- Connected analysis requires explicit user action and is rate- and turn-limited.
- Trips, preferences and chats remain isolated per signed anonymous browser identity.
- Privacy export and complete deletion remain available.
- No OpenAI secret or raw signed client token is embedded in public files.
- Production verification supports both V16 editions.
- Frontend V16 CI passed JavaScript, both manifests, sitemap XML, personal/public separation, SEO, launch-safe UX, privacy controls and secret scans.
- Backend CI passed Python 3.11 and 3.13 tests, readiness smoke checks, production-verifier compilation and Docker production build.
- The V16 release bundle passed secret scanning, assembly, checksums and independent ZIP verification.
- The verified release package contains 63 files excluding the checksum index.

## Frontend editions

Personal gift edition:

`https://kmswp7ms8t-arch.github.io/SafarMa/?v=16`

General public/business edition:

`https://kmswp7ms8t-arch.github.io/SafarMa/public.html?v=16`

Pilot pricing page:

`https://kmswp7ms8t-arch.github.io/SafarMa/pricing.html`

## Secure backend deployment

Repository Blueprint:

`https://render.com/deploy?repo=https://github.com/kmswp7ms8t-arch/SafarMa`

The hosting-account owner must authorize service creation and enter the server-side `OPENAI_API_KEY`. The Blueprint supplies the database disk, CORS origin, production mode, signing secret, rate limits, turn limits and readiness settings.

After Render returns the backend HTTPS URL, open the required edition once with:

Personal:

`https://kmswp7ms8t-arch.github.io/SafarMa/?v=16&api=https://YOUR-BACKEND-URL`

Public:

`https://kmswp7ms8t-arch.github.io/SafarMa/public.html?v=16&api=https://YOUR-BACKEND-URL`

The browser stores the public backend URL and a signed anonymous client token, never the OpenAI key.
