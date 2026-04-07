# Case 1 — Pre-trade decision

## Input
Inquiry kind: pretrade_decision  
Decision action: wait_manual  
Event: positive guidance raise  
Forecast: confidence near threshold with conflicting counterarguments

## Expected output
{
  "question_title": "Approve AAPL trade candidate?",
  "question_text": "A positive guidance event suggests a benchmark-relative edge, but the forecast is near the manual-review boundary and includes material 'already priced' risk. Using only the supplied event, evidence, and forecast, decide whether to approve, reject, or wait on this candidate.",
  "required_output_schema": {
    "decision": "approve|reject|wait|need_more_info",
    "reason_codes": ["already_priced", "clear_fundamental_repricing", "insufficient_context"],
    "notes": "short rationale"
  },
  "acceptance_rules": [
    "Use only the supplied evidence and forecast",
    "Do not browse externally",
    "If evidence is insufficient, return need_more_info"
  ],
  "sla_class": "fast"
}
