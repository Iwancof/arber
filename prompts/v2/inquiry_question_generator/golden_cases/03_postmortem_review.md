# Case 3 — Postmortem review

## Input
Inquiry kind: postmortem_review  
Decision action: closed_trade_wrong  
Event + forecast + realized outcome available

## Expected output
{
  "question_title": "Confirm likely failure mode",
  "question_text": "The system believes this miss was primarily caused by a macro override rather than an extraction error. Using only the supplied forecast, evidence, and realized outcome summary, confirm the likely failure code or relabel it if needed.",
  "required_output_schema": {
    "label": "confirm_failure_code|relabel|insufficient",
    "failure_codes": ["macro_override", "source_noise", "benchmark_mismatch"],
    "notes": "short rationale"
  },
  "acceptance_rules": [
    "Use only the provided forecast, evidence, and realized outcome context",
    "Do not introduce external facts",
    "If the context is insufficient, return insufficient"
  ],
  "sla_class": "slow"
}
