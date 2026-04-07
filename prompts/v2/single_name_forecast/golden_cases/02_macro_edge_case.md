# Case 2 — Edge case: macro event with weak relative edge

## Input
Symbol: MSFT  
Benchmark: SPY  
Event:
{
  "event_type": "macro_inflation_hot",
  "affected_assets": ["SPY", "QQQ", "IWM"],
  "direction_hint": "negative",
  "materiality": 0.84,
  "novelty": 0.78,
  "evidence_spans": [
    {"text": "Consumer prices rose 0.5% in March, above consensus forecasts", "start": 0, "end": 61}
  ]
}

## Expected output
{
  "hypotheses": [
    {
      "code": "higher_rate_pressure_on_duration",
      "weight": 0.56,
      "description": "hot inflation can pressure long-duration growth equities and mildly weigh on MSFT relative to SPY"
    },
    {
      "code": "benchmark_shared_exposure_limits_edge",
      "weight": 0.44,
      "description": "the benchmark is also rate-sensitive, limiting any clean relative edge"
    }
  ],
  "selected_hypothesis": "higher_rate_pressure_on_duration",
  "rejected_hypotheses": ["benchmark_shared_exposure_limits_edge"],
  "counterarguments": [
    {"code": "benchmark_shared_exposure", "severity": "high"},
    {"code": "macro_override", "severity": "medium"}
  ],
  "risk_flags": ["macro_shared_exposure"],
  "evidence_refs": ["evidence_spans[0]"],
  "confidence_before": 0.60,
  "confidence_after": 0.56,
  "direction_hint": "negative",
  "horizons": {
    "1d": {
      "p_outperform": 0.44,
      "p_underperform": 0.56,
      "ret_q10": -0.015,
      "ret_q50": -0.003,
      "ret_q90": 0.010
    },
    "5d": {
      "p_outperform": 0.47,
      "p_underperform": 0.53,
      "ret_q10": -0.024,
      "ret_q50": -0.004,
      "ret_q90": 0.015
    }
  }
}
