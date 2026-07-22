# SafarMa — Publish & Business Launch Handoff

## Final product decision

Keep the current approved design and product identity unchanged:

- Product name: **SafarMa | سفرِ ما**
- Positioning: personal/global AI travel-planning product
- Powered by: **Belink AI**
- Visual direction: current premium futuristic dark-blue/glassmorphism interface
- Brand characters: Belink Commander plus the six approved specialists
  - Belink Pilot
  - Belink Tour Leader
  - Belink Visa Officer
  - Belink Safety Analyst
  - Belink Budget Controller
  - Belink Concierge

Do not rename the product to “Belink AI Travel”. Belink AI is the intelligence layer inside SafarMa.

## Goal

Publish the current working version as a production-ready web app and prepare it for commercial launch without changing the approved design.

## Required deployment architecture

### Frontend
- Publish the approved SafarMa frontend as a static PWA.
- Keep Persian/English and RTL/LTR fully functional.
- Configure a custom domain and HTTPS.
- Set the runtime API base URL to the deployed backend.

### Backend
- Deploy `belink-ai-v2/backend` as a private server/container service.
- Run with `uv run python main.py`.
- Verify `/health` and `/ready`.
- Store all secrets as server-side environment variables only.
- Never place `OPENAI_API_KEY` in frontend code, GitHub Pages, mobile builds, or public repositories.

### Required production environment variables
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `ALLOWED_ORIGINS`
- `DATABASE_PATH`
- any provider keys used for travel research

## Functional acceptance checklist

Before launch, verify all of the following in both Persian and English:

1. Birthday/gift opening still works.
2. All questionnaire steps work.
3. Global destination recommendation completes.
4. Final result loads without JavaScript errors.
5. Visa and entry status shows its source and verification state.
6. Passport validity is compared with the entered expiry date.
7. Safety, weather, budget, flights, hotels, activities, videos, and traveller reviews render correctly.
8. Belink Commander explains the final decision.
9. Each Belink specialist appears in the correct section and keeps the approved role outfit.
10. Ask Belink AI chat works with the current trip context.
11. Missing or conflicting evidence is labelled as unknown/conditional; never fabricate certainty.
12. Shared links and Add to Home Screen work on iPhone.
13. No API key or secret is present in browser source, Git history, or network responses.
14. Mobile layout works on current iPhone and Android viewport sizes.

## Business launch — MVP offer

Start with three simple offers:

### Free Discovery
- basic questionnaire
- one recommended destination
- high-level budget and feasibility summary

### Premium AI Trip Plan
- full entry/passport analysis
- detailed budget
- daily itinerary
- hotel/flight search links
- alternatives and risk notes
- downloadable/shareable plan

### Human Concierge Add-on
- manual review by the team
- booking support
- itinerary adjustments
- customer support through WhatsApp/email

Do not implement complex subscriptions in the first release. Start with a one-time paid premium plan and concierge upsell, then add subscriptions only after real usage data exists.

## Business readiness checklist

- Add Terms of Use.
- Add Privacy Policy.
- Add travel-information disclaimer.
- Add refund/cancellation policy for paid plans.
- Add analytics and error monitoring with privacy-safe settings.
- Add support email and WhatsApp contact.
- Add a basic admin view for users, trips, usage, and failed AI requests.
- Configure OpenAI project usage alerts and spend limits.
- Create separate production and development API keys.
- Add rate limits and abuse protection.
- Log sources and timestamps for travel decisions.

## Launch sequence

1. Deploy backend to staging.
2. Connect staging frontend.
3. Run full mobile and bilingual QA.
4. Add production secret values.
5. Configure final custom domain and HTTPS.
6. Test one real trip end-to-end.
7. Enable the premium purchase flow.
8. Launch to a small invited group.
9. Review errors, AI cost, conversion, and user feedback.
10. Open public access only after the pilot is stable.

## Codex/developer instruction

Use this exact directive:

> Preserve the current approved SafarMa UI and Belink specialist character system. Do not redesign or rename the product. Complete production deployment, connect the existing frontend to the Belink AI backend, add secure server-side OpenAI configuration, run all tests, fix only functional or production-readiness issues, and prepare the MVP business launch described in this document. Never expose or commit secrets. Do not claim visa, passport, safety, price, or availability certainty without source evidence and timestamps.
