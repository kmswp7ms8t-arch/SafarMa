# SafarMa + Belink AI — Release status

Version: **8.0.0 RC2**

## Completed

- SafarMa remains the primary product identity.
- Belink AI is the intelligence layer inside SafarMa.
- Persian/English and RTL/LTR are preserved.
- Public PWA is published on GitHub Pages.
- Belink Commander frontend supports connected and transparent offline modes.
- Backend code, specialist agents, persistence, health checks and Docker deployment are included.
- Render Blueprint and backend CI are included.
- The OpenAI key is not stored in the repository or browser.
- Frontend static smoke test passed.
- Backend tests and health smoke test passed locally.
- Public Pages V8 asset verification passed.

## Production URL

Frontend:

`https://kmswp7ms8t-arch.github.io/SafarMa/?v=8`

## Account-owner action still required

A hosting account must authorize creation of the backend service and store `OPENAI_API_KEY` as a server-side secret. Use the repository `render.yaml` Blueprint. After deployment, enter the resulting HTTPS URL in the in-app **Secure backend connection** panel, then set it permanently in `belink-runtime.js` after staging QA.
