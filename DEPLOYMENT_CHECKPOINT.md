# SafarMa Deployment Checkpoint

Saved on: 2026-07-26 (Qatar time)

## Current state

- SafarMa V16 frontend is published from GitHub Pages.
- Personal and public editions are separated.
- Render Blueprint validation issue with `maxShutdownDelaySeconds` was fixed.
- Render Blueprint now uses `autoDeployTrigger: commit`.
- The user is currently on Render's **Payment Information Required** screen on mobile.
- Render is requesting billing information because the Blueprint uses the paid Starter web service plus a persistent 1 GB disk.
- No card information has been shared in ChatGPT or stored in GitHub.

## Next action

1. In Render, choose the correct country/region for the card billing address.
2. Enter billing address and card details directly in Render/Stripe.
3. Tap **Add Card**.
4. Return to the Blueprint screen.
5. Enter `OPENAI_API_KEY` only in Render's secret field.
6. Deploy the Blueprint.
7. Send the final `https://...onrender.com` service URL back to ChatGPT for final connection and production verification.

## Security rule

Never paste card details or the OpenAI API key into chat, GitHub, screenshots, frontend files, or localStorage.
