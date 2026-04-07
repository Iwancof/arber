# Case 2 — Position reassessment

## Input
Inquiry kind: position_reassessment  
Decision action: existing_long_under_review  
Event: adverse litigation headline against held name

## Expected output
{
  "question_title": "Reassess held position after litigation update",
  "question_text": "A new adverse legal event may weaken the thesis for an existing long position. Using only the provided evidence and current forecast context, decide whether the position should be held, reduced, exited, or left pending for more information.",
  "required_output_schema": {
    "action": "hold|reduce|exit|wait|need_more_info",
    "reason_codes": ["legal_overhang", "thesis_intact", "magnitude_unclear", "insufficient_context"],
    "notes": "short rationale"
  },
  "acceptance_rules": [
    "Use only the supplied evidence and system state",
    "Do not rely on outside information",
    "Return need_more_info if the supplied context is insufficient"
  ],
  "sla_class": "normal"
}
