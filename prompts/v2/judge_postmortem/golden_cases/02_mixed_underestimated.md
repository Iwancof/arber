# Case 2 — Mixed, underestimated move

## Input
Forecast: positive but moderate  
Realized 1d relative return: +0.041, above q90

## Expected output
{
  "verdict": "mixed",
  "direction_correct": true,
  "magnitude_assessment": "underestimated",
  "failure_codes": ["magnitude_underestimated"],
  "lessons_learned": [
    "widen upside tails for hard catalysts where mechanical repricing can dominate on day 1"
  ],
  "source_quality_note": "source quality was adequate",
  "prompt_quality_note": "the prompt captured direction but was too conservative on short-term magnitude"
}
