# Event Intelligence OS Prompt Refinement Pack v1

This pack contains revised prompt templates for the LLM stages used inside Event Intelligence OS.

Contents:
- `shared/official_taxonomy_and_calibration.md`
- `01_event_extract/`
- `02_single_name_forecast/`
- `03_skeptic_review/`
- `04_judge_postmortem/`
- `05_noise_classifier/`
- `06_inquiry_question_generator/`

Design goals:
1. Constrain event naming to a fixed taxonomy.
2. Increase signal/noise separation before expensive forecasting.
3. Make relative-return forecasts more mechanism-based and more calibrated.
4. Reduce confidence bunching around 0.50 by using explicit anchor bands.
5. Preserve v1 Policy Engine compatibility:
   - `confidence_after`
   - `horizons.1d.p_outperform`
   - `horizons.5d.p_outperform`
6. Keep JSON-only outputs and low implementation friction.

Recommended runtime notes:
- Use API-level structured outputs / JSON schema validation if available.
- Keep temperature low for extraction/classification tasks.
- Version prompts independently from code and schemas.
- Run golden cases in CI after every prompt change.
