# Case 1 — Typical signal: earnings beat + guidance raise

## Input
Headline: Apple tops quarterly estimates and raises full-year revenue guidance  
Body: Apple reported fiscal second-quarter revenue above analyst expectations and raised its full-year revenue outlook, citing stronger iPhone demand and services growth.

## Expected output
{
  "schema_name": "event_record",
  "schema_version": "1.0.0",
  "events": [
    {
      "event_type": "corp_earnings_beat",
      "affected_assets": ["AAPL"],
      "direction_hint": "positive",
      "materiality": 0.74,
      "novelty": 0.63,
      "evidence_spans": [
        {"text": "reported fiscal second-quarter revenue above analyst expectations", "start": 63, "end": 126}
      ]
    },
    {
      "event_type": "corp_guidance_raise",
      "affected_assets": ["AAPL"],
      "direction_hint": "positive",
      "materiality": 0.80,
      "novelty": 0.71,
      "evidence_spans": [
        {"text": "raised its full-year revenue outlook", "start": 131, "end": 166}
      ]
    }
  ]
}
