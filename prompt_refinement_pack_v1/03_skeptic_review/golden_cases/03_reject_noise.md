# Case 3 — Reject noisy forecast

## Input
Forecast: strong long thesis based only on a single analyst upgrade headline

## Expected output
{
  "overall_assessment": "disagree",
  "confidence_adjustment": -0.15,
  "counterarguments": [
    {
      "code": "weak_magnitude",
      "severity": "high",
      "description": "single-note analyst actions rarely justify a high-confidence benchmark-relative edge"
    },
    {
      "code": "headline_without_primary_source",
      "severity": "high",
      "description": "the forecast appears to rely on a headline without deeper supporting evidence"
    }
  ],
  "missing_evidence": ["no estimate revision, target detail, or channel checks supporting the thesis"],
  "alternative_hypothesis": "upgrade_is_weak_or_priced",
  "recommendation": "reject"
}
