# Case 3 — Routine / no-edge case

## Input
Symbol: JPM  
Benchmark: SPY  
Event:
{
  "event_type": "market_analyst_upgrade_material",
  "affected_assets": ["JPM"],
  "direction_hint": "positive",
  "materiality": 0.34,
  "novelty": 0.28,
  "evidence_spans": [
    {"text": "analyst upgraded shares to Buy", "start": 0, "end": 31}
  ]
}

## Expected output
{
  "hypotheses": [
    {
      "code": "analyst_note_supports_sentiment",
      "weight": 0.52,
      "description": "the note may help sentiment, but evidence of a durable benchmark-relative edge is limited"
    },
    {
      "code": "upgrade_is_weak_or_priced",
      "weight": 0.48,
      "description": "single-firm analyst actions often have weak persistence unless tied to new fundamental estimates"
    }
  ],
  "selected_hypothesis": "analyst_note_supports_sentiment",
  "rejected_hypotheses": ["upgrade_is_weak_or_priced"],
  "counterarguments": [
    {"code": "weak_magnitude", "severity": "high"},
    {"code": "already_priced", "severity": "medium"}
  ],
  "risk_flags": ["routine_update"],
  "evidence_refs": ["evidence_spans[0]"],
  "confidence_before": 0.54,
  "confidence_after": 0.51,
  "direction_hint": "positive",
  "horizons": {
    "1d": {
      "p_outperform": 0.51,
      "p_underperform": 0.49,
      "ret_q10": -0.008,
      "ret_q50": 0.001,
      "ret_q90": 0.009
    },
    "5d": {
      "p_outperform": 0.50,
      "p_underperform": 0.50,
      "ret_q10": -0.014,
      "ret_q50": 0.000,
      "ret_q90": 0.014
    }
  }
}
