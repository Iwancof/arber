# Case 1 — Moderate pushback

## Input
Forecast: strong positive forecast on earnings beat + guidance raise

## Expected output
{
  "overall_assessment": "partially_agree",
  "confidence_adjustment": -0.05,
  "counterarguments": [
    {
      "code": "already_priced",
      "severity": "medium",
      "description": "immediate post-headline repricing may absorb part of the upside"
    },
    {
      "code": "valuation_caps_upside",
      "severity": "medium",
      "description": "rich valuation can limit follow-through even when the event is positive"
    }
  ],
  "missing_evidence": ["no detail on the scale of the guidance revision versus buy-side expectations"],
  "alternative_hypothesis": "already_priced_mean_reversion",
  "recommendation": "reduce_size"
}
