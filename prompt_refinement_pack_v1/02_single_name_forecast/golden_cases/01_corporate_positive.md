# Case 1 — Corporate positive catalyst

## Input
Symbol: AAPL  
Benchmark: SPY  
Event:
{
  "event_type": "corp_guidance_raise",
  "affected_assets": ["AAPL"],
  "direction_hint": "positive",
  "materiality": 0.81,
  "novelty": 0.70,
  "evidence_spans": [
    {"text": "raised its full-year revenue outlook", "start": 0, "end": 35}
  ]
}

## Expected output
{
  "hypotheses": [
    {
      "code": "guidance_repricing",
      "weight": 0.70,
      "description": "higher guidance changes the forward earnings path and supports relative repricing vs SPY"
    },
    {
      "code": "already_priced_mean_reversion",
      "weight": 0.30,
      "description": "headline is positive but part of the move may already be reflected immediately"
    }
  ],
  "selected_hypothesis": "guidance_repricing",
  "rejected_hypotheses": ["already_priced_mean_reversion"],
  "counterarguments": [
    {"code": "already_priced", "severity": "medium"}
  ],
  "risk_flags": ["firm_specific_positive"],
  "evidence_refs": ["evidence_spans[0]"],
  "confidence_before": 0.72,
  "confidence_after": 0.67,
  "direction_hint": "positive",
  "horizons": {
    "1d": {
      "p_outperform": 0.64,
      "p_underperform": 0.36,
      "ret_q10": -0.011,
      "ret_q50": 0.009,
      "ret_q90": 0.026
    },
    "5d": {
      "p_outperform": 0.61,
      "p_underperform": 0.39,
      "ret_q10": -0.020,
      "ret_q50": 0.013,
      "ret_q90": 0.040
    }
  }
}
