# Prompt design review summary

This revision intentionally keeps the operational schema close to the current v1 pipeline while improving behavior in four ways:

1. Event names are constrained to a fixed taxonomy.
2. Headline-level noise gating is added before expensive forecasting.
3. Forecasting uses benchmark-relative, mechanism-based reasoning.
4. Skeptic and postmortem prompts use explicit checklists and calibration bands.

## Notable implementation recommendations
- Prefer API-level structured outputs and JSON schema validation when possible.
- Keep temperature low for extraction and noise classification.
- Add `benchmark_symbol` as an explicit variable to forecast prompts; default to SPY.
- Optionally pass `event_json` into `skeptic_review`.
- If event-type drift persists, embed 1-2 compact few-shot examples from the golden cases into the first user message for `event_extract` and `noise_classifier`.
