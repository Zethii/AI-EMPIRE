# Model Gateway Research — Initial Evaluation

**Research date:** 2026-11-20
**Status:** Candidate recommendation, not a production decision
**Budget target:** R0 for initial testing

## Candidate: OpenRouter

OpenRouter provides a unified API for multiple model providers, including free model variants. It is a promising gateway for early experiments because it reduces the need to build separate provider integrations first.

### Free-tier notes (verify again before use)
- Free model variants are priced at $0 per token, but rate-limited.
- Current free model variants have a reported cap of 20 requests per minute and 50 requests per day on a free account.
- The daily cap may increase to 1,000 requests/day after buying at least $10 in credits. We are not spending money to unlock this.
- Availability, model IDs, provider behavior, context limits, and feature support can change.
- Failed requests may consume free request quota.
- A generic free-model router can select among available models; this reduces model pinning and can make reproducibility harder.

## Preliminary decision

**Recommendation:** use OpenRouter as the first gateway candidate for a controlled API proof-of-concept, while keeping the system provider-neutral and preserving the ability to connect direct provider APIs later.

This is not yet a final decision. Before configuration, confirm:
1. Current free endpoints and model IDs.
2. API key creation and key security.
3. Request format and compatibility.
4. Tool/function calling support per model.
5. Streaming and structured output support where needed.
6. Free usage limits and failure behavior.
7. Data/privacy policies and retention implications.
8. Whether testing can remain within $0 without credit purchase.

## Test plan (not yet run)
- [ ] Account/API key readiness confirmed without sharing secrets.
- [ ] Make a simple text request to a selected free model.
- [ ] Record response, model ID, usage/limits, latency, and error behavior.
- [ ] Test a second free model independently.
- [ ] Verify structured output/tool support separately; don't assume all free models support it.
- [ ] Test bounded retry handling.
- [ ] Confirm API key is not exposed in repository, screenshots, or logs.

## Current conclusion
OpenRouter is the first gateway to test. No gateway has been installed, configured, or called from this repository yet. No API key has been created or stored here.

## Reference links
- OpenRouter free models: https://openrouter.ai/collections/free-models
- OpenRouter free router: https://openrouter.ai/openrouter/free
- Pricing and limits: https://openrouter.ai/pricing
- Support/free tier: https://openrouter.ai/support
