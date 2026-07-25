# SafarMa | سفرِ ما

SafarMa is a bilingual travel-planning PWA powered by **Belink AI**. The approved product now has two separate entry points without changing its core visual identity.

## Published editions

### Personal gift edition

Created by Amir for Sanaz, with the birthday opening and optional Trabzon trip preset:

**https://kmswp7ms8t-arch.github.io/SafarMa/?v=15**

### General public/business edition

Neutral onboarding with no birthday or personal preset content:

**https://kmswp7ms8t-arch.github.io/SafarMa/public.html?v=15**

### Pilot pricing

**https://kmswp7ms8t-arch.github.io/SafarMa/pricing.html**

## Product architecture

- Frontend: bilingual GitHub Pages PWA.
- Intelligence layer: Belink Commander with Pilot, Tour Leader, Visa Officer, Safety Analyst, Budget Controller and Concierge.
- Backend: FastAPI + OpenAI Agents SDK + SQLite.
- Identity: signed anonymous browser client.
- Privacy: authenticated JSON export and complete scoped deletion.
- Trust boundary: missing or conflicting entry, passport, safety or route evidence cannot become a confirmed feasible result.
- AI usage: explicit user action only, with rate and turn limits.

## Connected AI deployment

The static PWA works in transparent offline mode. Real OpenAI-connected analysis requires the backend to be deployed from the repository's `render.yaml` and `OPENAI_API_KEY` to be stored only as a server-side hosting secret.

Render Blueprint:

**https://render.com/deploy?repo=https://github.com/kmswp7ms8t-arch/SafarMa**

See `DEPLOY_NOW.md` and `FINAL_PRODUCTION_STATUS.md` for the full verification and launch procedure.

## Install on iPhone

Open the required edition in Safari, tap **Share**, select **Add to Home Screen**, enable **Open as Web App**, and tap **Add**.

## نصب روی آیفون

نسخه موردنظر را در Safari باز کنید، Share را بزنید، **Add to Home Screen** را انتخاب کنید و سپس **Add** را بزنید.

No OpenAI API key or provider secret is stored in the public frontend or repository.
