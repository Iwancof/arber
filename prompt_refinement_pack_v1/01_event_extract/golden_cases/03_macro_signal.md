# Case 3 — Macro signal: hotter CPI

## Input
Headline: U.S. CPI rises 0.5% in March, above economist expectations  
Body: Consumer prices rose 0.5% in March from the prior month, above consensus forecasts, reinforcing expectations that the Fed may keep policy tighter for longer.

## Expected output
{
  "schema_name": "event_record",
  "schema_version": "1.0.0",
  "events": [
    {
      "event_type": "macro_inflation_hot",
      "affected_assets": ["SPY", "QQQ", "IWM"],
      "direction_hint": "negative",
      "materiality": 0.84,
      "novelty": 0.78,
      "evidence_spans": [
        {"text": "rose 0.5% in March from the prior month, above consensus forecasts", "start": 56, "end": 120}
      ]
    }
  ]
}
