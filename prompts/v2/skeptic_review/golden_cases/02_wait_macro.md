# Case 2 — Wait due to macro / benchmark ambiguity

## Input
Forecast: hot CPI implies MSFT underperforms SPY

## Expected output
{
  "overall_assessment": "partially_agree",
  "confidence_adjustment": -0.10,
  "counterarguments": [
    {
      "code": "benchmark_shared_exposure",
      "severity": "high",
      "description": "SPY is also exposed to the same macro driver, reducing confidence in relative edge"
    },
    {
      "code": "macro_override",
      "severity": "medium",
      "description": "broad market dynamics may dominate idiosyncratic factor exposure"
    }
  ],
  "missing_evidence": ["no strong evidence that this symbol's factor loading is materially different from the benchmark"],
  "alternative_hypothesis": "benchmark_shared_exposure_limits_edge",
  "recommendation": "wait"
}
