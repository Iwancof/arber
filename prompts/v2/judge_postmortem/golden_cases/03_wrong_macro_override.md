# Case 3 — Wrong due to macro override

## Input
Forecast: stock outperforms benchmark after company news  
Realized 1d relative return: -0.024 during a broad market selloff

## Expected output
{
  "verdict": "wrong",
  "direction_correct": false,
  "magnitude_assessment": "overestimated",
  "failure_codes": ["direction_error", "macro_override", "counterargument_missed"],
  "lessons_learned": [
    "apply stronger macro-override penalties when idiosyncratic news competes with broad risk-off conditions"
  ],
  "source_quality_note": "the source itself was acceptable",
  "prompt_quality_note": "the prompt underweighted regime-level override risk"
}
